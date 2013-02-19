import sys
import pymongo
from pymongo import MongoClient

if len(sys.argv) != 2:
	print 'Usage: python search-gen.py <term-file>'
	sys.exit() 

term_file = sys.argv[1]
#industry_file = sys.argv[2]

wordcloud = open(term_file).read().splitlines()
#industry = open(industry_file).read().splitlines()

# generate search terms
terms = []
for word in wordcloud:
	#for ind in industry:
	#	t = ' '.join([word, ind])
	#	terms.append(t)
	terms.append(word)

for t in terms:
	print t

# Connect to MongoDB
connection = MongoClient()
db = connection.db
all_terms = db.all_terms

# Add terms into record 1. Upsert is set to True so that if the record doesn't exist, it gets created
ret = all_terms.update({'_id': 1},
		       {'$push': {'terms': terms}},
		       True ) 

connection.close()
