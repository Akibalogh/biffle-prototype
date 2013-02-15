biffle-prototype
================

Prototype for Biffle, a recommendation engine for Developer news
<br>
<br>
Components:
<br><b>article-parse</b>: Parse articles returned from a search
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
"_id": 
"q": "big data mongodb health care"
"sc": "score"
"c": "code"
"sd": "search date"
"pd": "publish date"
"url" "article url"
"abs": "summary text"
"sr": "article source"
"k": keyword list
"f": filename of downloaded full article
"m": metadata (retweets, etc.)
}
</pre>


<b>topics</b> (list of topics)
<pre>{
   "big data": [ "mongodb", "hbase", "infiniDB" ….] 
   "cloud computing": ["sss", "sdfds"]
}</pre>


<b>industries</b>
<pre>{ "in": ["healthcare", "transportation", …] }</pre>


<b>operations</b>
<pre>{"op": [ "deployment", "security", ,..] }</pre>


<b>recommended_articles</b>
<pre>{
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


<b>user_click</b>
<pre>{
"uid": 123,
"act": [ {"k": "keyword1", "c": count}, {"k": "keyword1", "c": count} ]
}</pre>


<b>user</b>
<pre>_id, linkedin unique ID, email address, linkedin interests, industry, keywords(list of products)

{ "_id": MongoDB ID,
  "lid": linkedin unique ID,
  "e": akibalogh@gmail.com,
  "ln": linkedin interests (pulled from profile summary, job summary and skills)
  "in": "computer software",
  "k": ["Greenplum", "InfiniDB"]
  }

TODO: Add weighted keyword?</pre>
