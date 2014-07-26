# Local modules
import constants
import models

# Other modules
from urlparse import urlparse

# Ensures string length is between 1 and MAX_STR_LEN characters
def validate_string(string, variable):
	string = string.strip()
	if not string:
		raise Exception, variable + ' cannot be empty.'
	if len(string) > constants.MAX_STR_LEN:
		raise Exception, variable + ' exceeds %s characters.' % constants.MAX_STR_LEN

	return string

# User attributes validation
def bio(bio):
	bio = bio.strip()
	if len(bio) > constants.MAX_STR_LEN:
		raise Exception, 'bio exceeds %s characters.' % constants.MAX_STR_LEN

	return bio

def contact(contact):
	return validate_string(contact, 'contact information')

def country(country):
	if country not in constants.COUNTRY_CODES:
		raise Exception, 'invalid country.'

	return country

def user_pic(user_pic):
	user_pic = user_pic.strip()
	if user_pic:
		if urlparse(user_pic).scheme != 'http' and urlparse(user_pic).scheme != 'https':
			raise Exception, 'image link must be http or https.'
		if len(user_pic) > constants.MAX_STR_LEN:
			raise Exception, 'image link exceeds %s characters.' % constants.MAX_STR_LEN
	else:
		user_pic = constants.DISPLAY_PIC

	return user_pic

def user_name(user_name):
	user_name = user_name.strip()
	if not user_name:
		raise Exception, 'display name cannot be empty.'
	if len(user_name) > constants.MAX_NAME_LEN:
		raise Exception, 'display name exceeds %s characters.' % constants.MAX_NAME_LEN
	qry = models.Person.query(models.Person.name == user_name)
	if qry.count():
		raise Exception, 'display name is already taken.'

	return user_name

# Location attributes validation
def address(address):
	return validate_string(address, 'address')

def location_name(location_name):
	return validate_string(location_name, 'location name')

# Game attributes validation
def title(title):
	return validate_string(title, 'game title')

def platform(platform):
	return validate_string(platform, 'game platform')

def game_pic(game_pic):
	game_pic = game_pic.strip()
	if game_pic:
		if urlparse(game_pic).scheme != 'http' and urlparse(game_pic).scheme != 'https':
			raise Exception, 'image link must be http or https.'
		if len(game_pic) > constants.MAX_STR_LEN:
			raise Exception, 'image link exceeds %s characters.' % constants.MAX_STR_LEN

	return game_pic

def game_description(game_description):
	game_description = game_description.strip()
	if len(game_description) > constants.MAX_STR_LEN:
		raise Exception, 'game description exceeds %s characters.' % constants.MAX_STR_LEN

	return game_description

def wrapped(wrapped):
	if wrapped == 'true':
		return True
	elif wrapped == 'false':
		return False
	else:
		raise Exception, 'game \'wrapped\' condition ' + wrapped + ' must be a boolean.'

# Trade attributes validation
def trade_description(trade_description):
	trade_description = trade_description.strip()
	if len(trade_description) > constants.MAX_STR_LEN:
		raise Exception, 'trade description exceeds %s characters.' % constants.MAX_STR_LEN

	return trade_description

# Comment validation
def comment(comment):
	return validate_string(comment, 'comment')

# Feedback validation
def feedback(feedback):
	return validate_string(feedback, 'feedback')