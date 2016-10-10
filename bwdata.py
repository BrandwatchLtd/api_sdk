"""
bwdata contains the BWData class.
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
            name:       You must pass in a query / group name (string).
            startDate:  You must pass in a start date (string).
            max_pages:  Maximum number of pages to retrieve, where each page is 5000 mentions by default - Optional.  If you don't pass max_pages, it will retrieve all mentions that match your request.
            kwargs:     All other filters are optional and can be found in filters.py.

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
            name:       You must pass in a query / group name (string).
            startDate:  You must pass in a start date (string).
            kwargs:     All other filters are optional and can be found in filters.py.

        Returns:
            A count of the mentions in a given timeframe.
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/count", params=params)['mentionsCount']

    def get_chart(self, name=None, startDate=None, y_axis=None, x_axis=None, breakdown_by=None, **kwargs):
        """
        Retrieves chart data. 

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            y_axis:         Pass in the y axis of your chart (string in camel case). See Brandwatch app dropdown menu "For (Y-Axis)" for options
            x_axis:         Pass in the x axis of your chart (string in camel case). See Brandwatch app dropdown menu "Show (X-Axis)" for options.
            breakdown_by:   Pass in breakdown_by (string in camel case). See Brandwatch app dropdown menu "Breakdown by" for options.
            kwargs:         You must pass in name (query name/group) and startDate (string).  Additionally, if you x_axis or breakdown_by consists of categories or tags you must pass in dim1Args or dim2Args, respectively, which should be a list of the names of those cats/tags. All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the specified chart

        Raises:
            KeyError:       If you fail to pass in x_axis, y_axis or breakdown_by.

        """
        if not (y_axis and x_axis and breakdown_by):
            raise KeyError("You must pass in an y_axis, x_axis and breakdown_by")

        params = self._fill_params(name, startDate, kwargs)
        if "dim1Args" in params:
            params["dim1Args"] = self._name_to_id(x_axis, params["dim1Args"])
        if "dim2Args" in params:
            params["dim2Args"] = self._name_to_id(breakdown_by, params["dim2Args"])

        return self.project.get(endpoint="data/"+y_axis+"/"+x_axis+"/"+breakdown_by, params=params)

    def get_topics(self, name=None, startDate=None, **kwargs):
        """
        Retrieves topics data. 

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the topics including everything that can be seen in the chart view of the topics cloud (e.g. the topic, the number of mentions including that topic, the number of mentions by sentiment, the burst value, etc)
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topics/queries", params=params)["topics"]

    def get_topics_comparison(self, name=None, startDate=None, **kwargs):
        """
        Retrieves topics comparison data. 

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the topics including everything that can be seen in the chart view of the topics comparison (e.g. the topic, the number of mentions including that topic, the number of mentions by sentiment, the burst value, etc)
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topics/compare/gender", params=params)["topics"]

    def get_authors(self, name=None, startDate=None, **kwargs):
        """
        Retrieves author data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the authors including everything that can be seen in the list of authors
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topauthors/queries", params=params)["results"]
        
    def get_history(self, name=None, startDate=None, **kwargs):
        """
        Retrieves history data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the history component, all the points of time that the timeline covers
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/queries/days", params=params)["results"]
    
    def get_topsites(self, name=None, startDate=None, **kwargs):
        """
        Retrieves top sites data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of top sites
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topsites/queries", params=params)["results"]
        
    def get_tweeters(self, name=None, startDate=None, **kwargs):
        """
        Retrieves tweeters data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of top tweeters
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/toptweeters/queries", params=params)["results"]
        
    def get_volume(self, name=None, startDate=None, **kwargs):
        """
        Retrieves volume data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of volume data
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/queries/pageTypes", params=params)["results"]

    def get_world(self, name=None, startDate=None, **kwargs):
        """
        Retrieves world overview (mentions map) data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of mapped mentions on a globe data
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/queries/countries", params=params)["results"]["values"]

    def get_keyinsights(self, name=None, startDate=None, **kwargs):
        """
        Retrieves key insights component data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the component key insights
        """
        key_insights = {"total_mentions":self.get_keyinsights_mention_count(name, startDate),
        "unique_authors":self.get_keyinsights_author_count(name, startDate),
        "topic_trends":self.get_keyinsights_topics(name, startDate),
        "rising_news":self.get_keyinsights_news(name, startDate)}
        return key_insights


    def get_keyinsights_mention_count(self, name=None, startDate=None, **kwargs):
        """
        Retrieves total mentions count data from key insights component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            An integer that represents the total number of mentions
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/count", params=params)["mentionsCount"]

    def get_keyinsights_author_count(self, name=None, startDate=None, **kwargs):
        """
        Retrieves total unique authors count data from key insights component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            An integer that represents the total number of unique authors
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/authors/months/queries", params=params)["results"][0]["values"][0]["value"] 

    def get_keyinsights_topics(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the top 3 trending topics data from key insights component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the top 3 trending topics
        """
        params = self._fill_params(name, startDate, kwargs)
        params["limit"] = kwargs["limit"] if "limit" in kwargs else 3
        return self.project.get(endpoint="data/volume/topics/queries", params=params)["topics"]

    def get_keyinsights_news(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the top 3 rising news data from the key insights component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the rising top 3 rising news urls
        """
        params = self._fill_params(name, startDate, kwargs)
        params["pageSize"] = kwargs["pageSize"] if "pageSize" in kwargs else 3
        return self.project.get(endpoint="data/mentions", params=params)["results"]

    def get_summary(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the summary component data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the summary component analysis
        """
        summary = {"sentiment":self.get_summary_sentiment(name, startDate),
        "topsites":self.get_summary_topsites(name, startDate),
        "pagetypes":self.get_summary_pagetypes(name, startDate)}
        return summary

    def get_summary_sentiment(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the sentiment data from the summary component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the summary sentiment analysis 
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/sentiment/days", params=params)["results"]

    def get_summary_topsites(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the top sites data from the summary component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the summary sites analysis 
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topsites/queries", params=params)["results"]

    def get_summary_pagetypes(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the top page type data from the summary component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the summary page type analysis 
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/queries/pageTypes", params=params)["results"]

    def get_twitter_insights(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the twitter insights component data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the twitter insights component data    
        """
        twitter_insights = {"hashtags":self.get_twitter_insights_feature(name,startDate,"hashtags"),
        "emoticons":self.get_twitter_insights_feature(name,startDate,"emoticons"),
        "urls":self.get_twitter_insights_feature(name,startDate,"urls"),
        "mentionedauthors":self.get_twitter_insights_feature(name,startDate,"mentionedauthors")}
        return twitter_insights

    def get_twitter_insights_feature(self, name=None, startDate=None, feature=None, **kwargs):
        """
        Retrieves the a feature from the twitter insights component.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            feature:        Pass in a feature of the twitter insights component (written in lowercase within a string). This is either hashtags, emoticons, urls, or mentionedauthors.
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns:
            A dictionary representation of the feature of the twitter insights analysis component
        """
        if not (feature):
            raise KeyError("You must pass in a feature")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+feature, params=params)

    def get_volume_group(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the volume for group data.

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            kwargs:         All other filters are optional and can be found in filters.py.
            
        Returns:
            A dictionary representation of the volume for group data
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/queries/sentiment", params=params)["results"]

    def get_date_range_comparison(self, name=None, startDate=None, date_ranges=None, **kwargs):
        """
        Retrieves the date range data

        Args:
            name:           You must pass in a query / group name (string).
            startDate:      You must pass in a start date (string).
            date_ranges:    You must pass in date range(s) ([list] of strings).
            kwargs:         All other filters are optional and can be found in filters.py.
        
        Returns: 
            A dictionary representation of the date range data applied on the query

        Raises:
            KeyError:       If you fail to pass in a date range
        """
        query_id = self.ids[name]
        date_range_list = self._get_date_ranges(query_id)
        date_range_ids = [dr["id"] for dr in date_range_list if dr["name"] in date_ranges]
        
        if (date_range_ids == [] or date_ranges == None) :
            raise KeyError("You must pass in a valid list of date range(s)")

        params = self._fill_params(name, startDate, kwargs)
        params["dateRanges"] = date_range_ids
        return self.project.get(endpoint="data/volume/dateRanges/days", params = params)["results"]

        ## Channels

    def get_fb_analytics(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the entire facebook analytics component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the entire facebook analytics component data    
        """
        fb_analytics = {"audience":self.get_fb_analytics_partial(name,startDate,"audience"),
        "ownerActivity":self.get_fb_analytics_partial(name,startDate,"ownerActivity"),
        "audienceActivity":self.get_fb_analytics_partial(name,startDate,"audienceActivity"),
        "impressions":self.get_fb_analytics_partial(name,startDate,"impressions")}
        return fb_analytics
        
    def get_fb_analytics_partial(self, name=None, startDate=None, metadata_type=None, **kwargs):
        """
        Retrieves the specified part of the facebook analytics component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).
            metadata_type:  You must pass in the type of facebook analytics data you want (string). This can be either audience, ownerActivity, audienceActivity, or impressions.

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the specified part of the facebook analytics component data    
        """
        if not (metadata_type):
            raise KeyError("You must pass in a metadata_type")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+metadata_type+"/queries/days", params = params)["results"][0]["values"]

    def get_fb_audience(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the facebook audience component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of facebook authors, each having a dictionary representation of their respective facebook data    
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/topfacebookusers/queries", params = params)["results"]

    def get_fb_comments(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the facebook comments component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of facebook authors, each having a dictionary representation of their respective facebook data    
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/facebookcomments", params = params)["results"]

    def get_fb_posts(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the facebook posts component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of facebook authors, each having a dictionary representation of their respective facebook data    
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/facebookposts", params = params)["results"]

    def get_ig_interactions(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the entire instagram interactions component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the entire instagram interactions component data.   
        """
        instagram_interactions ={"ownerActivity":self.get_ig_interactions_partial(name,startDate,"ownerActivity"),
        "audienceActivity":self.get_ig_interactions_partial(name,startDate,"audienceActivity")}
        return instagram_interactions

    def get_ig_interactions_partial(self, name=None, startDate=None, metadata_type=None, **kwargs):
        """
        Retrieves the specified part of the instagram interactions component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).
            metadata_type:  You must pass in the type of instagram interactions data you want (string). This can be either ownerActivity or audienceActivity.

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the specified part of the instagram interactions component data.   
        """
        if not (metadata_type):
            raise KeyError("You must pass in a metadata_type")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+metadata_type+"/queries/days", params = params)["results"][0]

    def get_ig_insights(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the entire instagram owner insights component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the entire instagram owner insights component data.   
        """
        instagram_insights ={"mentionedauthors":self.get_ig_insights_partial(name,startDate,"mentionedauthors"),
        "hashtags":self.get_ig_insights_partial(name,startDate,"hashtags"),
        "emoticons":self.get_ig_insights_partial(name,startDate,"emoticons")}
        return instagram_insights

    def get_ig_insights_partial(self, name=None, startDate=None, metadata_type=None, **kwargs):
        """
        Retrieves the specified part of the instagram owner insights component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).
            metadata_type:  You must pass in the type of instagram insights data you want (string). This can be either hashtags, mentionedauthors, or emoticons.

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of authors, hashtags, or emoticons, each having a dictionary representation of their respective instagram insights data    
        """
        if not (metadata_type):
            raise KeyError("You must pass in a metadata_type")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+metadata_type, params = params)["results"]

    def get_ig_posts(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the instagram posts component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of instagram authors, each having a dictionary representation of their respective instagram data 
        """

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions", params = params)["results"]

    def get_ig_followers(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the instagram total followers component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list with the follower count for each day in the date range, each day having a dictionary representation of their respective instagram follower count data 
        """

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/audience/queries/days", params = params)["results"][0]["values"]
    
    def get_tweets(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the twitter tweets component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of tweets with author, location, and other metadata, each tweet having a dictionary representation of their respective tweet data 
        """

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/mentions/tweets", params = params)["results"]
        
    def get_tw_analytics(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the entire twitter analytics component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the entire twitter analytics component data    
        """
        tw_analytics = {"audience":self.get_tw_analytics_partial(name,startDate,"audience"),
        "ownerActivity":self.get_tw_analytics_partial(name,startDate,"ownerActivity"),
        "audienceActivity":self.get_tw_analytics_partial(name,startDate,"audienceActivity"),
        "impressions":self.get_tw_analytics_partial(name,startDate,"impressions")}
        return tw_analytics

    def get_tw_analytics_partial(self, name=None, startDate=None, metadata_type=None, **kwargs):
        """
        Retrieves the specified part of the twitter analytics component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).
            metadata_type:  You must pass in the type of twitter analytics data you want (string). This can be either audience, ownerActivity, audienceActivity, or impressions.

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the specified part of the twitter analytics component data    
        """
        if not (metadata_type):
            raise KeyError("You must pass in a metadata_type")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/"+metadata_type+"/queries/days", params = params)["results"][0]["values"]

    def get_tw_audience(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the twitter audience component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A list of twitter authors, each having a dictionary representation of their respective twitter data    
        """
        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="data/volume/toptweeters/queries", params = params)["results"]

    def get_dem_summary(self, name=None, startDate=None, **kwargs):
        """
        Retrieves the entire demographics summary component data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).

            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the entire demographics summary component data    
        """
        dem_summary = {"gender":self.get_dem_summary_partial(name,startDate,"gender"),
        "interest":self.get_dem_summary_partial(name,startDate,"interest"),
        "profession":self.get_dem_summary_partial(name,startDate,"profession"),
        "countries":self.get_dem_summary_partial(name,startDate,"countries")}
        return dem_summary

    def get_dem_summary_partial(self, name=None, startDate=None, metadata_type=None, **kwargs):
        """
        Retrieves a specified part of the demographic summary component data extracted from twitter data.

        Args:
            name:           You must pass in a channel / group name (string).
            startDate:      You must pass in a start date (string).
            metadata_type:  You must pass in the type of demographic summary data you want (string). This can be either gender, interest, profession, or countries.


            kwargs:         All other filters are optional and can be found in filters.py.
               
        Returns: 
            A dictionary representation of the top breakdowns (gender, interest, etc) 
        """

        if not (metadata_type):
            raise KeyError("You must pass in a metadata_type")

        params = self._fill_params(name, startDate, kwargs)
        return self.project.get(endpoint="demographics/"+metadata_type, params = params)

    def _get_date_ranges(self, query_id=None):
        """
        Helper method: Gets the date range for a query

        Args: 
            query_id:       You must pass in a query / group id (integer).
            date_ranges:    You must pass in date range(s) ([list] of strings).

        Returns:
            A dictionary representation of the date ranges available for the specified query 
        
        """ 
        return self.project.get(endpoint="queries/"+str(query_id)+"/"+"date-range")   

    def _fill_params(self, name, startDate, data):
        try:
            int(name)
            numerical = True
        except ValueError:
            numerical = False

        if not name:
            raise KeyError("Must specify query or group name", data)
        elif numerical:
            if int(name) not in self.ids.values():
                raise KeyError("Could not find " + self.resource_type + " " + name, self.ids)
        elif not numerical:
            if name not in self.ids:
                raise KeyError("Could not find " + self.resource_type + " " + name, self.ids)
        if not startDate:
            raise KeyError("Must provide start date", data)

        filled = {}
        if numerical:
            filled[self.resource_id_name] = name
        else:
            filled[self.resource_id_name] = name

        filled["startDate"] = startDate
        filled["endDate"] = data["endDate"] if "endDate" in data else (
            datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        if "orderBy" in data:
            filled["orderBy"] = data["orderBy"]
        if "orderDirection" in data:
            filled["orderDirection"] = data["orderDirection"]

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