from google.appengine.ext import db
from user import Users
from post import Post

class Likes(db.Model):
	user = db.ReferenceProperty(Users, collection_name="likes")
	post = db.ReferenceProperty(Post, collection_name="likes")