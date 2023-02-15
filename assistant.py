#Local Modules
import os
import datetime as dt
import time
from time import ctime
import re
import threading
import multiprocessing as mp
import logging
import random
#Third-party Modules
import requests
from bs4 import BeautifulSoup as bs4
import speech_recognition as sr
import webbrowser
import playsound
import keyboard
import pyaudio
from gtts import gTTS
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Assistant:
    def __init__(self):
        now = dt.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        # Create and configures the logger
        logging.basicConfig(filename=f"logs{now}.log", format='%(asctime)s %(message)s', filemode='w')
        # Creates logging object
        logg = logging.getLogger()
        # Sets the level of logging
        logg.setLevel(logging.DEBUG)

        #Gmail Authenticator info
        SCOPES = ['https://mail.google.com/']
        email = 'EMAIL HERE'

        #Functoins the assistant can perform
        functions = ['HELP', 'SEARCH', 'LOOK UP', 'START', 'CHECK EMAIL', 'WHAT IS TODAY', 'WHAT TIME IS IT', 'EXIT', 'QUIT']

        #Assistant settings
        assist_name = 'Helen'
        user_name = 'User'

        # get the Gmail API service
        service = self.gmail_authenticate()

    def gmail_authenticate(self):
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)



    #Searches through set email accounts messages using specified query
    def search_messages(self, service, query):
        result = service.users().messages().list(userId='me',q=query).execute()
        messages = []
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages


    #reads the messages that are queiried, set as the messages recieved today
    def read_message(self, service, message):
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        payload = msg['payload']
        headers = payload.get("headers")
        parts = payload.get("parts")
        if headers:
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    self.speak(value)
                if name.lower() == "to":
                    self.speak(value)
                if name.lower() == "subject":
                    self.speak(value)


    # Records from default mic device and returns a string
    def get_audio(self, attempts: int = 0):
        attempt = attempts #tracks how many attempts at understanding speech
        if attempts <= 2:
            rec = sr.Recognizer()
            try:
                with sr.Microphone() as mic:    #use default set mic to listen to speech
                    user_audio = rec.listen(mic)
                    audio_text = rec.recognize_google(user_audio)
                    return audio_text      #retun speech as a string
            except sr.UnknownValueError:    #if not understood retry
                self.speak("Sorry didn't get that")
                self.logg.debug("attempted to understand what was said, trying again")
                return self.get_audio(attempts = attempt + 1)
        else:
            self.speak("Sorry we'll try again later")
            self.logg.debug("couldn't understand what was being said")


    # when event is triggered start the assistant
    def trigger(self, isOn=False):
        if isOn:
            self.speak("Hi, what can I do?")
            self.logg.debug("assistant powered on")
            self.execute_command(self.get_audio())


    #handles which command should be started
    def execute_command(self, command: str):
        try:
            if 'search' in command or 'look up' in command: #Goolge searches
                self.speak("What should I look for")
                self.logg.debug("listening...")
                search = self.get_audio()
                self.speak("Searching " + search)
                self.logg.debug("Opening google query in default browser")
                webbrowser.open('https://www.google.com/search?q=' + search)
                self.logg.debug("Browser is open")
            elif 'start' in command:    #starts apps on desktop, must match name known to OS
                self.speak("What should I start")
                app = self.get_audio().lower()
                self.speak("Starting " + app)
                self.logg.debug("Starting " + app)
                try:
                    os.system('start ', app)
                    self.logg.debug("app started successfully")
                except:
                    self.logg.warning("could not start app, maybe try a different name")
            elif 'what is today' in command or 'what time is it' in command:    #Tells today's date and time
                self.logg.debug("Grabbing today's date")
                self.speak("Today's date is " + str(ctime()))
                self.logg.info("Today's date: " + str(ctime()))
            elif 'email' in command.lower():    #reads out unread mail received today
                self.speak("checking email")
                self.logg.debug('checking email')
                count = 0
                msgs = self.search_messages(self.service, 'in:inbox inbox : after: ' + dt.date.today() + ' is: unread')
                for msg in msgs:
                    count += 1
                    self.read_message(self.service, msg)
                    self.logg.debug("reading message " + str(count))
            elif command == 'help': #reads list of available commands
                self.speak('you can say')
                for func in self.functions:
                    self.speak(func)
            elif command == 'exit' or command == 'quit': #exits out of the virtual assistant app
                self.speak('goodbye')
                exit()

        except AttributeError:
            self.logg.warning("String was not passed to the command function")
        except:
            self.logg.warning("Didn't understand: " + command)
            self.speak("Sorry could not perform that function, say help to see what you can say")
            self.logg.debug("could not follow that command")
        finally:
            self.logg.debug('finished command')
            return None


    #uses this to activate speach functions
    def speak(self, audio_string):
        tts = gTTS(text=audio_string, lang='en')
        r = random.randint(1,20000000)  #assigns random number to audio file
        audio_file = 'audio' + str(r) + '.mp3'
        tts.save(audio_file)
        self.logg.debug("log audio created")
        playsound.playsound(audio_file)
        self.logg.debug("speak(): " + audio_string)
        self.logg.debug(f"{self.assist_name}: {audio_string}")
        os.remove(audio_file)   #remoces file after being spoken


