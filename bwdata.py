"""
bwrdata contains the BWData class.
"""
import datetime
import filters

class BWData:
    """
    This class is a superclass for brandwatch BWQueries and BWGroups.  It was built to handle resources that access data (e.g. mentions, topics, charts, etc).
    """
    def get_mentions(self, name=None, startDate=None, max_pages=None, **kwargs):
        """
        Retrieves a list of mentions.
        Note: Clients do not have access to full Twitter mentions through the API because of our data agreement with Twitter.

        Args:
            max_pages:  Maximum number of pages to retrieve, where each page is 5000 mentions by default - Optional.  If you don't pass max_pages, it will retrieve all mentions that match your request.
            kwargs:     You must pass in name (list of query/group names), and startDate (string).  All other filters are optional and can be found in filters.py.

        Raises:
            KeyError:   If the mentions call fails.

        Returns:
            A list of mentions.
        """
        params = self._fill_params(name, startDate, kwargs)
        params["pageSize"] = kwargs["pageSize"] if "pageSize" in kwargs else 5000
        params["page"] = kwargs["page"] if "page" in kwargs else 0
        all_mentions = []

        while max_pages == None or params["page"] < max_pages:
            next_mentions = self._get_mentions_page(params, params["page"])

            if len(next_mentions) > 0:
                all_mentions += next_mentions

                if self.console_report:
                    print("Page " + str(params["page"]) + " of " + self.resource_type + " " + name + " retrieved")
            else:
                break

            params["page"] += 1

        if self.console_report:
            print(str(len(all_mentions)) + " mentions downloaded")
        return all_mentions

    def num_mentions(self, name=None, startDate=None, **kwargs):
        """
        Retrieves a count of the mentions in a given timeframe.

        Args:
            kwargs:     You must pass in name (query/group name) and startDate (string).  All other filters are optional and can be found in filters.py.

        Returns:
            A count of the mentions in a given timeframe.
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/count", params=params)

    def get_chart(self, name=None, startDate=None, y_axis=None, x_axis=None, breakdown_by=None, **kwargs):
        """
        Retrieves chart data. 

        Args:
            x_axis:         Pass in the x axis of your chart (string in camel case). See Brandwatch app dropdown menu "Show (Y-Axis)" for options.
            y_axis:         Pass in the y axis of your chart (string in camel case). See Brandwatch app dropdown menu "For (X-Axis)"for options
            breakdown_by:   Pass in breakdown_by (string in camel case). See Brandwatch app dropdown menu "Breakdown by" for options.
            kwargs:         You must pass in name (query name/group) and startDate (string).  All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the specified chart

        """
        if not (x_axis and y_axis and breakdown_by):
            raise KeyError("You must pass in an x_axis, y_axis and breakdown_by")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+y_axis+"/"+x_axis+"/"+breakdown_by, params=params)

    def get_topics(self, name=None, startDate=None, **kwargs):
        """
        Retrieves topics data. 

        Args:
            kwargs: You must pass in name (query name/group) and startDate (string).  All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the topics including everything that can be seen in the chart view of the topics cloud (e.g. the topic, the number of mentions including that topic, the number of mentions by sentiment, the burst value, etc)
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topics/queries", params=params)["topics"]

    def _fill_params(self, name, startDate, data):
        if not name:
            raise KeyError("Must specify query or group name", data)
        elif name not in self.ids:
            raise KeyError("Could not find " + self.resource_type + " " + name, self.ids)
        if not startDate:
            raise KeyError("Must provide start date", data)

        filled = {}
        filled[self.resource_id_name] = self.ids[name]
        filled["startDate"] = startDate
        filled["endDate"] = data["endDate"] if "endDate" in data else (
            datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        for param in data:
            setting = self._name_to_id(param, data[param])
            if self._valid_input(param, setting):
                filled[param] = setting
            else:
                raise KeyError("invalid input for given parameter", param)

        return filled

    def _get_mentions_page(self, params, page):
        params["page"] = page
        mentions = self.project.get(endpoint="data/mentions/fulltext", params=params)

        if "errors" in mentions:
            raise KeyError("Mentions GET request failed", mentions)
        
        return mentions["results"]

    def _valid_input(self, param, setting):
        if (param in filters.params) and (not isinstance(setting, filters.params[param])):
            return False
        elif param in filters.special_options and setting not in filters.special_options[param]:
            return False
        else:
            return True