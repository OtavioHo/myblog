from google.appengine.ext import db
from user import Users
from google.appengine.api import users
from google.appengine.ext import db

class Post(db.Model):
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	date = db.DateTimeProperty(auto_now_add = True)
	user_id = db.IntegerProperty(required = True)

	def post_id(self):
		return str(self.key().id())
