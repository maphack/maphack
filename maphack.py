import datetime
import jinja2
import ndbpager
import os
import webapp2
import json
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb
from math import radians, cos, sin, asin, sqrt
from operator import itemgetter
from urlparse import urlparse

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DISPLAY_PIC = '/images/display_pic.png'

COUNTRY_CODES = ['AF', 'AD', 'AE', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BM', 'BN', 'BO', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'ST', 'SV', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW']

ADMIN_MAIL = 'developer.maph4ck@gmail.com'

MAX_STR_LEN = 500

# Datastore definitions
class Person(ndb.Model):
	# Key: person id
	email = ndb.StringProperty()
	name = ndb.StringProperty()
	pic = ndb.StringProperty(default = DISPLAY_PIC, indexed = False)
	country = ndb.StringProperty()
	contact = ndb.StringProperty(indexed = False)
	bio = ndb.StringProperty(indexed = False)
	friend_keys = ndb.KeyProperty(repeated = True)
	setup = ndb.BooleanProperty(default = False, indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Location(ndb.Model):
	name = ndb.StringProperty(indexed = False)
	address = ndb.StringProperty(indexed = False)
	geopt = ndb.GeoPtProperty(indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True, indexed = False)

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
	listing_keys = ndb.KeyProperty(repeated = True, indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True, indexed = False)

class Listing(ndb.Model):
	owner_key = ndb.KeyProperty(indexed = False) 
	own_keys = ndb.KeyProperty(repeated = True, indexed = False)
	seek_keys = ndb.KeyProperty(repeated = True, indexed = False)
	own_games = ndb.StringProperty(repeated = True)
	seek_games = ndb.StringProperty(repeated = True)
	topup = ndb.IntegerProperty(default = 0)
	description = ndb.TextProperty(indexed = False)
	comment_keys = ndb.KeyProperty(repeated = True, indexed = False)
	subscriber_keys = ndb.KeyProperty(repeated = True, indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Comment(ndb.Model):
	owner_key  = ndb.KeyProperty(indexed = False)
	content = ndb.StringProperty(indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Message(ndb.Model):
	content = ndb.StringProperty(indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Conversation(ndb.Model):
	person_keys = ndb.KeyProperty(repeated = True)
	messages = ndb.StructuredProperty(Message, repeated = True)
	num_unread = ndb.IntegerProperty(indexed = False, repeated = True)
	date = ndb.DateTimeProperty()

class Feedback(ndb.Model):
	owner_key = ndb.KeyProperty(indexed = False)
	content = ndb.StringProperty(indexed = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Platform(ndb.Model):
	pass

class Owners(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Owner(ndb.Model):
	# Key: person id
	name = ndb.StringProperty()
	game_keys = ndb.KeyProperty(repeated = True, indexed = False)

class Seekers(ndb.Model):
	# Key: game title
	count = ndb.IntegerProperty(default = 0, indexed = False)

class Seeker(ndb.Model):
	# Key: person id
	name = ndb.StringProperty()
	game_keys = ndb.KeyProperty(repeated = True, indexed = False)

# JSON encoder
class NdbEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return {'y': obj.year,
				'm': obj.month,
				'd': obj.day,
				'h': obj.hour,
				's': obj.second,}

		if isinstance(obj, ndb.GeoPt):
			return {'lat': obj.lat, 'lon': obj.lon}

		if isinstance(obj, ndb.Key):
			return obj.urlsafe()

		return json.JSONEncoder.default(self, obj)

# Helper functions:
def user_with_distance(result):
	my_locations = ndb.gql('SELECT * '
		'FROM Location '
		'WHERE ANCESTOR IS :1 ',
		user.key)

	your_locations = ndb.gql('SELECT * '
		'FROM Location '
		'WHERE ANCESTOR IS :1 ',
		ndb.Key('Person', result.key.id()))

	nearest_distance = min_dist(my_locations, your_locations)

	return result, nearest_distance

def listing_all(listing):
	my_locations = ndb.gql('SELECT * '
			'FROM Location '
			'WHERE ANCESTOR IS :1 ',
			ndb.Key('Person', users.get_current_user().user_id()))

	your_locations = ndb.gql('SELECT * '
			'FROM Location '
			'WHERE ANCESTOR IS :1 ',
			listing.owner_key)

	return listing, ndb.get_multi(listing.own_keys), ndb.get_multi(listing.seek_keys), listing.owner_key.get(), your_locations, min_dist(my_locations, your_locations)

def listing_with_games(listing):
	return listing, ndb.get_multi(listing.own_keys), ndb.get_multi(listing.seek_keys)

def haversine(lat1, lon1, lat2, lon2):
    '''
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    '''
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

def jsonify(query):
	if type(query) is not ndb.Query:
		raise Exception, 'input is not of type ndb.Query'
	return json.dumps([ndb.Model.to_dict(result) for result in query], cls = NdbEncoder)

class MainPage(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			self.redirect('/dashboard')
		else:
			template = JINJA_ENVIRONMENT.get_template('front.html')
			self.response.out.write(template.render())

class Setup(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			if user is None:
				user = Person(id = users.get_current_user().user_id())
				user.email = users.get_current_user().email()
				user.put()

				inventory = Inventory(id = users.get_current_user().user_id())
				inventory.put()

				playlist = Playlist(id = users.get_current_user().user_id())
				playlist.put()

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('setup.html')
			self.response.out.write(template.render(template_values))

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user:
			if user.setup:
				self.redirect('/dashboard')
			else:
				error = []

				user.setup = True

				# validate contact
				try:
					user.contact = self.request.get('contact').rstrip()
					if not user.contact:
						raise Exception, 'contact information cannot be empty.'
				except Exception, e:
					error.append(str(e))

				# validate country
				try:
					user.country = self.request.get('country')
					if user.country not in COUNTRY_CODES:
						raise Exception, 'invalid country.'
				except Exception, e:
					error.append(str(e))

				# validate pic
				try:
					user.pic = self.request.get('pic').rstrip()
					if not user.pic:
						user.pic = DISPLAY_PIC
					elif (urlparse(user.pic).scheme != 'http') and (urlparse(user.pic).scheme != 'https'):
						raise Exception, 'image link must be http or https.'
				except Exception, e:
					error.append(str(e))

				# validate name
				try:
					user.name = self.request.get('name').rstrip()
					if not user.name:
						raise Exception, 'display name cannot be empty.'
					qry = Person.query(Person.name == user.name)
					if qry.count():
						raise Exception, 'display name is already taken.'
				except Exception, e:
					error.append(str(e))

				if error:
					self.error(403)
					self.response.out.write(error)
				else:
					user.put()
					mail.send_mail(sender="Admin at Maph4ck <%s>" %ADMIN_MAIL,
					to="%s <%s>" %(user.name, user.email),
					subject="Welcome to maph4ck, %s!" %user.name,
					body="""Hello, %s! Thank you for signing up at maph4ck. We hope you will enjoy your stay. Please look at the FAQ if you have any doubts.
					""" % user.name)

					self.response.out.write('setup complete.')
		else:
			self.redirect('/setup')

class Dashboard(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('dashboard.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class Profile(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('profile.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class ProfileEdit(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('profile_edit.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user is None or user.setup == False:
			self.redirect('/dashboard')
		else:
			error = []

			# validate contact
			try:
				if user.contact != self.request.get('contact').rstrip():
					user.contact = self.request.get('contact').rstrip()
					if not user.contact:
						raise Exception, 'contact information cannot be empty.'
			except Exception, e:
				error.append(str(e))

			# validate bio
			try:
				if user.bio != self.request.get('bio').rstrip():
					user.bio = self.request.get('bio').rstrip()
			except Exception, e:
				error.append(str(e))

			# validate country
			try:
				if user.country != self.request.get('country'):
					user.country = self.request.get('country')
					if user.country not in COUNTRY_CODES:
						raise Exception, 'invalid country.'
			except Exception, e:
				error.append(str(e))

			# validate pic
			try:
				if user.pic != self.request.get('pic').rstrip() and not (user.pic == DISPLAY_PIC and not self.request.get('pic').rstrip()):
					user.pic = self.request.get('pic').rstrip()
					if not user.pic:
						user.pic = DISPLAY_PIC
					elif (urlparse(user.pic).scheme != 'http') and (urlparse(user.pic).scheme != 'https'):
						raise Exception, 'image link must be http or https.'
			except Exception, e:
				error.append(str(e))

			# validate name
			try:
				old_name = user.name
				if user.name != self.request.get('name').rstrip():
					user.name = self.request.get('name').rstrip()
					if not user.name:
						raise Exception, 'display name cannot be empty.'
					qry = Person.query(Person.name == user.name)
					if qry.count():
						raise Exception, 'display name is already taken.'
			except Exception, e:
				error.append(str(e))

			if error:
				self.error(403)
				self.response.out.write(error)
			else:
				user.put()

				if user.name != old_name:
					# change names
					games = Owner.query(Owner.name == old_name)
					for game in games:
						game.name = user.name
						game.put()

					games = Seeker.query(Seeker.name == old_name)
					for game in games:
						game.name = user.name
						game.put()

				self.response.out.write('profile updated.')

class FriendsPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			friends = ndb.get_multi(user.friend_keys)

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'friends': friends,
			}
			template = JINJA_ENVIRONMENT.get_template('friends.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class FriendsAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/friends')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				person_key = ndb.Key(urlsafe = self.request.get('person_url'))
				if person_key.kind() != 'Person':
					raise Exception, 'invalid key.'
				if person_key == user.key:
					raise Exception, 'forever alone.'
				if person_key in user.friend_keys:
					raise Exception, 'person is already a friend.'
				person = person_key.get()
				if person is None:
					raise Exception, 'no such person.'

				user.friend_keys.append(person_key)
				user.put()
			except:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class FriendsDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/friends')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				person_key = ndb.Key(urlsafe = self.request.get('person_url'))
				if person_key.kind() != 'Person':
					raise Exception, 'invalid key.'
				if person_key not in user.friend_keys:
					raise Exception, 'person is not a friend.'

				user.friend_keys.remove(person_key)
				user.put()
			except:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class LocationsPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			locations = ndb.gql('SELECT * '
				'FROM Location '
				'WHERE ANCESTOR IS :1 ',
				user.key)

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'locations': locations,
			}
			template = JINJA_ENVIRONMENT.get_template('locations.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class LocationsAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			locations = ndb.gql('SELECT * '
				'FROM Location '
				'WHERE ANCESTOR IS :1 ',
				user.key)

			template_values = {
				'user': user,
				'locations': jsonify(locations),
			}
			template = JINJA_ENVIRONMENT.get_template('locations_add.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			error = []
			location = Location(parent = user.key)

			# validate name
			try:
				location.name = self.request.get('name').rstrip()
				if not location.name:
					raise Exception, 'location name cannot be empty.'
			except Exception, e:
				error.append(str(e))

			try:
				location.address = self.request.get('address').rstrip()
			except Exception, e:
				error.append(str(e))

			try:
				location.geopt = ndb.GeoPt(self.request.get('latitude'), self.request.get('longitude'))
			except Exception, e:
				error.append(str(e))

			if error:
				self.error(403)
				self.response.out.write(error)	
			else:
				location.put()

				self.response.out.write('location added.')
		else:
			self.redirect('/setup')

class LocationsDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/locations')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				location_key = ndb.Key(urlsafe = self.request.get('location_url'))
				if location_key.kind() != 'Location':
					raise Exception, 'invalid key.'
				if location_key.parent() != user.key:
					raise Exception, 'access denied.'

				location_key.delete()

				self.response.out.write('location deleted.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class LocationsEdit(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/locations')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				location_key = ndb.Key(urlsafe = self.request.get('location_url'))
				if location_key.kind() != 'Location':
					raise Exception, 'invalid key.'
				if location_key.parent() != user.key:
					raise Exception, 'access denied.'

				location = location_key.get()
				if location is None:
					raise Exception, 'no such location.'
				if location.name == self.request.get('name').rstrip():
					raise Exception, 'no changes were made.'

				location.name = self.request.get('name').rstrip()
				if not location.name:
					raise Exception, 'location name cannot be empty.'

				location.put()

				self.response.out.write('name changed.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class LocationsView(webapp2.RequestHandler):
	def get(self, location_url):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				location_key = ndb.Key(urlsafe = location_url)
				if location_key.kind() != 'Location':
					raise Exception, 'invalid key.'
				if location_key.parent() != user.key:
					raise Exception, 'access denied.'

				location = location_key.get()
				if location is None:
					raise Exception, 'no such location.'

				template_values = {
					'location': location,
				}
				template = JINJA_ENVIRONMENT.get_template('locations_view.html')
				self.response.out.write(template.render(template_values))
			except:
				self.redirect('/locations')
		else:
			self.redirect('/setup')

class InventoryPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			inventory = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Inventory', users.get_current_user().user_id()))

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'inventory': inventory,
			}
			template = JINJA_ENVIRONMENT.get_template('inventory.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class InventoryAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('inventory_add.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			error = []

			inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
			game = Game(parent = inventory_key)

			# validate title
			try:
				game.title = self.request.get('title').rstrip()
				if not game.title:
					raise Exception, 'title cannot be empty.'
			except Exception, e:
				error.append(str(e))

			# validate platform
			try:
				game.platform = self.request.get('platform').rstrip()
				if not game.platform:
					raise Exception, 'platform cannot be empty.'
			except Exception, e:
				error.append(str(e))

			# validate pic
			try:
				game.pic = self.request.get('pic').rstrip()
				if game.pic:
					if (urlparse(game.pic).scheme != 'http') and (urlparse(game.pic).scheme != 'https'):
						raise Exception, 'image link must be http or https.'
			except Exception, e:
				error.append(str(e))

			# validate description
			try:
				game.description = self.request.get('description').rstrip()
			except Exception, e:
				error.append(str(e))

			if error:
				self.error(403)
				self.response.out.write(error)
			else:
				game.put()

				inventory = inventory_key.get()
				inventory.count += 1
				inventory.put()

				owners_key = ndb.Key('Owners', game.title,
					parent = ndb.Key('Platform', game.platform))
				owners = owners_key.get()
				if owners is None:
					owners = Owners(parent = ndb.Key('Platform', game.platform),
						id = game.title)
				owners.count += 1
				owners.put()

				owner_key = ndb.Key('Owner', users.get_current_user().user_id(),
					parent = owners_key)
				owner = owner_key.get()
				if owner is None:
					owner = Owner(parent = owners_key,
						id = users.get_current_user().user_id())
				owner.name = user.name
				owner.game_keys.append(game.key)
				owner.put()

				self.response.out.write('game added.')
		else:
			self.redirect('/setup')

class InventoryDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/inventory')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
				game_to_delete_key = ndb.Key(urlsafe = self.request.get('game_url'))
				if game_to_delete_key.kind() != 'Game':
					raise Exception, 'invalid key.'
				if game_to_delete_key.parent() != inventory_key:
					raise Exception, 'access denied.'

				game_to_delete = game_to_delete_key.get()
				if game_to_delete is None:
					raise Exception, 'no such game.'

				for listing_key in game_to_delete.listing_keys:
					listing = listing_key.get()
					listing_key.delete()

					for game_key in listing.own_keys:
						game = game_key.get()
						game.listing_keys.remove(listing_key)
						game.put()

					for game_key in listing.seek_keys:
						game = game_key.get()
						game.listing_keys.remove(listing_key)
						game.put()

				game_to_delete_key.delete()

				inventory = inventory_key.get()
				inventory.count -= 1
				inventory.put()

				owners_key = ndb.Key('Owners', game_to_delete.title,
					parent = ndb.Key('Platform', game_to_delete.platform))
				owners = owners_key.get()
				owners.count -= 1
				owners.put()

				owner_key = ndb.Key('Owner', users.get_current_user().user_id(),
					parent = owners_key)
				owner = owner_key.get()
				owner.game_keys.remove(game_to_delete.key)
			
				if owner.game_keys:
					owner.put()
				else:
					owner_key.delete()

				self.response.out.write('game deleted.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class PlaylistPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			playlist = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Playlist', users.get_current_user().user_id()))

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'playlist': playlist,
			}
			template = JINJA_ENVIRONMENT.get_template('playlist.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class PlaylistAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('playlist_add.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			error = []

			playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())
			game = Game(parent = playlist_key)

			# validate title
			try:
				game.title = self.request.get('title').rstrip()
				if not game.title:
					raise Exception, 'title cannot be empty.'
			except Exception, e:
				error.append(str(e))

			# validate platform
			try:
				game.platform = self.request.get('platform').rstrip()
				if not game.platform:
					raise Exception, 'platform cannot be empty.'
			except Exception, e:
				error.append(str(e))

			# validate pic
			try:
				game.pic = self.request.get('pic').rstrip()
				if game.pic:
					if (urlparse(game.pic).scheme != 'http') and (urlparse(game.pic).scheme != 'https'):
						raise Exception, 'image link must be http or https'
			except Exception, e:
				error.append(str(e))

			# validate description
			try:
				game.description = self.request.get('description').rstrip()
			except Exception, e:
				error.append(str(e))

			if error:
				self.error(403)
				self.response.out.write(error)
			else:
				game.put()

				playlist = playlist_key.get()
				playlist.count += 1
				playlist.put()

				seekers_key = ndb.Key('Seekers', game.title,
					parent = ndb.Key('Platform', game.platform))
				seekers = seekers_key.get()
				if seekers is None:
					seekers = Seekers(parent = ndb.Key('Platform', game.platform),
						id = game.title)
				seekers.count += 1
				seekers.put()

				seeker_key = ndb.Key('Seeker', users.get_current_user().user_id(),
					parent = seekers_key)
				seeker = seeker_key.get()
				if seeker is None:
					seeker = Seeker(parent = seekers_key,
						id = users.get_current_user().user_id())
				seeker.name = user.name
				seeker.game_keys.append(game.key)
				seeker.put()

				self.response.out.write('game added.')
		else:
			self.redirect('/setup')

class PlaylistDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/playlist')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())
				game_to_delete_key = ndb.Key(urlsafe = self.request.get('game_url'))
				if game_to_delete_key.kind() != 'Game':
					raise Exception, 'invalid key.'
				if game_to_delete_key.parent() != playlist_key:
					raise Exception, 'access denied.'

				game_to_delete = game_to_delete_key.get()
				if game_to_delete is None:
					raise Exception, 'no such game.'

				for listing_key in game_to_delete.listing_keys:
					listing = listing_key.get()
					listing_key.delete()

					for game_key in listing.own_keys:
						game = game_key.get()
						game.listing_keys.remove(listing_key)
						game.put()

					for game_key in listing.seek_keys:
						game = game_key.get()
						game.listing_keys.remove(listing_key)
						game.put()

				game_to_delete_key.delete()

				playlist = playlist_key.get()
				playlist.count -= 1
				playlist.put()

				seekers_key = ndb.Key('Seekers', game_to_delete.title,
					parent = ndb.Key('Platform', game_to_delete.platform))
				seekers = seekers_key.get()
				seekers.count -= 1
				seekers.put()

				seeker_key = ndb.Key('Seeker', users.get_current_user().user_id(),
					parent = seekers_key)
				seeker = seeker_key.get()
				seeker.game_keys.remove(game_to_delete.key)
			
				if seeker.game_keys:
					seeker.put()
				else:
					seeker_key.delete()

				self.response.out.write('game deleted.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class ListingsPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			listings = ndb.gql('SELECT * '
				'FROM Listing '
				'WHERE ANCESTOR IS :1 '
				'ORDER BY date DESC',
				user.key)
			listings = listings.map(listing_with_games)

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'listings': listings,
			}
			template = JINJA_ENVIRONMENT.get_template('listings.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class ListingsAdd(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			inventory = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Inventory', users.get_current_user().user_id()))

			playlist = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Playlist', users.get_current_user().user_id()))

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'inventory': inventory,
				'playlist': playlist,
			}
			template = JINJA_ENVIRONMENT.get_template('listings_add.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				jdata = json.loads(self.request.body)
				own_urls = jdata['own_urls']
				seek_urls = jdata['seek_urls']
				offer_amt = int(jdata['offer_amt'])
				request_amt = int(jdata['request_amt'])
				description = jdata['description']

				if offer_amt is None or request_amt is None:
					raise Exception, 'topup amounts cannot be empty.'
				if offer_amt < 0 or request_amt < 0:
					raise Exception, 'topup amounts cannot be negative.'
				if offer_amt > 0 and request_amt > 0:
					raise Exception, 'topup amounts cannot be positive at the same time.'
				if len(own_urls) == 0 and len(seek_urls) == 0:
					raise Exception, 'listing cannot be empty.'
				if (len(own_urls) > 0 or offer_amt > 0) and len(seek_urls) == 0 and request_amt == 0:
					raise Exception, 'offer cannot be empty.'
				if (len(seek_urls) > 0 or request_amt > 0) and len(own_urls) == 0 and offer_amt == 0:
					raise Exception, 'request cannot be empty.'
				if len(description) > 500:
					raise Exception, 'description exceeds 500 characters.'

				listing = Listing(parent = user.key)
				inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
				playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())

				listing.owner_key = user.key

				if offer_amt > 0:
					listing.topup = offer_amt
				else:
					listing.topup = -request_amt

				for game_url in own_urls:
					game_key = ndb.Key(urlsafe = game_url)
					if game_key.kind() != 'Game':
						raise Exception, 'invalid key.'
					if game_key.parent() != inventory_key:
						raise Exception, 'access denied.'

					game = game_key.get()
					if game is None:
						raise Exception, 'no such game in inventory.'

					listing.own_keys.append(game_key)
					listing.own_games.append(game.title + game.platform)

				for game_url in seek_urls:
					game_key = ndb.Key(urlsafe = game_url)
					if game_key.kind() != 'Game':
						raise Exception, 'invalid key.'
					if game_key.parent() != playlist_key:
						raise Exception, 'access denied.'

					game = game_key.get()
					if game is None:
						raise Exception, 'no such game in playlist.'

					listing.seek_keys.append(game_key)
					listing.seek_games.append(game.title + game.platform)

				listing.description = description
				listing.put()

				for game_key in listing.own_keys:
					game = game_key.get()
					game.listing_keys.append(listing.key)
					game.put()

				for game_key in listing.seek_keys:
					game = game_key.get()
					game.listing_keys.append(listing.key)
					game.put()

				self.response.out.write('listing added.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class ListingsDelete(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/listings')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				listing_key = ndb.Key(urlsafe = self.request.get('listing_url'))
				if listing_key.kind() != 'Listing':
					raise Exception, 'invalid key.'
				if listing_key.parent() != user.key:
					raise Exception, 'access denied.'
				
				listing = listing_key.get()
				if listing is None:
					raise Exception, 'no such listing.'
				listing_key.delete()

				for game_key in listing.own_keys:
					game = game_key.get()
					game.listing_keys.remove(listing.key)
					game.put()

				for game_key in listing.seek_keys:
					game = game_key.get()
					game.listing_keys.remove(listing.key)
					game.put()

				for comment_key in listing.comment_keys:
					comment_key.delete()

				self.response.out.write('listing deleted.')
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class ListingsRecent(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				try:
					qry = Listing.query().order(-Listing.date)
					pager = ndbpager.Pager(query = qry, page = self.request.get('page', default_value = 1))
					listings, cursor, more = pager.paginate(page_size = 10)

					my_locations = ndb.gql('SELECT * '
						'FROM Location '
						'WHERE ANCESTOR IS :1 ',
						user.key)

					listings = [(listing,
						ndb.get_multi(listing.own_keys),
						ndb.get_multi(listing.seek_keys),
						listing.owner_key.get(),
						min_dist(my_locations, ndb.gql('SELECT * '
							'FROM Location '
							'WHERE ANCESTOR IS :1 ',
							listing.owner_key))) for listing in listings]

					template_values = {
						'user': user,
						'logout': users.create_logout_url(self.request.host_url),
						'listings': listings,
						'pager': pager,
					}
					template = JINJA_ENVIRONMENT.get_template('listings_recent.html')
					self.response.out.write(template.render(template_values))
				except:
					self.redirect('/dashboard')
			else:
				self.redirect('/setup')
		else:
			try:
				qry = Listing.query().order(-Listing.date)
				pager = ndbpager.Pager(query = qry, page = self.request.get('page', default_value = 1))
				listings, cursor, more = pager.paginate(page_size = 10)

				listings = [(listing,
					ndb.get_multi(listing.own_keys),
					ndb.get_multi(listing.seek_keys),
					listing.owner_key.get()) for listing in listings]

				template_values = {
					'login': users.create_login_url(self.request.uri),
					'listings': listings,
					'pager': pager,
				}
				template = JINJA_ENVIRONMENT.get_template('listings_recent_public.html')
				self.response.out.write(template.render(template_values))
			except:
				self.redirect('/')

class ListingsSearch(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				inventory = ndb.gql('SELECT * '
					'FROM Game '
					'WHERE ANCESTOR IS :1 ',
					ndb.Key('Inventory', users.get_current_user().user_id()))

				playlist = ndb.gql('SELECT * '
					'FROM Game '
					'WHERE ANCESTOR IS :1 ',
					ndb.Key('Playlist', users.get_current_user().user_id()))

				template_values = {
					'user': user,
					'logout': users.create_logout_url(self.request.host_url),
					'inventory': inventory,
					'playlist': playlist,
					'own_url': self.request.get('own_url'),
					'seek_url': self.request.get('seek_url'),
				}
				template = JINJA_ENVIRONMENT.get_template('listings_search.html')
				self.response.out.write(template.render(template_values))
			else:
				self.redirect('/dashboard')
		else:
			try:
				query_type = self.request.get('query_type')
				title = self.request.get('title')
				platform = self.request.get('platform')

				if query_type == 'own':
					qry = Listing.query(Listing.seek_games == title + platform).order(-Listing.date)
				elif query_type == 'seek':
					qry = Listing.query(Listing.own_games == title + platform).order(-Listing.date)
				else:
					raise Exception, 'invalid query.'

				pager = ndbpager.Pager(query = qry, page = self.request.get('page', default_value = 1))
				listings, cursor, more = pager.paginate(page_size = 10)

				listings = [(listing,
					ndb.get_multi(listing.own_keys),
					ndb.get_multi(listing.seek_keys),
					listing.owner_key.get()) for listing in listings]

				template_values = {
					'login': users.create_login_url(self.request.uri),
					'listings': listings,
					'pager': pager,
					'query_type': query_type,
					'title': title,
					'platform': platform,
				}
				template = JINJA_ENVIRONMENT.get_template('listings_search_public.html')
				self.response.out.write(template.render(template_values))
			except:
				self.redirect('/')

	def post(self):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				try:
					jdata = json.loads(self.request.body)
					own_urls = jdata['own_urls']
					seek_urls = jdata['seek_urls']

					if len(own_urls) == 0 and len(seek_urls) == 0:
						raise Exception, 'listing cannot be empty.'

					inventory_key = ndb.Key('Inventory', users.get_current_user().user_id())
					playlist_key = ndb.Key('Playlist', users.get_current_user().user_id())

					qry = None

					for game_url in own_urls:
						game_key = ndb.Key(urlsafe = game_url)
						if game_key.kind() != 'Game':
							raise Exception, 'invalid key.'
						if game_key.parent() != inventory_key:
							raise Exception, 'access denied.'

						game = game_key.get()
						if game is None:
							raise Exception, 'no such game in inventory.'

						if qry is None:
							qry = Listing.query(Listing.seek_games == game.title + game.platform)
						else:
							qry = qry.filter(Listing.seek_games == game.title + game.platform)

					for game_url in seek_urls:
						game_key = ndb.Key(urlsafe = game_url)
						if game_key.kind() != 'Game':
							raise Exception, 'invalid key.'
						if game_key.parent() != playlist_key:
							raise Exception, 'access denied.'

						game = game_key.get()
						if game is None:
							raise Exception, 'no such game in playlist.'

						if qry is None:
							qry = Listing.query(Listing.own_games == game.title + game.platform)
						else:
							qry = qry.filter(Listing.own_games == game.title + game.platform)

					listings = qry.map(listing_all)
	 
					template_values = {
						'listings': listings,
					}
					template = JINJA_ENVIRONMENT.get_template('listings_search_results.html')
					self.response.out.write(template.render(template_values))
				except Exception, e:
					self.error(403)
					self.response.out.write([e])
			else:
				self.redirect('/setup')
		else:
			self.redirect('/')

class ListingsSearchMap(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			locations = ndb.gql('SELECT * '
				'FROM Location '
				'WHERE ANCESTOR IS :1 ',
				user.key)

			template_values = {
				'user': user,
				'locations': jsonify(locations),
			}
			template = JINJA_ENVIRONMENT.get_template('listings_search_view.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class ListingPage(webapp2.RequestHandler):
	def get(self, listing_url):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				try:
					listing = ndb.Key(urlsafe = listing_url).get()
					if listing.key.kind() != 'Listing':
						raise Exception, 'invalid key.'
					if listing is None:
						raise Exception, 'no such listing.'

					if listing.owner_key == user.key:
						person = user
						distance = 0
					else:
						person = listing.owner_key.get()

						my_locations = ndb.gql('SELECT * '
							'FROM Location '
							'WHERE ANCESTOR IS :1 ',
							user.key)

						your_locations = ndb.gql('SELECT * '
							'FROM Location '
							'WHERE ANCESTOR IS :1 ',
							listing.owner_key)

						distance = min_dist(my_locations, your_locations)

					own_games = ndb.get_multi(listing.own_keys)
					seek_games = ndb.get_multi(listing.seek_keys)
					comments = ndb.get_multi(listing.comment_keys)

					template_values = {
						'user': user,
						'logout': users.create_logout_url(self.request.host_url),
						'listing': listing,
						'person': person,
						'distance': distance,
						'own_games': own_games,
						'seek_games': seek_games,
						'comments': comments,
					}
					template = JINJA_ENVIRONMENT.get_template('listing.html')
					self.response.out.write(template.render(template_values))
				except Exception, e:
					self.redirect('/dashboard')
			else:
				self.redirect('/setup')
		else:
			try:
				listing = ndb.Key(urlsafe = listing_url).get()
				if listing.key.kind() != 'Listing':
					raise Exception, 'invalid key.'
				if listing is None:
					raise Exception, 'no such listing.'

				person = listing.owner_key.get()
				own_games = ndb.get_multi(listing.own_keys)
				seek_games = ndb.get_multi(listing.seek_keys)
				comments = ndb.get_multi(listing.comment_keys)

				template_values = {
					'login': users.create_login_url(self.request.uri),
					'listing': listing,
					'person': person,
					'own_games': own_games,
					'seek_games': seek_games,
					'comments': comments,
				}
				template = JINJA_ENVIRONMENT.get_template('listing_public.html')
				self.response.out.write(template.render(template_values))
			except Exception, e:
				self.redirect('/')

class ListingComment(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				listing = ndb.Key(urlsafe = self.request.get('listing_url')).get()
				if listing.key.kind() != 'Listing':
					raise Exception, 'invalid key.'
				if listing is None:
					raise Exception, 'no such listing.'

				comment = Comment(parent = user.key)
				comment.owner_key = user.key
				comment.content = self.request.get('comment').rstrip()
				if not comment.content:
					raise Exception, 'comment cannot be empty.'
				if len(comment.content) > 500:
					raise Exception, 'comment exceeds 500 characters.'
				comment.put()

				listing.comment_keys.append(comment.key)

				for key in listing.subscriber_keys:
					subscriber = key.get()
					if subscriber is not user:
						mail.send_mail(sender="Admin at Maph4ck <%s>" %ADMIN_MAIL,
										to="%s <%s>" %(subscriber.name, subscriber.email),
										subject="New comment posted",
										body="""%s has posted a new comment at http://maph4cktest.appspot.com/listing/%s:\n\n%s
										""" % (user.name, listing.key.urlsafe(), comment.content) )

				if user.key not in listing.subscriber_keys:
					listing.subscriber_keys.append(user.key)
				listing.put()

				template_values = {
					'user': user,
					'comment': comment,
				}
				template = JINJA_ENVIRONMENT.get_template('comment.html')
				self.response.out.write(template.render(template_values))
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

class UserPage(webapp2.RequestHandler):
	def get(self, person_url):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			person_key = ndb.Key(urlsafe = person_url)
			if person_key.kind() != 'Person':
				raise Exception, 'invalid key.'

			if person_key == user.key:
				raise Exception, 'same user.'

			person = person_key.get()
			if person is None:
				raise Exception, 'no such person.'

			my_inventory = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Inventory', users.get_current_user().user_id()))

			my_playlist = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Playlist', users.get_current_user().user_id()))

			your_inventory = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Inventory', person_key.id()))

			your_playlist = ndb.gql('SELECT * '
				'FROM Game '
				'WHERE ANCESTOR IS :1 ',
				ndb.Key('Playlist', person_key.id()))

			my_locations = ndb.gql('SELECT * '
				'FROM Location '
				'WHERE ANCESTOR IS :1 ',
				user.key)

			your_locations = ndb.gql('SELECT * '
				'FROM Location '
				'WHERE ANCESTOR IS :1 ',
				person_key)

			listings = ndb.gql('SELECT * '
				'FROM Listing '
				'WHERE ANCESTOR IS :1 '
				'ORDER BY date DESC',
				person_key)

			listings = listings.map(listing_with_games)

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
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
				'person': person,
				'my_diff': my_diff,
				'my_match': my_match,
				'your_match': your_match,
				'your_diff': your_diff,
				'nearest_distance': nearest_distance,
				'listings': listings,
				}
			template = JINJA_ENVIRONMENT.get_template('user.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

class UserLocations(webapp2.RequestHandler):
	def get(self, person_url):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				try:
					person_key = ndb.Key(urlsafe = person_url)
					if person_key.kind() != 'Person':
						raise Exception, 'invalid key.'
					if person_key == user.key:
						raise Exception, 'same user.'
					person = person_key.get()
					if person is None:
						raise Exception, 'no such person.'

					my_locations = ndb.gql('SELECT * '
						'FROM Location '
						'WHERE ANCESTOR IS :1 ',
						user.key)

					your_locations = ndb.gql('SELECT * '
						'FROM Location '
						'WHERE ANCESTOR IS :1 ',
						person_key)

					template_values = {
						'user': user,
						'person': person,
						'my_locations': json.dumps([ndb.Model.to_dict(location, include = ['geopt']) for location in my_locations], cls = NdbEncoder),
						'your_locations': json.dumps([ndb.Model.to_dict(location, include = ['geopt']) for location in your_locations], cls = NdbEncoder),
					}
					template = JINJA_ENVIRONMENT.get_template('user_locations.html')
					self.response.out.write(template.render(template_values))
				except:
					self.redirect('/dashboard')
			else:
				self.redirect('/setup')
		else:
			try:
				person_key = ndb.Key(urlsafe = person_url)
				if person_key.kind() != 'Person':
					raise Exception, 'invalid key.'
				person = person_key.get()
				if person is None:
					raise Exception, 'no such person.'

				locations = ndb.gql('SELECT * '
					'FROM Location '
					'WHERE ANCESTOR IS :1 ',
					person_key)

				template_values = {
					'person': person,
					'locations': json.dumps([ndb.Model.to_dict(location, include = ['geopt']) for location in locations], cls = NdbEncoder),
				}
				template = JINJA_ENVIRONMENT.get_template('user_locations_public.html')
				self.response.out.write(template.render(template_values))
			except:
				self.redirect('/')

class ConversationsPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			conversations = ndb.gql('SELECT * '
				'FROM Conversation '
				'WHERE ANCESTOR IS :1 ',
				user.key)

			template_values = {
						'user': user,
						'conversations': conversations,
					}
			template = JINJA_ENVIRONMENT.get_template('conversations.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			jdata = json.loads(self.request.body)
			person_urls = jdata['person_urls']

			qry = Conversation.query(Conversation.person_keys == user.key)
			person_keys = None
			for person_url in person_urls:
				person_keys.append(ndb.Key(urlsafe = person_url))
				if person_key.kind() != 'Person':
					raise Exception, 'invalid key.'
				if person_key == user.key:
					raise Exception, 'you cannot add yourself to conversation.'
				if not person_key.get():
					raise Exception, 'no such person.'

				qry = qry.filter(Conversation.person_keys == person_key)

			if qry:
				conversation = qry.fetch(1)
			else:
				conversation = Conversation()
				conversation.person_keys.append(user.key)
				for person_key in person_keys:
					conversation.person_keys.append(person_key)

				conversation.num_unread = [0] * len(person_keys)

			message = Message()
			message.content = self.request.get('message').rstrip()
			if not message.content:
				raise Exception, 'message cannot be empty.'
			if len(message) > MAX_STR_LEN:
				raise Exception, 'message exceeds max length.'
			conversation.messages.append(message)

			for counter, person_key in enumerate(person_keys):
				if person_key == user.key:
					num_unread[counter] = 0
				else:
					num_unread[counter] += 1

			conversation.date = message.date
			conversation.put()

			self.response.out.write('message sent.')
		else:
			self.redirect('/setup')

class MarkAsRead(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/conversations')
		else:
			self.redirect('/setup')
	def post(self, conversation_url):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			conversation_key = ndb.Key(urlsafe = conversation_url)
			if conversation_key.kind() != 'Conversation':
				raise Exception, 'invalid key.'
			conversation = conversation_key.get()
			if conversation is None:
				raise Exception, 'no such conversation.'
			if user.key not in conversation.person_keys:
				raise Exception, 'access denied.'
			
			conversation.num_unread[conversation.person_keys.index(user.key)] = 0
			conversation.put()

			self.response.out.write('conversation read.')
		else:
			self.redirect('/setup')

class FeedbackPage(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('feedback.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			try:
				feedback = Feedback(parent = user.key)
				feedback.owner_key = user.key
				feedback.content = self.request.get('feedback').rstrip()
				if not feedback.content:
					raise Exception, 'feedback cannot be empty.'
				if len(feedback.content) > 500:
					raise Exception, 'feedback exceeds 500 characters.'
				feedback.put()
			except Exception, e:
				self.error(403)
				self.response.out.write([e])
		else:
			self.redirect('/setup')

# Unused handlers
class GetListing(webapp2.RequestHandler):
	def get(self):
		qry = Listing.query().order(-Listing.date).fetch(1)
		listing = qry[0]
		person = listing.owner_key.get()
		own_games = ndb.get_multi(listing.own_keys)
		seek_games = ndb.get_multi(listing.seek_keys)

		template_values = {
			'listing': listing,
			'person': person,
			'own_games': own_games,
			'seek_games': seek_games,
		}
		template = JINJA_ENVIRONMENT.get_template('latest_listing.html')
		self.response.out.write(template.render(template_values))

class SearchResults(webapp2.RequestHandler):
	def show(self, query_type = '', title = '', platform = '', results = '', distances = '', error = ''):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
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
		else:
			self.redirect('/setup')

	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			query_type = self.request.get('query_type')
			if query_type == 'have':
				title = self.request.get('title')
				platform = self.request.get('platform')

				owners_key = ndb.Key('Owners', title,
					parent = ndb.Key('Platform', platform))

				owners = ndb.gql('SELECT * '
					'FROM Owner '
					'WHERE ANCESTOR IS :1 ',
					owners_key)

				results = owners.map(user_with_distance)
				results = sorted(results, key = itemgetter(1))
				
				self.show(query_type, title, platform, results)

			elif query_type == 'want':
				title = self.request.get('title')
				platform = self.request.get('platform')

				seekers_key = ndb.Key('Seekers', title,
					parent = ndb.Key('Platform', platform))

				seekers = ndb.gql('SELECT * '
					'FROM Seeker '
					'WHERE ANCESTOR IS :1 ',
					seekers_key)

				results = seekers.map(user_with_distance)
				results = sorted(results, key = itemgetter(1))

				self.show(query_type, title, platform, results)

			else:
				error = 'invalid query.'
				self.show(error = error)
		else:
			self.redirect('/setup')

class FAQ(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('faq.html')
			self.response.out.write(template.render(template_values))
		else:
			self.redirect('/setup')

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/setup', Setup),
	('/dashboard', Dashboard),
	('/profile', Profile),
	('/profile/edit', ProfileEdit),
	('/friends', FriendsPage),
	('/friends/add', FriendsAdd),
	('/friends/delete', FriendsDelete),
	('/locations', LocationsPage),
	('/locations/add', LocationsAdd),
	('/locations/delete', LocationsDelete),
	('/locations/edit', LocationsEdit),
	('/locations/view/(.*)', LocationsView),
	('/inventory', InventoryPage),
	('/inventory/add', InventoryAdd),
	('/inventory/delete', InventoryDelete),
	('/playlist', PlaylistPage),
	('/playlist/add', PlaylistAdd),
	('/playlist/delete', PlaylistDelete),
	('/listings', ListingsPage),
	('/listings/add', ListingsAdd),
	('/listings/delete', ListingsDelete),
	('/listings/recent', ListingsRecent),
	('/listings/search', ListingsSearch),
	('/listings/search/map', ListingsSearchMap),
	('/listing/comment', ListingComment),
	('/listing/(.*)', ListingPage),
	('/user/locations/(.*)', UserLocations),
	('/user/(.*)', UserPage),
	('/conversations', ConversationsPage),
	('/feedback', FeedbackPage),
	('/faq', FAQ),

	('/get/listing', GetListing),
	('/search/results', SearchResults),
	('/*', Dashboard),
	], debug=True)