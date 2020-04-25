import tweepy
import json
import os.path
import pathlib
from os import path
from datetime import datetime
from telethon import TelegramClient
from credentials import *
from matplotlib import pyplot as plt
#TO-DO
# - make another version that takes data from http://www.protezionecivile.gov.it/media-comunicazione/comunicati-stampa
# - fix if json file is empty
# - improve chart
# - improve Telegram message
# - add other charts


#Returns data from the json file as a list of dictionaries
def jsonPrepare(x, y):
    temp = []
    with open(str(pathlib.Path(__file__).parent.absolute()) + "\Data\data.txt") as json_file:
        data = json.load(json_file)
        for d in data:
            temp.append({
                'date' : d['date'],
                'infecteds' : d['infecteds'],
                'deaths' : d['deaths'],
                'treateds' : d['treateds']
            })
            tempDate = datetime.strptime(d['date'], '%Y-%m-%d')
            x.append(tempDate)
            y.append(d['infecteds'] + d['deaths'] + d['treateds'])
        return temp

#Prepares the output list by inserting daily data into it
def jsonWrite(counter, infected, death, treated, date, output):
    output.insert(counter, {
        'date' : date,
        'infecteds' : infected,
        'deaths' : death,
        'treateds' : treated
    })

    
#Gets the next useful value from the tweet
def getValue(tweetText):
    result = int(tweetText.find("("))
    if(result >= 0):
        number = ""
        if(tweetText[result + 1] == "-"):
            number = "-"

        i = result + 2
        while(tweetText[i].isnumeric() or (tweetText[i] == "." or tweetText[i] == " ")):
            if(tweetText[i] != "." and tweetText[i] != " "):
                number += tweetText[i]
            i += 1
        return number
    else:
        return 0

#Sends the chart and the message to the CovidTestChannel
async def sendChart(client, message):
    await client.send_message('CovidTestChannel', message, file = str(pathlib.Path(__file__).parent.absolute()) + "\Data\chart.png")
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def main(api):
    client = TelegramClient('anon', telegramID, telegramHash)
    x = []
    y = []

    output = jsonPrepare(x, y)
    #Using cursor to bypass the limit of 200 tweets
    covidTweets = tweepy.Cursor(api.user_timeline, screen_name = "you_trend", count = 200, tweet_mode='extended').items()
    #Get the date of the last checked tweet (else set the date to 2019/01/01)
    if(len(output) > 0):
        datetime_str = output[0]['date']
    else:
        datetime_str = "2019-01-01"
    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    message = ""
    counter = 0
    #Check every tweet
    for tweet in covidTweets:
        #If the current tweet has been checked before, exit
        if(tweet.created_at.date() <= datetime_object.date()):
            break
        #Check if the tweet contains useful data
        if("Coronavirus" in tweet.full_text and "aggiornamento" in tweet.full_text and "Guariti:" in tweet.full_text):
            checkTotal = False

            text = str(tweet.full_text)
            if(int(text.find("(")) < int(text.find("Deceduti"))):
                infecteds = int(getValue(text))
            else:
                #If there is no "Nuovi casi" set this to True, so they will be calculated later
                checkTotal = True

            #Find and store the deaths value
            i = text.find("Deceduti")
            if(i < 0):
                i = text.find("Morti:")
            text = text[i:]
            deaths = int(getValue(text))

            #Find and store the trateds value
            i = text.find("Guariti")
            text = text[i:]
            treateds = int(getValue(text))

            #Calculate the infecteds of this day
            if(checkTotal):
                i = text.find("Totale casi:")
                if(i < 0):
                    i = text.find("TOTALE CASI:")
                text = text[i:]
                infecteds = (int(getValue(text)) - deaths - treateds)
            
            #If this is the last tweet, prepare the message
            if(counter == 0):
                message = "**- Nuovi casi:** " + str(infecteds)
                message += "\n**- Nuove morti:** " + str(deaths)
                message += "\n**- Nuovi guariti:** " + str(treateds)
                message += "\n\n**• Variazione casi totali:** +" + str(infecteds + deaths + treateds)
            #Prepare the "output" list to be writed into the json
            jsonWrite(counter, infecteds, deaths, treateds, str(tweet.created_at.date()), output)
            print(str(tweet.created_at))
            #Insert the values into the plot
            x.insert(counter, tweet.created_at)
            y.insert(counter, infecteds + deaths + treateds)
            counter += 1
    #If a new tweet has been found, prepare the plot and send everything to the Telegram channel
    if counter > 0:
        with open(str(pathlib.Path(__file__).parent.absolute()) + "\Data\data.txt", 'w') as outfile:
            json.dump(output, outfile)
        plt.figure(figsize=(8, 6))
        plt.plot(x, y)
        plt.xlabel("Data")
        plt.ylabel("Incremento contagi")
        plt.xticks(rotation=30)
        plt.savefig(str(pathlib.Path(__file__).parent.absolute()) + "\Data\chart.png")
        #plt.show()
        with client:
            client.loop.run_until_complete(sendChart(client, message))
