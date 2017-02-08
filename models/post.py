from user import Users
from google.appengine.api import users
from google.appengine.ext import db

class Post(db.Model):
	user = db.ReferenceProperty(Users, collection_name="posts")
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	date = db.DateTimeProperty(auto_now_add = True)
	
	def post_id(self):
		return str(self.key().id())
