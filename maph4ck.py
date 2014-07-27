# Local modules
import constants
import models
import ndbpager
import utils
import validate

# Other modules
import datetime
import jinja2
import json
import os
import webapp2
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

# Base handler that checks if user is logged in.
class BaseHandler(webapp2.RequestHandler):
	def get(self, **kwargs):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				self.get_user(user, **kwargs)
			else:
				self.redirect('/setup')
		else:
			self.get_public(**kwargs)

	def post(self, **kwargs):
		if users.get_current_user():
			user = ndb.Key('Person', users.get_current_user().user_id()).get()
			if user and user.setup:
				self.post_user(user, **kwargs)
			else:
				self.error(403)
				self.response.write(['please refresh your page and try again.'])
		else:
			self.post_public(**kwargs)

class MainPage(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/dashboard')

	def get_public(self, **kwargs):
		template = JINJA_ENVIRONMENT.get_template('public/front.html')
		self.response.write(template.render())

class Setup(webapp2.RequestHandler):
	def get(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user and user.setup:
			self.redirect('/dashboard')
		else:
			if user is None:
				user = models.Person(id = users.get_current_user().user_id())
				user.email = users.get_current_user().email()
				user.put()

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.host_url),
			}
			template = JINJA_ENVIRONMENT.get_template('user/setup.html')
			self.response.write(template.render(template_values))

	def post(self):
		user = ndb.Key('Person', users.get_current_user().user_id()).get()
		if user:
			if user.setup:
				self.error(403)
				self.response.write(['please refresh your page and try again.'])
			else:
				error = []

				user.setup = True

				try:
					user.contact = validate.contact(self.request.get('contact'))
				except Exception, e:
					error.append(str(e))

				try:
					user.country = validate.country(self.request.get('country'))
				except Exception, e:
					error.append(str(e))

				try:
					user.pic = validate.user_pic(self.request.get('pic'))
				except Exception, e:
					error.append(str(e))

				try:
					user.name = validate.user_name(self.request.get('name'))
				except Exception, e:
					error.append(str(e))

				if error:
					self.error(403)
					self.response.write(error)
				else:
					user.put()
					mail.send_mail(
						sender = "Admin at maph4ck <%s>" %constants.ADMIN_MAIL,
						to = "%s <%s>" % (user.name, user.email),
						subject = "Welcome to maph4ck",
						body = """Hello, %s! Thank you for signing up at maph4ck. You can now sign in at %s using your Google Account.""" % (user.name, self.request.host_url),
					)

					self.response.write('setup complete.')
		else:
			self.error(403)
			self.response.write(['please refresh your page and try again.'])

class Dashboard(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
		}
		template = JINJA_ENVIRONMENT.get_template('user/dashboard.html')
		self.response.write(template.render(template_values))

class Profile(BaseHandler):
	def get_user(self, user, **kwargs):
		inventory = models.InventoryGame.query(ancestor = user.key)
		playlist = models.PlaylistGame.query(ancestor = user.key)

		trades = models.Trade.query(ancestor = user.key)
		trades = trades.map(utils.trade_with_games)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url + '/user/' + user.key.urlsafe()),
			'inventory': inventory,
			'playlist': playlist,
			'trades': trades,
		}
		template = JINJA_ENVIRONMENT.get_template('user/profile.html')
		self.response.write(template.render(template_values))

class ProfileEdit(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
		}
		template = JINJA_ENVIRONMENT.get_template('user/profile_edit.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		error = []

		try:
			user.pic = validate.user_pic(self.request.get('pic'))
		except Exception, e:
			error.append(str(e))

		try:
			user.country = validate.country(self.request.get('country'))
		except Exception, e:
			error.append(str(e))

		try:
			user.contact = validate.contact(self.request.get('contact'))
		except Exception, e:
			error.append(str(e))

		try:
			user.bio = validate.bio(self.request.get('bio'))
		except Exception, e:
			error.append(str(e))

		if error:
			self.error(403)
			self.response.write(error)
		else:
			user.put()

			self.response.write('profile updated.')

class Friends(BaseHandler):
	def get_user(self, user, **kwargs):
		friends = ndb.get_multi(user.friend_keys)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'friends': friends,
		}
		template = JINJA_ENVIRONMENT.get_template('user/friends.html')
		self.response.write(template.render(template_values))

class FriendsAdd(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/friends')

	def post_user(self, user, **kwargs):
		try:
			person_key = ndb.Key(urlsafe = self.request.get('person_url'))
			if person_key.kind() != 'Person':
				raise Exception, 'invalid key.'
			if person_key == user.key:
				raise Exception, 'you cannot add yourself as a friend.'
			if person_key in user.friend_keys:
				raise Exception, 'person is already a friend.'
			person = person_key.get()
			if person is None:
				raise Exception, 'no such person.'

			user.friend_keys.append(person_key)
			user.put()

			self.response.write('friend added.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class FriendsDelete(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/friends')

	def post_user(self, user, **kwargs):
		try:
			person_key = ndb.Key(urlsafe = self.request.get('person_url'))
			if person_key not in user.friend_keys:
				raise Exception, 'person is not a friend.'

			user.friend_keys.remove(person_key)
			user.put()

			self.response.write('friend removed.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class Locations(BaseHandler):
	def get_user(self, user, **kwargs):
		locations = models.Location.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'locations': locations,
		}
		template = JINJA_ENVIRONMENT.get_template('user/locations.html')
		self.response.write(template.render(template_values))

class LocationsAdd(BaseHandler):
	def get_user(self, user, **kwargs):
		locations = models.Location.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'locations': json.dumps([ndb.Model.to_dict(location, include = ['name', 'location']) for location in locations], cls = utils.NdbEncoder),
		}
		template = JINJA_ENVIRONMENT.get_template('user/locations_add.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		error = []

		location = models.Location(parent = user.key)

		try:
			location.name = validate.location_name(self.request.get('name'))
		except Exception, e:
			error.append(str(e))

		try:
			location.address = validate.address(self.request.get('address'))
		except Exception, e:
			error.append(str(e))

		try:
			location.location = ndb.GeoPt(self.request.get('latitude'), self.request.get('longitude'))
		except Exception, e:
			error.append(str(e))

		if error:
			self.error(403)
			self.response.write(error)
		else:
			location.put()

			self.response.write('location added.')

class LocationsDelete(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/locations')

	def post_user(self, user, **kwargs):
		try:
			location_key = ndb.Key(urlsafe = self.request.get('location_url'))
			if location_key.kind() != 'Location':
				raise Exception, 'invalid key.'
			if location_key.parent() != user.key:
				raise Exception, 'access denied.'

			location_key.delete()

			self.response.write('location deleted.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class LocationsEdit(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/locations')

	def post_user(self, user, **kwargs):
		try:
			location_key = ndb.Key(urlsafe  = self.request.get('location_url'))
			if location_key.kind() != 'Location':
				raise Exception, 'invalid key.'
			if location_key.parent() != user.key:
				raise Exception, 'access denied.'

			location = location_key.get()
			if location is None:
				raise Exception, 'no such location.'

			location.name = validate.location_name(self.request.get('name'))
			location.put()

			self.response.write('location name changed.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class LocationsView(BaseHandler):
	def get_user(self, user, **kwargs):
		location_url = kwargs['location_url']

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
		template = JINJA_ENVIRONMENT.get_template('user/locations_view.html')
		self.response.write(template.render(template_values))

class Inventory(BaseHandler):
	def get_user(self, user, **kwargs):
		inventory = models.InventoryGame.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'inventory': inventory,
		}
		template = JINJA_ENVIRONMENT.get_template('user/inventory.html')
		self.response.write(template.render(template_values))

class InventoryAdd(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
		}
		template = JINJA_ENVIRONMENT.get_template('user/inventory_add.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		error = []

		game = models.InventoryGame(parent = user.key)

		try:
			game.title = validate.title(self.request.get('title'))
		except Exception, e:
			error.append(str(e))

		try:
			game.platform = validate.platform(self.request.get('platform'))
		except Exception, e:
			error.append(str(e))

		try:
			game.pic = validate.game_pic(self.request.get('pic'))
		except Exception, e:
			error.append(str(e))

		try:
			game.description = validate.game_description(self.request.get('description'))
		except Exception, e:
			error.append(str(e))

		try:
			game.wrapped = validate.wrapped(self.request.get('wrapped'))
		except Exception, e:
			error.append(str(e))

		if error:
			self.error(403)
			self.response.write(error)
		else:
			game.put()

			user.inventory_count += 1
			user.put()

			self.response.write('game added to inventory.')

class InventoryDelete(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/inventory')

	def post_user(self, user, **kwargs):
		try:
			game_to_delete_key = ndb.Key(urlsafe = self.request.get('game_url'))
			if game_to_delete_key.kind() != 'InventoryGame':
				raise Exception, 'invalid key.'
			if game_to_delete_key.parent() != user.key:
				raise Exception, 'access denied.'

			game_to_delete = game_to_delete_key.get()
			if game_to_delete is None:
				raise Exception, 'no such game in inventory.'

			for trade_key in game_to_delete.trade_keys:
				trade = trade_key.get()
				trade_key.delete()

				for game_key in trade.own_keys:
					game = game_key.get()
					game.trade_keys.remove(trade_key)
					game.put()

				for game_key in trade.seek_keys:
					game = game_key.get()
					game.trade_keys.remove(trade_key)
					game.put()

			game_to_delete_key.delete()

			user.inventory_count -= 1
			user.put()

			self.response.write('game deleted from inventory.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class Playlist(BaseHandler):
	def get_user(self, user, **kwargs):
		playlist = models.PlaylistGame.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'playlist': playlist,
		}
		template = JINJA_ENVIRONMENT.get_template('user/playlist.html')
		self.response.write(template.render(template_values))

class PlaylistAdd(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
		}
		template = JINJA_ENVIRONMENT.get_template('user/playlist_add.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		error = []

		game = models.PlaylistGame(parent = user.key)

		try:
			game.title = validate.title(self.request.get('title'))
		except Exception, e:
			error.append(str(e))

		try:
			game.platform = validate.platform(self.request.get('platform'))
		except Exception, e:
			error.append(str(e))

		try:
			game.pic = validate.game_pic(self.request.get('pic'))
		except Exception, e:
			error.append(str(e))

		try:
			game.description = validate.game_description(self.request.get('description'))
		except Exception, e:
			error.append(str(e))

		try:
			game.wrapped = validate.wrapped(self.request.get('wrapped'))
		except Exception, e:
			error.append(str(e))

		if error:
			self.error(403)
			self.response.write(error)
		else:
			game.put()

			user.playlist_count += 1
			user.put()

			self.response.write('game added to playlist.')

class PlaylistDelete(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/playlist')

	def post_user(self, user, **kwargs):
		try:
			game_to_delete_key = ndb.Key(urlsafe = self.request.get('game_url'))
			if game_to_delete_key.kind() != 'PlaylistGame':
				raise Exception, 'invalid key.'
			if game_to_delete_key.parent() != user.key:
				raise Exception, 'access denied.'

			game_to_delete = game_to_delete_key.get()
			if game_to_delete is None:
				raise Exception, 'no such game in playlist.'

			for trade_key in game_to_delete.trade_keys:
				trade = trade_key.get()
				trade_key.delete()

				for game_key in trade.own_keys:
					game = game_key.get()
					game.trade_keys.remove(trade_key)
					game.put()

				for game_key in trade.seek_keys:
					game = game_key.get()
					game.trade_keys.remove(trade_key)
					game.put()

			game_to_delete_key.delete()

			user.playlist_count -= 1
			user.put()

			self.response.write('game deleted from playlist.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class Trades(BaseHandler):
	def get_user(self, user, **kwargs):
		trades = models.Trade.query(ancestor = user.key).order(-models.Trade.date)
		trades = trades.map(utils.trade_with_games)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'trades': trades,
		}
		template = JINJA_ENVIRONMENT.get_template('user/trades.html')
		self.response.write(template.render(template_values))

class TradesAdd(BaseHandler):
	def get_user(self, user, **kwargs):
		inventory = models.InventoryGame.query(ancestor = user.key)
		playlist = models.PlaylistGame.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'inventory': inventory,
			'playlist': playlist,
		}
		template = JINJA_ENVIRONMENT.get_template('user/trades_add.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		try:
			jdata = json.loads(self.request.body)
			own_urls = jdata['own_urls']
			seek_urls = jdata['seek_urls']
			offer_amt = int(jdata['offer_amt'])
			request_amt = int(jdata['request_amt'])
			description = validate.trade_description(jdata['description'])

			if offer_amt is None or request_amt is None:
				raise Exception, 'topup amounts cannot be empty.'
			if offer_amt < 0 or request_amt < 0:
				raise Exception, 'topup amounts cannot be negative.'
			if offer_amt > 0 and request_amt > 0:
				raise Exception, 'topup amounts cannot be positive at the same time.'
			if len(own_urls) == 0 and len(seek_urls) == 0:
				raise Exception, 'trade cannot be empty.'
			if (len(own_urls) > 0 or offer_amt > 0) and len(seek_urls) == 0 and request_amt == 0:
				raise Exception, 'offer cannot be empty.'
			if (len(seek_urls) > 0 or request_amt > 0) and len(own_urls) == 0 and offer_amt == 0:
				raise Exception, 'request cannot be empty.'

			trade = models.Trade(parent = user.key)
			
			for game_url in own_urls:
				game_key = ndb.Key(urlsafe = game_url)
				if game_key.kind() != 'InventoryGame':
					raise Exception, 'invalid key.'
				if game_key.parent() != user.key:
					raise Exception, 'access denied.'

				game = game_key.get()
				if game is None:
					raise Exception, 'no such game in inventory.'

				trade.own_keys.append(game_key)
				trade.own_games.append(game.title + game.platform)

			for game_url in seek_urls:
				game_key = ndb.Key(urlsafe = game_url)
				if game_key.kind() != 'PlaylistGame':
					raise Exception, 'invalid key.'
				if game_key.parent() != user.key:
					raise Exception, 'access denied.'

				game = game_key.get()
				if game is None:
					raise Exception, 'no such game in playlist.'

				trade.seek_keys.append(game_key)
				trade.seek_games.append(game.title + game.platform)

			if offer_amt > 0:
				trade.topup = offer_amt
			else:
				trade.topup = -request_amt
			
			trade.description = description
			trade.subscriber_keys.append(user.key)
			trade.put()

			for game_key in trade.own_keys:
				game = game_key.get()
				game.trade_keys.append(trade.key)
				game.put()

			for game_key in trade.seek_keys:
				game = game_key.get()
				game.trade_keys.append(trade.key)
				game.put()

			self.response.write('trade added.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class TradesDelete(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/trades')

	def post_user(self, user, **kwargs):
		try:
			trade_key = ndb.Key(urlsafe = self.request.get('trade_url'))
			if trade_key.kind() != 'Trade':
				raise Exception, 'invalid key.'
			if trade_key.parent() != user.key:
				raise Exception, 'access denied.'

			trade = trade_key.get()
			if trade is None:
				raise Exception, 'no such trade.'
			trade_key.delete()

			for game_key in trade.own_keys:
				game = game_key.get()
				game.trade_keys.remove(trade_key)
				game.put()

			for game_key in trade.seek_keys:
				game = game_key.get()
				game.trade_keys.remove(trade_key)
				game.put()

			for comment_key in trade.comment_keys:
				comment_key.delete()
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class TradesRecent(BaseHandler):
	def get_user(self, user, **kwargs):
		try:
			page = kwargs.get('page', 1)

			qry = models.Trade.query().order(-models.Trade.date)
			pager = ndbpager.Pager(query = qry, page = page)
			trades, cursor, more = pager.paginate(page_size = constants.PAGE_SIZE)

			my_locations = models.Location.query(ancestor = user.key)

			trades = [(trade,
				ndb.get_multi(trade.own_keys),
				ndb.get_multi(trade.seek_keys),
				trade.key.parent().get(),
				utils.min_dist(my_locations, models.Location.query(ancestor = trade.key.parent()))
				) for trade in trades]

			template_values = {
				'user': user,
				'logout': users.create_logout_url(self.request.uri),
				'trades': trades,
				'pager': pager,
			}
			template = JINJA_ENVIRONMENT.get_template('user/trades_recent.html')
			self.response.write(template.render(template_values))
		except:
			self.redirect('/dashboard')

	def get_public(self, **kwargs):
		try:
			page = kwargs.get('page', 1)

			qry = models.Trade.query().order(-models.Trade.date)
			pager = ndbpager.Pager(query = qry, page = page)
			trades, cursor, more = pager.paginate(page_size = constants.PAGE_SIZE)

			trades = [(trade,
				ndb.get_multi(trade.own_keys),
				ndb.get_multi(trade.seek_keys),
				trade.key.parent().get(),
				) for trade in trades]

			template_values = {
				'login': users.create_login_url(self.request.uri),
				'trades': trades,
				'pager': pager,
			}
			template = JINJA_ENVIRONMENT.get_template('public/trades_recent.html')
			self.response.write(template.render(template_values))
		except:
			self.redirect('/')

class TradesSearch(BaseHandler):
	def get_user(self, user, **kwargs):
		inventory = models.InventoryGame.query(ancestor = user.key)
		playlist = models.PlaylistGame.query(ancestor = user.key)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.uri),
			'inventory': inventory,
			'playlist': playlist,
			'own_url': self.request.get('own'),
			'seek_url': self.request.get('seek'),
		}
		template = JINJA_ENVIRONMENT.get_template('user/trades_search.html')
		self.response.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		jdata = json.loads(self.request.body)
		own_urls = jdata['own_urls']
		seek_urls = jdata['seek_urls']

		if len(own_urls) == 0 and len(seek_urls) == 0:
			raise Exception, 'trade cannot be empty.'

		trades = models.Trade.query()
		for game_url in own_urls:
			game_key = ndb.Key(urlsafe = game_url)
			if game_key.kind() != 'InventoryGame':
				raise Exception, 'invalid key.'
			if game_key.parent() != user.key:
				raise Exception, 'access denied.'

			game = game_key.get()
			if game is None:
				raise Exception, 'no such game in inventory.'

			trades = trades.filter(models.Trade.seek_games == game.title + game.platform)

		for game_url in seek_urls:
			game_key = ndb.Key(urlsafe = game_url)
			if game_key.kind() != 'PlaylistGame':
				raise Exception, 'invalid key.'
			if game_key.parent() != user.key:
				raise Exception, 'access denied.'

			game = game_key.get()
			if game is None:
				raise Exception, 'no such game in playlist.'

			trades = trades.filter(models.Trade.own_games == game.title + game.platform)

		trades.order(-models.Trade.date)
		trades = trades.map(utils.trade_all)

		template_values = {
			'trades': trades,
		}
		template = JINJA_ENVIRONMENT.get_template('user/trades_search_results.html')
		self.response.write(template.render(template_values))

class TradesSearchMap(BaseHandler):
	def get_user(self, user, **kwargs):
		locations = models.Location.query(ancestor = user.key)

		template_values = {
			'user': user,
			'locations': json.dumps([ndb.Model.to_dict(location, include = ['name', 'location']) for location in locations], cls = utils.NdbEncoder)
		}
		template = JINJA_ENVIRONMENT.get_template('user/trades_search_view.html')
		self.response.write(template.render(template_values))

class Trade(BaseHandler):
	def get_user(self, user, **kwargs):

		trade_url = kwargs['trade_url']

		trade_key = ndb.Key(urlsafe = trade_url)
		if trade_key.kind() != 'Trade':
			raise Exception, 'invalid key.'

		trade = trade_key.get()
		if trade is None:
			raise Exception, 'no such trade.'

		if trade.key.parent() == user.key:
			person = user
			distance = 0
		else:
			person = trade.key.parent().get()

			my_locations = models.Location.query(ancestor = user.key)
			your_locations = models.Location.query(ancestor = person.key)
			distance = utils.min_dist(my_locations, your_locations)

		own_games = ndb.get_multi(trade.own_keys)
		seek_games = ndb.get_multi(trade.seek_keys)
		comments = ndb.get_multi(trade.comment_keys)

		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.uri),
			'trade': trade,
			'own_games': own_games,
			'seek_games': seek_games,
			'person': person,
			'comments': comments,
			'distance': distance,
		}
		template = JINJA_ENVIRONMENT.get_template('user/trade.html')
		self.response.write(template.render(template_values))


	def get_public(self, **kwargs):
		try:
			trade_url = kwargs['trade_url']

			trade_key = ndb.Key(urlsafe = trade_url)
			if trade_key.kind() != 'Trade':
				raise Exception, 'invalid key.'

			trade = trade_key.get()
			if trade is None:
				raise Exception, 'no such trade.'

			own_games = ndb.get_multi(trade.own_keys)
			seek_games = ndb.get_multi(trade.seek_keys)
			person = trade.key.parent().get()
			comments = ndb.get_multi(trade.comment_keys)

			template_values = {
				'login': users.create_login_url(self.request.uri),
				'trade': trade,
				'own_games': own_games,
				'seek_games': seek_games,
				'person': person,
				'comments': comments,
			}
			template = JINJA_ENVIRONMENT.get_template('public/trade.html')
			self.response.write(template.render(template_values))
		except:
			self.redirect('/')

class TradeComment(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/trades')

	def get_public(self, **kwargs):
		self.redirect('/')

	def post_user(self, user, **kwargs):
		try:
			trade_key = ndb.Key(urlsafe = self.request.get('trade_url'))
			if trade_key.kind() != 'Trade':
				raise Exception, 'invalid key.'

			trade = trade_key.get()
			if trade is None:
				raise Exception, 'no such trade.'

			comment = models.Comment(parent = user.key)
			comment.content = validate.comment(self.request.get('comment'))
			comment.put()

			trade.comment_keys.append(comment.key)

			for subscriber_key in trade.subscriber_keys:
				if subscriber_key != user.key:
					subscriber = subscriber_key.get()
					mail.send_mail(
						sender = "Admin at maph4ck <%s>" %constants.ADMIN_MAIL,
						to = "%s <%s>" % (subscriber.name, subscriber.email),
						subject = "New comment on maph4ck",
						body = """Hello, %s! %s has posted a new comment at %s/trade/%s:\n\n%s""" % (subscriber.name, user.name, self.request.host_url, trade_key.urlsafe(), comment.content),
					)

			if user.key not in trade.subscriber_keys:
				trade.subscriber_keys.append(user.key)

			trade.put()

			template_values = {
				'user': user,
				'comment': comment,
			}
			template = JINJA_ENVIRONMENT.get_template('user/comment.html')
			self.response.write(template.render(template_values))
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class TradeSubscribe(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/trades')

	def get_public(self, **kwargs):
		self.redirect('/')

	def post_user(self, user, **kwargs):
		try:
			trade_key = ndb.Key(urlsafe = self.request.get('trade_url'))
			if trade_key.kind() != 'Trade':
				raise Exception, 'invalid key.'

			trade = trade_key.get()
			if trade is None:
				raise Exception, 'no such trade.'
			if user.key in trade.subscriber_keys:
				raise Exception, 'you are already subscribed to this trade.'

			trade.subscriber_keys.append(user.key)
			trade.put()

			self.response.write('subscribed to this trade.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class TradeUnsubscribe(BaseHandler):
	def get_user(self, user, **kwargs):
		self.redirect('/trades')

	def get_public(self, **kwargs):
		self.redirect('/')

	def post_user(self, user, **kwargs):
		try:
			trade_key = ndb.Key(urlsafe = self.request.get('trade_url'))
			if trade_key.kind() != 'Trade':
				raise Exception, 'invalid key.'

			trade = trade_key.get()
			if trade is None:
				raise Exception, 'no such trade.'
			if user.key not in trade.subscriber_keys:
				raise Exception, 'you are not subscribed to this trade.'

			trade.subscriber_keys.remove(user.key)
			trade.put()

			self.response.write('unsubscribed from this trade.')
		except Exception, e:
			self.error(403)
			self.response.write([str(e)])

class User(BaseHandler):
	def get_user(self, user, **kwargs):
		try:
			person_url = kwargs['person_url']

			person_key = ndb.Key(urlsafe = person_url)
			if person_key.kind() != 'Person':
				raise Exception, 'invalid key.'

			person = person_key.get()
			if person is None:
				raise Exception, 'no such person.'

			if person_key == user.key:
				self.redirect('/profile')
			else:
				my_locations = models.Location.query(ancestor = user.key)
				your_locations = models.Location.query(ancestor = person_key)
				distance = utils.min_dist(my_locations, your_locations)

				my_inventory = models.InventoryGame.query(ancestor = user.key)
				my_playlist = models.PlaylistGame.query(ancestor = user.key)
				your_inventory = models.InventoryGame.query(ancestor = person_key)
				your_playlist = models.PlaylistGame.query(ancestor = person_key)

				trades = models.Trade.query(ancestor = person_key)
				trades = trades.map(utils.trade_with_games)

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

				template_values = {
					'user': user,
					'logout': users.create_logout_url(self.request.host_url),
					'person': person,
					'distance': distance,
					'my_diff': my_diff,
					'my_match': my_match,
					'your_match': your_match,
					'your_diff': your_diff,
					'trades': trades,
					}
				template = JINJA_ENVIRONMENT.get_template('user/user.html')
				self.response.write(template.render(template_values))
		except:
			self.redirect('/dashboard')				

	def get_public(self, **kwargs):

		person_url = kwargs['person_url']

		person_key = ndb.Key(urlsafe = person_url)
		if person_key.kind() != 'Person':
			raise Exception, 'invalid key.'

		person = person_key.get()
		if person is None:
			raise Exception, 'no such person.'

		inventory = models.InventoryGame.query(ancestor = person_key)
		playlist = models.PlaylistGame.query(ancestor = person_key)
		trades = models.Trade.query(ancestor = person_key)
		trades = trades.map(utils.trade_with_games)

		template_values = {
			'login': users.create_login_url(self.request.uri),
			'person': person,
			'inventory': inventory,
			'playlist': playlist,
			'trades': trades,
		}
		template = JINJA_ENVIRONMENT.get_template('public/user.html')
		self.response.write(template.render(template_values))

class UserLocations(BaseHandler):
	def get_user(self, user, **kwargs):
		try:
			person_url = kwargs['person_url']

			person_key = ndb.Key(urlsafe = person_url)
			if person_key.kind() != 'Person':
				raise Exception, 'invalid key.'

			person = person_key.get()
			if person is None:
				raise Exception, 'no such person.'

			my_locations = models.Location.query(ancestor = user.key)
			your_locations = models.Location.query(ancestor = person_key)

			template_values = {
				'user': user,
				'person': person,
				'my_locations': json.dumps([ndb.Model.to_dict(location, include = ['location']) for location in my_locations], cls = utils.NdbEncoder),
				'your_locations': json.dumps([ndb.Model.to_dict(location, include = ['location']) for location in your_locations], cls = utils.NdbEncoder),
			}
			template = JINJA_ENVIRONMENT.get_template('user/user_locations.html')
			self.response.write(template.render(template_values))
		except:
			self.redirect('/dashboard')

	def get_public(self, **kwargs):
		try:
			person_url = kwargs['person_url']

			person_key = ndb.Key(urlsafe = person_url)
			if person_key.kind() != 'Person':
				raise Exception, 'invalid key.'

			person = person_key.get()
			if person is None:
				raise Exception, 'no such person.'

			locations = models.Location.query(ancestor = person_key)

			template_values = {
				'person': person,
				'locations': json.dumps([ndb.Model.to_dict(location, include = ['location']) for location in my_locations], cls = utils.NdbEncoder),
			}
			template = JINJA_ENVIRONMENT.get_template('public/user_locations.html')
			self.response.write(template.render(template_values))
		except:
			self.redirect('/')

class ConversationsPage(BaseHandler):
	def get_user(self, user):
		conversations = models.Conversation.query(models.Conversation.person_keys == user.key).order(-models.Conversation.date)
		conversations = conversations.map(utils.conversation_with_messages)
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
			'conversations': conversations,
		}
		template = JINJA_ENVIRONMENT.get_template('user/conversations.html')
		self.response.out.write(template.render(template_values))

	def post_user(self, user):
		try:
			jdata = json.loads(self.request.body)
			names = jdata['names']
			content = jdata['message']

			qry = models.Conversation.query(models.Conversation.person_keys == user.key)

			person_keys = []
			for name in names:
				person = models.Person.query(models.Person.name == name).get()
				if not person:
					raise Exception, 'the person %s does not exist.' %name
				person_key = person.key
				if person_key.kind() != 'Person':
					raise Exception, 'invalid key.'
				if person_key == user.key:
					raise Exception, 'you cannot message yourself.'
				person_keys.append(person_key)

				qry = qry.filter(models.Conversation.person_keys == person_key)

			qry = qry.filter(models.Conversation.num_pple == len(person_keys) + 1)

			conversation = qry.get()
			if conversation is None:
				conversation = models.Conversation()
				conversation.num_pple = len(person_keys) + 1
				conversation.person_keys.append(user.key)
				conversation.subscriber_keys.append(user.key)
				for person_key in person_keys:
					conversation.person_keys.append(person_key)
					conversation.subscriber_keys.append(person_key)

				conversation.num_unread = [0] * (len(person_keys) + 1)

			message = models.Message()
			message.content = content
			message.owner = user.name
			if not message.content:
				raise Exception, 'message cannot be empty.'
			if len(content) > constants.MAX_STR_LEN:
				raise Exception, 'message exceeds %d characters.' % constants.MAX_STR_LEN
			conversation.messages.append(message)

			for counter, person_key in enumerate(person_keys):
				if person_key == user.key:
					conversation.num_unread[counter] = 0
				else:
					conversation.num_unread[counter] += 1
			message.put()
			conversation.date = message.date
			conversation.put()

			for key in conversation.subscriber_keys:
				subscriber = key.get()
				if subscriber is not user:
					mail.send_mail(sender="Messages at maph4ck <%s>" %constants.ADMIN_MAIL,
									to="%s <%s>" %(subscriber.name, subscriber.email),
									subject="New private message from %s" %user.name,
									body="""%s has sent you a private message:\n\n%s
									""" % (user.name, message.content) )

			self.response.out.write('message sent.')
		except Exception, e:
			self.error(403)
			self.response.out.write([str(e)])

class ConversationSubscribe(BaseHandler):
	def get_user(self, user):
		self.redirect('/conversations')

	def post_user(self, user):
		try:
			conversation_key = ndb.Key(urlsafe = self.request.get('conversation_url'))
			conversation = conversation_key.get()
			if conversation_key.kind() != 'Conversation':
				raise Exception, 'invalid key.'
			if conversation is None:
				raise Exception, 'no such conversation.'
			if user.key not in conversation.subscriber_keys:
				conversation.subscriber_keys.append(user.key)
			else:
				raise Exception, 'you are already subscribed to this conversation.'
			conversation.put()
		except Exception, e:
			self.error(403)
			self.response.out.write([str(e)])

class ConversationUnsubscribe(BaseHandler):
	def get_user(self, user):
		self.redirect('/conversations')

	def post_user(self, user):
		try:
			conversation_key = ndb.Key(urlsafe = self.request.get('conversation_url'))
			conversation = conversation_key.get()
			if conversation_key.kind() != 'Conversation':
				raise Exception, 'invalid key.'
			if conversation is None:
				raise Exception, 'no such conversation.'
			if user.key in conversation.subscriber_keys:
				conversation.subscriber_keys.remove(user.key)
			else:
				raise Exception, 'you are not subscribed to this conversation.'
			conversation.put()
		except Exception, e:
			self.error(403)
			self.response.out.write([str(e)])

class Feedback(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.uri),
		}
		template = JINJA_ENVIRONMENT.get_template('user/feedback.html')
		self.response.out.write(template.render(template_values))
	
	def get_public(self, **kwargs):
		template_values = {
			'login': users.create_logout_url(self.request.uri),
		}
		template = JINJA_ENVIRONMENT.get_template('public/feedback.html')
		self.response.out.write(template.render(template_values))

	def post_user(self, user, **kwargs):
		try:
			feedback = models.Feedback(parent = user.key)
			feedback.content = validate.feedback(self.request.get('feedback'))
			feedback.put()

			mail.send_mail(
				sender = "Admin at maph4ck <%s>" % constants.ADMIN_MAIL,
				to = "maph4ck admin <%s>" % constants.ADMIN_MAIL,
				subject = "Feedback from %s (%s)" % (user.name, user.email),
				body = """%s""" % feedback.content,
			)

			self.response.write('feedback sent.')
		except:
			self.error(403)
			self.response.write([str(e)])

	def post_public(self, **kwargs):
		try:
			feedback = models.Feedback()
			feedback.content = validate.feedback(self.request.get('feedback'))
			feedback.put()

			mail.send_mail(
				sender = "Admin at maph4ck <%s>" % constants.ADMIN_MAIL,
				to = "maph4ck admin <%s>" % constants.ADMIN_MAIL,
				subject = "Feedback from public",
				body = """%s""" % feedback.content,
			)
		except:
			self.error(403)
			self.response.write([str(e)])

class FAQ(BaseHandler):
	def get_user(self, user, **kwargs):
		template_values = {
			'user': user,
			'logout': users.create_logout_url(self.request.host_url),
		}
		template = JINJA_ENVIRONMENT.get_template('user/faq.html')
		self.response.write(template.render(template_values))

	def get_public(self, **kwargs):
		template_values = {
			'login': users.create_login_url(self.request.uri),
		}
		template = JINJA_ENVIRONMENT.get_template('public/faq.html')
		self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/setup', Setup),
	('/dashboard', Dashboard),
	('/profile', Profile),
	('/profile/edit', ProfileEdit),
	('/friends', Friends),
	('/friends/add', FriendsAdd),
	('/friends/delete', FriendsDelete),
	('/locations', Locations),
	('/locations/add', LocationsAdd),
	('/locations/delete', LocationsDelete),
	('/locations/edit', LocationsEdit),
	webapp2.Route('/locations/view/<location_url>', LocationsView),
	('/inventory', Inventory),
	('/inventory/add', InventoryAdd),
	('/inventory/delete', InventoryDelete),
	('/playlist', Playlist),
	('/playlist/add', PlaylistAdd),
	('/playlist/delete', PlaylistDelete),
	('/trades', Trades),
	('/trades/add', TradesAdd),
	('/trades/delete', TradesDelete),
	('/trades/recent', TradesRecent),
	webapp2.Route('/trades/recent/<page>', TradesRecent),
	('/trades/search/map', TradesSearchMap),
	('/trades/search.*', TradesSearch),
	('/trade/comment', TradeComment),
	('/trade/subscribe', TradeSubscribe),
	('/trade/unsubscribe', TradeUnsubscribe),
	webapp2.Route('/trade/<trade_url>', Trade),
	webapp2.Route('/user/locations/<person_url>', UserLocations),
	webapp2.Route('/user/<person_url>', User),
	('/conversations', ConversationsPage),
	('/conversation/subscribe', ConversationSubscribe),
	('/conversation/unsubscribe', ConversationUnsubscribe),
	('/feedback', Feedback),
	('/faq', FAQ),
], debug=True)