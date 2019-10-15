"""
bwresources contains the BWMentions, BWQueries, BWGroups, BWRules, BWTags, BWCategories, BWSiteLists, BWAuthorLists, BWLocationLists, and BWSignals classes.
"""

import json
from . import filters
from . import bwdata
import logging


logger = logging.getLogger("bcr")


class AmbiguityError(ValueError):
    """Simple class to make errors when handling resource IDs more clear"""

    pass


class BWResource:
    """
    This class is a superclass for brandwatch resources (queries, groups, mentions, tags, sitelists, authorlists, locationlists and signals).

    Attributes:
        project:        Brandwatch project.  This is a BWProject object.
        names:            Query names, organized in a dictionary of the form {query1id: query1name, query2id: query2name, ...}
    """

    def __init__(self, bwproject):
        """
        Creates a BWResource object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        self.project = bwproject
        self.names = {}
        self.reload()

    def reload(self):
        """
        Refreshes names and ids.

        This function is used internally after editing any resource (e.g. uploading) so that our local copy of the id information matches the system's.
        The only potential danger is that someone else is editing a resource at the same time you are - in which case your local copy could differ from the system's.
        If you fear this has happened, you can call reload() directly.

        Raises:
            KeyError: If there was an error with the request for resource information.
        """
        response = self.project.get(endpoint=self.general_endpoint)

        if "results" not in response:
            raise KeyError("Could not retrieve" + self.resource_type, response)

        self.names = {
            resource["id"]: resource["name"] for resource in response["results"]
        }

    def get_resource_id(self, resource=None):
        """Takes in a resource ID or name and returns the resource ID. Raises an error if an ambiguous name is provided (e.g. if user calls this function with 'Query1' and there is actually a query and a logo query with that name)
        """
        if not resource:
            return (
                ""
            )  # return empty string rather than none to avoid stringified "None" becoming part of the url of an API call
        if isinstance(resource, int):
            if resource not in self.names.keys():
                raise KeyError(
                    "Could not find the resource ID {} in the project".format(resource)
                )
            resource_id = resource
        elif isinstance(resource, str):
            entries = [
                resource_id
                for resource_id, name in self.names.items()
                if name == resource
            ]
            if len(entries) > 1:
                raise AmbiguityError(
                    "The resource name {} is ambiguous: {}".format(resource, entries)
                )
            if entries:
                return entries[0]
            else:
                try:
                    resource_id = int(resource)
                except ValueError:
                    raise KeyError(
                        "Could not find the resource name {} in the project".format(
                            resource
                        )
                    )
        if resource_id not in self.names.keys():
            raise KeyError(
                "Could not find the resource ID {} in the project".format(resource)
            )
        if resource_id:
            return resource_id

    def check_resource_exists(self, resource):
        try:
            self.get_resource_id(resource)
            return True
        # Check the type of error
        # Key errors relate to the resource not being present, if KeyError return False, because the resource doesn't exist
        # If there's a ValueError, we want that still to be raised, because it means the resource name is ambiguous, and we want to raise that
        except AmbiguityError:
            raise
        except KeyError:
            return False

    def get(self, name=None):
        """
        If you specify an ID, this function will retrieve all information for that resource as it is stored in Brandwatch.
        If you specify a name, this will be mapped to the appropriate ID. An error will be raised if there are two IDs with the name specified.
        If you do not pass anything in with the `name` argument, this function will retrieve all information for all resources of that type as they are stored in Brandwatch.

        Args:
            name: ID or name of the resource that you'd like to retrieve - Optional.  If you do not specify an ID, all resources of that type will be retrieved.

        Raises:
            KeyError:   If you specify a resource ID and the resource does not exist.

        Returns:
            All information for the specified resource, or a list of information on every resource of that type in the account.
        """
        id_num = self.get_resource_id(resource=name)
        return self.project.get(endpoint=self.specific_endpoint + "/" + str(id_num))

    def upload(self, create_only=False, modify_only=False, **kwargs):
        """
        Uploads a resource.

        Args:
            create_only:    If True and the resource already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:    If True and the resource does not exist, no action will be triggered - Optional.  Defaults to False.
            kwargs:         Keyword arguments for resource information.  Error handling is handeled in the child classes.

        Returns:
            The uploaded resource information in a dictionary of the form {resource1name: resource1id}

        """
        return self.upload_all([kwargs], create_only, modify_only)

    def upload_all(self, data_list, create_only=False, modify_only=False):
        """
        Uploads a list of resources.

        Args:
            data_list:      List of data for each resource. Error handling is handeled in the child classes.
            create_only:    If True and the query already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:    If True and the query does not exist, no action will be triggered - Optional.  Defaults to False.

        Returns:
            The uploaded resource information in a dictionary of the form {resource1name: resource1id, resource2name: resource2id, ...}
        """
        resources = {}

        for data in data_list:
            # eventually make _fill_data() a BWResource func
            filled_data = self._fill_data(data)
            name = data["name"]

            if self.check_resource_exists(name) and not create_only:
                resource_id = self.get_resource_id(name)
                response = self.project.put(
                    endpoint=self.specific_endpoint + "/" + str(resource_id),
                    data=filled_data,
                )
            elif (
                not self.check_resource_exists(name) and not modify_only
            ):  # if resource does not exist
                response = self.project.post(
                    endpoint=self.specific_endpoint, data=filled_data
                )
            else:
                continue

            logger.info("Uploading {} {}".format(self.resource_type, response["name"]))
            resources[response["name"]] = response["id"]

        self.reload()
        return resources

    def rename(self, name, new_name):
        """
        Renames an existing resource.

        Args:
            name:       Name of existing resource.
            new_name:   New name for the resource.

        Raises:
            KeyError:   If the resource does not exist.
        """
        if not self.check_resource_exists(name):  # if the resource does not exist
            raise KeyError(
                "Cannot rename a " + self.resource_type + " which does not exist", name
            )
        else:
            info = self.get(
                name=name
            )  # will raise error if ambiguous name provided, so we should be okay to provide a name from this point forward (it won't be ambiguous if we get past this stage)
            info.pop("name")
            self.upload(name=name, new_name=new_name, **info)

    def delete(self, name):
        """
        Deletes a resource.

        Args:
            name:   Name of the resource that you'd like to delete.
        """
        self.delete_all([name])

    def delete_all(self, names):
        """
        Deletes a list of resources.

        Args:
            names:   A list of the names of the queries that you'd like to delete.
        """
        resource_ids = [self.get_resource_id(x) for x in names]

        for resource_id in resource_ids:
            if resource_id in self.names.keys():
                self.project.delete(
                    endpoint=self.specific_endpoint + "/" + str(resource_id)
                )
                logger.info(
                    "{} {} deleted".format(self.resource_type, self.names[resource_id])
                )

        self.reload()

    def _fill_data():
        raise NotImplementedError


class BWQueries(BWResource, bwdata.BWData):
    """
    This class provides an interface for query level operations within a prescribed project (e.g. uploading, downloading, renaming, downloading a list of mentions).

    Attributes:
        tags:           All tags in the project - handeled at the class level to prevent repetitive API calls.  This is a BWTags object.
        categories:     All categories in the project - handeled at the class level to prevent repetitive API calls.  This is a BWCategories object.
    """

    general_endpoint = "queries"
    specific_endpoint = "queries"
    resource_type = "queries"
    resource_id_name = "queryId"

    def __init__(self, bwproject):
        """
        Creates a BWQueries object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        super(BWQueries, self).__init__(bwproject)
        self.tags = BWTags(self.project)
        self.categories = BWCategories(self.project)

    def upload(self, create_only=False, modify_only=False, **kwargs):
        """
        Uploads a query.

        Args:
            name: Query name
            booleanQuery: Query boolean (e.g. "cat AND dog")
            startDate: Date for query data to be collected from (equivalent to backfill_date in Analytics SDK)
            contentSources: Optional, defaults to same sources in UI
            description: Optional, defaults to empty string (e.g. "a query to find mentions about cats and dogs")
            languages: Optional, defaults to en. Pass in None to make the query language agnostic
            monitor_sample_percentage: Optional, defaults to 100 (percent)
            query_type: Optional, defaults to 'monitor'

        Raises:
            KeyError: If you do not pass name and booleanQuery for each query in the data_list.

        Returns:
            The uploaded query information in a dictionary of the form {query1name: query1id}
        """
        return self.upload_all([kwargs], create_only, modify_only)

    def upload_all(self, data_list, create_only=False, modify_only=False):
        """
        Uploads multiple queries.

        Args:
            name: Query name
            booleanQuery: Query boolean (e.g. "cat AND dog")
            startDate: Date for query data to be collected from (equivalent to backfill_date in Analytics SDK)
            contentSources: Optional, defaults to same sources in UI
            description: Optional, defaults to empty string (e.g. "a query to find mentions about cats and dogs")
            languages: Optional, defaults to en. Pass in None to make the query language agnostic
            monitor_sample_percentage: Optional, defaults to 100 (percent)
            query_type: Optional, defaults to 'monitor'

        Raises:
            KeyError: If you do not pass name and booleanQuery for each query in the data_list.

        Returns:
            The uploaded query information in a dictionary of the form {query1name: query1id, query2name: query2id, ...}
        """

        queries = super(BWQueries, self).upload_all(
            data_list, create_only=False, modify_only=False
        )

        return queries

    def rename(self, name, new_name):
        """
        Renames an existing resource.

        Args:
            name:       Name of existing resource.
            new_name:   New name for the resource.

        Raises:
            KeyError:   If the resource does not exist.
        """
        if not self.check_resource_exists(name):
            raise KeyError(
                "Cannot rename a " + self.resource_type + " which does not exist", name
            )
        else:
            info = self.get(name=name)
            info.pop("name")
            if info["type"] == "search string":
                self.upload(name=name, new_name=new_name, **info)
            else:
                raise KeyError(
                    "We cannot support automated renaming of channels at this time."
                )

    def get_mention(self, **kwargs):
        """
        Retrieves a single mention by url or resource id.
        This is ONLY a valid function for queries (not groups), which is why it isn't split out into bwdata.
        Note: Clients do not have access to full Twitter mentions through the API because of our data agreement with Twitter.

        Args:
            kwargs:     You must pass in name (query name), and either url or resourceId.

        Raises:
            KeyError:   If the mentions call fails.

        Returns:
            A single mention.
        """
        params = self._fill_mention_params(kwargs)
        resource_id = self.get_resource_id(kwargs["name"])
        mention = self.project.get(
            endpoint="query/" + str(resource_id) + "/mentionfind", params=params
        )

        if "errors" in mention:
            raise KeyError("Mentions GET request failed", mention)
        return mention["mention"]

    def _name_to_id(self, attribute, setting):
        if isinstance(setting, int):
            return setting

        elif isinstance(setting, list):
            try:
                return [int(i) for i in setting]
            except ValueError:
                pass

        if attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            ids = []
            for category in setting:
                parent = category
                children = setting[category]
                for child in children:
                    ids.append(self.categories.ids[parent]["children"][child])
            return ids

        elif attribute in [
            "parentCategory",
            "xparentCategory",
            "parentCategories",
            "categories",
        ]:
            # plural included for get_charts syntax
            # note: parentCategories and categories params will be ignored for everything but chart calls
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            # plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.get_resource_id(s))
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in [
            "locationGroup",
            "xlocationGroup",
            "authorLocationGroup",
            "xauthorLocationGroup",
        ]:
            locationlists = BWLocationLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(locationlists.get(s)["id"])
            return ids

        elif attribute in ["siteGroup", "xsiteGroup"]:
            sitelists = BWSiteLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(sitelists.get(s)["id"])
            return ids

        else:
            return setting

    def _fill_data(self, data):

        default_content_sources = [
            "qq",
            "news",
            "youtube",
            "forum",
            "twitter",
            "review",
            "facebook",
            "reddit",
            "tumblr",
            "instagram",
            "blog",
        ]

        filled = dict()

        if ("name" not in data) or ("booleanQuery" not in data):
            raise KeyError("Need name and booleanQuery to post query", data)

        filled["booleanQuery"] = data["booleanQuery"]

        # if resource exists, create value for filled['id']
        if self.check_resource_exists(data["name"]):
            filled["id"] = self.get_resource_id(data["name"])
        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:  # if resource doesn't exist, add name to filled dictionary
            filled["name"] = data["name"]

        # params with default values
        filled["type"] = data.get("query_type", "monitor")
        filled["contentSources"] = data.get("contentSources", default_content_sources)
        filled["monitorSamplePercentage"] = data.get("monitorSamplePercentage", 100)
        filled["description"] = data.get("description", "")
        # currently languages field defaults to 'en', similar to UI, but it could alternatively default to False, to create a language agnostic query
        filled["languages"] = data.get(
            "languages", "en"
        )  # BUG: Might need to turn single item into list
        # If user passes in string to languages parameter, turn into a list containing only that string
        if isinstance(filled["languages"], str):
            filled["languages"] = [filled["languages"]]

        # optional params, with no defaults
        if "startDate" in data:
            filled["startDate"] = data["startDate"]

        # set languageAgnostic to True if user explicitly passes in `None` within `languages` parameter
        if "language" in data:
            filled["languageAgnostic"] = False
        if "language" not in data:
            filled["languageAgnostic"] = True

        # validating the query search - comment this out to skip validation
        self.project.validate_query_search(
            query=filled["booleanQuery"], language=filled["languages"]
        )
        return json.dumps(filled)

    def _fill_mention_params(self, data):
        if "name" not in data:
            raise KeyError("Must specify query or group name", data)
        elif not self.check_resource_exists(data["name"]):  # if resource does not exist
            raise KeyError("Could not find " + self.resource_type + " " + data["name"])
        if ("url" not in data) and ("resourceId" not in data):
            raise KeyError("Must provide either a url or a resourceId", data)

        filled = {}
        if "url" in data:
            filled["url"] = data["url"]
        else:
            filled["resourceId"] = data["resourceId"]

        return filled


class BWGroups(BWResource, bwdata.BWData):
    """
    This class provides an interface for group level operations within a prescribed project.

    Attributes:
        queries:        All queries in the project - handeled at the class level to prevent repetitive API calls.  This is a BWQueries object.
        tags:           All tags in the project - handeled at the class level to prevent repetitive API calls.  This is a BWTags object.
        categories:     All categories in the project - handeled at the class level to prevent repetitive API calls.  This is a BWCategories object.
    """

    general_endpoint = "querygroups"
    specific_endpoint = "querygroups"
    resource_type = "groups"
    resource_id_name = "queryGroupId"

    def __init__(self, bwproject):
        """
        Creates a BWGroups object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """

        super(BWGroups, self).__init__(bwproject)
        self.queries = BWQueries(self.project)
        self.tags = self.queries.tags
        self.categories = self.queries.categories

    def rename(self, name, new_name):
        """
        Renames an existing resource.

        Args:
            name:       Name of existing resource.
            new_name:   New name for the resource.

        Raises:
            KeyError:   If the resource does not exist.
        """
        if not self.check_resource_exists(name):
            raise KeyError(
                "Cannot rename a " + self.resource_type + " which does not exist", name
            )
        else:
            info = self.get(name=name)
            queries = [x["name"] for x in info["queries"]]
            self.upload(name=name, new_name=new_name, queries=queries)

    def upload_queries_as_group(
        self,
        group_name,
        query_data_list,
        create_only=False,
        modify_only=False,
        **kwargs
    ):
        """
        Uploads a list of queries and saves them as a group.

        Args:
            group_name:         Name of the group.
            query_data_list:    List of dictionaries, where each dictionary includes the information for one query in the following format {name: queryname, includedTerms: searchstring}
            create_only:        If True and the group already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:        If True and the group does not exist, no action will be triggered - Optional.  Defaults to False.
            kwargs:             You can pass in shared, sharedProjectIds and users - Optional.

        Returns:
            The uploaded group information in a dictionary of the form {groupname: groupid}
        """
        kwargs["queries"] = self.queries.upload_all(
            query_data_list, create_only, modify_only
        )
        kwargs["name"] = group_name
        return self.upload(create_only, modify_only, **kwargs)

    def deep_delete(self, name):
        """
        Deletes a group and all of the queries in the group.

        Args:
            name:   Name of the group that you'd like to delete.
        """
        # No need to delete the group itself, since a group will be deleted automatically when empty
        BWQueries(self.project).delete_all(self.get_group_queries(name))
        logger.info("Group {} deleted".format(name))

    def get_group_queries(self, name):
        """
        Retrieves information about the queries in the group.

        Args:
            name:   Name of the group that you'd like to retrieve.

        Returns:
            A dictionary of the form {query1name: query1id, query2name:query2id, ...}.
        """
        return {q["name"]: q["id"] for q in self.get(name)["queries"]}

    def _name_to_id(self, attribute, setting):
        if isinstance(setting, int):
            return setting

        elif isinstance(setting, list):
            try:
                return [int(i) for i in setting]
            except ValueError:
                pass

        if attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            ids = []
            for category in setting:
                parent = category
                children = setting[category]
                for child in children:
                    ids.append(self.categories.ids[parent]["children"][child])
            return ids

        elif attribute in [
            "parentCategory",
            "xparentCategory",
            "parentCategories",
            "categories",
        ]:
            # plural included for get_charts syntax
            # note: parentCategories and categories params will be ignored for everything but chart calls
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            # plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.get_resource_id(s))
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in [
            "locationGroup",
            "xlocationGroup",
            "authorLocationGroup",
            "xauthorLocationGroup",
        ]:
            locationlists = BWLocationLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(locationlists.get(s)["id"])
            return ids

        elif attribute in ["siteGroup", "xsiteGroup"]:
            sitelists = BWSiteLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(sitelists.get(s)["id"])
            return ids

        else:
            return setting

    def _fill_data(self, data):
        filled = {}
        if ("name" not in data) or ("queries" not in data):
            raise KeyError("Need name and queries to upload group", data)
        if self.check_resource_exists(
            data["name"]
        ):  # if resource exists, create value for filled['id']
            filled["id"] = self.get_resource_id(data["name"])

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        queries = data["queries"]
        query_ids = [self.queries.get_resource_id(resource=x) for x in queries]

        # now we have a reliable list of ids, we can turn this into a list of dictionaries in the form [{'name': 'MyQuery', 'id': 1111}]
        filled["queries"] = [
            {"name": self.queries.names[resource_id], "id": resource_id}
            for resource_id in query_ids
        ]
        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = (
            data["sharedProjectIds"]
            if "sharedProjectIds" in data
            else [self.project.project_id]
        )
        filled["users"] = (
            data["users"]
            if "users" in data
            else [{"id": self.project.get_self()["id"]}]
        )
        return json.dumps(filled)


class BWMentions:
    """
    This class handles patching lists of mentions.
    For retrieving mentions, see the BWQueries or BWGroups class instead (as you must specify a query or group in order to retrieve mentions, we thought it most sensible to tie that task to the BWQueries and BWGroups classes).

    Attributes:
        tags:           All tags in the project - handeled at the class level to prevent repetitive API calls.  This is a BWTags object.
        categories:     All categories in the project - handeled at the class level to prevent repetitive API calls.  This is a BWCategories object.
    """

    def __init__(self, bwproject):
        """
        Creates a BWMentions object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        self.project = bwproject
        self.tags = BWTags(self.project)
        self.categories = BWCategories(self.project)

    def patch_mentions(self, mentions, action, setting):
        """
        Edits a list of mentions by adding or removing categories, tags, priority, status, or assignment, or changing sentiment, checked or starred status, or location.
        This function will also handle uploading categories and tags, if you want to edit mentions by adding categories or tags that do not yet exist in the system.

        Args:
            mentions:   List of mentions to be edited.
            action:     Action to be taken when editing the mention.  See the list titled mutable in filters.py for the possible actions you can take to edit a mention.
            setting:    If the action is addTag or removeTag, the setting is a list of string(s) where each string is a tag name.  If the action is addCategories or removeCategories, the setting is a dictionary of in the format: {parent:[child1, child2, etc]} for any number of subcatagories (parent subcatagory names are strings).  See the dictionary titled mutable_options in filters.py for the accepted values for other actions.

        Raises:
            KeyError:   If you pass in an invalid action or setting.
            KeyError:   If there is an error when attempting to edit the mentions.
        """

        # add cats and tags if they don't exist
        if action in ["addCategories", "removeCategories"]:
            # the following loop is only one iteration
            for category in setting:
                parent = category
                children = setting[category]

            self.categories.upload(name=parent, children=children)
            setting = []
            for child in children:
                setting.append(self.categories.ids[parent]["children"][child])

        elif action in ["addTag", "removeTag"]:
            for s in setting:
                self.tags.upload(name=s, create_only=True)

        filled_data = []
        for mention in mentions:
            if action in filters.mutable and self._valid_patch_input(action, setting):
                filled_data.append(
                    self._fill_mention_data(
                        mention=mention, action=action, setting=setting
                    )
                )
            else:
                raise KeyError("invalid action or setting", action, setting)
        response = self.project.patch(
            endpoint="data/mentions", data=json.dumps(filled_data)
        )

        if "errors" in response:
            raise KeyError("patch failed", response)

        logger.info("{} mentions updated".format(len(response)))

    def _valid_patch_input(self, action, setting):
        """ internal use """
        if not isinstance(setting, filters.mutable[action]):
            return False
        if (
            action in filters.mutable_options
            and setting not in filters.mutable_options[action]
        ):
            return False
        else:
            return True

    def _fill_mention_data(self, **data):
        """ internal use """
        # pass in mention, filter_type, setting
        filled = {}

        filled["queryId"] = data["mention"]["queryId"]
        filled["resourceId"] = data["mention"]["resourceId"]

        if data["action"] in filters.mutable:
            filled[data["action"]] = data["setting"]
        else:
            raise KeyError("not a mutable field", data["action"])

        return filled


class BWAuthorLists(BWResource):
    """
    This class provides an interface for Author List operations within a prescribed project.
    """

    general_endpoint = "group/author/summary"
    specific_endpoint = "group/author"
    resource_type = "authorlists"

    def add_items(self, name, items):
        """
        Adds authors to an existing author list.

        Args:
            name:   Name of the author list to edit.
            items:  List of new authors to add.
        """
        prev_list = set(self.get(name)["authors"])
        prev_list.update(items)
        new_list = list(prev_list)

        self.upload(name=name, authors=new_list)

    def _fill_data(self, data):
        filled = {}

        if ("name" not in data) or ("authors" not in data):
            raise KeyError("Need name and authors to upload authorlist", data)
        if self.check_resource_exists(
            data["name"]
        ):  # if resource exists, create value for filled['id']
            filled["id"] = self.get_resource_id(data["name"])

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["authors"] = data["authors"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = (
            data["sharedProjectIds"]
            if "sharedProjectIds" in data
            else [self.project.project_id]
        )

        filled["userName"] = self.project.username
        filled["userId"] = self.project.get_self()["id"]
        return json.dumps(filled)


class BWSiteLists(BWResource):
    """
    This class provides an interface for Site List operations within a prescribed project.
    """

    general_endpoint = "group/site/summary"
    specific_endpoint = "group/site"
    resource_type = "sitelists"

    def add_items(self, name, items):
        """
        Adds sites to an existing site list.

        Args:
            name:   Name of the site list to edit.
            items:  List of new sites to add.
        """
        prev_list = set(self.get(name)["domains"])
        prev_list.update(items)
        new_list = list(prev_list)

        self.upload(name=name, domains=new_list)

    def _fill_data(self, data):
        filled = {}

        if ("name" not in data) or ("domains" not in data):
            raise KeyError("Need name and domains to upload sitelist", data)

        if self.check_resource_exists(
            data["name"]
        ):  # if resource exists, create value for filled['id']
            filled["id"] = self.get_resource_id(data["name"])

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["domains"] = data["domains"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = (
            data["sharedProjectIds"]
            if "sharedProjectIds" in data
            else [self.project.project_id]
        )

        filled["userName"] = self.project.username
        filled["userId"] = self.project.get_self()["id"]
        return json.dumps(filled)


class BWLocationLists(BWResource):
    """
    This class provides an interface for Location List operations within a prescribed project.
    """

    general_endpoint = "group/location/summary"
    specific_endpoint = "group/location"
    resource_type = "locationlists"

    def add_items(self, name, items):
        """
        Adds sites to an existing site list.

        Args:
            name:   Name of the location list to edit.
            items:  List of new locations to add.
        """
        prev_list = self.get(name)["locations"]
        new_list = prev_list
        for item in items:
            new_list.append(item)

        self.upload(name=name, locations=new_list)

    def _fill_data(self, data):
        filled = {}

        if ("name" not in data) or ("locations" not in data):
            raise KeyError("Need name and locations to upload locationlist", data)

        if self.check_resource_exists(data["name"]):
            filled["id"] = self.get_resource_id(data["name"])

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["locations"] = data["locations"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = (
            data["sharedProjectIds"]
            if "sharedProjectIds" in data
            else [self.project.project_id]
        )

        filled["userName"] = self.project.username
        filled["userId"] = self.project.get_self()["id"]
        return json.dumps(filled)


class BWTags(BWResource):
    """
    This class provides an interface for Tag operations within a prescribed project.
    """

    general_endpoint = "tags"
    specific_endpoint = "tags"
    resource_type = "tags"

    def clear_all_in_project(self):
        """ WARNING: This is the nuclear option.  Do not use lightly.  It deletes ALL tags in the project. """
        self.delete_all(list(self.names))

    def _fill_data(self, data):
        filled = {}

        if "name" not in data:
            raise KeyError("Need name to upload " + self.parameter, data)

        if "new_name" in data:
            filled["id"] = self.get_resource_id(data["name"])
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        return json.dumps(filled)


class BWCategories:
    """
    This class provides an interface for Category operations within a prescribed project.

    This class is odd because of its id structure, and for this reason it does not inherit from BWResource.
    Instead of just storing parent category id, we need to store parent categories and their ids, as well as their children and their children ids - hence the nested dictionary.

    Attributes:
        project:        Brandwatch project.  This is a BWProject object.
        ids:            Category information, organized in a dictionary of the form {category1name: {id: category1id, multiple: True/False, children: {child1name: child1id, ...}}, ...}.  Where multiple is a boolean flag to indicate whether or not to make subcategories mutually exclusive.
    """

    def __init__(self, bwproject):
        """
        Creates a BWCategories object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        self.project = bwproject
        self.ids = {}
        self.reload()

    def reload(self):
        """
        Refreshes category.ids.

        This function is used internally after editing any categories (e.g. uploading) so that our local copy of the id information matches the system's.
        The only potential danger is that someone else is editing categories at the same time you are - in which case your local copy could differ from the system's.
        If you fear this has happened, you can call reload() directly.

        Raises:
            KeyError: If there was an error with the request for category information.
        """
        response = self.project.get(endpoint="categories")

        if "results" not in response:
            raise KeyError("Could not retrieve categories", response)

        else:
            self.ids = {}
            for cat in response["results"]:
                children = {}
                for child in cat["children"]:
                    children[child["name"]] = child["id"]
                self.ids[cat["name"]] = {
                    "id": cat["id"],
                    "multiple": cat["multiple"],
                    "children": children,
                }

    def upload(
        self, create_only=False, modify_only=False, overwrite_children=False, **kwargs
    ):
        """
        Uploads a category.

        You can upload a new category, add subcategories to an existing category, overwrite the subcategories of an existing category, or change the name of an existing category with this function.

        Args:
            create_only:        If True and the category already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:        If True and the category does not exist, no action will be triggered - Optional.  Defaults to False.
            overwrite_children: Boolen flag that indicates if existing subcategories should be appended or overwriten - Optional.  Defaults to False (appending new subcategories).
            kwargs:             You must pass in name (parent category name) and children (list of subcategories).  You can optionally pass in multiple (boolean - indicates if subcategories are mutually exclusive) and/or new_name (string) if you would like to change the name of an existing category.

        Returns:
            A dictionary of the form {id: categoryid, multiple: True/False, children: {child1name: child1id, ...}}
        """
        return self.upload_all([kwargs], create_only, modify_only, overwrite_children)

    def upload_all(
        self, data_list, create_only=False, modify_only=False, overwrite_children=False
    ):
        """
        Uploads a list of categories.

        You can upload a new categories, add subcategories to existing categories, overwrite the subcategories of existing categories, or change the name of an existing categories with this function.

        Args:
            data_list:          List of dictionaries where each dictionary contains at least name (parent category name) and children (list of subcategories), and optionally multiple (boolean - indicates if subcategories are mutually exclusive) and/or new_name (string) if you would like to change the name of an existing category.
            create_only:        If True and the category already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:        If True and the category does not exist, no action will be triggered - Optional.  Defaults to False.
            overwrite_children: Boolen flag that indicates if existing subcategories should be appended or overwriten - Optional.  Defaults to False (appending new subcategories).

        Raises:
            KeyError:   If you do not pass in a category name.
            KeyError:   If you do not pass in a list of children. (You cannot upload a parent category that has no subcategories).

        Returns:
            A dictionary for each of the uploaded queries in the form {id: categoryid, multiple: True/False, children: {child1name: child1id, ...}}
        """
        for data in data_list:
            if "name" not in data:
                raise KeyError("Need name to upload " + self.parameter, data)
            elif "children" not in data:
                raise KeyError("Need children to upload categories", data)
            else:
                name = data["name"]

            if name in self.ids and not create_only:

                new_children = []
                existing_children = list(self.ids[name]["children"])
                for child in data["children"]:
                    if child not in existing_children:
                        new_children.append(child)

                if new_children or overwrite_children:
                    if not overwrite_children:
                        # add the new children to the existing children
                        for child in self.ids[name]["children"]:
                            # don't append or else the data object will be affected outside of this function
                            data["children"] = data["children"] + [child]

                    filled_data = self._fill_data(data)
                    self.project.put(
                        endpoint="categories/" + str(self.ids[name]["id"]),
                        data=filled_data,
                    )
                elif "new_name" in data:
                    filled_data = self._fill_data(data)
                    self.project.put(
                        endpoint="categories/" + str(self.ids[name]["id"]),
                        data=filled_data,
                    )
                    name = data["new_name"]

            elif name not in self.ids and not modify_only:
                filled_data = self._fill_data(data)
                self.project.post(endpoint="categories", data=filled_data)
            else:
                continue

        self.reload()
        cat_data = {}
        for data in data_list:
            if "new_name" in data:
                name = data["new_name"]
            else:
                name = data["name"]
            if name in self.ids:
                cat_data[name] = self.ids[name]
        return cat_data

    def rename(self, name, new_name):
        """
        Renames an existing category.

        Args:
            name:       Name of existing parent category.
            new_name:   New name for the parent category.

        Raises:
            KeyError:   If the category does not exist.
        """
        if name not in self.ids:
            raise KeyError("Cannot rename a category which does not exist", name)
        else:
            children = list(self.ids[name]["children"])
            self.upload(
                name=name,
                new_name=new_name,
                id=self.ids[name]["id"],
                multiple=self.ids[name]["multiple"],
                children=children,
            )

    def delete(self, name):
        """
        Deletes an entire parent category or subcategory.

        Args:
            name:   Category name if you wish to delete an entire parent category or a dictionary of the form {name: parentname, children: [child1todelete, child2todelete, ...]}, if you wish to delete a subcategory or list of subcateogries.
        """
        self.delete_all([name])

    def delete_all(self, names):
        """
        Deletes a list of categories or subcategories.
        If you're deleting the entire parent category then you can pass in a simple list of parent category names.  If you're deleting subcategories, then you need to pass in a list of dictionaries in the format: {name: parentname, children: [child1todelete, child2todelete, ...]}

        Args:
            names:   List of parent category names to delete or dictionary with subcategories to delete.
        """
        for item in names:
            if isinstance(item, str):
                if item in self.ids:
                    self.project.delete(
                        endpoint="categories/" + str(self.ids[item]["id"])
                    )
            elif isinstance(item, dict):
                if item["name"] in self.ids:
                    name = item["name"]
                    updated_children = []
                    existing_children = list(self.ids[name]["children"])

                    for child in existing_children:
                        if child not in item["children"]:
                            updated_children.append(child)

                    data = {
                        "name": name,
                        "children": updated_children,
                        "multiple": self.ids[name]["multiple"],
                    }

                    filled_data = self._fill_data(data)
                    self.project.put(
                        endpoint="categories/" + str(self.ids[name]["id"]),
                        data=filled_data,
                    )
        self.reload()

    def clear_all_in_project(self):
        """ WARNING: This is the nuclear option.  Do not use lightly.  It deletes ALL categories in the project. """
        for cat in self.ids:
            self.delete(self.ids[cat]["id"])

    def _fill_data(self, data):
        """ internal use """
        filled = {}

        if "id" in data:
            filled["id"] = data["id"]
        if "new_name" in data:
            filled["id"] = self.ids[data["name"]]["id"]
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        if "multiple" in data:
            filled["multiple"] = data["multiple"]
        else:
            filled["multiple"] = True

        filled["children"] = []
        for child in data["children"]:
            if (data["name"] in self.ids) and (
                child in self.ids[data["name"]]["children"]
            ):
                child_id = self.ids[data["name"]]["children"][child]
            else:
                child_id = None
            filled["children"].append({"name": child, "id": child_id})
        return json.dumps(filled)


class BWRules(BWResource):
    """
    This class provides an interface for Rule operations within a prescribed project.

    Attributes:
        queries:        All queries in the project - handeled at the class level to prevent repetitive API calls.  This is a BWQueries object.
        tags:           All tags in the project - handeled at the class level to prevent repetitive API calls.  This is a BWTags object.
        categories:     All categories in the project - handeled at the class level to prevent repetitive API calls.  This is a BWCategories object.
    """

    general_endpoint = "rules"
    specific_endpoint = "rules"
    resource_type = "rules"

    def __init__(self, bwproject):
        """
        Creates a BWRules object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        super(BWRules, self).__init__(bwproject)
        # store queries, tags and cats as a rule attribute so you don't have to reload a million times
        self.queries = BWQueries(self.project)
        self.tags = self.queries.tags
        self.categories = self.queries.categories

    def upload_all(self, data_list, create_only=False, modify_only=False):
        """
        Uploads a list of rules.
        Args:
            data_list:          A list of dictionaries, where each dictionaries contains a name, ruleAction and (optional but recommended) filters.  It is best practice to first call rule_action() and filters() to generate error checked versions of these two required dictionaries.  Optionally, you can also pass in enabled (boolean: default True), scope (string. default based on presence or absence of term queryName) and/or backfill (boolean. default False. To apply the rule to already existing mentions, set backfill to True).
            create_only:        If True and the category already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:        If True and the category does not exist, no action will be triggered - Optional.  Defaults to False.

        Raises:
            KeyError:   If an item in the data_list does not include a name.
            KeyError:   If an item in the data_list does not include a ruleAction.

        """

        rules = []

        for rule in data_list:
            rule = {**rule}
            if "filter" in rule:
                rule["filter"] = {
                    **rule["filter"],
                    "projectId": self.project.project_id,
                }
            rules.append(rule)

        rules_to_id = super(BWRules, self).upload_all(
            rules, create_only=False, modify_only=False
        )

        for rule in rules:
            if "backfill" in rule and rule["backfill"]:
                self.project.post(
                    endpoint="bulkactions/rule/" + str(rules_to_id[rule["name"]])
                )

    def rename(self, name, new_name):
        """
        Renames an existing resource.

        Args:
            name:       Name of existing resource.
            new_name:   New name for the resource.

        Raises:
            KeyError:   If the resource does not exist.
        """
        if not self.check_resource_exists(name):
            raise KeyError(
                "Cannot rename a " + self.resource_type + " which does not exist", name
            )
        else:
            info = self.get(name=name)
            rule = {}
            rule["ruleAction"] = self.rule_action(**info["ruleAction"])
            if info["filter"]["queryName"] == "Whole Project":
                info["filter"].pop("queryName")
            rule["filter"] = self.filters(**info["filter"])
            self.upload(name=name, new_name=new_name, **rule)

    def rule_action(self, action, setting):
        """
        Formats rule action into dictionary and checks that its contents are valid.
        If the action is category or tag related and the cat or tag doesn't yet exist, we upload it here.

        Args:
            action:     Action to be taken by the rule.  See the list "mutable" in filters.py for a full list of options.
            setting:    Setting for the action.  E.g. If action is addCategories or removeCategories: setting = {parent:[child]}.

        Raises:
            KeyError:   If the action input is invalid.
            KeyError:   If the setting input is invalid.

        Returns:
            A dictionary of the form {action: setting}
        """
        if action in ["addCategories", "removeCategories"]:
            # the following loop is only one iteration
            for category in setting:
                parent = category
                children = setting[category]

            self.categories.upload(name=parent, children=children)
            setting = []
            for child in children:
                setting.append(self.categories.ids[parent]["children"][child])

        elif action in ["addTag", "removeTag"]:
            for s in setting:
                self.tags.upload(name=s, create_only=True)

        if action not in filters.mutable:
            raise KeyError("invalid rule action", action)
        elif not self._valid_action_input(action, setting):
            raise KeyError("invalid setting", setting)

        return {action: setting}

    def filters(self, queryName="", **kwargs):
        """
        Prepares rule filters in a dictionary.

        Args:
            queryName:  List of queries which the rule will be applied to.
            kwargs:     Any number of filters, passed through in the form filter_type = filter_setting.  For a full list of filters see filters.py.

        Returns:
            A dictionary of filters in the form {filter1type: filter1setting, filter2type: filter2setting, ...}
        """
        fil = {}
        if queryName != "":
            if not isinstance(queryName, list):
                queryName = [queryName]
            fil["queryId"] = []
            for query in queryName:
                fil["queryId"].append(self.queries.get_resource_id(query))

        for param in kwargs:
            setting = self._name_to_id(param, kwargs[param])
            fil[param] = setting
        return fil

    def rule(self, name, action, filter, **kwargs):
        """
        When using upload_all(), it may be useful to use this function first to keep rule dictionaries organized and formatted correctly.

        Args:
            name:   Rule name.
            action: Rule action.  It is best practice to first call rule_action() to generate an error checked version of this required dictionary.
            filter: Rule filter.  It is best practice to first call filters() to generate a formatted version of this required dictionary.
            kwargs: Additional rule information - Optional.  Accepted keyword arguments are enabled (boolean: default True), scope (string. default based on presence or absence of term queryName) and/or backfill (boolean. default False. To apply the rule to already existing mentions, set backfill to True).

        Returns:
            Dictionary with all rule information, ready to be uploaded.
        """
        rule = {}
        rule["name"] = name
        rule["ruleAction"] = action
        rule["filter"] = filter
        if "scope" in kwargs:
            rule["scope"] = kwargs["scope"]
        if "backfill" in kwargs:
            rule["backfill"] = kwargs["backfill"]
        if "enabled" in kwargs:
            rule["enabled"] = kwargs["enabled"]
        return rule

    def clear_all_in_project(self):
        """ WARNING: This is the nuclear option.  Do not use lightly.  It deletes ALL rules in the project. """
        for resource_id in self.names.keys():
            self.project.delete(endpoint="rules/" + str(resource_id))
        self.reload()

    def get(self, name=None):
        """
        Retrieves all information for a list of existing rules, and formats each rule in the following way {"name":name, "queries":queries, "filter":filters, "ruleAction":ruleAction}
        Returns:
            List of dictionaries in the format {"name":name, "queries":queries, "filter":filters, "ruleAction":ruleAction}
        """
        if not name:
            ruledata = self.project.get(endpoint="rules")
            if "errors" not in ruledata:
                ruledata = ruledata["results"]
            else:
                exit()
        elif not self.check_resource_exists(name):
            raise KeyError("Could not find " + self.resource_type + ": " + name)
        else:
            resource_id = self.get_resource_id(name)
            ruledata = self.project.get(
                endpoint=self.specific_endpoint + "/" + str(resource_id)
            )
            ruledata = [ruledata]

        rules = []
        for rule in ruledata:
            name = rule["name"]
            queryIds = rule["filter"]["queryId"]
            if queryIds is None:  # scope = project, so specific queries are not listed
                queries = "Whole Project"
            else:
                queries = [self.queries.names[q] for q in queryIds]
            filters = {"queryName": queries}
            for fil in rule["filter"]:
                value = rule["filter"].get(fil)
                if value is not None and fil != "queryId":
                    filters[fil] = self._id_to_name(fil, value)

            ruleAction = {}
            for action in rule["ruleAction"]:
                value = rule["ruleAction"].get(action)
                if value is not None:
                    ruleAction["action"] = action
                    ruleAction["setting"] = self._id_to_name(action, value)
                    break

            rules.append({"name": name, "filter": filters, "ruleAction": ruleAction})
        if len(rules) == 1:
            return rules[0]
        else:
            return rules

    def _fill_data(self, data):
        """ internal use """
        filled = {}
        if ("name" not in data) or ("ruleAction" not in data):
            raise KeyError("Need name to and ruleAction to upload rule", data)

        # for PUT calls, need id, projectName, queryName in addition to the rest of the data below
        if self.check_resource_exists(data["name"]):
            filled["id"] = self.get_resource_id(data["name"])
            filled["projectName"] = (
                data["projectName"]
                if ("projectName" in data)
                else self.project.project_name
            )
            filled["queryName"] = data["queryName"] if ("queryName" in data) else None

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["enabled"] = data["enabled"] if ("enabled" in data) else True
        filled["filter"] = data["filter"] if ("filter" in data) else {}
        filled["ruleAction"] = data["ruleAction"]
        filled["projectId"] = self.project.project_id

        # validating the query search - comment this out to skip validation
        if "search" in filled["filter"]:
            self.project.validate_rule_search(
                query=filled["filter"]["search"], language="en"
            )

        if "scope" in data:
            filled["scope"] = data["scope"]
        elif "queryId" in data["filter"]:
            filled["scope"] = "query"
        else:
            filled["scope"] = "project"

        return json.dumps(filled)

    def _name_to_id(self, attribute, setting):
        if isinstance(setting, int):
            return setting

        elif isinstance(setting, list):
            try:
                return [int(i) for i in setting]
            except ValueError:
                pass

        elif attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            for category in setting:
                parent = category
                child = setting[category][0]
            return self.categories.ids[parent]["children"][child]

        elif attribute in [
            "parentCategory",
            "xparentCategory",
            "parentCategories",
            "categories",
        ]:
            # plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            # plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.get_resource_id(s))
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in [
            "locationGroup",
            "xlocationGroup",
            "authorLocationGroup",
            "xauthorLocationGroup",
        ]:
            locationlists = BWLocationLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(locationlists.get(s)["id"])
            return ids

        elif attribute in ["siteGroup", "xsiteGroup"]:
            sitelists = BWSiteLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(sitelists.get(s)["id"])
            return ids

        else:
            return setting

    def _valid_action_input(self, action, setting):
        """ internal use """
        if not isinstance(setting, filters.mutable[action]):
            return False
        if (
            action in filters.mutable_options
            and setting not in filters.mutable_options[action]
        ):
            return False
        else:
            return True

    def _id_to_name(self, attribute, setting):
        if not setting or isinstance(setting, str):
            return setting

        if isinstance(setting, list) and isinstance(setting[0], str):
            return setting

        elif attribute in ["tag", "xtag", "addTag", "removeTag"]:
            return self.tags.get_resource_id(setting)

        elif attribute in [
            "category",
            "xcategory",
            "addCategories",
            "removeCategories",
        ]:
            names = {}
            subcats = []

            for category in self.categories.ids:
                for subcategory in self.categories.ids[category]["children"]:
                    if (
                        self.categories.ids[category]["children"][subcategory]
                        in setting
                    ):
                        subcats.append(subcategory)
                if subcats:
                    names[category] = subcats
                subcats = []

            return names

        elif attribute == "parentCategory" or attribute == "xparentCategory":
            for category in self.categories.ids:
                for cat in setting:
                    if cat == self.categories.ids[category]["id"]:
                        return category

        elif attribute == "authorGroup" or attribute == "xauthorGroup":
            resource_obj = BWAuthorLists(self.project)
            for resource_id, resource_name in resource_obj.names.items():
                for aulist in setting:
                    if resource_id == aulist:
                        return resource_name

        elif attribute == "locationGroup" or attribute == "xlocationGroup":
            resource_obj = BWLocationLists(self.project)
            for resource_id, resource_name in resource_obj.names.items():
                for aulist in setting:
                    if resource_id == aulist:
                        return resource_name

        elif attribute == "authorLocationGroup" or attribute == "xauthorLocationGroup":
            resource_obj = BWLocationLists(self.project)
            for resource_id, resource_name in resource_obj.names.items():
                for aulist in setting:
                    if resource_id == aulist:
                        return resource_name

        elif attribute == "siteGroup" or attribute == "xsiteGroup":
            resource_obj = BWSiteLists(self.project)
            for resource_id, resource_name in resource_obj.names.items():
                for aulist in setting:
                    if resource_id == aulist:
                        return resource_name

        else:
            return setting


class BWSignals(BWResource):
    """
    This class provides an interface for signals operations within a prescribed project (e.g. uploading, downloading).

    Attributes:
        queries:        All queries in the project - handeled at the class level to prevent repetitive API calls.  This is a BWQueries object.
        tags:           All tags in the project - handeled at the class level to prevent repetitive API calls.  This is a BWTags object.
        categories:     All categories in the project - handeled at the class level to prevent repetitive API calls.  This is a BWCategories object.
    """

    general_endpoint = "signals/groups"
    specific_endpoint = "signals/groups"
    resource_type = "signals"

    def __init__(self, bwproject):
        """
        Creates a BWSignals object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        super(BWSignals, self).__init__(bwproject)
        self.queries = BWQueries(self.project)
        self.tags = self.queries.tags
        self.categories = self.queries.categories

    def rename(self, name, new_name):
        """
        Renames an existing resource.

        Args:
            name:       Name of existing resource.
            new_name:   New name for the resource.

        Raises:
            KeyError:   If the resource does not exist.
        """
        if not self.get_resource_id(name):
            raise KeyError(
                "Cannot rename a " + self.resource_type + " which does not exist", name
            )
        else:
            info = self.get(name=name)
            info.pop("name")
            info["queries"] = info.pop("queryIds")
            self.upload(name=name, new_name=new_name, **info)

    def _fill_data(self, data):
        filled = {}

        if (
            ("name" not in data)
            or ("queries" not in data)
            or ("subscribers" not in data)
        ):
            raise KeyError(
                "Need name, queries and subscribers to create a signal", data
            )

        for subscriber in data["subscribers"]:
            if (
                ("emailAddress" not in subscriber)
                or ("notificationThreshold" not in subscriber)
                or (subscriber["notificationThreshold"] not in [1, 2, 3])
            ):
                raise KeyError(
                    "subscribers must be in the format {emailAddress: emailaddress, notificationThreshold: 1/2/3} where the notificationThreshold must be 1 (all signals), 2 (medium - high priority signals) or 3 (only high priority signals)",
                    subscriber,
                )

        if self.check_resource_exists(data["name"]):
            filled["id"] = self.get_resource_id(data["name"])
        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["queryIds"] = []
        for query in data["queries"]:
            if isinstance(query, int):
                filled["queryIds"].append(query)
            else:
                filled["queryIds"].append(self.queries.get_resource_id(query))

        filled["subscribers"] = data["subscribers"]

        for param in data:
            filled.update(self._name_to_id(param, data[param]))

        return json.dumps(filled)

    def _name_to_id(self, attribute, setting):
        """ internal use """
        ids = []
        if attribute in ["includeCategoryIds", "excludeCategoryIds"]:
            for category in setting:
                if not isinstance(category, int):
                    # already in ID form
                    raise KeyError(
                        "Must pass in ids with "
                        + attribute
                        + " parameter, or use names and the appropriate category/xcategory or parentCategory/xparentCategory parameter."
                    )
            return {attribute: setting}

        elif attribute in ["category", "xcategory"]:
            for category in setting:
                if isinstance(category, int):
                    # already in ID form
                    ids.append(category)
                else:
                    parent = category
                    for child in setting[category]:
                        ids.append(self.categories.ids[parent]["children"][child])

            if attribute == "category":
                return {"includeCategoryIds": ids}
            else:
                return {"excludeCategoryIds": ids}

        elif attribute in ["parentCategory", "xparentCategory"]:
            if not isinstance(setting, list):
                setting = [setting]

            for category in setting:
                if isinstance(category, int):
                    # already in ID form
                    ids.append(category)
                else:
                    ids.append(self.categories.ids[category]["id"])

            if attribute == "parentCategory":
                return {"includeCategoryIds": ids}
            else:
                return {"excludeCategoryIds": ids}

        elif attribute in ["tag", "xtag", "includeTagIds", "excludeTagIds"]:
            if not isinstance(setting, list):
                setting = [setting]
            for tag in setting:
                if isinstance(tag, int):
                    # already in ID form
                    ids.append(tag)
                else:
                    ids.append(self.tags.get_resource_id(tag))

            if attribute in ["tag", "includeTagIds"]:
                return {"includeTagIds": ids}
            else:
                return {"excludeTagIds": ids}
        else:
            return {}
