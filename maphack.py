import jinja2
import os
import webapp2
import json
from google.appengine.api import users
from google.appengine.ext import ndb
from math import radians, cos, sin, asin, sqrt
from operator import itemgetter
from urlparse import urlparse

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DISPLAY_PIC = '../images/display_pic.png'

# Datastore definitions
class Person(ndb.Model):
	# Key: person id
	email = ndb.StringProperty()
	name = ndb.StringProperty()
	pic = ndb.StringProperty(default = DISPLAY_PIC, indexed = False)
	inventory_count = ndb.IntegerProperty(default = 0, indexed = False)
	playlist_count = ndb.IntegerProperty(default = 0, indexed = False)
	bio = ndb.StringProperty(default = '', indexed = False)
	setup = ndb.BooleanProperty(default = False, indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True, indexed = False)

class Location(ndb.Model):
	name = ndb.StringProperty()
	address = ndb.StringProperty(indexed = False)
	geopt = ndb.GeoPtProperty()
	date = ndb.DateTimeProperty(auto_now_add = True)

class Inventory(ndb.Model):
	# Key: person id
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Playlist(ndb.Model):
	# Key: person id
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Game(ndb.Model):
	title = ndb.StringProperty()
	platform = ndb.StringProperty()
	pic = ndb.StringProperty(indexed = False)
	description = ndb.TextProperty(indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Listing(ndb.Model):
	owner_id = ndb.StringProperty()
	trade_away_ids = ndb.IntegerProperty(repeated = True)
	trade_for_ids = ndb.IntegerProperty(repeated = True)	
	trade_away_titles = ndb.StringProperty(repeated = True)
	trade_for_titles = ndb.StringProperty(repeated = True)
	trade_away_platforms = ndb.StringProperty(repeated = True)
	trade_for_platforms = ndb.StringProperty(repeated = True)
	top_up = ndb.FloatProperty()	
	date = ndb.DateTimeProperty(auto_now_add = True)

class Platform(ndb.Model):
	pass

class Owners(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Owner(ndb.Model):
	# Key: person id
	name = ndb.StringProperty()
	game_ids = ndb.IntegerProperty(repeated = True, indexed = False)
	descriptions = ndb.TextProperty(repeated = True, indexed = False)

class Seekers(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Seeker(ndb.Model):
	# Key: person id
	name = ndb.StringProperty()
	game_ids = ndb.IntegerProperty(repeated = True, indexed = False)
	descriptions = ndb.TextProperty(repeated = True, indexed = False)

# Helper functions:
def user_game_map(result):
	my_locations = ndb.gql("SELECT * "
		"FROM Location "
		"WHERE ANCESTOR IS :1 "
		"ORDER BY date ASC",
		ndb.Key('Person', users.get_current_user().user_id()))

	your_locations = ndb.gql("SELECT * "
		"FROM Location "
		"WHERE ANCESTOR IS :1 "
		"ORDER BY date ASC",
		ndb.Key('Person', result.key.id()))

	nearest_distance = min_dist(my_locations, your_locations)

	return result, nearest_distance

def locations_map(result):
	return [result.geopt.lat, result.geopt.lon]

def haversine(lat1, lon1, lat2, lon2):
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

def min_dist(locs1, locs2):
	min_dist = float('inf')
	for loc1 in locs1:
		for loc2 in locs2:
			dist = haversine(loc1.geopt.lat, loc1.geopt.lon, loc2.geopt.lat, loc2.geopt.lon)
			if dist < min_dist:
				min_dist = dist
	return min_dist

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
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('dashboard.html')
			self.response.out.write(template.render(template_values))

class Setup(webapp2.RequestHandler):
	def show(self, error = '', input_name = '', input_pic = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			if user == None:
				user = Person(id = users.get_current_user().user_id())
				user.email = users.get_current_user().email()
				user.put()

			if input_pic == DISPLAY_PIC:
				input_pic = ''

			template_values = {
				'pic': DISPLAY_PIC,
				'name': users.get_current_user().nickname(),
				'logout': users.create_logout_url(self.request.host_url),
				'error': error,
				'input_name': input_name,
				'input_pic': input_pic
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
			error = ''

			# Validate name
			try:
				input_name = self.request.get('name').rstrip()
				if input_name == '':
					raise Exception, 'display name cannot be empty'
				qry = Person.query(Person.name == input_name)
				if qry.count():
					raise Exception, 'name is already taken'
			except Exception, e:
				error = error  + 'error with display name. ' + str(e) + '. '

			# Validate pic
			try:
				input_pic = self.request.get('pic').rstrip()
				if input_pic == '':
					input_pic = DISPLAY_PIC
				else:
					if (urlparse(input_pic).scheme != 'http') and (urlparse(input_pic).scheme != 'https'):
						raise Exception, 'image link must be http or https'
			except Exception, e:
				error = error  + 'error with image link. ' + str(e) + '. '

			if error == '':
				user.name = input_name
				user.pic = input_pic
				user.setup = True
				user.put()

				inventory = Inventory(id = users.get_current_user().user_id())
				inventory.put()

				playlist = Playlist(id = users.get_current_user().user_id())
				playlist.put()

				self.redirect('/dashboard')
			else:
				self.show(error, input_name, input_pic)

class Profile(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/dashboard')
		else:
			template_values = {
				'pic': user.pic,
				'name': user.name,
				'bio': user.bio,
				'logout': users.create_logout_url(self.request.host_url),
				}
			template = JINJA_ENVIRONMENT.get_template('profile.html')
			self.response.out.write(template.render(template_values))

class ProfileEdit(webapp2.RequestHandler):
	def show(self, error = '', input_name = '', input_pic = '', input_bio = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/dashboard')
		else:
			# Fill form with user attributes
			if not input_name:
				input_name = user.name
			if not input_pic:
				input_pic = user.pic
			if input_pic == DISPLAY_PIC:
				input_pic = ''
			if not input_bio:
				input_bio = user.bio

			template_values = {
				'pic': user.pic,
				'name': user.name,
				'bio': user.bio,
				'logout': users.create_logout_url(self.request.host_url),
				'error': error,
				'input_name': input_name,
				'input_pic': input_pic,
				'input_bio': input_bio,
				}
			template = JINJA_ENVIRONMENT.get_template('profile_edit.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		self.show()

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/dashboard')
		else:
			error = ''

			# Validate name
			try:
				input_name = self.request.get('name').rstrip()
				if input_name == '':
					raise Exception, 'display name cannot be empty'
				if input_name != user.name:
					qry = Person.query(Person.name == input_name)
					if qry.count():
						raise Exception, 'name is already taken'
			except Exception, e:
				error = error  + 'error with display name. ' + str(e) + '. '

			# Validate pic
			try:
				input_pic = self.request.get('pic').rstrip()
				if input_pic == '':
					input_pic = DISPLAY_PIC
				else:
					if (urlparse(input_pic).scheme != 'http') and (urlparse(input_pic).scheme != 'https'):
						raise Exception, 'image link must be http or https'
			except Exception, e:
				error = error  + 'error with image link. ' + str(e) + '. '

			#Validate bio
			try:
				input_bio = self.request.get('bio').rstrip()
			except Exception, e:
				error = error  + 'error with bio. ' + str(e) + '. '

			if error == '':
				# Change names
				games = Owner.query(Owner.name == user.name)
				for game in games:
					game.name = input_name
					game.put()

				games = Seeker.query(Seeker.name == user.name)
				for game in games:
					game.name = input_name
					game.put()

				user.name = input_name
				user.pic = input_pic
				user.bio = input_bio
				user.put()

				self.redirect('/profile')
			else:
				self.show(error, input_name, input_pic, input_bio)

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
				'pic': user.pic,
				'name': user.name,
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
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			location = Location(parent = ndb.Key('Person', users.get_current_user().user_id()))
			location.name = self.request.get('name')
			location.address = self.request.get('address')
			location.geopt = ndb.GeoPt(self.request.get('latitude'), self.request.get('longitude'))

			location.put()

class LocationsDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			self.redirect('/locations')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
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
			template_values = {
				'name': self.request.get('name'),
				'location_id': self.request.get('location_id'),
				'latitude': self.request.get('latitude'),
				'longitude': self.request.get('longitude'),
			}
			template = JINJA_ENVIRONMENT.get_template('locations_view.html')
			self.response.out.write(template.render(template_values))

	def post(self):
		location_key = ndb.Key('Person', users.get_current_user().user_id(),
				'Location', int(self.request.get('location_id')))
		location = location_key.get()

		if location == None:
			self.error(403)
			self.response.out.write("invalid location id; you are being redirected.")
		else:
			location.name = self.request.get('name')
			location.put()

class InventoryPage(webapp2.RequestHandler):
	def show(self, error = '', input_title = '', input_platform = '', input_pic = '', input_description = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			inventory = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id()))

			template_values = {
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				'inventory': inventory,
				'error': error,
				'input_title': input_title,
				'input_platform': input_platform,
				'input_pic': input_pic,
				'input_description': input_description,
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
			error = ''

			# Validate title
			try:
				input_title = self.request.get('title').rstrip()
				if input_title == '':
					raise Exception, 'title cannot be empty'
			except Exception, e:
				error = error + 'error with game title. ' + str(e) + '. '

			# Validate platform
			try:
				input_platform = self.request.get('platform').rstrip()
				if input_platform == '':
					raise Exception, 'platform cannot be empty'
			except Exception, e:
				error = error + 'error with game platform. ' + str(e) + '. '

			# Validate pic
			try:
				input_pic = self.request.get('pic').rstrip()
				if input_pic != '':
					if (urlparse(input_pic).scheme != 'http') and (urlparse(input_pic).scheme != 'https'):
						raise Exception, 'image link must be http or https'
			except Exception, e:
				error = error  + 'error with image link. ' + str(e) + '. '

			#Validate description
			try:
				input_description = self.request.get('description').rstrip()
			except Exception, e:
				error = error  + 'error with description. ' + str(e) + '. '

			if error == '':
				inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
				inventory = inventory_key.get()
				inventory.count += 1
				inventory.put()

				game = Game(parent = inventory_key)
				game.title = input_title
				game.platform = input_platform
				game.description = input_description
				game.pic = input_pic
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
				owner.name = user.name
				owner.game_ids.append(game.key.id())
				owner.descriptions.append(game.description)
				owner.put()

				self.show()
			else:
				self.show(error, input_title, input_platform, input_pic, input_description)

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
			
			game_key = ndb.Key('Game', int(self.request.get('game_id')),
				parent = inventory_key)
			game = game_key.get()

			if game:
				inventory = inventory_key.get()
				inventory.count -= 1
				inventory.put()

				game_key.delete()

				owners_key = ndb.Key('Owners', game.title,
					parent = ndb.Key('Platform', game.platform))
				owners = owners_key.get()
				owners.count -= 1
				owners.put()

				owner_key = ndb.Key('Owner', users.get_current_user().user_id(),
					parent = owners_key)
				owner = owner_key.get()
				owner.game_ids.remove(game.key.id())
				owner.descriptions.remove(game.description)
			
				if owner.game_ids == []:
					owner_key.delete()
				else:
					owner.put()

			self.redirect('/inventory')

class PlaylistPage(webapp2.RequestHandler):
	def show(self, error = '', input_title = '', input_platform = '', input_pic = '', input_description = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			playlist = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id()))

			template_values = {
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				'playlist': playlist,
				'error': error,
				'input_title': input_title,
				'input_platform': input_platform,
				'input_pic': input_pic,
				'input_description': input_description,
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
			error = ''

			# Validate title
			try:
				input_title = self.request.get('title').rstrip()
				if input_title == '':
					raise Exception, 'title cannot be empty'
			except Exception, e:
				error = error + 'error with game title. ' + str(e) + '. '

			# Validate platform
			try:
				input_platform = self.request.get('platform').rstrip()
				if input_platform == '':
					raise Exception, 'platform cannot be empty'
			except Exception, e:
				error = error + 'error with game platform. ' + str(e) + '. '

			# Validate pic
			try:
				input_pic = self.request.get('pic').rstrip()
				if input_pic != '':
					if (urlparse(input_pic).scheme != 'http') and (urlparse(input_pic).scheme != 'https'):
						raise Exception, 'image link must be http or https'
			except Exception, e:
				error = error  + 'error with image link. ' + str(e) + '. '

			#Validate description
			try:
				input_description = self.request.get('description').rstrip()
			except Exception, e:
				error = error  + 'error with description. ' + str(e) + '. '

			if error == '':
				playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())
				playlist = playlist_key.get()
				playlist.count += 1
				playlist.put()

				game = Game(parent = playlist_key)
				game.title = input_title
				game.platform = input_platform
				game.description = input_description
				game.pic = input_pic
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
				seeker.name = user.name
				seeker.game_ids.append(game.key.id())
				seeker.descriptions.append(game.description)
				seeker.put()

				self.show()
			else:
				self.show(error, input_title, input_platform, input_pic, input_description)

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
			
			game_key = ndb.Key('Game', int(self.request.get('game_id')),
				parent = playlist_key)
			game = game_key.get()

			if game:
				playlist = playlist_key.get()
				playlist.count -= 1
				playlist.put()

				game_key.delete()

				seekers_key = ndb.Key('Seekers', game.title,
					parent = ndb.Key('Platform', game.platform))
				seekers = seekers_key.get()
				seekers.count -= 1
				seekers.put()

				seeker_key = ndb.Key('Seeker', users.get_current_user().user_id(),
					parent = seekers_key)
				seeker = seeker_key.get()
				seeker.game_ids.remove(game.key.id())
				seeker.descriptions.remove(game.description)
			
				if seeker.game_ids == []:
					seeker_key.delete()
				else:
					seeker.put()

			self.redirect('/playlist')

class SearchResults(webapp2.RequestHandler):
	def show(self, query_type = '', title = '', platform = '', results = '', distances = '', error = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			template_values = {
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				'query_type': query_type,
				'title': title,
				'platform': platform,
				'results': results,
				'error': error,
				}
			template = JINJA_ENVIRONMENT.get_template('search_results.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			query_type = self.request.get('query_type')
			if query_type == 'have':
				title = self.request.get('title')
				platform = self.request.get('platform')

				owners_key = ndb.Key('Owners', title,
					parent = ndb.Key('Platform', platform))

				owners = ndb.gql("SELECT * "
					"FROM Owner "
					"WHERE ANCESTOR IS :1 ",
					owners_key)

				results = owners.map(user_game_map)
				results = sorted(results, key = itemgetter(1))
				
				self.show(query_type, title, platform, results)

			elif query_type == 'want':
				title = self.request.get('title')
				platform = self.request.get('platform')

				seekers_key = ndb.Key('Seekers', title,
					parent = ndb.Key('Platform', platform))

				seekers = ndb.gql("SELECT * "
					"FROM Seeker "
					"WHERE ANCESTOR IS :1 ",
					seekers_key)

				results = seekers.map(user_game_map)
				results = sorted(results, key = itemgetter(1))

				self.show(query_type, title, platform, results)

			else:
				error = 'invalid query.'
				self.show(error = error)

class UserPage(webapp2.RequestHandler):
	def get(self, person_id):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			if user.key.id() == person_id:
				self.redirect('/dashboard')
			else:
				person = ndb.Key('Person', person_id).get()
				if person == None:
					self.redirect('/dashboard')
				else:
					my_inventory = ndb.gql("SELECT * "
						"FROM Game "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date DESC",
						ndb.Key('Inventory', users.get_current_user().user_id()))

					my_playlist = ndb.gql("SELECT * "
						"FROM Game "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date DESC",
						ndb.Key('Playlist', users.get_current_user().user_id()))

					your_inventory = ndb.gql("SELECT * "
						"FROM Game "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date DESC",
						ndb.Key('Inventory', person_id))

					your_playlist = ndb.gql("SELECT * "
						"FROM Game "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date DESC",
						ndb.Key('Playlist', person_id))

					my_locations = ndb.gql("SELECT * "
						"FROM Location "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date ASC",
						ndb.Key('Person', users.get_current_user().user_id()))

					your_locations = ndb.gql("SELECT * "
						"FROM Location "
						"WHERE ANCESTOR IS :1 "
						"ORDER BY date ASC",
						ndb.Key('Person', person_id))

					my_diff = []
					my_match = []
					your_match = []
					your_diff = []

					for i_own in my_inventory:
						found = False
						for you_seek in your_playlist:
							if i_own.title == you_seek.title and i_own.platform == you_seek.platform:
								my_match.append(i_own)
								found = True;
								break;
						if not found:
							my_diff.append(i_own)

					for you_own in your_inventory:
						found = False
						for i_seek in my_playlist:
							if you_own.title == i_seek.title and you_own.platform == i_seek.platform:
								your_match.append(you_own)
								found = True;
								break;
						if not found:
							your_diff.append(you_own)

					nearest_distance = min_dist(my_locations, your_locations)

					template_values = {
						'pic': user.pic,
						'name': user.name,
						'logout': users.create_logout_url(self.request.host_url),
						'person_pic': person.pic,
						'person_name': person.name,
						'person_id': person_id,
						'my_diff': my_diff,
						'my_match': my_match,
						'your_match': your_match,
						'your_diff': your_diff,
						'nearest_distance': nearest_distance,
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
			if person == None:
				self.redirect('/dashboard')

			my_locations = ndb.gql("SELECT * "
				"FROM Location "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date ASC",
				ndb.Key('Person', users.get_current_user().user_id()))

			your_locations = ndb.gql("SELECT * "
				"FROM Location "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date ASC",
				ndb.Key('Person', person_id))

			my_locations = my_locations.map(locations_map)
			your_locations = your_locations.map(locations_map)

			template_values = {
				'my_locations': my_locations,
				'your_locations': your_locations,
				'person_name': person.name,
			}
			template = JINJA_ENVIRONMENT.get_template('user_locations.html')
			self.response.out.write(template.render(template_values))

class ListingsPage(webapp2.RequestHandler):
	def show(self, error = '', input_title = '', input_platform = '', input_pic = '', input_description = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == None or user.setup == False:
			self.redirect('/setup')
		else:
			listings = ndb.gql("SELECT * "
				"FROM Listing "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Listing', users.get_current_user().user_id()))

			playlist = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id()))

			inventory = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id()))

			template_values = {
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				'listings': listings,
				'playlist': playlist,
				'inventory': inventory,
				'error': error,
				'input_title': input_title,
				'input_platform': input_platform,
				'input_pic': input_pic,
				'input_description': input_description,
				}
			template = JINJA_ENVIRONMENT.get_template('listings.html')
			self.response.out.write(template.render(template_values))

	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			listings = ndb.gql("SELECT * "
				"FROM Listing "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Listing', users.get_current_user().user_id()))

			playlist = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Playlist', users.get_current_user().user_id()))

			inventory = ndb.gql("SELECT * "
				"FROM Game "
				"WHERE ANCESTOR IS :1 "
				"ORDER BY date DESC",
				ndb.Key('Inventory', users.get_current_user().user_id()))

			template_values = {
				'pic': user.pic,
				'name': user.name,
				'logout': users.create_logout_url(self.request.host_url),
				'listings': listings,	
				'playlist': playlist,
				'inventory': inventory,
				}
			template = JINJA_ENVIRONMENT.get_template('listings.html')
			self.response.out.write(template.render(template_values))
			
	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user == None or user.setup == False:
			self.redirect('/setup')
		else:
			error = ''
			jdata = json.loads(self.request.body)

			# Validate list of games to trade away
			try:
				topup = jdata['topUp']
				away_list = jdata['toTrade']
				if len(away_list) == 0 and topup == 0:	
					raise Exception, 'you must choose at least one game to trade away'
			except Exception, e:
				error = error + 'error with list of games chosen. ' + str(e) + '. '

			# Validate list of games to receive in trade
			try:
				receive_list = jdata['toReceive']
				if len(receive_list) == 0 and topup == 0:
					raise Exception, 'you must choose at least one game you want'
			except Exception, e:
				error = error + 'error with list of games chosen. ' + str(e) + '. '

			if error == '':
				trade_away_titles = []
				trade_away_platforms = []
				trade_away_ids = []
				trade_for_titles = []
				trade_for_platforms = []
				trade_for_ids = []
				
				for game in away_list:
					trade_away_titles.append(game['Title'])
					trade_away_platforms.append(game['Platform'])
					trade_away_ids.append(int(game['Id']))

				for game in receive_list:
					trade_for_titles.append(game['Title'])
					trade_for_platforms.append(game['Platform'])
					trade_for_ids.append(int(game['Id']))

				listing = Listing(parent = ndb.Key('Person', users.get_current_user().user_id()))
				listing.owner_id = users.get_current_user().user_id()
				listing.top_up = float(topup)
				listing.trade_away_titles = trade_away_titles
				listing.trade_away_platforms = trade_away_platforms
				listing.trade_away_ids = trade_away_ids
				listing.trade_for_titles = trade_for_titles
				listing.trade_for_platforms = trade_for_platforms
				listing.trade_for_ids = trade_for_ids
				listing.put()

				self.show()
			else:
				self.show(error)

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
	('/search/results', SearchResults),
	('/user/locations/(.*)', UserLocations),
	('/user/(.*)', UserPage),
	('/listings', ListingsPage),
	('/*', Dashboard),
], debug=True)