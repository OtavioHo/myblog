# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import urllib
import random
import hashlib
import string
import hmac

from collections import namedtuple

from google.appengine.api import users
from google.appengine.ext import db

import webapp2
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   autoescape = True)
SECRET = 'NSLlYWrouJa40kFPavLS'

from models import Post
from models import Users
from models import Likes
from models import Comments


def make_valid_cookie(user_id):
	h = hmac.new(SECRET, user_id).hexdigest()
	cookie = str(user_id + "|" + h)
	return cookie

def is_valid_cookie(h):
	val = h.split('|')[0]
	if h == make_valid_cookie(val):
		return val

def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
	salt = h.split('|')[1]
	return h == make_pw_hash(name, pw, salt)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class RenderPost:
	def render_post(self, post):
		name = post.user.username
		pid = post.post_id()
		return render_str("post.html", post = post, pid = pid)

class RenderComment:
	def render_comment(self, comment):
		return render_str("comment.html", comment = comment)

class Nav:
	def __init__(self, link3, link4, nav3, nav4):
		self.link3 = link3
		self.link4 = link4
		self.nav3 = nav3
		self.nav4 = nav4
	def render_nav(self):
		return render_str("nav.html", nav = self)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render_page(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def read_cookie(self, name):
		val = self.request.cookies.get(name)
		if val:
			uid = is_valid_cookie(val)
			if uid:
				key = db.Key.from_path('Users', int(uid))
				user = db.get(key)
			if uid and user:
				return uid

	def login(self, user):
		cookie = str("login = " + make_valid_cookie(str(user.key().id())) + "; Path=/")
		self.response.headers.add_header('Set-Cookie', cookie)

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'login=; Path=/')

	def render(self, template, **kw):
		uid = self.read_cookie('login')
		if uid:
			nav = Nav('/blog/myposts','/blog/logout', 'MY POSTS', 'LOGOUT')
		else:
			nav = Nav('/blog/login','/blog/signup', "LOGIN", "REGISTER")

		self.render_page(template, nav = nav, **kw)

class MainPage(Handler):
    def get(self):
    	self.redirect("/blog")

class Form(Handler):
	def render_form(self):
		self.render("form.html", title = "", content="",error = "")

	def get(self):
		uid = self.read_cookie('login')
		if uid:
			self.render("form.html")
		else:
			self.redirect("/blog/login")

	def post(self):
		title = self.request.get("title")
		content = self.request.get("content")
		uid = int(self.read_cookie('login'))
		user = Users.get_by_id(uid)

		if title and content:
			post = Post(title = title, content = content, user = user)
			post.put()
			post_id = "/blog/"+str(post.key().id())
			self.redirect(post_id)
		else:
			error = "Please insert both Title and Content"
			self.render("form.html", title=title,content=content, error=error)

class BlogFront(Handler):
	def get(self):
		posts = db.GqlQuery("select * from Post order by date desc")
		p = posts.count()
		if p == 0:
			self.render("noposts.html")
		else:
			render = RenderPost()
			self.render("blog.html", posts = posts, render = render)

class Teste(Handler):
	def get(self):
		posts = db.GqlQuery("select * from Post").count()
		x = posts
		self.write(str(x))
	
class PostPage(Handler):
	def get(self, post_id):
		errors = {"del_permission":"You can only delete your own Post",
				  "edit_permission":"You can only edit yout own Post",
				  "like_permission": "You must be logged in",
				  "like_alrd": "You already liked this post",
				  "like_own": "You cant like your own post" }
		render = RenderPost()
		renderComment = RenderComment()
		error = ""
		key = db.Key.from_path('Post', int(post_id))
		post = db.get(key)
		e = self.request.get("e")
		if e:
			error = errors[e]

		comments = post.comments.order("-date")
		if not post:
			self.write("ERROR 404")
		else:
			likes = post.likes.count()
			self.render("permalink.html", post = post, error = error, likes = likes, render = render, comment_error = "", renderComment = renderComment, comments = comments)

	def post(self, post_id):
		renderComment = RenderComment()
		render = RenderPost()
		login = self.read_cookie('login')
		uid = None
		if login:
			uid = int(login)
			user = Users.get_by_id(uid)
		content = self.request.get("content")
		post = Post.get_by_id(int(post_id))
		likes = post.likes.count()
		comments = post.comments.order("-date")
		if uid:
			if content:
				comment = Comments(post = post, user = user, content = content)
				comment.put()
				self.redirect("/blog/"+post_id)
			else:
				self.render("permalink.html", post = post, error = "", likes = likes, render = render, comment_error = "Type something!", renderComment = renderComment, comments = comments)
		else:
			self.render("permalink.html", post = post, error = "", likes = likes, render = render, comment_error = "you must be logged in", renderComment = renderComment, comments = comments)

	
class LoginPage(Handler):
	def get(self):
		uid = self.read_cookie('login')
		if uid:
			self.redirect("/blog/welcome")
		else:
			self.render("login.html")	

	def post(self):
		username = self.request.get("username")
		password = self.request.get("pw")
		
		if username and password:
			query = "select * from Users where username = '"+username+"'"
			user = db.GqlQuery(query).get()

			if user:
				if valid_pw(username, password, user.password):
					self.login(user)
					self.redirect("/blog/welcome")
				else:
					error = "Your password is wrong!"
					self.render("login.html",username = username,  error = error)
			else:
				error = "This username does not exist!"
				self.render("login.html", error = error)
		else:
			error = "Enter your Username and Password"
			self.render("login.html", error = error)

class SignUpPage(Handler):
	def get(self):
		uid = self.read_cookie('login')
		if uid:
			self.redirect("/blog/welcome")
		else:
			self.render("signup.html")

	def post(self):
		username = self.request.get("username")
		password = self.request.get("pw")
		verify = self.request.get("verify")
		email = self.request.get("email")
		exist_usrname = db.GqlQuery(str("select * from Users where username = '" + username + "'")).get()

		if exist_usrname:
			error = "This username already exist"
			self.render("/signup.html", username = username, email = email, error = error)
		else:
			if password != verify:
				error = "Passwords don't match"
				self.render("/signup.html", username = username, email = email, error = error)
			else:
				if username and password:
					password = make_pw_hash(username, password)
					user = Users(username = username, password = password, email = email)
					user.put()
					self.login(user)
					self.redirect("/blog")
				else:
					error = "You did something wrong!"
					self.render("/signup.html", username = username, email = email, error = error)

class WelcomePage(Handler):
	def get(self):
		uid = self.read_cookie('login')
		if uid:
			name = Users.get_by_id(int(uid)).username
			self.render("welcome.html", name = name)
		else:
			self.redirect("/blog/login")

class Logout(Handler):
	def get(self):
		self.render("logout.html")

	def post(self):
		self.logout()
		self.redirect("/blog")

class MyPosts(Handler):
	def get(self):
		uid = self.read_cookie('login')
		user = Users.get_by_id(int(uid))
		render = RenderPost()
		posts = user.posts
		p = posts.count()
		if p == 0:
			self.render("noposts.html")
		else:
			self.render("blog.html", posts = posts, render = render)

class PostDeleted(Handler):
	def get(self):
		login = self.read_cookie('login')
		uid = None
		if login:
			uid = int(login) 
		post_id = self.request.get("p")
		if post_id:
			post = Post.get_by_id(int(post_id))
		else:
			self.redirect("/blog")
		if uid and int(uid) == int(post.user.key().id()):
			post.delete()
			self.render("deleted.html")
		else:
			self.redirect("/blog/" + post_id + "?e=del_permission")

class EditPost(Handler):
	def get(self, post_id):
		login = self.read_cookie('login')
		uid = None
		if login:
			uid = int(login)
		key = db.Key.from_path("Post", int(post_id))
		post = db.get(key)
		title = post.title
		content = post.content
		if uid and int(uid) == int(post.user.key().id()):
			self.render("edit.html", title = title, content = content, error =  "")
		else:
			self.redirect("/blog/" + post_id + "?e=edit_permission")	

	def post(self, post_id):
		key = db.Key.from_path("Post", int(post_id))
		post = db.get(key)
		title = self.request.get("title")
		content = self.request.get("content")

		if title and content:
			post.title = title
			post.content = content
			post.put()
			post_id = "/blog/"+str(post.key().id())
			self.redirect(post_id)
		else:
			error = "Please insert both Title and Content"
			self.render("edit.html", title=title,content=content, error=error)

class LikePost(Handler):
	def get(self):
		login = self.read_cookie('login')
		uid = None
		if login:
			uid = int(login)
			user = Users.get_by_id(uid)
		post_id = self.request.get("p")
		if post_id:
			if uid:
				post = Post.get_by_id(int(post_id))
				if int(uid) == int(post.user.key().id()):
					#your own post
					self.redirect("/blog/" + post_id + "?e=like_own")
				else:
					likes = db.GqlQuery("select * from Likes where user = :1 and post = :2", user.key(), post.key())
					if likes.count() == 0:
						new_like = Likes(post = post, user = user)
						new_like.put()
						self.redirect("/blog/" + str(post.key().id()))
					else:
						self.redirect("/blog/" + post_id + "?e=like_alrd")
			else:
				self.redirect("/blog/" + post_id + "?e=like_permission")
		else:
			self.redirect("/blog")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog/newpost', Form),
    ('/Teste', Teste),
    ('/blog', BlogFront),
    ('/blog/([0-9]+)', PostPage),
    ('/blog/login', LoginPage),
    ('/blog/signup', SignUpPage),
    ('/blog/welcome', WelcomePage),
    ('/blog/logout', Logout),
    ('/blog/myposts', MyPosts),
    ('/blog/deleted', PostDeleted),
    ('/blog/edit/([0-9]+)', EditPost),
    ('/blog/like', LikePost)]
    , debug=True)