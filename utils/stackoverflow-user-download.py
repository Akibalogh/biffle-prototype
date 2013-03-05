import SEAPI
import pymongo
from pymongo import MongoClient

connection = MongoClient()
db = connection.db
so_users = db.so_users

so = SEAPI.SEAPI(site="stackoverflow")

# NOTE: min_delay of 0.5 should be acceptable
# As of Feb 27 2013, there were 1.7M users on StackOverflow. Thus page limit around 30,000 should be acceptable
# To make less than 10,000 API requests per day, set the delay to 10 seconds (max delay 8.64s)
#so_fetched_users = so.fetch("users", db, min_delay=0.5, page_limit=10)
so_fetched_users = so.fetch("users", db, min_delay=10, page_limit=30000)

print "Download and insert finished. Status: " + str(so.last_status)

user_counter = so_users.find().count()
no_em_counter = so_users.find({ "eh": "" }).count()


if (user_counter > 0):
	print "Unable to get email hash for " + str(no_em_counter) + "/" + str(user_counter) + " users (" + str(float(float(no_em_counter) / float(user_counter)) * 100) + "%)"
