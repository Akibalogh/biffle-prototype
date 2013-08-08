import sys
import pymongo
from pymongo import MongoClient
import itertools
from itertools import combinations

import local_passwords
AAFTER_CURL_URL = local_passwords.AAFTER_CURL_URL

def gen_terms(all_terms, users):
	# make a list of lists with keywords and options that users are interested in
	query_term_options = []

	for u in users:
		for k in u['k']:
			all_option_combinations = []

			if (isinstance(u['opt'], basestring)):
				# There is only one option
				all_option_combinations.append(u['opt'])
				option = u['opt']
			
				option_combination = ""
				option_combination_in_query = ""
			
				# Generate query using term without option	
				query = '\\"' + k + '\\"' + option_combination_in_query
				query_term_options.append([query, k, option_combination])
				
				# Generate query using term with option
				option_combination_in_query += ' ' + '\\"' + str(option) + '\\"'
				option_combination += ' ' + str(option)
				
				query = '\\"' + k + '\\"' + option_combination_in_query
				query_term_options.append([query, k, option_combination])
			else:
				# There are multiple options; look for combinations
				all_option_combinations = generate_option_combinations(u['opt'])

				for i in range(len(all_option_combinations)):
					option_combination = " "
					option_combination_in_query = " "

					for option in all_option_combinations[i]:
						option_combination_in_query += '\\"' + str(option) + '\\" '
						option_combination +=  str(option) + ' '

					query = '\\"' + k + '\\"' + option_combination_in_query

					# Remove last ' ' from variables
					option_combination = option_combination.rstrip(' ')
					query = query.rstrip(' ')

					query_term_options.append([query, k, option_combination])
	return query_term_options

def build_php_code(query, priority, seed_url):
	lines = [
	"<?php",
	"$data = array(",
	"'keyword' => \"" + query + '",',
	"'priority' => '" + priority + "',",
#	"'seed_url' => '" + seed_url + "'",
	"'exclude_domain' => \"meetup.com\"",
	");",
	"$ch = curl_init();",
	"curl_setopt($ch, CURLOPT_SLL_VERIFYHOST, 0);",
	"curl_setopt($ch, CURLOPT_SSL_VERFIYPEER, false);",
	"curl_setopt($ch, CURLOPT_URL, '"+AAFTER_CURL_URL+"');",
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

def gen_scripts_from_qto(file_name, term, option, query, output_dir):
	# Generate .php files for all news articles
	file_name = file_name + ".php"
	print file_name + " created"

	# TODO: Generate real priorities
	priority = "10"

	# TODO: Implement seed_urls. Right now passing blank
	seed_url = ""

	f = open(output_dir+'/'+file_name, 'w')
	f.write(build_php_code(query, priority, seed_url))
	f.close()

def gen_scripts_from_term(file_name, term, output_dir):
	# Generate .php files for all news articles
	file_name = file_name + ".php"
	print file_name + " created"

	# TODO: Generate real priorities
	priority = "10"

	# TODO: Implement seed_urls. Right now passing blank
	seed_url = ""

	f = open(output_dir+'/'+file_name, 'w')
	f.write(build_php_code(term, priority, seed_url))
	f.close()

def generate_option_combinations(options):
	# For every term-option combination, generate a corresponding term-option script
	# Ex: given term and options = [option1, option2], generate:
	# term
	# term option1
	# term option1 option2
	# term option2

	all_option_combinations = []

	for i in range(0, len(options) + 1):	
		for subset in itertools.combinations(options, i):
			all_option_combinations.append(subset)

	return all_option_combinations


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print 'Usage: python search-gen.py <output-dir>'
		print 'Defaulting to /var/www/html/search-scripts/'
		output_dir = '/var/www/html/search-scripts/' 
	else:
		output_dir = sys.argv[1]

	# Connect to MongoDB
	connection = MongoClient()
	db = connection.db
	cursor = db.all_terms.find({'_id': 1})
	all_terms = cursor[0]['terms']
	users = db.users.find()
	#print "User count: ", users.count()
	

	# Generate scripts based on terms recognized from a user's profile
	#query_term_options = gen_terms(all_terms, users)
	#queries = db.queries

	# save 1 record with _id 1. Upsert is set to true
	#ret = queries.save({'_id': 1, 'q': query_term_options})

	#for qto in query_term_options:
	#	query = qto[0]
	#	term = qto[1]
	#	option = qto[2]

	#	#print "Option-combination = " + option

	#	file_name = (term + "-" + option).replace(' ','_').replace('/','_')
	#	gen_scripts_from_qto(file_name, term, option, query, output_dir)
	
	connection.close()

	for term in all_terms[0]:
		file_name = term.replace(' ','_').replace('/','_')
		gen_scripts_from_term(file_name, term, output_dir)
