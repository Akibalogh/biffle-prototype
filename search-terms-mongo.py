
import sys
import pymongo
from pymongo import MongoClient

if len(sys.argv) != 3:
	print 'Usage: python search-gen.py <term-file> <industry-file>'
	sys.exit() 

term_file = sys.argv[1]
industry_file = sys.argv[2]

wordcloud = open(term_file).read().splitlines()
industry = open(industry_file).read().splitlines()

# generate search terms
terms = []
for word in wordcloud:
	for ind in industry:
		t = ' '.join([word, ind])
		terms.append(t)
	terms.append(word)

for t in terms:
	print t

# Connect to MongoDB
connection = MongoClient()
db = connection.db
search_terms = db.all_terms

# save 1 record with _id 1
ret = search_terms.save({'_id': 1, 'terms': terms})
print ret

connection.close()
