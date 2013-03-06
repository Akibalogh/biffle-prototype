# Note: this library was forked from https://github.com/stared/se-api-py

import requests
import pymongo
from pymongo import MongoClient
try:
    import simplejson as json
except:
    import json
from time import time, sleep
import sys

class SEAPI():
    def __init__(self, key, **kwargs):
        """Use kwargs to set default parameters, e.g.
        >>> se = SEAPI(site="stackoverflow")"""
        self.default_params = {"pagesize": 100}  # explicit "pagesize" is required
        self.default_params.update(kwargs)

        self.api_address = "http://api.stackexchange.com"
        self.api_version = "2.1"
        self.key = key
        self.access_token = ""

        if self.key:
            self.default_params['key'] = self.key
        if self.access_token:
            self.default_params['access_token'] = self.access_token

        self.last_call = ["", {}]
        self.last_status = {}
        self.last_response_times = []

    def _find_placeholders(self, raw_command, **kwargs):
        parts = raw_command.split("/")
        curly_params = {}   # e.g. for "{id}"
        curly_list_params = {}  # e.g. for "{ids}"; and dict with max 1 element
        for part in parts:
            if part.startswith("{"):
                if part.endswith("s}"):
                    curly_list_params[part[1:-1]] = kwargs[part[1:-1]]
                elif part.endswith("}"):
                    curly_params[part[1:-1]] = kwargs[part[1:-1]]
        return (parts, curly_params, curly_list_params)

    def _combine_placeholders(self, parts, curly_params, curly_list_params):
        parts_filled = parts[:]
        for i, part in enumerate(parts_filled):
            if part.startswith("{"):
                if part.endswith("s}"):
                    parts_filled[i] = ";".join(map(str, curly_list_params[part[1:-1]]))
                elif part.endswith("}"):
                    parts_filled[i] = str(curly_params[part[1:-1]])
        return "/".join(parts_filled)

    def _chunks(self, li, k):
        """Splits a list in list of k elements, e.g.
        >>> split([2, 3, 5, 7, 11, 13, 17, 19], 3)
        [[2, 3, 5], [7, 11, 13], [17, 19]]"""
        return [li[i:(i + k)] for i in xrange(0, len(li), k)]

    def clean_return(self, fetch_return, so_users):
	return_list = []

	for user in fetch_return:
		# Ignore users already in MongoDB
		if (so_users.find_one({"sid": user['user_id']}) == None):
			try:
        	        	email_hash = user['profile_image'][31:63]
	        	        if(len(email_hash) < 32):
                       			email_hash = ""
		        except KeyError:
        		        email_hash = ""

		        try:
        		        location = user['location']
	        	except KeyError:
        	        	location = ""

		        try:
        		        web_url = user['website_url']
	       		except KeyError:
        		        web_url = ""

			single_user = {  
				"sid": user['user_id'],
				"dn": user['display_name'],
				"eh": email_hash,
				"l": location,
				"w": web_url }
			return_list.append(single_user)
	return return_list


    def fetch_one(self, command, subcommand=False, parse_curly_parameters=True, **kwargs):
        """Returns one page of results for a given command;
        EXAMPLE:
        >>> seapi.fetch_one("users/{ids}", ids=[1,3,7,9,13], site="stackoverflow")
        >>> seapi.fetch_one("posts", order="desc", sort="votes", site="stackoverflow", page=3)"""

        parameters = self.default_params.copy()

        if parse_curly_parameters:
            parts, curly_params, curly_list_params = self._find_placeholders(command, **kwargs)
            command = self._combine_placeholders(parts, curly_params, curly_list_params)
            parameters.update(
                dict([(k, v) for k, v in kwargs.items()
                if (k not in curly_params) and (k not in curly_list_params)])
                )
        else:
            parameters.update(kwargs)

        url = "%s/%s/%s" % (self.api_address, self.api_version, command)

        t0 = time()
        r = requests.get(url, params=parameters)
        if not subcommand:
            self.last_response_times = []
        self.last_response_times.append(time() - t0)

        data = json.loads(r.content)
        self.last_call = [url, parameters]
        self.last_status = dict([(k, data[k]) for k in data if k != 'items'])

        return data['items']

    def fetch(self, command, mongo_db, starting_page=1, page_limit=2000, print_progress=True, min_delay=0.05, **kwargs):
        """Returns all pages (withing the limit) of results for a given command;
        automatically splits lists for {ids} in appropriate chunks
        EXAMPLE -> check for fetch_one (without 'page' parameter!)
        NOTE: Here is a lot of room for improvements and additional features, e.g.:
        - gevent for concurrency to get optimal rate
        - dealing with 'Violation of backoff parameter' """
	so_users = mongo_db.so_users
        res = []
        self.last_response_times = []
        parts, curly_params, curly_list_params = self._find_placeholders(command, **kwargs)

        parameters = self.default_params.copy()
        parameters.update(
            dict([(k, v) for k, v in kwargs.items()
            if (k not in curly_params) and (k not in curly_list_params)])
            )

        if curly_list_params:
            assert(len(curly_list_params) == 1)
            curly_name, curly_list = curly_list_params.items()[0]
            pieces = self._chunks(curly_list, parameters['pagesize'])
            for piece in pieces:
                command = self._combine_placeholders(parts, curly_params, {curly_name: piece})
                fetch_return = self.fetch_one(command, subcommand=True, parse_curly_parameters=False, **parameters)
		fetch_return = self.clean_return(fetch_return, so_users)
		if (len(fetch_return) > 0):
			ret = so_users.insert(fetch_return)
   		res += fetch_return
                # ^ maybe also with try/except/once_again?
                if self.last_response_times[-1] < min_delay:
                        sleep(min_delay - self.last_response_times[-1])
                        if print_progress:
                            print "Waited {0:.2} sec. API calls left: {1}. Total users: {2}".format(min_delay - self.last_response_times[-1], self.last_status['quota_remaining'], so_users.count())
        else:
            command = self._combine_placeholders(parts, curly_params, {})
            if print_progress:
                print "Fetching pages: \n",
            for i in xrange(starting_page, starting_page + page_limit):
                if print_progress:
                    print i,
                try:
                    fetch_return = self.fetch_one(command, subcommand=True, parse_curly_parameters=False, page=i, **parameters)
		    fetch_return = self.clean_return(fetch_return, so_users)
		    if (len(fetch_return) > 0):
		    	ret = so_users.insert(fetch_return)
		    res += fetch_return
                except:
                    print sys.exc_info()
                    print self.last_status
		    print "waiting 60s and trying once more"  # mainly for 'Violation of backoff parameter'
                    sleep(60.)
		    fetch_return = self.fetch_one(command, subcommand=True, parse_curly_parameters=False, page=i, **parameters)
		    fetch_return = self.clean_return(fetch_return, so_users)
		    if (len(fetch_return) > 0):
		    	ret = so_users.insert(fetch_return)
		    res += fetch_return
                if not self.last_status['has_more']:
                    break
                if self.last_response_times[-1] < min_delay:
                    sleep(min_delay - self.last_response_times[-1])
                    if print_progress:
                        print "Waited {0:.2} sec. API calls left: {1}. Total users: {2}".format(min_delay - self.last_response_times[-1], self.last_status['quota_remaining'], so_users.count())
        return res

    def status_of(self, command, **kwargs):
        self.fetch_one(command, **kwargs)
        return self.last_status

