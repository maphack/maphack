import jinja2
import os
import urllib
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

# Datastore definitions
class Person(ndb.Model):
	# Key: user id
	email = ndb.StringProperty()
	display_name = ndb.StringProperty()
	img_url = ndb.StringProperty()
	bio = ndb.StringProperty()
	setup = ndb.BooleanProperty()   # whether profile is set up

class Inventory(ndb.Model):
	# Key: user id
	next_game = ndb.IntegerProperty()

class Playlist(ndb.Model):
	# Key: user id
	next_game = ndb.IntegerProperty()

class Game(ndb.Model):
	# Key: game id
	game_id = ndb.IntegerProperty()
	title = ndb.StringProperty()
	platform = ndb.StringProperty()
	img_url = ndb.StringProperty()
	description = ndb.TextProperty()
	date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			self.redirect('/dashboard')
		else:
			template = JINJA_ENVIRONMENT.get_template('front.html')
			self.response.out.write(template.render())

class Dashboard(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('dashboard.html')
			self.response.out.write(template.render(template_values))

class Setup(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			user = Person(id = users.get_current_user().user_id())
			user.email = users.get_current_user().email()
			user.display_name = users.get_current_user().nickname()
			user.img_url = "../images/profile_pic.png"
			user.setup = False
			user.put()

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('setup.html')
			self.response.out.write(template.render(template_values))

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			user.display_name = self.request.get('display_name')
			user.img_url = self.request.get('img_url')

			if user.display_name.rstrip() != '':    # display name cannot be empty
				user.setup = True
				user.put()
				self.redirect('/dashboard')
			else:
				self.redirect('/setup')

class Profile(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'bio': user.bio,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('profile.html')
			self.response.out.write(template.render(template_values))

class ProfileEdit(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'bio': user.bio,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('profile_edit.html')
			self.response.out.write(template.render(template_values))

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			user.display_name = self.request.get('display_name')
			user.img_url = self.request.get('img_url')
			user.bio = self.request.get('bio')

			if user.display_name.rstrip() != '':    # display name cannot be empty
				user.put()
			self.redirect('/profile')

class InventoryPage(webapp2.RequestHandler):
	def show(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			games = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id(), 
					parent = ndb.Key('Person', users.get_current_user().user_id())))

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'games': games, 
				}
			template = JINJA_ENVIRONMENT.get_template('inventory.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.show()

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			inventory_key = ndb.Key('Inventory', users.get_current_user().user_id(), 
				parent = ndb.Key('Person', users.get_current_user().user_id()))
			inventory = inventory_key.get()

			if inventory == None:
				inventory = Inventory(parent = ndb.Key('Person', users.get_current_user().user_id()), 
					id = users.get_current_user().user_id())
				inventory.next_game = 1

			game = Game(parent = inventory_key, id = str(inventory.next_game))

			game.game_id = inventory.next_game
			game.title = self.request.get('title')
			game.platform = self.request.get('platform')
			game.img_url = self.request.get('img_url')
			game.description = self.request.get('description')

			if game.title.rstrip() != '' and game.platform.rstrip() != '':
				inventory.next_game += 1
				inventory.put()
				game.put()

			self.show()

class InventoryDeleteGame(webapp2.RequestHandler):
	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			game = ndb.Key('Person', users.get_current_user().user_id(), 
				'Inventory', users.get_current_user().user_id(), 
				'Game', self.request.get('game_id'))
			game.delete()

			self.redirect('/inventory')

class PlaylistPage(webapp2.RequestHandler):
	def show(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			games = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id(), 
					parent = ndb.Key('Person', users.get_current_user().user_id())))

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'games': games, 
				}
			template = JINJA_ENVIRONMENT.get_template('playlist.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.show()

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			playlist_key = ndb.Key('Playlist', users.get_current_user().user_id(), 
				parent = ndb.Key('Person', users.get_current_user().user_id()))
			playlist = playlist_key.get()

			if playlist == None:
				playlist = Playlist(parent = ndb.Key('Person', users.get_current_user().user_id()), 
					id = users.get_current_user().user_id())
				playlist.next_game = 1

			game = Game(parent = playlist_key, id = str(playlist.next_game))

			game.game_id = playlist.next_game
			game.title = self.request.get('title')
			game.platform = self.request.get('platform')
			game.img_url = self.request.get('img_url')
			game.description = self.request.get('description')

			if game.title.rstrip() != '' and game.platform.rstrip() != '':
				playlist.next_game += 1
				playlist.put()
				game.put()

			self.show()

class PlaylistDeleteGame(webapp2.RequestHandler):
	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			game = ndb.Key('Person', users.get_current_user().user_id(), 
				'Playlist', users.get_current_user().user_id(), 
				'Game', self.request.get('game_id'))
			game.delete()

			self.redirect('/playlist')

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/dashboard', Dashboard),
	('/setup', Setup),
	('/profile', Profile),
	('/profile/edit', ProfileEdit),
	('/inventory', InventoryPage),
	('/inventory/deletegame', InventoryDeleteGame),
	('/playlist', PlaylistPage),
	('/playlist/deletegame', PlaylistDeleteGame),
	], debug=True)