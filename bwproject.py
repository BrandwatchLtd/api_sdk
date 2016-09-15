"""
bwproject contains the BWUser and BWProject classes
"""

import os
import requests
import time


class BWUser:
    """
    This class handles user-level tasks in the Brandwatch API, including authentication and HTTP requests.  For tasks which are bound to a project
    (e.g. working with queries or groups) use the subclass BWProject instead. 

    Attributes:
        apiurl:     Brandwatch API url.  All API requests will be appended to this url.
        oauthpath:  Path to append to the API url to get an access token.
        username:   Brandwatch username.
        password:   Brandwatch password.
        token:      Access token.
    """
    def __init__(self, token=None, token_path="tokens.txt", username=None, password=None, console_report=True, grant_type="api-password", client_id="brandwatch-api-client"):
        """
        Creates a BWUser object.

        Args:
            username:   Brandwatch username.
            password:   Brandwatch password - Optional if you already have an access token.
            token:      Access token - Optional.
            token_path:  File path to the file where access tokens will be read from and written to - Optional.  Defaults to tokens.txt, pass None to disable.
        """
        self.apiurl = "https://newapi.brandwatch.com/"
        self.oauthpath = "oauth/token"
        self.console_report = console_report

        if token:
            self.username, self.token = self._test_auth(username, token)
            if token_path is not None:
                self._write_auth(token_path)
        elif username is not None and password is not None:
            self.username, self.token = self._get_auth(username, password, token_path, grant_type, client_id)
            if token_path is not None:
                self._write_auth(token_path)
        elif username is not None:
            self.username, self.token = self._read_auth(username, token_path)
        else:
            raise KeyError("Must provide valid token, username and password, or username and path to token file")

    def _test_auth(self, username, token):
        user = requests.get(self.apiurl + "me", params={"access_token": token}).json()
        if "username" in user:
            if username is None:
                return user["username"], token
            elif user["username"] == username:
                return username, token
            else:
                raise KeyError("Username " + username + " does not match provided token", user)
        else:
            raise KeyError("Could not validate provided token", user)

    def _get_auth(self, username, password, token_path, grant_type, client_id):
        token = requests.get(
            self.apiurl + self.oauthpath,
            params={
                "username": username,
                "password": password,
                "grant_type": grant_type,
                "client_id": client_id
            }).json()
        if "access_token" in token:
            return username, token["access_token"]
        else:
            raise KeyError("Authentication failed", token)

    def _read_auth(self, username, token_path):
        user_tokens = self._read_auth_file(token_path)
        if username in user_tokens:
            return self._test_auth(username, user_tokens[username])
        else:
            raise KeyError("Token not found in file: " + token_path)

    def _write_auth(self, token_path):
        user_tokens = self._read_auth_file(token_path)
        user_tokens[self.username] = self.token
        with open(token_path, "w") as token_file:
            token_file.write("\n".join(["\t".join(item) for item in user_tokens.items()]))

    def _read_auth_file(self, token_path):
        user_tokens = {}
        if os.path.isfile(token_path):
            with open(token_path) as token_file:
                for line in token_file:
                    try:
                        user, token = line.split()
                    except ValueError:
                        pass

                    user_tokens[user] = token       
        return user_tokens

    def get_projects(self):
        """
        Gets a list of projects accessible to the user.

        Returns:
            List of dictionaries, where each dictionary is the information (name, id, clientName, timezone, ....) for one project.
        """
        response = self.request(verb=requests.get, address="projects")
        return response["results"] if "results" in response else response

    def get_self(self):
        """ Gets username and id """
        return self.request(verb=requests.get, address="me")

    def validate_query_search(self, **kwargs):
        """
        Checks a query search to see if it contains errors.  Same query debugging as used in the front end.

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

        valid_search = self.request(verb=requests.get, address="query-validation", params=kwargs)
        if valid_search["errors"]:
            raise KeyError("Search string error: ", valid_search["errors"])

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

        valid_search = self.request(verb=requests.get, address="query-validation/searchwithin", params=kwargs)
        if valid_search["errors"]:
            raise KeyError("Search string error: ", valid_search["errors"])

    def request(self, verb, address, params={}, data={}):
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
        return self.bare_request(verb=verb, address_root=self.apiurl, address_suffix=address, access_token=self.token,
                                 params=params, data=data)

    def bare_request(self, verb, address_root, address_suffix, access_token="", params={}, data={}):
        """
        Makes a request to the Brandwatch API.

        Args:
            verb:           Type of request you want to make (e.g. 'requests.get').
            address_root:   In most cases this will the the Brandwatch API url, but we leave the flexibility to change this for a different root address if needed.
            address_suffix: Address to append to the root url.
            access_token:   Access token - Optional.
            params:         Any additional parameters - Optional.
            data:           Any additional data - Optional.

        Returns:
            The response json
        """
        time.sleep(.5)
        if access_token:
            params["access_token"] = access_token

        if data == {}:
            response = verb(address_root + address_suffix, params=params)
        else:
            response = verb(address_root + address_suffix,
                            params=params,
                            data=data,
                            headers={"Content-type": "application/json"})

        if "errors" in response.json() and response.json()["errors"] and self.console_report:
            print(response.json())

        # printing the response url can be helpful for debugging purposes
        if self.console_report:
            print(response.url)

        return response.json()


class BWProject(BWUser):
    """
    This class is required for working with project-level resources, such as queries or groups.

    Attributes:
        project_name:       Brandwatch project name.
        project_id:         Brandwatch project id.
        project_address:    Path to append to the Brandwatch API url to make any project level calls.
        console_report:     Boolean flag to control console reporting.  It defaults to True, so set to False if you do not want console reporting.  
    """
    def __init__(self, project, token=None, token_path="tokens.txt", username=None, password=None, console_report=True, grant_type="api-password", client_id="brandwatch-api-client"):
        """
        Creates a BWProject object - inheriting directly from the BWUser class.

        Args:
            username:       Brandwatch username.
            project:        Brandwatch project name.
            password:       Brandwatch password - Optional if you already have an access token.
            token:          Access token - Optional.
            token_path:     File path to the file where access tokens will be read from and written to - Optional.
            console_report: Boolean flag to control console reporting.  It defaults to True, so set to False if you do not want console reporting.  
        """
        super().__init__(token=token, token_path=token_path, username=username, password=password,
                         console_report=console_report, grant_type=grant_type, client_id=client_id)
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
        projects = self.get_projects()
        project_found = False

        try:
            int(project)
            numerical = True
        except:
            numerical = False

        for p in projects:
            found = False
            if numerical:
                if p["id"] == int(project):
                    found = True
            else:
                if p["name"] == project:
                    found = True
            if found:
                self.project_name = p["name"]
                self.project_id = p["id"]
                self.project_address = "projects/" + str(self.project_id) + "/"
                project_found = True
                break

        if not project_found:
            raise KeyError("Project " + project + " not found")

    def get(self, endpoint, params={}):
        """ 
        Makes a project level GET request 

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project information is already included so you don't have to re-append that bit.
            params:     Additional parameters.

        Returns:
            Server's response to the HTTP request.
        """
        return self.request(verb=requests.get, address=self.project_address + endpoint, params=params)

    def delete(self, endpoint, params={}):
        """ 
        Makes a project level DELETE request 

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project information is already included so you don't have to re-append that bit.
            params:     Additional parameters.

        Returns:
            Server's response to the HTTP request.
        """
        return self.request(verb=requests.delete, address=self.project_address + endpoint, params=params)

    def post(self, endpoint, params={}, data={}):
        """ 
        Makes a project level POST request 

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        return self.request(verb=requests.post, address=self.project_address + endpoint, params=params, data=data)

    def put(self, endpoint, params={}, data={}):
        """ 
        Makes a project level PUT request 

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        return self.request(verb=requests.put, address=self.project_address + endpoint, params=params, data=data)

    def patch(self, endpoint, params={}, data={}):
        """ 
        Makes a project level PATCH request 

        Args:
            endpoint:   Path to append to the Brandwatch project API url. Warning: project information is already included so you don't have to re-append that bit.
            params:     Additional parameters.
            data:       Additional data.

        Returns:
            Server's response to the HTTP request.
        """
        return self.request(verb=requests.patch, address=self.project_address + endpoint, params=params, data=data)
