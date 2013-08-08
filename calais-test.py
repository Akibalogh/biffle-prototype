#import httplib2
import urllib2
import json

import local_passwords
CALAIS_API_KEY = local_passwords.CALAIS_API_KEY
 
# Some sample text from a news story to pass to Calais for analysis
test_body = """
Some huge announcements were made at Apple's Worldwide Developer's Conference Monday, including the new mobile operating system iOS 5, PC software OS X Lion, and the unveiling of the iCloud.
"""
 
def get_calais_anotation(text, calais_api_key):
    headers = {
        'x-calais-licenseID': calais_api_key,
        'content-type': 'text/raw',
        'enableMetadataType': 'GenericRelations,SocialTags',
        'accept': 'application/json'
    }
 
    CALAIS_TAG_API = 'http://api.opencalais.com/tag/rs/enrich'

    req = urllib2.Request(CALAIS_TAG_API, data=text, headers=headers)
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        print e.code
        print e.read()
    
    result = response.read()
    anotation =  json.loads(result)

    entities = []
    social_tags = []
    topics = []
    for i in anotation.iteritems():
	typeGroup = i[1].get('_typeGroup')
	if typeGroup == 'entities':
	    entities.append({i[1].get('_type'): i[1].get('name')})
	if typeGroup == 'socialTag':
	    social_tags.append(i[1].get('name'))
	if typeGroup == 'topics':
	    topics.append(i[1].get('categoryName'))

    return {'entities': entities, 'topics': topics, 'socialTags': social_tags}
content = get_calais_anotation(test_body, CALAIS_API_KEY)
print content
#print json.dumps(content, indent=4) 



