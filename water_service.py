#import RPi.GPIO as GPIO
from datetime import datetime
import threading
import traceback
from time import sleep
import httplib2
import os
import oauth2client
from oauth2client import client, tools, file
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

#so that we can keep track of things we will use a logger for help
class Logger:
    def __init__(self, log_file):
        self.log_file=log_file

    def log(message):
        with open("log.txt","a") as f:
            aux=datetime.today()   
            time_aux=aux.strftime("%m.%d.%Y..%H.%M")
            f.write(f"{time_aux} {message}\n")


#we will host everything in a class
class Endpoint:
    def __init__(self, config_file="/home/aloe/config.txt", log_file="/home/aloe/log.txt", motor_pin=16, signal_pin=18, water_level_pin=22):
        #we save start variables
        #TODO: this can be updated to *args or **kargs
        self.logger=Logger(log_file) #file where we will log things
        self.motor_pin=motor_pin #motor pin, this pin controls start and stop of water pump
        self.signal_pin=signal_pin # this pin reads the voltage in the water pump contactor (signal)
        self.water_level_pin=water_level_pin #this pin reads the voltage in the water pump contactor after the sounding line (power)
        self.state="init"
        #init GPIO pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD) # definimos la numeración 
        GPIO.setup(self.motor_pin, GPIO.OUT) # definimos el pin como salida
        GPIO.setup(self.signal_pin, GPIO.IN, GPIO.PUD_DOWN) # definimos el pin como entrada pull down
        GPIO.setup(self.water_level_pin, GPIO.IN, GPIO.PUD_DOWN) # definimos el pin como entrada pull down
        

        #read config
        self.read_config(config_file)


        #TODO: we can use a thread for checking pins to lighten state machine code
        #thread of status
        #self.status_thread = threading.Thread(target=self.pin_status)



        #state machine, this could be done with threads and other things
        while True:
            if state=="init":
                if self.water_time(True): #if we want to water
                    state="water"
                    GPIO.output(self.motor_pin, GPIO.HIGH)
                else:
                    state="sleep"
                    GPIO.output(self.motor_pin, GPIO.LOW)

            elif state=="water":
                if self.water_time(False): #if we dont want to water anymore
                    GPIO.output(self.motor_pin, GPIO.LOW)
                elif (GPIO.input(self.signal_pin)!=1) or (GPIO.input(self.water_level_pin)!=1): #if pump is not working
                    self.alert_off()
                    state="external_off"

            elif state=="sleep":
                sleep(5) #we will sleep a lot to make sure there are not any residual charge
                if self.water_time(True): #if we want to water again
                    state="water"
                    GPIO.output(self.motor_pin, GPIO.HIGH)
                elif (GPIO.input(self.signal_pin)) or (GPIO.input(self.water_level_pin)):
                    self.logger.log("external power on")
                    self.alert_on()
                    state="external_on"

                
            elif state=="external_off":
                start=datetime.today()
                    while ((GPIO.input(self.signal_pin)!=1) or (GPIO.input(self.water_level_pin)!=1)) and self.water_time(True):
                        sleep(1)
                if self.water_time(False):
                    self.logger.log("pump was disconnected while there is no water")
                else:
                    time=datetime.today()-start
                    self.logger.log(f"water came back after {time}")
                state="init"

            elif state=="external_on":
                start=datetime.today()
                    while ((GPIO.input(self.signal_pin)) or (GPIO.input(self.water_level_pin))) and self.water_time(False):
                        sleep(1)
                if self.water_time(False):
                    self.logger.log("manual mode was on till water time")
                else:
                    time=datetime.today()-start
                    self.logger.log(f"manual mode turned off after {time}")
                state="init"


            else:
                self.logger.log("incoherent state")
                state="init"

            sleep(1)

    def alert_off(self):
        to = "to@address.com"
        sender = "navelaramona@gmail.com"
        subject = "subject"
        msgHtml = "Hi<br/>Html Email"
        msgPlain = "Hi\nPlain Email"

        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        msg.attach(MIMEText(msgPlain, 'plain'))
        msg.attach(MIMEText(msgHtml, 'html'))
        text = {'raw': base64.urlsafe_b64encode(msg.as_bytes())}

        try:
            message = (service.users().messages().send(userId=service, body=text).execute())
        except errors.HttpError as error:
            self.logger.log('An error occurred: %s' % error)


    def alert_on(self):
        pass

    def read_config(self,config_file):
        weekdays=["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"] #string with names of day of weeks
        self.water=[[] for i in range(7)] #we create empty list
        with open(config_file,"r") as f: #we read the file
            for line in f: #each line
                aux=line.split(" ") 
                day=aux[0]
                hours=aux[1].strip()
                hours=hours.split(",")
                for i in hours:
                    self.water[weekdays.index(day)].append(i.split("-"))

    def



if __name__ == '__main__':
    endopoint=Endpoint()