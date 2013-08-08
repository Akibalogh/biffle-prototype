import pymongo
from pymongo import MongoClient
import functools
import math
import re
import sys
import os
from datetime import date
import sendgrid

<<<<<<< HEAD
=======
sys.path.append('..')
import local_passwords
SENDMAIL_EMAIL = local_passwords.SENDMAIL_EMAIL
SENDMAIL_PASS = local_passwords.SENDMAIL_PASS

>>>>>>> 3ab802079d1cacd61afabb9188a86cd8a7d7982f
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


def export_wordcloud_to_file(wordcloud_coll, outfilepath):
	outfile = open(outfilepath, 'w')
	for word in wordcloud_coll.find():
		#outfile.write('{0:<25}{1:>60}\n'.format(word['w'], word['d']))
		outfile.write('{0:<50}||{1:>50}\n'.format(word['d'], word['w']))
	outfile.close()

def dump_current_keywords(wordcloud_coll, outfilepath):
	outfile = open(outfilepath, 'w')
	for word in wordcloud_coll.find():
		outfile.write('{0}\n'.format(word['d']))
	outfile.close()

def import_wordcloud_from_file(wordcloud_coll, infilepath):
	infile = open(infilepath, 'r')

	for line in infile.readlines():
		try:
			#parsed_line = re.search('(.+)||(.+)\n', line)
			#word = parsed_line.group(2)
			#word_corrected = parsed_line.group(1)
			#print word_corrected
			word_corrected, word = line.rstrip().split('||')
		except:
			print "ERROR parsing: " + line.rstrip()

		# Write words to MongoDB
		ret = wordcloud_coll.update(    {'w': word.lstrip(' ')},
						{'$set': {'d': word_corrected.rstrip(' ')}},
						upsert = True )

	# Delete the exported file
        os.unlink(infilepath)

def sendkeywordfile(dumpfilename, fulldumpfilepath):
<<<<<<< HEAD
        s = sendgrid.Sendgrid('akibalogh@gmail.com', 'Generation1234!', secure=True)
        message = sendgrid.Message("aki@biffle.co", "Today's Biffle Keywords",
=======
        s = sendgrid.Sendgrid(SENDMAIL_EMAIL, SENDMAIL_PASS, secure=True)
        message = sendgrid.Message(SENDMAIL_EMAIL, "Today's Biffle Keywords",
>>>>>>> 3ab802079d1cacd61afabb9188a86cd8a7d7982f
                "plaintext message body", "Today's keywords in the attachment")

	if (os.path.isfile(fulldumpfilepath)):
		message.add_attachment(dumpfilename, fulldumpfilepath) 
	else:
		print "ERROR: Attachment not found", fulldumpfilepath

<<<<<<< HEAD
        # Email Subhankar
        message.add_to("sray@bostonpredictiveanalytics.com")

	# Email Ted
        message.add_to("yangxiao9901@gmail.com")
	
        message.add_to("aki@informite.com") # CC: Aki on everything for testing purposes
=======
        message.add_to(SENDMAIL_EMAIL) # CC: on everything for testing purposes
>>>>>>> 3ab802079d1cacd61afabb9188a86cd8a7d7982f

        # use the Web API to send your message
        s.web.send(message)
        # use the SMTP API to send your message
        #s.smtp.send(message)


if __name__ == "__main__":
	if (len(sys.argv) != 2):
	        print 'Usage: python curate-wordcloud.py (export|import|dump)'
       		sys.exit()
	
	command = sys.argv[1].rstrip()

	if (command not in ['import', 'export', 'dump']):
	        print 'Usage: python curate-wordcloud.py (export|import|dump)'
       		sys.exit()

	wordcloud_coll = MongoClient().db.wordcloud_dictionary
	filepath = 'exported_wordcloud'
	
	dumpfilename = "keyword_" + str(date.today().strftime('%Y_%m_%d')) + ".txt"
	fulldumpfilepath = "/root/biffle-prototype/sub_api/" + dumpfilename

	if (command == 'export'):
		export_wordcloud_to_file(wordcloud_coll, filepath)
	elif (command == 'import'):
		import_wordcloud_from_file(wordcloud_coll, filepath)
	elif (command == 'dump'):
		dump_current_keywords(wordcloud_coll, fulldumpfilepath)
		sendkeywordfile(dumpfilename, fulldumpfilepath)		
	else:
		raise Exception("ERROR: Invalid argument")
