"""
bwproject contains the BWUser and BWProject classes
"""

import logging
import os
import requests

from bwexceptions import BrandwatchApiException

logger = logging.getLogger('bwapi.%s' % __name__)


class BWUser(object):
    """
    This class handles user-level tasks in the Brandwatch API, including authentication and
    HTTP requests.  For tasks which are bound to a project
    (e.g. working with queries or groups) use the subclass BWProject instead.

    Attributes:
        api_url:     Brandwatch API url.  All API requests will be appended to this url.
        oauthpath:  Path to append to the API url to get an access token.
        username:   Brandwatch username.
        password:   Brandwatch password.
        token:      Access token.
    """

    def __init__(self, token=None, token_path="tokens.txt", username=None, password=None,
                 grant_type="api-password", client_id="brandwatch-api-client",
                 api_url="https://newapi.brandwatch.com/"):
        """
        Creates a BWUser object.

        Args:
            username:   Brandwatch username.
            password:   Brandwatch password - Optional if you already have an access token.
            token:      Access token - Optional.
            token_path:  File path to the file where access tokens will be read from and
                         written to - Optional.  Defaults to tokens.txt, pass None to disable.
        """
        self.api_url = api_url
        self.oauthpath = "oauth/token"

        if token:
            self._update_by_test_auth(username, token)
            self._write_auth(token_path)
        elif username is not None and password is not None:
            self._update_by_auth(username, password, token_path, grant_type, client_id)
            self._write_auth(token_path)
        elif username is not None:
            self._read_auth(username, token_path)
        else:
            raise KeyError("Must provide valid token, username and password,"
                           " or username and path to token file")

    def _update_by_test_auth(self, username, token):
        """Update ``username`` and ``token`` (test)

        :param username: :class:`str`
        :param token: :class:`str`
        """
        user = requests.get("%sme" % self.api_url, params={"access_token": token}).json()

        if "username" in user:
            if username is None or user["username"] == username:
                self.username = user["username"]
                self.token = token
            else:
                raise KeyError("Username %s does not match provided token" % username, user)
        else:
            raise KeyError("Could not validate provided token", user)

    def _update_by_auth(self, username, password, token_path, grant_type, client_id):
        """Update ``username`` and ``token``

        :param username: :class:`str`
        :param password: :class:`str`
        :param token_path: :class:`str`
        :param grant_type: :class:`str`
        :param client_id: :class:`str`
        """
        token = requests.post(
            self.api_url + self.oauthpath,
            params={
                "username": username,
                "password": password,
                "grant_type": grant_type,
                "client_id": client_id
            }).json()
        if "access_token" in token:
            self.username = username
            self.token = token["access_token"]
        else:
            raise KeyError("Authentication failed", token)

    def _read_auth(self, username, token_path):
        user_tokens = self._read_auth_file(token_path)
        if username in user_tokens:
            self._update_by_test_auth(username, user_tokens[username])
        else:
            raise KeyError("Token not found in file: %s" % token_path)

    def _write_auth(self, token_path):
        if token_path is None:
            return

        user_tokens = self._read_auth_file(token_path)
        user_tokens[self.username.lower()] = self.token
        with open(token_path, "w") as token_file:
            token_file.write("\n".join(["\t".join(item) for item in user_tokens.items()]))

    def _read_auth_file(self, token_path):
        user_tokens = {}
        if os.path.isfile(token_path):
            with open(token_path) as token_file:
                for line in token_file:
                    try:
                        user, token = line.split()
                        user_tokens[user.lower()] = token
                    except ValueError:
                        pass
        return user_tokens

    def get_projects(self):
        """
        Gets a list of projects accessible to the user.

        Returns:
            List of dictionaries, where each dictionary is the information (name,
            id, clientName, timezone, ....) for one project.
        """
        response = self.request(verb=requests.get, address="projects")
        # FIXME: if no results, must we raise an exception?
        return response["results"] if "results" in response else response

    def get_self(self):
        """ Gets username and id """
        return self.request(verb=requests.get, address="me")

    def validate_query_search(self, **kwargs):
        """
        Checks a query search to see if it contains errors.  Same query debugging as
        used in the front end.

        Keyword Args:
            query: Search terms included in the query.
            language: List of the languages in which you'd like to test the query - Optional.

        Raises:
            KeyError: If you don't pass a search or if the search has errors in it.
        """
        if "query" not in kwargs:
            raise KeyError("Must pass: query = 'search terms'")
        if "language" not in kwargs:
            kwargs["language"] = ["en"]

        return self.request(verb=requests.get, address="query-validation", params=kwargs)

    def validate_rule_search(self, **kwargs):
        """
        Checks a rule search to see if it contains errors.  Same rule debugging as used in the front end.

        Keyword Args:
            query: Search terms included in the rule.
            language: List of the languages in which you'd like to test the query - Optional.

        Raises:
            KeyError: If you don't pass a search or if the search has errors in it.
        """
        if "query" not in kwargs:
            raise KeyError("Must pass: query = 'search terms'")
        if "language" not in kwargs:
            kwargs["language"] = ["en"]

        return self.request(verb=requests.get, address="query-validation/searchwithin", params=kwargs)

    def request(self, verb, address, params=None, data=None):
        """
        Makes a request to the Brandwatch API.

        Args:
            verb:       Type of request you want to make (e.g. 'requests.get').
            address:    Address to append to the Brandwatch API url.
            params:     Any additional parameters - Optional.
            data:       Any additional data - Optional.

        Returns:
            The response json
        """
        return BWUser.bare_request(verb=verb, address_root=self.api_url,
                                   address_suffix=address,
                                   access_token=self.token,
                                   params=params or dict(),
                                   data=data or dict())

    @staticmethod
    def bare_request(verb, address_root, address_suffix, access_token="",
                     params=None, data=None):
        """
        Makes a request to the Brandwatch API.

        Args:
            verb:           Type of request you want to make (e.g. 'requests.get').
            address_root:   In most cases this will the the Brandwatch API url, but we
                            leave the flexibility to change this for a different root
                            address if needed.
            address_suffix: Address to append to the root url.
            access_token:   Access token - Optional.
            params:         Any additional parameters - Optional.
            data:           Any additional data - Optional.

        Returns:
            The response json
        """
        params = params or dict()
        data = data or dict()
        url = "%s%s" % (address_root, address_suffix)

        if access_token:
            params["access_token"] = access_token

        try:
            if data:
                response = verb(url,
                                params=params,
                                data=data,
                                headers={"Content-type": "application/json"})
            else:
                response = verb(url, params=params)
            response_json = response.json()
        except Exception as e:
            logger.error("Something was wrong getting a response from "
                         "URL %s" % url)
            raise BrandwatchApiException(str(e))
        else:
            errors = response_json.get('errors')
            if errors:
                logger.error("There was an error with this "
                             "request: \n{}\n{}\n{}".format(response.url, data,
                                                            errors))
                raise BrandwatchApiException(errors)

            return response_json


class BWProject(BWUser):
    """
    This class is required for working with project-level resources, such as queries or groups.

    Attributes:
        project_name:       Brandwatch project name.
        project_id:         Brandwatch project id.
        project_address:    Path to append to the Brandwatch API url to make any project level calls.
    """

    def __init__(self, project, token=None, token_path="tokens.txt", username=None, password=None,
                 grant_type="api-password", client_id="brandwatch-api-client",
                 api_url="https://newapi.brandwatch.com/"):
        """
        Creates a BWProject object - inheriting directly from the BWUser class.

        Args:
            username:       Brandwatch username.
            project:        Brandwatch project name.
            password:       Brandwatch password - Optional if you already have an access token.
            token:          Access token - Optional.
            token_path:     File path to the file where access tokens will be read from and written to - Optional.
        """
        super(BWProject, self).__init__(token=token, token_path=token_path, username=username,
                                        password=password,
                                        grant_type=grant_type, client_id=client_id, api_url=api_url)
        self.project_name = ""
        self.project_id = -1
        self.project_address = ""
        self.get_project(project)

    def get_project(self, project):
        """
        Returns a dictionary of the project information (name, id, clientName, timezone, ....).

        Args:
            project:    Brandwatch project.
        """
        project_name = project

        try:
            # FIXME: project should be an integer or str, no both
            project_id = int(project)
        except ValueError:
            project_id = None

        try:
            # Find the first project occurrence
            project_found = next(p for p in self.get_projects() if p["id"] == project_id
                                 or p["name"] == project_name)
            # FIXME: use namedtuple instead? create a self.project = dict()?
            self.project_name = project_found["name"]
            self.project_id = project_found["id"]
            self.project_address = "projects/%s/" % self.project_id
        except StopIteration:
            logger.error("Project %s not found" % project)
            raise KeyError

    def get(self, endpoint, params=None):
        """
        Makes a project level GET request

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project
                        information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
        Returns:
            Server's response to the HTTP request.
        """
        params = params or dict()
        return self.request(verb=requests.get, address=self.project_address + endpoint,
                            params=params)

    def delete(self, endpoint, params=None):
        """
        Makes a project level DELETE request

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project
                        information is already included so you don't have to re-append that bit.
            params:     Additional parameters.

        Returns:
            Server's response to the HTTP request.
        """
        params = params or dict()
        return self.request(verb=requests.delete, address=self.project_address + endpoint,
                            params=params)

    def post(self, endpoint, params=None, data=None):
        """
        Makes a project level POST request

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project
                        information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        params = params or dict()
        data = data or dict()
        return self.request(verb=requests.post, address=self.project_address + endpoint,
                            params=params, data=data)

    def put(self, endpoint, params=None, data=None):
        """
        Makes a project level PUT request

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project
                        information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        params = params or dict()
        data = data or dict()
        return self.request(verb=requests.put, address=self.project_address + endpoint,
                            params=params, data=data)

    def patch(self, endpoint, params=None, data=None):
        """
        Makes a project level PATCH request

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project
                        information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        params = params or dict()
        data = data or dict()
        return self.request(verb=requests.patch, address=self.project_address + endpoint,
                            params=params, data=data)
