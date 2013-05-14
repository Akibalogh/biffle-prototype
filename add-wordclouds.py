import pymongo
from pymongo import MongoClient
import functools
import math

# Word segmentation script from: http://jeremykun.com/2012/01/15/word-segmentation/
class OneGramDist(dict):
   def __init__(self):
      self.gramCount = 0
      
      for line in open('one-grams.txt'):
         (word, count) = line[:-1].split('\t')
         self[word] = int(count)
         self.gramCount += self[word]
   
   def __call__(self, key):
      if key in self:
         return float(self[key]) / self.gramCount
      else:
         return 1.0 / (self.gramCount * 10**(len(key)-2))

singleWordProb = OneGramDist()
def wordSeqFitness(words):
   return functools.reduce(lambda x,y: x+y, (math.log10(singleWordProb(w)) for w in words))

def memoize(f):
   cache = {}
   
   def memoizedFunction(*args):
      if args not in cache:
         cache[args] = f(*args)
      return cache[args]

   memoizedFunction.cache = cache
   return memoizedFunction

@memoize
def segment(word):
   if not word: return []
   word = word.lower() # change to lower case
   allSegmentations = [[first] + segment(rest) for (first,rest) in splitPairs(word)]
   return max(allSegmentations, key = wordSeqFitness)

def splitPairs(word):
   return [(word[:i+1], word[i+1:]) for i in range(len(word))]

#def splitPairs(word, maxWordLength = 10):
#   upperBound = min(len(word), maxWordLength)
#   return [(word[:i+1], word[i+1:]) for i in range(upperBound)]


users = MongoClient().db.users
wordcloud_coll = MongoClient().db.wordcloud_dictionary

for user in users.find():
	wordcloud = []

	try:
		# Add digital footprint terms from FullContact
		for term in user['fc']['digitalFootprint']['topics']:
			wordcloud.append(term['value'])
	except KeyError:
		pass

	if user.has_key('in'):
		# Add LinkedIn industry
		wordcloud.append(user['in'])
		if user.has_key('sk'):
		# Add LinkedIn skills
			for skill in user['sk']:
				#print user['e'], skill
				wordcloud.append(skill)

	# Get StackOverflow terms
	if user.has_key('ta'):
		for tag in user['ta'][0]:
			wordcloud.append(tag)
	if user.has_key('tq'):
		for tag in user['tq'][0]:
			wordcloud.append(tag)
	if user.has_key('tt'):
		for tag in user['tt'][0]:
			wordcloud.append(tag)

	# Run through wordcloud terms and apply word segmentation
	#for word in wordcloud:
	#	print segment(word)
	
	for word in wordcloud:
		# If the word doesn't exist already
		if(wordcloud_coll.find_one({'w': word}) is None):
			# Write words to MongoDB
			ret = wordcloud_coll.update(    {'w': word},
							{'$set': {'d': word}},
							upsert = True )
		else:
			pass

	wordcloud_corrected = []
	
	for word in wordcloud:
		#outfile.write('\t{0:<10}{1:>55}\n'.format(word, user['e']))
		#outfile.write('\t{0}\n'.format(word)
		word_in_MongoDB = wordcloud_coll.find_one({'w': word})
		if (word_in_MongoDB is None):
			wordcloud_corrected.append(word)
		else:
			wordcloud_corrected.append(word_in_MongoDB['d'])

	if (len(wordcloud) != len(wordcloud_corrected)):
			raise Exception("Wordclouds aren't the same length")

	# Upsert wordcloud into user
	print "Wordcloud with " + str(len(wordcloud_corrected)) + " elements added to " + user['e']
	ret = users.update({'e': user['e']},
	        {'$set': {'wc': wordcloud_corrected}},
	        upsert = True )

