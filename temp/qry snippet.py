				results = []
				for listing in qry:
					results.append([ndb.Model.to_dict(listing, include = ['topup', 'date']), 
						[ndb.Model.to_dict(game_key.get(), exclude=['listing_keys', 'date']) for game_key in listing.own_keys], 
						[ndb.Model.to_dict(game_key.get(), exclude=['listing_keys', 'date']) for game_key in listing.seek_keys]])

				self.response.out.write(json.dumps(results, cls=NdbEncoder))