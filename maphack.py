import jinja2
import os
import urllib
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from math import radians, cos, sin, asin, sqrt

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
	img_url = ndb.StringProperty(default = '../images/profile_pic.png')
	bio = ndb.StringProperty(default = '')
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
	# Key: platform name
	pass

class Owners(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0)

class Owner(ndb.Model):
	# Key: person id
	person_key = ndb.KeyProperty()
	game_keys = ndb.KeyProperty(repeated = True)

class Seekers(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0)

class Seeker(ndb.Model):
	person_key = ndb.KeyProperty()
	game_keys = ndb.KeyProperty(repeated = True)

# Helper functions
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km 

# Handlers
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
			user.put()

			inventory = Inventory(id = users.get_current_user().user_id())
			inventory.put()

			playlist = Playlist(id = users.get_current_user().user_id())
			playlist.put()

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

class LocationsPage(webapp2.RequestHandler):
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

class LocationsView(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			template = JINJA_ENVIRONMENT.get_template('locations_view.html')
			self.response.out.write(template.render())

	def post(self):
		location_key = ndb.Key('Person', users.get_current_user().user_id(),
				'Location', int(self.request.get('id')))
		location = location_key.get()
		location.name = self.request.get('name')

		location.put()

class InventoryPage(webapp2.RequestHandler):
	def show(self, error = ""):
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
				'error': error,
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

				inventory.count += 1
				inventory.put()

				game = Game(parent = inventory_key)
				game.title = self.request.get('title')
				game.platform = self.request.get('platform')
				game.img_url = self.request.get('img_url')
				game.description = self.request.get('description')
				game.put()

				owners_key = ndb.Key('Owners', game.title,
					parent = ndb.Key('Platform', game.platform))
				owners = owners_key.get()

				if owners == None:
					owners = Owners(parent = ndb.Key('Platform', game.platform),
						id = game.title)

				owners.count += 1
				owners.put()

				owner_key = ndb.Key('Owner', users.get_current_user().user_id(),
					parent = owners_key)
				owner = owner_key.get()

				if owner == None:
					owner = Owner(parent = owners_key,
						id = users.get_current_user().user_id())
					owner.person_key = ndb.Key('Person', users.get_current_user().user_id())

				owner.game_keys.append(game.key)
				owner.put()

				self.show()

			else:
				error = "Error: Problem with game title and/or platform."
				self.show(error)

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
			inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
			inventory = inventory_key.get()

			inventory.count -= 1
			inventory.put()

			game_key = ndb.Key('Game', int(self.request.get('game_id')),
				parent = inventory_key)
			game = game_key.get()
			game_key.delete()

			owners_key = ndb.Key('Owners', game.title,
				parent = ndb.Key('Platform', game.platform))
			owners = owners_key.get()
			owners.count -= 1
			owners.put()

			owner_key = ndb.Key('Owner', users.get_current_user().user_id(),
				parent = owners_key)
			owner = owner_key.get()
			owner.game_keys.remove(game_key)
			
			if owner.game_keys == []:
				owner_key.delete()
			else:
				owner.put()

			self.redirect('/inventory')

class PlaylistPage(webapp2.RequestHandler):
	def show(self, error = ""):
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

				playlist.count += 1
				playlist.put()

				game = Game(parent = playlist_key)
				game.title = self.request.get('title')
				game.platform = self.request.get('platform')
				game.img_url = self.request.get('img_url')
				game.description = self.request.get('description')
				game.put()

				seekers_key = ndb.Key('Seekers', game.title,
					parent = ndb.Key('Platform', game.platform))
				seekers = seekers_key.get()

				if seekers == None:
					seekers = Seekers(parent = ndb.Key('Platform', game.platform),
						id = game.title)

				seekers.count += 1
				seekers.put()

				seeker_key = ndb.Key('Seeker', users.get_current_user().user_id(),
					parent = seekers_key)
				seeker = seeker_key.get()

				if seeker == None:
					seeker = Seeker(parent = seekers_key,
						id = users.get_current_user().user_id())
					seeker.person_key = ndb.Key('Person', users.get_current_user().user_id())

				seeker.game_keys.append(game.key)
				seeker.put()

				self.show()

			else:
				error = "Error: Problem with game title and/or platform."
				self.show(error)

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
			playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())
			playlist = playlist_key.get()

			playlist.count -= 1
			playlist.put()

			game_key = ndb.Key('Game', int(self.request.get('game_id')),
				parent = playlist_key)
			game = game_key.get()
			game_key.delete()

			seekers_key = ndb.Key('Seekers', game.title,
				parent = ndb.Key('Platform', game.platform))
			seekers = seekers_key.get()
			seekers.count -= 1
			seekers.put()

			seeker_key = ndb.Key('Seeker', users.get_current_user().user_id(),
				parent = seekers_key)
			seeker = seeker_key.get()
			seeker.game_keys.remove(game_key)
			
			if seeker.game_keys == []:
				seeker_key.delete()
			else:
				seeker.put()

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
	def show(self, query_type, title, platform, persons, error = ""):
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
				'persons': persons,
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

				owners_key = ndb.Key('Owners', title,
					parent = ndb.Key('Platform', platform))

				results = ndb.gql("SELECT * "
					"FROM Owner "
					"WHERE ANCESTOR IS :1 ",
					owners_key)

				persons = []
				for owner in results:
					person = [owner.person_key.get().display_name, owner.person_key.id()]
					persons.append(person)

				self.show(query_type, title, platform, persons)

			elif self.request.get('query_type') == "want":
				query_type = "want"
				title = self.request.get('title')
				platform = self.request.get('platform')

				seekers_key = ndb.Key('Seekers', title,
					parent = ndb.Key('Platform', platform))

				results = ndb.gql("SELECT * "
					"FROM Seeker "
					"WHERE ANCESTOR IS :1 ",
					seekers_key)

				persons = []
				for seeker in results:
					person = [seeker.person_key.get().display_name, seeker.person_key.id()]
					persons.append(person)

				self.show(query_type, title, platform, persons)
			else:
				error = "Error: Problem with search query."
				self.show(error = error)

class UserPage(webapp2.RequestHandler):
	def get(self, person_id):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			person = ndb.Key('Person', person_id).get()

			me_inventory = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id()))

			me_playlist = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id()))

			you_inventory = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', person_id))

			you_playlist = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', person_id))

			me_locations = ndb.gql("SELECT * "
				"FROM Location "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date ASC",
				ndb.Key('Person', users.get_current_user().user_id()))

			you_locations = ndb.gql("SELECT * "
				"FROM Location "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date ASC",
				ndb.Key('Person', person_id))

			me_diff = []
			me_match = []
			you_match = []
			you_diff = []

			for me_own in me_inventory:
				found = False
				for you_seek in you_playlist:
					if me_own.title == you_seek.title and me_own.platform == you_seek.platform:
						me_match.append([me_own.title, me_own.platform, me_own.description, me_own.img_url, me_own.key.id()])
						found = True;
						break;
				if not found:
					me_diff.append([me_own.title, me_own.platform])

			for you_own in you_inventory:
				found = False
				for me_seek in me_playlist:
					if you_own.title == me_seek.title and you_own.platform == me_seek.platform:
						you_match.append([you_own.title, you_own.platform, you_own.description, you_own.img_url, you_own.key.id()])
						found = True;
						break;
				if not found:
					you_diff.append([you_own.title, you_own.platform, you_own.description, you_own.img_url, you_own.key.id()])

			nearest_dist = float("inf")
			me_nearest_loc = None
			you_nearest_loc = None
			for you_location in you_locations:
				for me_location in me_locations:
					dist = haversine(you_location.geopt.lat, you_location.geopt.lon, me_location.geopt.lat, me_location.geopt.lon)
					if dist < nearest_dist:
						nearest_dist = dist
						me_nearest_loc = me_location
						you_nearest_loc = you_location

			template_values = {
				'img_url': user.img_url,
				'display_name': user.display_name,
				'logout': users.create_logout_url(self.request.host_url),
				'person_pic': person.img_url,
				'person_name': person.display_name,
				'person_id': person_id,
				'me_diff': me_diff,
				'me_match': me_match,
				'you_match': you_match,
				'you_diff': you_diff,
				'me_locations': me_locations,
				'you_locations': you_locations,
				'nearest_dist': nearest_dist,
				'me_nearest_loc': me_nearest_loc,
				'you_nearest_loc': you_nearest_loc,
				}
			template = JINJA_ENVIRONMENT.get_template('user.html')
			self.response.out.write(template.render(template_values))

class UserLocations(webapp2.RequestHandler):
	def get(self, person_id):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			person = ndb.Key('Person', person_id).get()

			qry = Location.query(ancestor=ndb.Key('Person', person_id))
			locPts = qry.fetch(projection=[Location.geopt])

			locLats = []
			locLons = []

			for x in range(0, len(locPts)):
				locLats.append(locPts[x].geopt.lat)
				locLons.append(locPts[x].geopt.lon)

			myqry = Location.query(ancestor=ndb.Key('Person', user.person_id))
			myLocPts = myqry.fetch(projection=[Location.geopt])

			myLocLats = []
			myLocLons = []

			for x in range(0, len(myLocPts)):
				myLocLats.append(myLocPts[x].geopt.lat)
				myLocLons.append(myLocPts[x].geopt.lon)

			template_values = {
				'you_lats': locLats,
				'you_lons': locLons,
				'my_lats': myLocLats,
				'my_lons': myLocLons,
				'person_name': person.display_name,
			}
			template = JINJA_ENVIRONMENT.get_template('user_locations.html')
			self.response.out.write(template.render(template_values))

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/dashboard', Dashboard),
	('/setup', Setup),
	('/profile', Profile),
	('/profile/edit', ProfileEdit),
	('/locations', LocationsPage),
	('/locations/add', LocationsAdd),
	('/locations/delete', LocationsDelete),
	('/locations/view', LocationsView),
	('/inventory', InventoryPage),
	('/inventory/delete', InventoryDelete),
	('/playlist', PlaylistPage),
	('/playlist/delete', PlaylistDelete),
	('/search', Search),
	('/search/results', SearchResults),
	('/user/(.*)/locations', UserLocations),
	('/user/(.*)', UserPage),	
	], debug=True)