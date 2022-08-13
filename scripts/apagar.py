import RPi.GPIO as GPIO
from datetime import datetime
aux=datetime.today()       
name=str("/home/aloe/log.txt")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) # definimos la numeración 
GPIO.setup(16, GPIO.OUT) # definimos el pin como salida
GPIO.output(16, GPIO.LOW)
with open("log.txt","a") as f:
    time_aux=aux.strftime("%m.%d.%Y..%H.%M")
    f.write("apagado en {time_aux}\n")