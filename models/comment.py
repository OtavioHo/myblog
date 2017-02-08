from google.appengine.ext import db
from post import Post
from user import Users

class Comments(db.Model):
	post = db.ReferenceProperty(Post, collection_name = "comments")
	content = db.TextProperty(required = True)
	user = db.ReferenceProperty(Users, collection_name = "comments")
	date = db.DateTimeProperty(auto_now_add = True)