# SMS-BOT ![CI status](https://img.shields.io/badge/build-passing-brightgreen.svg)

I made an SMS-bot for Arable Labs - here is a tutorial. 
I will walk you through how I made this SMS bot, so you can do the same. 

## Requirements

* Heroku account
* Install and Activate Heroku CLI(Command Line Tools)
* Twilio Account
* Postgres installed
* Git installed and logged in
* New Directory for SMS-Bot
* Python 2.7

* python library for twilio
`$ pip install twilio`
* python library for web hosting
`$ pip install flask`
* python library for python requirements storage and virtual environment
`$ pip install pipenv`

## Constructing your SMS-Bot

### Part 1: Python File

![alt text](http://blog.klocwork.com/wp-content/uploads/fly-images/10699/python-logo-348x350-c.png "Python Logo")

Create a baseline 'main.py' that you can customize to your needs. 
Here's an example:

```python
import os
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from flask import Flask, redirect, request
import requests

def makeMessage(input):
    return "The string you want to respond with"

@app.route("/", methods=['GET', 'POST'])
def incoming_sms():
    message = request.values.get('Body', None)
    resp = MessagingResponse()
    resp.message(makeMessage(str(message)))
    return(str(resp))
```

### Part 2: Heroku App

![alt text](https://www.perfect.org/images/heroku-logo.jpg "Heroku Logo")

[Great link for reference](https://devcenter.heroku.com/articles/getting-started-with-python)


1. Enter Directory in terminal and type:
`git init`
then
`heroku login`
Here you have to enter your login and password for Heroku
2. Make two files in the Directory. One will be called Pipfile and the other will be called Procfile. Do not use any suffix for the files. In Pipfile, write your python package dependencies. This is an example:

```
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
datetime = "*"
pandas = "*"
numpy = "*"
twilio = "*"
flask = "*"
gunicorn = "*"
requests = "*"



[dev-packages]

[requires]
python_full_version = "2.7.15"
```

In Procfile, write the process that you want the app to run. This format can be found here: https://devcenter.heroku.com/articles/procfile. This is what it should look like:

``` 
web: gunicorn main:app --log-file -
```
3. Type in terminal: 
`heroku create YOUR_PROJECT_NAME`

This creates a Heroku project, and gives you a project URL.
For example: https://YOUR_PROJECT_NAME.heroku.com/

4. Type in terminal:
`pipenv install`
then
`pipenv lock`

This locks your dependencies and creates a new file - Pipfile.lock - which the heroku app needs for a reference to dependencies. 

5.Type in terminal:
`git push heroku master`
This sends your app to Heroku under the url that you got earlier
Now you may type: 
`heroku logs`
to see the logs of your project

**Note: You are using a free Heroku subscription, but you may incur costs if you scale up your app.**

### Part 3: Twilio

![alt text](https://www.twilio.com/marketing/bundles/marketing/img/favicons/favicon.ico "Twilio Logo")

1. Go to your Twilio Account and buy a phone number. It will be **$1/month**
2. Go to 'Configure' under the phone number. Find 'Messaging.'
* For 'Configure With' select 'Webhooks, TwiML Bins, functions, Studio, or Proxy'
* For 'A message comes in' select 'Webhook', type in the url of your Heroku app(https://YOUR_PROJECT_NAME.heroku.com/), and select 'HTTP POST' on the right.
3. Navigate to studio.twilio.com and make a new flow. Call it 'Error Message'. 
* Add a new message widget, and write the error message you would like in the message widget.
* Then connect the widget with 'Incoming Message' and Publish your flow.
4. Now go back to 'Configure.' Under 'Primary Handler Fails' select 'Studio Flow' and in the dropdown select 'Error'

We have just uploaded your Flask app to Heroku, then connected it to Twilio, and created a backup message if something goes wrong. 

Please feel free to take inspiration from main.py in creating a flask app suited to your needs. Enjoy! 


## Author

This is a repository for a SMS-bot made for Arable Labs by Om Suchak 2018.
Email: om.suchak@gmail.com
LinkedIn: https://www.linkedin.com/in/omsuchak/

## License
[MIT](https://choosealicense.com/licenses/mit/)
