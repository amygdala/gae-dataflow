# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The app for the 'frontend' service, which handles cron job requests to
fetch tweets and store them in the Datastore.
"""

import logging
import os

from google.appengine.ext import ndb
import tweepy
import webapp2


class Tweet(ndb.Model):
  """Define the Tweet model."""
  user = ndb.StringProperty()
  text = ndb.StringProperty()
  created_at = ndb.DateTimeProperty()
  tid = ndb.IntegerProperty()
  urls = ndb.StringProperty(repeated=True)


class FetchTweets(webapp2.RequestHandler):
  """..."""

  def get(self):

    # set up the twitter client. These env vars are set in app.yaml.
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    last_id = None
    public_tweets = None

    # see if we can get the id of the most recent tweet stored.
    tweet_entities = ndb.gql('select * from Tweet order by tid desc limit 1')
    last_id = None
    for te in tweet_entities:
      last_id = te.tid
      break
    if last_id:
      logging.info("last id is: %s", last_id)

    public_tweets = []
    # grab tweets from the home timeline of the auth'd account.
    try:
      if last_id:
        public_tweets = api.home_timeline(count=200, since_id=last_id)
      else:
        public_tweets = api.home_timeline(count=20)
        logging.warning("Could not get last tweet id from datastore.")
    except Exception as e:
      logging.warning("Error getting tweets: %s", e)

    # store the retrieved tweets in the datastore
    logging.info("got %s tweets", len(public_tweets))
    for tweet in public_tweets:
      tw = Tweet()
      # logging.info("text: %s, %s", tweet.text, tweet.user.screen_name)
      tw.text = tweet.text
      tw.user = tweet.user.screen_name
      tw.created_at = tweet.created_at
      tw.tid = tweet.id
      urls = tweet.entities['urls']
      urllist = []
      for u in urls:
        expanded_url = u['expanded_url']
        urllist.append(expanded_url)
      tw.urls = urllist
      tw.key = ndb.Key(Tweet, tweet.id)
      tw.put()

    self.response.write('Done')


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.write('nothing to see.')


app = webapp2.WSGIApplication(
    [('/', MainPage), ('/timeline', FetchTweets)], debug=True)
