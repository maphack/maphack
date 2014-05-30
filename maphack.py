import jinja2
import os
import urllib
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

# Datastore definitions
class Person(ndb.Model):
	# Key: person id
	person_id = ndb.StringProperty()
	email = ndb.StringProperty()
	display_name = ndb.StringProperty()
	img_url = ndb.StringProperty()
	bio = ndb.StringProperty()
	setup = ndb.BooleanProperty(default = False)
	date = ndb.DateTimeProperty(auto_now_add=True)

class Location(ndb.Model):
	name = ndb.StringProperty()
	address = ndb.StringProperty()
	geopt = ndb.GeoPtProperty()
	date = ndb.DateTimeProperty(auto_now_add=True)

class Inventory(ndb.Model):
	# Key: person id
	count = ndb.IntegerProperty(default = 0)

class Playlist(ndb.Model):
	# Key: person id
	count = ndb.IntegerProperty(default = 0)

class Game(ndb.Model):
	title = ndb.StringProperty()
	platform = ndb.StringProperty()
	img_url = ndb.StringProperty()
	description = ndb.TextProperty()
	date = ndb.DateTimeProperty(auto_now_add=True)

class Platform(ndb.Model):
	pass

class GameAggregate(ndb.Model):
	# Key: game title
	num_have = ndb.IntegerProperty(default = 0)
	num_want = ndb.IntegerProperty(default = 0)
	owner_ids = ndb.StringProperty(repeated = True)
	hunter_ids = ndb.StringProperty(repeated = True)

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
		if user == None or user.setup == False:
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
	def show(self, error = ""):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			user = Person(id = users.get_current_user().user_id())
			user.person_id = users.get_current_user().user_id()
			user.email = users.get_current_user().email()
			user.display_name = users.get_current_user().nickname()
			user.img_url = '../images/profile_pic.png'
			user.put()

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'error': error,
				}
			template = JINJA_ENVIRONMENT.get_template('setup.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.show()

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None:
			self.redirect('/setup')
		else:
			if self.request.get('display_name').rstrip() != '':    # display name cannot be empty
				user.display_name = self.request.get('display_name')

				if self.request.get('img_url').rstrip() != '':
					user.img_url = self.request.get('img_url')

				user.setup = True
				user.put()
				self.redirect('/dashboard')
			else:
				error = "Error: Problem with display name."
				self.show(error)

class Profile(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
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
	def show(self, error = ""):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'bio': user.bio,
				'logout': users.create_logout_url(self.request.host_url),
				'error': error
				}
			template = JINJA_ENVIRONMENT.get_template('profile_edit.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.show()

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			if self.request.get('display_name').rstrip() != '':    # display name cannot be empty
				user.display_name = self.request.get('display_name')

				if self.request.get('img_url').rstrip() != '':
					user.img_url = self.request.get('img_url')
				
				user.bio = self.request.get('bio')
				user.put()
				self.redirect('/profile')
			else:
				error = "Error: Problem with display name."
				self.show(error)

class Locations(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			locations = ndb.gql("SELECT * "
				"FROM Location "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date ASC",
				ndb.Key('Person', users.get_current_user().user_id()))

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'locations': locations,
				}
			template = JINJA_ENVIRONMENT.get_template('locations.html')
			self.response.out.write(template.render(template_values))

class LocationsAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			template = JINJA_ENVIRONMENT.get_template('locations_add.html')
			self.response.out.write(template.render())

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			location = Location(parent = ndb.Key('Person', users.get_current_user().user_id()))
			location.name = self.request.get('name')
			location.address = self.request.get('address')
			location.geopt = ndb.GeoPt(self.request.get('latitude'), self.request.get('longitude'))

			location.put()

class LocationsDelete(webapp2.RequestHandler):
	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			location_key = ndb.Key('Person', users.get_current_user().user_id(),
				'Location', int(self.request.get('location_id')))
			location_key.delete()

			self.redirect('/locations')

class InventoryPage(webapp2.RequestHandler):
	def show(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			games = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id()))

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
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			if self.request.get('title').rstrip() != '' and self.request.get('platform').rstrip() != '':
				inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
				inventory = inventory_key.get()

				if inventory == None:
					inventory = Inventory(id = users.get_current_user().user_id())

				inventory.count += 1

				game = Game(parent = inventory_key)
				game.title = self.request.get('title')
				game.platform = self.request.get('platform')
				game.img_url = self.request.get('img_url')
				game.description = self.request.get('description')

				gameaggregate_key = ndb.Key('GameAggregate', game.title, 
					parent = ndb.Key('Platform', game.platform))
				gameaggregate = gameaggregate_key.get()

				if gameaggregate == None:
					gameaggregate = GameAggregate(parent = ndb.Key('Platform', game.platform),
						id = game.title)
				
				gameaggregate.num_have += 1
				gameaggregate.owner_ids.append(users.get_current_user().user_id())

				inventory.put()
				game.put()
				gameaggregate.put()

				self.show()

class InventoryDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			self.redirect('/inventory')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			game_key = ndb.Key('Inventory', users.get_current_user().user_id(),
				'Game', int(self.request.get('game_id')))
			game = game_key.get()

			gameaggregate_key = ndb.Key('GameAggregate', game.title, 
					parent = ndb.Key('Platform', game.platform))
			gameaggregate = gameaggregate_key.get()

			gameaggregate.num_have -= 1
			gameaggregate.owner_ids.remove(users.get_current_user().user_id())

			game_key.delete()
			gameaggregate.put()

			self.redirect('/inventory')

class PlaylistPage(webapp2.RequestHandler):
	def show(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			games = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id()))

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
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			if self.request.get('title').rstrip() != '' and self.request.get('platform').rstrip() != '':
				playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())
				playlist = playlist_key.get()

				if playlist == None:
					playlist = Playlist(id = users.get_current_user().user_id())

				playlist.count += 1

				game = Game(parent = playlist_key)
				game.title = self.request.get('title')
				game.platform = self.request.get('platform')
				game.img_url = self.request.get('img_url')
				game.description = self.request.get('description')

				gameaggregate_key = ndb.Key('GameAggregate', game.title, 
					parent = ndb.Key('Platform', game.platform))
				gameaggregate = gameaggregate_key.get()

				if gameaggregate == None:
					gameaggregate = GameAggregate(parent = ndb.Key('Platform', game.platform),
						id = game.title)
				
				gameaggregate.num_want += 1
				gameaggregate.hunter_ids.append(users.get_current_user().user_id())

				playlist.put()
				game.put()
				gameaggregate.put()

				self.show()

class PlaylistDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			self.redirect('/playlist')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			game_key = ndb.Key('Inventory', users.get_current_user().user_id(),
				'Game', int(self.request.get('game_id')))
			game = game_key.get()

			gameaggregate_key = ndb.Key('GameAggregate', game.title, 
					parent = ndb.Key('Platform', game.platform))
			gameaggregate = gameaggregate_key.get()

			gameaggregate.num_want -= 1
			gameaggregate.hunter_ids.remove(users.get_current_user().user_id())

			game_key.delete()
			gameaggregate.put()

			self.redirect('/playlist')

class Search(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('search.html')
			self.response.out.write(template.render(template_values))

class SearchResults(webapp2.RequestHandler):
	def show(self, query_type, title, platform, person_ids, error = ""):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'query_type': query_type,
				'title': title,
				'platform': platform,
				'person_ids': person_ids,
				'error': error,
				}
			template = JINJA_ENVIRONMENT.get_template('search_results.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.redirect('/search')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			if self.request.get('query_type') == "have":
				query_type = "have"
				title = self.request.get('title')
				platform = self.request.get('platform')
				person_ids = []

				gameaggregate_key = ndb.Key('GameAggregate', title, 
					parent = ndb.Key('Platform', platform))
				gameaggregate = gameaggregate_key.get()

				if gameaggregate:
					for person_id in gameaggregate.owner_ids:
						person_ids.append(person_id)

				self.show(query_type, title, platform, person_ids)

			elif self.request.get('query_type') == "want":
				query_type = "want"
				title = self.request.get('title')
				platform = self.request.get('platform')
				person_ids = []

				gameaggregate_key = ndb.Key('GameAggregate', title, 
					parent = ndb.Key('Platform', platform))
				gameaggregate = gameaggregate_key.get()

				if gameaggregate:
					for person_id in gameaggregate.hunter_ids:
						person_ids.append(person_id)

				self.show(query_type, title, platform, person_ids)
			else:
				error = "Error: Problem with search query."
				self.show(error)

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/dashboard', Dashboard),
	('/setup', Setup),
	('/profile', Profile),
	('/profile/edit', ProfileEdit),
	('/locations', Locations),
	('/locations/add', LocationsAdd),
	('/locations/delete', LocationsDelete),
	('/inventory', InventoryPage),
	('/inventory/delete', InventoryDelete),
	('/playlist', PlaylistPage),
	('/playlist/delete', PlaylistDelete),
	('/search', Search),
	('/search/results', SearchResults),
	], debug=True)