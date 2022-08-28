

class Test:
    def __init__(self, config_file="/home/aloe/config.txt", log_file="/home/aloe/log.txt", motor_pin=16, signal_pin=18, water_level_pin=22):
        self.read_config(config_file)

    def read_config(self,config_file):
        weekdays=["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"] #string with names of day of weeks
        self.water=[[] for i in range(7)] #we create empty list
        with open(config_file,"r") as f: #we read the file
            self.init_message(f)
            for line in f: #each line
                aux=line.split(" ") 
                day=aux[0]
                hours=aux[1].strip()
                hours=hours.split(",")
                for i in hours:
                    self.water[weekdays.index(day)].append(i.split("-"))

        print(self.water)
            
    def init_message(self, mensaje):
        mess="El sistema se ha reiniciado, el riego programado es:"
        for i in mensaje:
            mess+=i
        print(mess)
        return


if __name__ == '__main__':
    test=Test(config_file="config.txt", log_file="log.txt")


