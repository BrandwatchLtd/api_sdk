"""
bwresources contains the BWMentions, BWQueries, BWGroups, BWRules, BWTags, BWCategories, BWSiteLists, BWAuthorLists, BWLocationLists, and BWSignals classes.
"""

import json
import datetime
import filters
import requests
import threading
import bwdata

class BWResource:
    """
    This class is a superclass for brandwatch resources (queries, groups, mentions, tags, sitelists, authorlists, locationlists and signals). 

    Attributes:
        project:        Brandwatch project.  This is a BWProject object.
        console_report: Boolean flag to control console reporting.  Inherited from the project.
        ids:            Query ids, organized in a dictionary of the form {query1name: query1id, query2name: query2id, ...}
    """

    def __init__(self, bwproject):
        """
        Creates a BWResource object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        self.project = bwproject
        self.console_report = bwproject.console_report
        self.ids = {}
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

        self.ids = {resource["name"]: resource["id"] for resource in response["results"]}

    def get(self, name=None):
        """
        If you specify a name, this function will retrieve all information for that resource as it is stored in Brandwatch.  
        If you do not specify a name, this function will retrieve all information for all resources of that type as they are stored in Brandwatch.

        Args:
            name:   Name of the resource that you'd like to retrieve - Optional.  If you do not specify a name, all resources of that type will be retrieved.

        Raises:
            KeyError:   If you specify a resource name and the resource does not exist.

        Returns:
            All information for the specified resource, or a list of information on every resource of that type in the account.
        """
        if not name:
            return self.project.get(endpoint=self.general_endpoint)["results"]
        elif name not in self.ids:
            raise KeyError("Could not find " + self.resource_type + ": " + name, self.ids)
        else:
            resource_id = self.ids[name]
            return self.project.get(endpoint=self.specific_endpoint + "/" + str(resource_id))

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

            if name in self.ids and not create_only:
                response = self.project.put(endpoint=self.specific_endpoint + "/" + str(self.ids[name]),
                                            data=filled_data)
            elif name not in self.ids and not modify_only:
                response = self.project.post(endpoint=self.specific_endpoint,
                                             data=filled_data)
            else:
                continue

            if "errors" not in response:
                resources[response["name"]] = response["id"]

            if self.console_report:
                print(self.resource_type + ": " + response["name"] + " posted")

        self.reload()
        return resources

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
        for name in names:
            if name in self.ids:
                resource_id = self.ids[name]
                self.project.delete(endpoint=self.specific_endpoint + "/" + str(resource_id))

                if self.console_report:
                    print(self.resource_type + ": " + name + " deleted")

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

    def upload(self, create_only=False, modify_only=False, backfill_date="", **kwargs):
        """
        Uploads a query.

        Args:
            create_only:    If True and the query already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:    If True and the query does not exist, no action will be triggered - Optional.  Defaults to False.
            backfill_date:  Date which you'd like to backfill the query too (yyyy-mm-dd) - Optional.
            kwargs:         You must pass in name (string) and includedTerms (string).  You can also optionally pass in languages, type, industry and samplePercent.

        Returns:
            The uploaded query information in a dictionary of the form {query1name: query1id}
        """
        return self.upload_all([kwargs], create_only, modify_only, backfill_date)

    def upload_all(self, data_list, create_only=False, modify_only=False, backfill_date=""):
        """
        Uploads multiple queries.

        Args:
            data_list:      You must pass in name (string) and includedTerms (string).  You can also optionally pass in languages, type, industry and samplePercent.
            create_only:    If True and the query already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:    If True and the query does not exist, no action will be triggered - Optional.  Defaults to False.
            backfill_date:  Date which you'd like to backfill the query too (yyyy-mm-dd) - Optional.

        Raises:
            KeyError: If you do not pass name and includedTerms for each query in the data_list.

        Returns:
            The uploaded query information in a dictionary of the form {query1name: query1id, query2name: query2id, ...}
        """

        queries = super(BWQueries, self).upload_all(data_list, create_only=False, modify_only=False)

        if backfill_date != "":
            for query in queries:
                self.backfill(queries[query], backfill_date)

        return queries

    def upload_channel(self, **kwargs):
        """
        Uploads a channel.

        Args:
            kwargs:	You must pass in name, handle and channel_type.

        Returns:
            The uploaded channel information in a dictionary of the form {channel1name: channel1id}
        """
        return self.upload_all_channel([kwargs])

    def upload_all_channel(self, query_data_list):
        """
        Uploads a list of channels.

        Args:
            query_data_list:	You must pass in a dictionary of the form {name: channelname, handle: channelhandle, channel_type: twitter/facebook}.

        Raise:
            KeyError:	If you fail to pass in name, handle or channel_type for any of the channels in the query_data_list.
            KeyError:	If you pass channel_type = facebook.  We cannot support automated Facebook channel uploads at this time.
            KeyError:	If you pass in channel_type other than twitter or facebook.

        Returns:
            The uploaded channel information in a dictionary of the form {channel1name: channel1id, channel2name: channel2id, ...}
        """

        returnMess = {}
        for channel in query_data_list:
            if ("name" not in channel) or ("handle" not in channel) or ("channel_type" not in channel):
                raise KeyError("You must pass a name, a handle and a channel_type to upload a channel")

            if channel["channel_type"] in ["twitter", "Twitter", "TWITTER"]:
                userId = self.project.bare_request(verb=requests.get,
                                                   address_root="http://app.brandwatch.net/",
                                                   address_suffix="twitterapi/users/show.json",
                                                   params={"screen_name": channel["handle"]})["id_str"]

                params = {"confirm": "false"}
                data = json.dumps({"name": channel["name"],
                                   "twitterScreenName": channel["handle"],
                                   "twitterUserId": userId,
                                   "industry": "general-(recommended)"})

                response = self.project.post(endpoint="twitterqueries",
                                             data=data,
                                             params=params)

            elif channel["channel_type"] in ["facebook", "Facebook", "FACEBOOK"]:
                raise KeyError("We cannot support automated Facebook channel uploads at this time.")

            # IN PROGRESS
            # params = {"facebookConsumerKey": "",
            # 		"facebookPageName": ""}

            # data = json.dumps({"facebookPageId": "",
            # 				"facebookPageName": "",
            # 				"facebookPageURL": "https://www.facebook.com/"+channel["name"]+"/",
            # 				"industry": "general-(recommended)",
            # 				"name": channel["name"],
            # 				"type": "publicfacebook"})

            # response = self.project.post(endpoint = "facebookqueries",
            # 							data = data,
            # 							params = params)
            else:
                raise KeyError("You must specify if the channel_type is twitter or facebook.")

            if "errors" not in response:
                returnMess[response["name"]] = response["id"]
            elif self.console_report:
                print(response)

        self.reload()
        return returnMess

    def backfill(self, query_id, backfill_date):
        """
        Backfills a query to a specified date.

        Args:
            query_id:       Query id
            backfill_date:  Date that you'd like to backfill the query to (yyy-mm-dd).

        Returns:
            Server's response to the post request.
        """
        backfill_endpoint = "queries/" + str(query_id) + "/backfill"
        backfill_data = {"minDate": backfill_date, "queryId": query_id}
        return self.project.post(endpoint=backfill_endpoint, data=json.dumps(backfill_data))

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
        mention = self.project.get(endpoint="query/"+str(self.ids[kwargs["name"]])+"/mentionfind", params=params)

        if "errors" in mention:
            raise KeyError("Mentions GET request failed", mention)
        return mention["mention"]

    def _name_to_id(self, attribute, setting):

        if isinstance(setting, int):
            # already in ID form
            return setting

        elif attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            ids = []
            for category in setting:
                parent = category
                children = setting[category]
            for child in children:
                ids.append(self.categories.ids[parent]["children"][child])
            return ids

        elif attribute in ["parentCategory", "xparentCategory", "parentCategories", "categories"]:
            #plural included for get_charts syntax
            #note: parentCategories and categories params will be ignored for everything but chart calls
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            #plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.ids[s])
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in ["locationGroup", "xlocationGroup", "authorLocationGroup", "xauthorLocationGroup"]:
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

        if ("name" not in data) or ("includedTerms" not in data):
            raise KeyError("Need name and includedTerms to post query", data)

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]
        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["includedTerms"] = data["includedTerms"]
        filled["languages"] = data["languages"] if "languages" in data else ["en"]
        filled["type"] = data["type"] if "type" in data else "search string"
        filled["industry"] = data["industry"] if "industry" in data else "general-(recommended)"
        filled["samplePercent"] = data["samplePercent"] if "samplePercent" in data else 100
        filled["languageAgnostic"] = data["languageAgnostic"] if "languageAgnostic" in data else False

        # validating the query search - comment this out to skip validation
        self.project.validate_query_search(query=filled["includedTerms"], language=filled["languages"])

        return json.dumps(filled)

    def _fill_mention_params(self, data):
        if "name" not in data:
            raise KeyError("Must specify query or group name", data)
        elif data["name"] not in self.ids:
            raise KeyError("Could not find " + self.resource_type + " " + data["name"], self.ids)
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

    def upload_queries_as_group(self, group_name, query_data_list, create_only=False, modify_only=False,
                                backfill_date="", **kwargs):
        """
        Uploads a list of queries and saves them as a group.

        Args:
            group_name:         Name of the group.
            query_data_list:    List of dictionaries, where each dictionary includes the information for one query in the following format {name: queryname, includedTerms: searchstring}
            create_only:        If True and the group already exists, no action will be triggered - Optional.  Defaults to False.
            modify_only:        If True and the group does not exist, no action will be triggered - Optional.  Defaults to False.
            backfill_date:      Date which you'd like to backfill the queries too (yyyy-mm-dd) - Optional.
            kwargs:             You can pass in shared, sharedProjectIds and users - Optional.

        Returns:
            The uploaded group information in a dictionary of the form {groupname: groupid}
        """
        kwargs["queries"] = self.queries.upload_all(query_data_list, create_only, modify_only, backfill_date)
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

        if self.console_report:
            print("Group " + name + " deleted")

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
            # already in ID form
            return setting

        elif attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            ids = []
            for category in setting:
                parent = category
                children = setting[category]
            for child in children:
                ids.append(self.categories.ids[parent]["children"][child])
            return ids

        elif attribute in ["parentCategory", "xparentCategory", "parentCategories", "categories"]:
            #plural included for get_charts syntax
            #note: parentCategories and categories params will be ignored for everything but chart calls
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            #plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.ids[s])
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in ["locationGroup", "xlocationGroup", "authorLocationGroup", "xauthorLocationGroup"]:
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

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        queries = data["queries"]
        filled["queries"] = [{"name": q, "id": self.queries.ids[q]} for q in queries]
        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = data["sharedProjectIds"] if "sharedProjectIds" in data else [
            self.project.project_id]
        filled["users"] = data["users"] if "users" in data else [{"id": self.project.get_self()["id"]}]
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
        self.console_report = bwproject.console_report
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
                filled_data.append(self._fill_mention_data(mention=mention, action=action, setting=setting))
            else:
                raise KeyError("invalid action or setting", action, setting)
        response = self.project.patch(endpoint="data/mentions", data=json.dumps(filled_data))

        if "errors" in response:
            raise KeyError("patch failed", response)

        if self.console_report:
            print(str(len(response)) + " mentions updated")

    def _valid_patch_input(self, action, setting):
        """ internal use """
        if not isinstance(setting, filters.mutable[action]):
            return False
        if action in filters.mutable_options and setting not in filters.mutable_options[action]:
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

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["authors"] = data["authors"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = data["sharedProjectIds"] if "sharedProjectIds" in data else [
            self.project.project_id]

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

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["domains"] = data["domains"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = data["sharedProjectIds"] if "sharedProjectIds" in data else [
            self.project.project_id]

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
            raise KeyError("Need name and authors to upload locationlist", data)

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]

        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["locations"] = data["locations"]

        filled["shared"] = data["shared"] if "shared" in data else "public"
        filled["sharedProjectIds"] = data["sharedProjectIds"] if "sharedProjectIds" in data else [
            self.project.project_id]

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
        self.delete_all(list(self.ids))

    def _fill_data(self, data):
        filled = {}

        if ("name" not in data):
            raise KeyError("Need name to upload " + self.parameter, data)

        if "new_name" in data:
            filled["id"] = self.ids.get(data["name"])
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        return json.dumps(filled)


class BWCategories():
    """
    This class provides an interface for Category operations within a prescribed project.  

    This class is odd because of its id structure, and for this reason it does not inherit from BWResource. 
    Instead of just storing parent category id, we need to store parent categories and their ids, as well as their children and their children ids - hence the nested dictionary.

    Attributes:
        project:        Brandwatch project.  This is a BWProject object.
        console_report: Boolean flag to control console reporting.  Inherited from the project.
        ids:            Category information, organized in a dictionary of the form {category1name: {id: category1id, multiple: True/False, children: {child1name: child1id, ...}}, ...}.  Where multiple is a boolean flag to indicate whether or not to make subcategories mutually exclusive.
    """

    def __init__(self, bwproject):
        """
        Creates a BWCategories object.

        Args:
            bwproject:  Brandwatch project.  This is a BWProject object.
        """
        self.project = bwproject
        self.console_report = bwproject.console_report
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
                self.ids[cat["name"]] = {"id": cat["id"],
                                         "multiple": cat["multiple"],
                                         "children": children}

    def upload(self, create_only=False, modify_only=False, overwrite_children=False, **kwargs):
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

    def upload_all(self, data_list, create_only=False, modify_only=False, overwrite_children=False):
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
            if ("name" not in data):
                raise KeyError("Need name to upload " + self.parameter, data)
            elif ("children" not in data):
                raise KeyError("Need children to upload categories", data)
            else:
                name = data["name"]

            if name in self.ids and not create_only:

                new_children = []
                existing_children = list(self.ids[name]["children"])
                for child in data["children"]:
                    if child not in existing_children:
                        new_children.append(child)

                if new_children:
                    if not overwrite_children:
                        # add the new children to the existing children
                        for child in self.ids[name]["children"]:
                            # don't append or else the data object will be affected outside of this function
                            data["children"] = data["children"] + [child]

                    filled_data = self._fill_data(data)
                    self.project.put(endpoint="categories/" + str(self.ids[name]["id"]), data=filled_data)
                elif "new_name" in data:
                    filled_data = self._fill_data(data)
                    self.project.put(endpoint="categories/" + str(self.ids[name]["id"]), data=filled_data)
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
            self.upload(name=name, new_name=new_name, id=self.ids[name]["id"], multiple=self.ids[name]["multiple"],
                        children=children)

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
                    self.project.delete(endpoint="categories/" + str(self.ids[item]["id"]))
            elif isinstance(item, dict):
                if item["name"] in self.ids:
                    name = item["name"]
                    updated_children = []
                    existing_children = list(self.ids[name]["children"])

                    for child in existing_children:
                        if child not in item["children"]:
                            updated_children.append(child)

                    data = {"name": name,
                            "children": updated_children,
                            "multiple": self.ids[name]["multiple"]}

                    filled_data = self._fill_data(data)
                    self.project.put(endpoint="categories/" + str(self.ids[name]["id"]), data=filled_data)
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
            if (data["name"] in self.ids) and (child in self.ids[data["name"]]["children"]):
                child_id = self.ids[data["name"]]["children"][child]
            else:
                child_id = None
            filled["children"].append({"name": child,
                                       "id": child_id})
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
        	data_list:			A list of dictionaries, where each dictionaries contains a name, ruleAction and (optional but recommended) filters.  It is best practice to first call rule_action() and filters() to generate error checked versions of these two required dictionaries.  Optionally, you can also pass in enabled (boolean: default True), scope (string. default based on presence or absence of term queryName) and/or backfill (boolean. default False. To apply the rule to already existing mentions, set backfill to True).
        	create_only:        If True and the category already exists, no action will be triggered - Optional.  Defaults to False.
        	modify_only:        If True and the category does not exist, no action will be triggered - Optional.  Defaults to False.
        
        Raises:
        	KeyError:	If an item in the data_list does not include a name.
        	KeyError:	If an item in the data_list does not include a ruleAction.

        Returns:
            A dictionary of the form {rule1name: rule1id, rule2name: rule2id, ...}
        """

        rules = super(BWRules, self).upload_all(data_list, create_only=False, modify_only=False)

        for data in data_list:
            if "backfill" in data and data["backfill"] == True:
                self.project.post(endpoint="rules/" + str(rules[data["name"]]) + "/backfill")

    def rule_action(self, action, setting):
        """ 
        Formats rule action into dictionary and checks that its contents are valid. 
        If the action is category or tag related and the cat or tag doesn't yet exist, we upload it here.

        Args:
        	action:		Action to be taken by the rule.  See the list "mutable" in filters.py for a full list of options.
        	setting:	Setting for the action.  E.g. If action is addCategories or removeCategories: setting = {parent:[child]}. 

        Raises:
        	KeyError:	If the action input is invalid.
        	KeyError:	If the setting input is invalid.

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
        	queryName:	List of queries which the rule will be applied to.
        	kwargs:	 	Any number of filters, passed through in the form filter_type = filter_setting.  For a full list of filters see filters.py.

        Returns:
        	A dictionary of filters in the form {filter1type: filter1setting, filter2type: filter2setting, ...}
        """
        fil = {}
        if queryName != "":
            if not isinstance(queryName, list):
                queryName = [queryName]
            fil["queryId"] = []
            for query in queryName:
                fil["queryId"].append(self.queries.ids[query])

        for param in kwargs:
            setting = self._name_to_id(param, kwargs[param])
            fil[param] = setting
        return fil

    def rule(self, name, action, filter, **kwargs):
        """ 
        When using upload_all(), it may be useful to use this function first to keep rule dictionaries organized and formatted correctly.

        Args:
        	name:	Rule name.
        	action:	Rule action.  It is best practice to first call rule_action() to generate an error checked version of this required dictionary.
        	filter:	Rule filter.  It is best practice to first call filters() to generate a formatted version of this required dictionary.
        	kwargs:	Additional rule information - Optional.  Accepted keyword arguments are enabled (boolean: default True), scope (string. default based on presence or absence of term queryName) and/or backfill (boolean. default False. To apply the rule to already existing mentions, set backfill to True).  

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
        for name in self.ids:
            self.project.delete(endpoint="rules/" + str(self.ids[name]))
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
        elif name not in self.ids:
            raise KeyError("Could not find " + self.resource_type + ": " + name, self.ids)
        else:
            resource_id = self.ids[name]
            ruledata = self.project.get(endpoint=self.specific_endpoint + "/" + str(resource_id))
            ruledata = [ruledata]

        rules = []
        for rule in ruledata:
            name = rule["name"]
            queryIds = rule["filter"]["queryId"]
            if queryIds is None:  # scope = project, so specific queries are not listed
                queries = "Whole Project"
            else:
                queries = []
                for query in queryIds:
                    for q in self.queries.ids:
                        if self.queries.ids[q] == query:
                            queries.append(q)

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
        return rules

    def _fill_data(self, data):
        """ internal use """
        filled = {}
        if ("name" not in data) or ("ruleAction" not in data):
            raise KeyError("Need name to and ruleAction to upload rule", data)

        # for PUT calls, need id, projectName, queryName in addition to the rest of the data below
        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]
            filled["projectName"] = data["projectName"] if ("projectName" in data) else self.project.project_name
            filled["queryName"] = data["queryName"] if ("queryName" in data) else None

        filled["enabled"] = data["enabled"] if ("enabled" in data) else True
        filled["filter"] = data["filter"] if ("filter" in data) else {}
        filled["ruleAction"] = data["ruleAction"]
        filled["name"] = data["name"]
        filled["projectId"] = self.project.project_id

        # validating the query search - comment this out to skip validation
        if "search" in filled["filter"]:
            self.project.validate_rule_search(query=filled["filter"]["search"], language="en")

        if "scope" in data:
            filled["scope"] = data["scope"]
        elif "queryId" in data["filter"]:
            filled["scope"] = "query"
        else:
            filled["scope"] = "project"

        return json.dumps(filled)

    def _name_to_id(self, attribute, setting):
        """ internal use """
        if isinstance(setting, int):
            # already in ID form
            return setting

        elif attribute in ["category", "xcategory"]:
            # setting is a dictionary with one key-value pair, so this loop iterates only once
            # but is necessary to extract the values in the dictionary
            for category in setting:
                parent = category
                child = setting[category][0]
            return self.categories.ids[parent]["children"][child]

        elif attribute in ["parentCategory", "xparentCategory", "parentCategories", "categories"]:
            #plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.categories.ids[s]["id"])
            return ids

        elif attribute in ["tag", "xtag", "tags"]:
            #plural included for get_charts syntax
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(self.tags.ids[s])
            return ids

        elif attribute in ["authorGroup", "xauthorGroup"]:
            authorlists = BWAuthorLists(self.project)
            if not isinstance(setting, list):
                setting = [setting]
            ids = []
            for s in setting:
                ids.append(authorlists.get(s)["id"])
            return ids

        elif attribute in ["locationGroup", "xlocationGroup", "authorLocationGroup", "xauthorLocationGroup"]:
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
        if action in filters.mutable_options and setting not in filters.mutable_options[action]:
            return False
        else:
            return True

    def _id_to_name(self, attribute, setting):
        if not setting or isinstance(setting, str):
            return setting

        if isinstance(setting, list) and isinstance(setting[0], str):
            return setting

        elif attribute in ["tag", "xtag", "addTag", "removeTag"]:
            for tag in self.tags.ids:
                name = self.tags.ids[tag]
                if name == setting:
                    return name

        elif attribute in ["category", "xcategory", "addCategories", "removeCategories"]:
            names = {}
            subcats = []

            for category in self.categories.ids:
                for subcategory in self.categories.ids[category]["children"]:
                    if self.categories.ids[category]["children"][subcategory] in setting:
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
            authorlists = BWAuthorLists(self.project)
            for authorlist in authorlists.ids:
                for aulist in setting:
                    if authorlists.ids[authorlist] == aulist:
                        return authorlist

        elif attribute == "locationGroup" or attribute == "xlocationGroup":
            locationlists = BWLocationLists(self.project)
            for locationlist in locationlists.ids:
                for loclist in setting:
                    if locationlists.ids[locationlist] == loclist:
                        return locationlist

        elif attribute == "authorLocationGroup" or attribute == "xauthorLocationGroup":
            locationlists = BWLocationLists(self.project)
            for locationlist in locationlists.ids:
                for loclist in setting:
                    if locationlists.ids[locationlist] == loclist:
                        return locationlist

        elif attribute == "siteGroup" or attribute == "xsiteGroup":
            sitelists = BWSiteLists(self.project)
            for sitelist in sitelists.ids:
                for slist in setting:
                    if sitelists.ids[sitelist] == slist:
                        return sitelist

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

    def _fill_data(self, data):
        filled = {}

        if ("name" not in data) or ("queries" not in data) or ("subscribers" not in data):
            raise KeyError("Need name, queries and subscribers to create a signal", data)

        for subscriber in data["subscribers"]:
            if ("emailAddress" not in subscriber) or ("notificationThreshold" not in subscriber) or (
                        subscriber["notificationThreshold"] not in [1, 2, 3]):
                raise KeyError(
                    "subscribers must be in the format {emailAddress: emailaddress, notificationThreshold: 1/2/3} where the notificationThreshold must be 1 (all signals), 2 (medium - high priority signals) or 3 (only high priority signals)",
                    subscriber)

        if data["name"] in self.ids:
            filled["id"] = self.ids[data["name"]]
        if "new_name" in data:
            filled["name"] = data["new_name"]
        else:
            filled["name"] = data["name"]

        filled["queryIds"] = []
        for query in data["queries"]:
            filled["queryIds"].append(self.queries.ids[query])

        filled["subscribers"] = data["subscribers"]

        for param in data:
            filled.update(self._name_to_id(param, data[param]))

        return json.dumps(filled)

    def _name_to_id(self, attribute, setting):
        """ internal use """
        ids = []
        if attribute in ["category", "xcategory"]:

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

        elif attribute in ["tag", "xtag"]:
            if not isinstance(setting, list):
                setting = [setting]
            for tag in setting:
                if isinstance(tag, int):
                    # already in ID form
                    ids.append(tag)
                else:
                    ids.append(self.tags.ids[tag])

            if attribute == "tag":
                return {"includeTagIds": ids}
            else:
                return {"excludeTagIds": ids}
        else:
            return {}
