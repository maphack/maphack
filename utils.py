# Local modules
import models

# Other modules
import datetime
import json
from google.appengine.api import users
from google.appengine.ext import ndb
from math import radians, cos, sin, asin, sqrt

# JSON encoder
class NdbEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return {'year': obj.year,
				'month': obj.month,
				'day': obj.day,
				'hour': obj.hour,
				'minute': obj.minute,
				'second': obj.second,}

		if isinstance(obj, ndb.GeoPt):
			return {'lat': obj.lat, 'lon': obj.lon}

		if isinstance(obj, ndb.Key):
			return obj.urlsafe()

		return json.JSONEncoder.default(self, obj)

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
	distance = float('inf')
	for loc1 in locs1:
		for loc2 in locs2:
			dist = haversine(loc1.location.lat, loc1.location.lon, loc2.location.lat, loc2.location.lon)
			if dist < distance:
				distance = dist
	return distance

def trade_with_games(trade):
	return trade, ndb.get_multi(trade.own_keys), ndb.get_multi(trade.seek_keys)

def trade_all(trade):
	my_locations = models.Location.query(ancestor = ndb.Key('Person', users.get_current_user().user_id()))
	your_locations = models.Location.query(ancestor = trade.key.parent())

	return trade, ndb.get_multi(trade.own_keys), ndb.get_multi(trade.seek_keys), trade.key.parent().get(), your_locations, min_dist(my_locations, your_locations)

def conversation_with_messages(conversation):
	return conversation, conversation.messages, ndb.get_multi(conversation.person_keys)