import RPi.GPIO as GPIO
from datetime import datetime
import threading
import traceback
from time import sleep
import pickle
import os
import base64
import googleapiclient.discovery
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#so that we can keep track of things we will use a logger for help
class Logger:
    def __init__(self, log_file):
        self.log_file=log_file
        # Get the path to the pickle file
        home_dir = os.path.expanduser('~')
        pickle_path = os.path.join(home_dir, 'gmail.pickle')

        # Load our pickled credentials
        self.creds = pickle.load(open(pickle_path, 'rb'))

    def log(self, message):
        with open("log.txt","a") as f:
            aux=datetime.today()   
            time_aux=aux.strftime("%m.%d.%Y..%H.%M")
            f.write(f"{time_aux} {message}\n")

    def init_message(self, mensaje):
        self.log(mensaje)
        # Build the service
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=self.creds)

        # Create a message
        my_email = 'navelaramona@gmail.com'
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Init nave Ramona'
        msg['From'] = f'{my_email}'
        msg['To'] = ", ".join(['bfbdj92@gmail.com', 'ecasadog@dipucordoba.es'])
        msgPlain = "El sistema se ha reiniciado, el riego programado es:"
        msgHtml = f'<b>El sistema se ha reiniciado, el riego programado es:'
        for i in mensaje:
            msgPlain += "\n"+i
            msgHtml += "<br>"+i
        msgHtml += "</b>"
        msg.attach(MIMEText(msgPlain, 'plain'))
        msg.attach(MIMEText(msgHtml, 'html'))
        raw = base64.urlsafe_b64encode(msg.as_bytes())
        raw = raw.decode()
        body = {'raw': raw}

        message1 = body
        message = (
            service.users().messages().send(
                userId="me", body=message1).execute())

    def send_message(self, mensaje):
        self.log(mensaje)
        # Build the service
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=self.creds)

        # Create a message
        my_email = 'navelaramona@gmail.com'
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Estado Nave la Ramona'
        msg['From'] = f'{my_email}'
        msg['To'] = ", ".join(['bfbdj92@gmail.com', 'ecasadog@dipucordoba.es'])
        msgPlain = mensaje
        msgHtml = f'<b>{msgPlain}</b>'
        msg.attach(MIMEText(msgPlain, 'plain'))
        msg.attach(MIMEText(msgHtml, 'html'))
        raw = base64.urlsafe_b64encode(msg.as_bytes())
        raw = raw.decode()
        body = {'raw': raw}

        message1 = body
        message = (
            service.users().messages().send(
                userId="me", body=message1).execute())
#we will host everything in a class
class Endpoint:
    def __init__(self, config_file="/home/aloe/config.txt", log_file="/home/aloe/log.txt", motor_pin=16, signal_pin=18, water_level_pin=22):
        #we save start variables
        #TODO: this can be updated to *args or **kargs
        self.logger=Logger(log_file) #file where we will log things
        self.motor_pin=motor_pin #motor pin, this pin controls start and stop of water pump
        self.signal_pin=signal_pin # this pin reads the voltage in the water pump contactor (signal)
        self.water_level_pin=water_level_pin #this pin reads the voltage in the water pump contactor after the sounding line (power)
        state="init"
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
        start=datetime.today()
        temp=start.strftime("%m.%d.%Y..%H.%M")
        #state machine, this could be done with threads and other things
        while True:
            if state=="init":
                if self.water_time(True): #if we want to water
                    state="water"
                    GPIO.output(self.motor_pin, GPIO.HIGH)
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.log(f"encendido programado a las {temp}")
                else:
                    state="sleep"
                    GPIO.output(self.motor_pin, GPIO.LOW)
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.log(f"apagado programado a las {temp}")

            elif state=="water":
                sleep(1)
                if self.water_time(False): #if we dont want to water anymore
                    state="init"
                elif (GPIO.input(self.signal_pin)!=1) or (GPIO.input(self.water_level_pin)!=1): #if pump is not working
                    state="external_off"

            elif state=="sleep":
                sleep(5) #we will sleep a lot to make sure there is not any residual charge
                if self.water_time(True): #if we want to water again
                    state="init"                
                elif (GPIO.input(self.signal_pin)) or (GPIO.input(self.water_level_pin)):
                    self.logger.log("external power on")
                    state="external_on"

                
            elif state=="external_off":
                start=datetime.today()
                temp=start.strftime("%m.%d.%Y..%H.%M")
                false_negative=False
                for i in range(5):
                    sleep(1)
                    if ((GPIO.input(self.signal_pin)) and (GPIO.input(self.water_level_pin))):
                        false_negative=True
                if false_negative:
                    state="water"
                    continue
                self.logger.log(f"{(GPIO.input(self.signal_pin))} {(GPIO.input(self.water_level_pin))} at {temp}<")
                self.logger.send_message(f"La bomba se ha apagado debido a las sondas a las {temp}, por seguridad, la sonda seguirá apagada 10 mins")
                GPIO.output(self.motor_pin, GPIO.LOW)
                for i in range (60):
                    sleep(10)
                    if self.water_time(False):
                        break
                if self.water_time(False):
                    self.logger.log("pump was disconnected while there is no water")
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.send_message(f"sistema desconectado por protocolo a las {temp}")
                else:
                    time=datetime.today()-start
                    self.logger.log(f"water came back after {time}")
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.send_message(f"La bomba ha vuelto a la normalidad a las {temp} despues de {time}")
                state="init"

            elif state=="external_on":
                start=datetime.today()
                temp=start.strftime("%m.%d.%Y..%H.%M")
                false_positive=False
                for i in range(20):
                    sleep(1)
                    if ((GPIO.input(self.signal_pin)==0) or (GPIO.input(self.water_level_pin)==0)):
                        false_positive=True
                if false_positive:
                    state="sleep"
                    continue

                self.logger.send_message(f"modo manual encendido fuera de hora a las {temp}")

                while ((GPIO.input(self.signal_pin)) or (GPIO.input(self.water_level_pin))) and self.water_time(False):
                    sleep(1)
                if self.water_time(False):
                    self.logger.log("manual mode was on till water time")
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.send_message(f"El modo manual se ha sobreescrito debido a llegar a hora de riego")

                else:
                    time=datetime.today()-start
                    start=datetime.today()
                    temp=start.strftime("%m.%d.%Y..%H.%M")
                    self.logger.log(f"manual mode turned off after {time}")
                    self.logger.send_message(f"el modo manual se ha apagado a las {temp} despues de {time}")

                state="init"


            else:
                self.logger.log("incoherent state")
                start=datetime.today()
                temp=start.strftime("%m.%d.%Y..%H.%M")
                self.logger.send_message(f"Ha habido uh bug a las {temp} estado = {state}")
                state="init"

            sleep(1)

    def read_config(self,config_file):
        weekdays=["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"] #string with names of day of weeks
        self.water=[[] for i in range(7)] #we create empty list
        with open(config_file,"r") as f: #we read the file
            mess=[] #empty string for logs
            for line in f: #each line
                mess.append(line)
                aux=line.split(" ") 
                day=aux[0]
                hours=aux[1].strip()
                hours=hours.split(",")
                for i in hours:
                    self.water[weekdays.index(day)].append(i.split("-"))
            self.logger.init_message(mess)


    def water_time(self, flag):
        today=datetime.today()
        actualtime=int(today.strftime("%H%M"))
        do_we_water=False
        for time_frame in self.water[today.weekday()]:
            start=int(time_frame[0].replace(":",""))
            end=int(time_frame[1].replace(":",""))
            if actualtime>=start and actualtime<end:
                do_we_water=True
        if flag==do_we_water:
            return True
        else: 
            return False
            



if __name__ == '__main__':
    endopoint=Endpoint()
