import tweepy
from credentials import *
from elaborate import *

#NB: credentials have not been uploaded, they have to be added to get the script work

class MyStreamListener(tweepy.StreamListener):
    #Gets called when a new tweet has been found
    def on_status(self, status):
        text = ""
        #If the tweet can be extended, send the full text
        if hasattr(status, 'extended_tweet'):
            text = status.extended_tweet['full_text']
        else:
            text = status.text
        #If the tweet contains useful data, elaborate it
        if("Coronavirus" in text and "aggiornamento" in text and "Guariti:" in text):
            print("yep")
            main(api)
        else:
            print("nope")

auth = tweepy.OAuthHandler(consumerAPIKey, consumerAPISecretKey)
auth.set_access_token(accessToken, accessTokenSecret)
api = tweepy.API(auth)

#Define the listener
listener = MyStreamListener()
#Define the stream
stream = tweepy.Stream(auth = auth, listener = listener)
#Make the stream follow the YouTrend Twitter account
stream.filter(follow=["404064077"])

#Me
#stream.filter(follow=["444565727"])

