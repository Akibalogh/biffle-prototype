biffle-prototype
================

Prototype for Biffle, a recommendation engine for Developer news
<br>
<br>
Components:
<br><b>parse-and-download</b>: Download and parse news articles and websites
<br><b>profile-parse</b>: Parse a LinkedIn profile and insert into MongoDB
<br><b>search-generation</b>:Generate a combination of search terms based on product names and industries
<br>Written by Victor Hong
<br><b>textrank</b>:Python script that implements nltk to tokenize input text.
<br>Written by Victor Hong
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
