
import sys
import pymongo
from pymongo import MongoClient

if len(sys.argv) != 2:
	print 'Usage: python search-gen.py <output-dir>'
	sys.exit() 

output_dir = sys.argv[1]

# Connect to MongoDB
connection = MongoClient()
db = connection.db

# get terms
cursor = db.search_terms.find({'_id': 1})
search_terms = cursor[0]['terms']
users = db.users.find()
print "User count: ", users.count()

def gen_terms(search_terms, users):
	# make a list of keywords users interested in
	user_keywords=[]
	for u in users:
		user_keywords=user_keywords+ u['k']
	user_keywords=list(set(user_keywords))

	# find a list of search terms contains user_keyword
	terms=[]
	for t in search_terms:
		for k in user_keywords:
			if t.find(k) != -1 and t not in terms:
				terms.append(t)	
	print terms
	return terms

def build_php_code(terms):
	lines = [
	"<?php",
	"$data = array('keyword' => '"+terms+"');",
	"$ch = curl_init();",
	"curl_setopt($ch, CURLOPT_SLL_VERIFYHOST, 0);",
	"curl_setopt($ch, CURLOPT_SSL_VERFIYPEER, false);",
	"curl_setopt($ch, CURLOPT_URL, 'http://aafter.org/news_search/index1.php?uid=123456&afid=abcdef');",
	"curl_setopt($ch, CURLOPT_POST, 1);",
	"curl_setopt($ch, CURLOPT_POSTFIELDS, $data);",
	"ob_start();",
	"curl_exec($ch);",
	"curl_close($ch);",
	"$str_xml = ob_get_contents();",
	"ob_end_clean();",
	"print $str_xml;",
	"?>"]
	return '\n'.join(lines)

def gen_scripts(search_terms, output_dir):
	for t in search_terms:
		file_name=t.replace(' ','_')
		file_name = file_name+".php"
		print file_name
		f = open(output_dir+'/'+file_name, 'w')
		f.write(build_php_code(t))
		f.close()

terms=gen_terms(search_terms, users)
gen_scripts(terms, output_dir)
