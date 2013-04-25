biffle-prototype
================

Prototype for Biffle, a recommendation engine for Developer news
<br>
<br>
Components:
<br><b>master-shell-script</b>: Controller for scripts below
<br><b>profile-parse</b>: Parse LinkedIn profiles and insert them into MongoDB.
<br><b>SO-tag-download</b>: Download StackOverflow tags for users and add them to the user object
<br><b>/add-wordclouds</b>: Take all of user's tags and create a wordcloud for that individual user, then save it to the user's object
<br><b>search-terms-mongo</b>: Import a data file into MongoDB that contains all of the terms that Biffle 'understands' (currently 100 Big Data database names)
<br><b>search-gen-for-articles</b>: Generate PHP files based on terms that Biffle understands
<br><b>parse-and-download</b>: Download and parse news articles and websites.
<br><b>make-recommendations</b>: Make article recommendations. Currently recommends using ElasticSearch relevance score based on all words in user's word cloud
<br><b>send-recommendations</b>: Sends recommendations to users via email
<br><b>textrank</b>:Python script that implements nltk to tokenize input text
<br><b>/utils/3gram-keyword-dump</b>: Dump all words in a user's wordcloud
<br><b>/utils/add-tweets</b>: Add Tweets to a user's object
<br><b>/utils/SO-all-user-download</b>: Download entire StackOverflow database of users and their email hashes
<br><b>/utils/technorati-scraper</b>: Download URLs for 40,000+ tech blogs from Technorati


<br>

Schemas
=======

<b>articles</b>
<pre>
{
"_id": MongoDB ID
"q": "big data mongodb health care"
"sc": "score"
"c": "code"
"sd": "search date"
"pd": "publish date"
"url" "article url"
"t": "article title"
"abs": "summary text"
"sr": "article source"
"k": keyword list
"f": filename of downloaded full article
"m": metadata (retweets, etc.)
}
</pre>

<b>webpages</b>
<pre>
{
"_id": MongoDB ID
"q": "query"
"nr": "number of total results returned from search query"
"url": "webpage url"
"t": "webpage title"
"md": "meta description content tag"
"mk": "meta keywords"
"abs": "webpage summary"
"s": "webpage score"
"v": "version??",
"k": "keywords in webpage",
"f": "file path on disk"
}
</pre>

<b>topics - Not Implemented</b> (list of topics)
<pre>{
   "big data": [ "mongodb", "hbase", "infiniDB" ….] 
   "cloud computing": ["sss", "sdfds"]
}</pre>


<b>industries</b>
<pre>{ "in": ["healthcare", "transportation", …] }</pre>


<b>operations - Not Implemented</b>
<pre>{"op": [ "deployment", "security", ,..] }</pre>


<b>recommended_articles</b>
<pre>{
"_id": MongoDB ID
"uid": user id
"aid": article id
"rt": recommend_datetime
"ct": click_datetime
"st": save_datetime
"uk": user_keywords_list
"pk": presented_keywords
"lt": like_datetime
"sit": share_datetime
}</pre>

<b>recommended_webpages</b>
<pre>{
"_id": MongoDB ID
"uid": user id
"wid": webpage id
"rt": recommended_datetime
"uk": user_keywords_list
"pk": presented_keywords
}</pre>

<b>user_clicks</b>
<pre>
{
   "_id": MongoDB ID,
   "uid": 123,
   "aid": article id (if article was clicked)
   "wid": webpage id (if webpage was clicked)
   "ad_url": url of ad (if ad was clicked)
   "ct": date/time of click
}</pre>


<b>users</b>
<pre>
{
  "_id": MongoDB ID,
  "lid": linkedin unique ID,
  "e": akibalogh@gmail.com,
  "n": Aki Balogh,
  "ln": linkedin interests (pulled from profile summary, job summary and skills)
  "in": "computer software",
  "k": ["Greenplum", "InfiniDB"]
}</pre>
<br>
<b>TODO: Add weighted keyword?</b>
<br>

<b>so_users</b>
<pre>
{  
   "_id": MongoDB ID,
   "sid": StackOverflow ID,
   "dn": "akibalogh",
   "eh": "2dd0d3404eed2283b5307d16cec68896",
   "l": "Cambridge, MA",
   "w": "linkedin.com/in/akibalogh"
}
</pre>

<b>tech_blogs</b>
<pre>
{  
   "_id": page number of blog on Technorati, (i.e. '1' for http://technorati.com/blogs/directory/technology/page-1)
   "u": list of blog URLs on page
}
</pre>
