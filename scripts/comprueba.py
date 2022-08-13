import RPi.GPIO as GPIO
from datetime import datetime
import time

aux=datetime.today()       
name=str("/home/aloe/log.txt")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) # definimos la numeración 
GPIO.setup(18, GPIO.IN, GPIO.PUD_DOWN) # definimos el pin como salida
GPIO.setup(22, GPIO.IN, GPIO.PUD_DOWN) # definimos el pin como salida
while True:
    time.sleep(1)
    print(f"{GPIO.input(18)} {GPIO.input(22)}")