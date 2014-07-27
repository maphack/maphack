# Local modules
import constants

# Other modules
from google.appengine.ext import ndb

class Person(ndb.Model):
	email = ndb.StringProperty()
	name = ndb.StringProperty()
	pic = ndb.StringProperty(default = constants.DISPLAY_PIC)
	country = ndb.StringProperty()
	contact = ndb.StringProperty()
	bio = ndb.StringProperty()
	friend_keys = ndb.KeyProperty(repeated = True)
	inventory_count = ndb.IntegerProperty(default = 0)
	playlist_count = ndb.IntegerProperty(default = 0)
	setup = ndb.BooleanProperty(default = False)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Location(ndb.Model):
	name = ndb.StringProperty()
	address = ndb.StringProperty()
	location = ndb.GeoPtProperty()
	date = ndb.DateTimeProperty(auto_now_add = True)

class InventoryGame(ndb.Model):
	title = ndb.StringProperty()
	platform = ndb.StringProperty()
	pic = ndb.StringProperty()
	description = ndb.StringProperty()
	wrapped = ndb.BooleanProperty(default = False)
	trade_keys = ndb.KeyProperty(repeated = True)
	date = ndb.DateTimeProperty(auto_now_add = True)

class PlaylistGame(ndb.Model):
	title = ndb.StringProperty()
	platform = ndb.StringProperty()
	pic = ndb.StringProperty()
	description = ndb.StringProperty()
	wrapped = ndb.BooleanProperty(default = False)
	trade_keys = ndb.KeyProperty(repeated = True)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Trade(ndb.Model):
	own_keys = ndb.KeyProperty(repeated = True)
	seek_keys = ndb.KeyProperty(repeated = True)
	own_games = ndb.StringProperty(repeated = True)
	seek_games = ndb.StringProperty(repeated = True)
	own_titles = ndb.StringProperty(repeated = True)
	seek_titles = ndb.StringProperty(repeated = True)
	topup = ndb.IntegerProperty(default = 0)
	description = ndb.StringProperty()
	comment_keys = ndb.KeyProperty(repeated = True)
	subscriber_keys = ndb.KeyProperty(repeated = True)
	date = ndb.DateTimeProperty(auto_now_add = True)

class Comment(ndb.Model):
	content = ndb.StringProperty()
	date = ndb.DateTimeProperty(auto_now_add = True)

class Message(ndb.Model):
	owner = ndb.StringProperty()
	content = ndb.StringProperty()
	date = ndb.DateTimeProperty(auto_now_add = True)

class Conversation(ndb.Model):
	num_pple = ndb.IntegerProperty()
	person_keys = ndb.KeyProperty(repeated = True)
	subscriber_keys = ndb.KeyProperty(repeated = True)
	messages = ndb.StructuredProperty(Message, repeated = True)
	num_unread = ndb.IntegerProperty(repeated = True)
	date = ndb.DateTimeProperty()

class Feedback(ndb.Model):
	content = ndb.StringProperty()
	date = ndb.DateTimeProperty(auto_now_add = True)