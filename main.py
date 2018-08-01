### THIS IS SPECIFICALlY FOR FARMERS IN NEBRASKA
import os
from flask import redirect, Flask, request
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from arable.client import ArableClient
import datetime
from datetime import date, datetime, timedelta
from io import StringIO
import pandas as pd
import numpy as np
import math
import requests
import json
import urllib
from dateutil.parser import parse
#make sure to add any new packages to pipfile and pipenv lock

#these are needed to access data in Arable Client
email = os.environ['email']
password = os.environ['password']
tenant = os.environ['tenant']

#Get Table returns a Pandas Dataframe from a query on Arable Client
def getTable(measure, device, days, limit):
    a = ArableClient()
    a.connect(email,password,tenant)

    end = datetime.now()
    sta = end - timedelta(days=days)
    end = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    sta = sta.strftime("%Y-%m-%dT%H:%M:%SZ")

    c = a.query(select='all',
                  format='csv',
                  devices=[device],
                  measure= str(measure),
                  end=end, start=sta,
                  limit=limit)

    c = StringIO(c)
    c = pd.read_csv(c, sep=',', error_bad_lines=False)
    return c
#Get location ID retrieves the unique location ID for a given device
def getLocationId(device):
    a = ArableClient()
    a.connect(email,password,tenant)
    location_id = a.devices(name=device)['location']['id']
    return location_id

#Device String maker
def device_string_maker(device):
    #Using Arable Client
    client = ArableClient()
    client.connect(email,password,tenant)
    d = client.devices(name=device)
#This is the UTC time offset(in seconds) specifically for Nebraska.
#To access local time offsets for different devices, use the location_id under device
    offset = -18000

    #getting last post time
    sync = str(d['last_post'])
    #'Parse' parses a datetime string into a datetime object so that we can use datetime function on that object
    sync_dt = parse(sync)
    #Timedelta is a way of shifting a datetime object based on a time offset.
    sync_offset = sync_dt + timedelta(seconds = offset)

    #Strftime is short for string format time
    #It basically reformats datetime object
    #More info on formatting datetime objects here: https://stackoverflow.com/questions/311627/how-to-print-date-in-a-regular-format-in-python
    sync_final = sync_offset.strftime("%A, %B %d %Y %H:%M")
    sync_final = str(sync_final)

    #same process for last deploy time
    deploy = str(d['last_deploy'])
    deploy_dt = parse(deploy)
    deploy_offset = deploy_dt + timedelta(seconds = offset)

    deploy_final = deploy_offset.strftime("%A, %B %d %Y %H:%M")
    #:%S
    deploy_final = str(deploy_final)

    device_string = str(d['name'])+": Times in local time.\nLast Deploy: "+deploy_final+"\nLast Sync: "+sync_final+"\n"
    signal_strength_string = "Signal Strength: "+str(d['signal_strength']+"\n")

    return device_string+signal_strength_string

#Returns a Google Map Link
def map_string_maker(device):
    c = getTable("raw",device,2,288)

    #Getting the Lat and Long to put into the Google Maps link to return
    column = c.loc[:,'lat']
    just_numbers = column.dropna()
    LAT = just_numbers.iloc[0]

    column = c.loc[:,'long']
    just_numbers = column.dropna()
    LONG = just_numbers.iloc[0]

    location_string = "Link to Mark location: https://maps.google.com/maps?q="+str(LAT)+","+str(LONG)+"&hl=en&z=14&amp;output=embed"
    return location_string

#Returns conditions data around device
def data_string_maker(device):
    c = getTable("calibrated",device,2,288)
    #Getting the Air temperature
    column = c.loc[:,'Tair']
    TEMP_C = column.iloc[0]
    TEMP_F = (TEMP_C * 1.8) + 32
    TEMP_C = int(TEMP_C)
    TEMP_F = int(TEMP_F)

    temp_string = "Temperature: "+str(TEMP_C) +" C or "+str(TEMP_F)+" F\n"

    #Relative Humidity
    column = c.loc[:,'RH']
    RH = column.iloc[0]
    RH = int(RH)
    rh_string = "Relative Humidity: "+str(RH)+"%\n"

    #Pressure
    column = c.loc[:,'P']
    P = column.iloc[0]
    P = int(P)
    p_string = "Pressure: "+str(P)+" mb\n"
    return temp_string+rh_string+p_string

#returns battery percentage of device
def health_string_maker(device):
    health = getTable("health",device,2,288)
    column = health.loc[:,'batt_pct']
    just_numbers = column.dropna()
    batt = just_numbers.iloc[0]
    batt_string = "Battery percentage: "+str(batt)+"%\n"

    return batt_string

#returns
def ET_string_maker(device):
    daily = getTable("daily",device,5,500)

    column = daily.loc[:,'ET']
    five_numbers = column[0:5]
    mean_just_numbers = five_numbers.dropna().mean()
    for i in five_numbers:
        if i == 0:
            i = mean_just_numbers
    pastET = round(five_numbers.sum()*0.039, 3)
    pastET = "ET past 5 days : "+str(pastET)+" in\n"

    #auth_token = a.header['Authorization']
    location_id = getLocationId(device)
    weather_api_url = os.environ['weather_api_url']
    url = weather_api_url+str(location_id)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    data = data[0]

    ET01 = data['ET01']
    ET02 = data['ET02']
    ET03 = data['ET03']
    ET04 = data['ET04']
    ET05 = data['ET05']
    future = ET01 + ET02 + ET03 + ET04 + ET05
    future = round((future * 0.039), 3)
    futureET = "ET next 5 days: "+ str(future)+" in\n"
    return pastET + futureET

#Returns precipitation data
def rain_string_maker(device):
    daily = getTable("daily",device,11,2888)

    column = daily.loc[:,'precip']
    just_numbers = column.dropna()
    precip = just_numbers.iloc[0]
    precip_string = "Precip last 24 hrs: "+str(round(precip * 0.039, 3))+" in\n"

    column = daily.loc[:,'precip']
    just_numbers = column.fillna(0)
    just_numbers = just_numbers.iloc[0:10]
    total_precip = 0
    for i in range(10):
        precip_day = just_numbers.iloc[i]
        total_precip = precip_day + total_precip

    precip_string_2 = "Precip last 10 days: "+str(round(total_precip * 0.039, 3))+" in\n"

    return precip_string+precip_string_2

#This function sends a message through a Slack webhook to our Slack channel so we can help with Customer Support
#Read this for more info on Slack webhooks:  https://api.slack.com/incoming-webhooks
def slackSend(message):
    webhook_url = os.environ['slack_webhook']
    s_data = "MESSAGE ==> "+str(message)

    slack_data = {'text': s_data}

    response = requests.post(
    webhook_url, data=json.dumps(slack_data),
    headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
        )
#this initiates a Flask app.
#Flask is a python package that makes it easy to host a server
#More info: http://flask.pocoo.org
app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def incoming_sms():
    DEBUG = False
#MessagingResponse is a Twilio Package function, that creates a response to a SMS
    resp = MessagingResponse()
    #Get the message the user sent our Twilio number
    message = request.values.get('Body', None).split()
    slackSend("INBOUND MESSAGE: "+request.values.get('Body', None))
    device = str(message[0])
    #Sanity checks
    #Check if Device is valid
    try:
        a = ArableClient()
        a.connect(email,password,tenant)
        d = a.devices(name=device)
        string = str(d['name'])
    except:
        errorString = "This is not a valid device\nMore help available from support@arable.com"
        resp.message(errorString)
        slackSend(str(device)+" INVALID DEVICE "+errorString)
        return str(resp)

    #Check if Device is active
    testWord = str(d['state']).lower()
    if testWord != 'active':
        errorString = "This device is listed as inactive \nMore help available from support@arable.com"
        slackSend(str(device)+" INACTIVE DEVICE "+errorString)
        resp.message(errorString)
        return str(resp)

    args = len(message)-1
    #First part of the message is the device name
    #Second part of the message is the keyword
    if args > 0:
        keyword = message[1]
        #This is to make it case-insensitive
        key = keyword.lower()
        #Below are all of the implementations for the keywords
        #some keywords like 'map' and 'batt' need us to send only one of the function outputs
        #but other keywords like 'all' need us to send many function outputs
        if key == 'map':
            try:
                #resp.message fills the MessagingResponse we made above with text.
                resp.message(map_string_maker(device))
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to make a Google Maps link for you \nMore help available from support@arable.com")
                #This is an example of sending an error through slack for Customer Support
                slackSend(str(device)+": ERROR --> "+keyword)
            return str(resp)
        elif key == 'data':
            try:
                resp.message(data_string_maker(device))
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to data for you \nMore help available from support@arable.com")
                slackSend(str(device)+": ERROR --> "+keyword)
            return str(resp)
        elif key == 'rain':
            try:
                resp.message(rain_string_maker(device))
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to return rain values for you\nMore help available from support@arable.com")
                slackSend(str(device)+" ERROR --> "+str(keyword))
            return str(resp)
        elif key == 'batt':
            try:
                resp.message(health_string_maker(device))
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to return this device's battery percentage\nMore help available from support@arable.com")
                slackSend(str(device)+" ERROR --> "+str(keyword))
            return str(resp)
        elif key == 'et':
            try:
                resp.message(ET_string_maker(device))
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to return ET values\nMore help available from support@arable.com")
                slackSend(str(device)+" ERROR --> "+str(keyword))
            return str(resp)
        elif key == 'help':
            try:
                resp.message("Commands are: tnc, all, batt, map, rain, et, data, and help\nMore help available from support@arable.com")
                slackSend("HELP")
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to return help\nMore help available from support@arable.com")
                slackSend("ERROR --> HELP")
            return str(resp)
        elif key == 'all':
            try:
                d = device_string_maker(device)
                h = health_string_maker(device)
                data = data_string_maker(device)
                rain = rain_string_maker(device)
                map = map_string_maker(device)
                ET = ET_string_maker(device)
                batt_pct = health_string_maker(device)
                string_concat = str(d)+str(h)+str(rain)+str(data)+str(map)+str(ET)+str(batt_pct)
                resp.message(string_concat)
                slackSend(str(device)+" "+str(keyword))
                if(DEBUG):
                    slackSend(str(resp))
            except:
                resp.message("There was an error when trying to return the requested data\nPlease contact support@arable.com")
                slackSend(str(device)+" ERROR --> "+str(keyword))
            return str(resp)
            #The else statement below sends an error message saying that the Keyword was not one of the ones listed
        else:
            resp.message("Commands are: tnc, all, batt, map, rain, et, data, and help\nMore help available from support@arable.com")
            slackSend(str(device)+": UNRECOGNIZED KEYWORD ERROR -->"+str(keyword))
            return str(resp)
    #this else statement is to have a default message given a device name
    else:
        try:
            resp.message(device_string_maker(device))
            slackSend(str(device))
            if(DEBUG):
                slackSend(str(resp))
        #If there is an error that we have not accounted for, send this message
        except:
            resp.message("There was an error when trying to return device data\nMore help available from support@arable.com")
            slackSend(str(device) + "DEVICE ERROR")
        return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
