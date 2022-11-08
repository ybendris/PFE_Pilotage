import sys
import os
import logging
from datetime import datetime
import csv
from pilotage_entite import EntitePilotage

HOST = 'localhost'
PORT = 65432
SESSION_NAME = ''
dt_string = ''
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class LogCollector(EntitePilotage):
    def __init__(self, host, port, name, abonnement):

        print(f"{host},{port},{name},{abonnement}")

        try:
            os.mkdir("CSV_LOG")
        except FileExistsError:
            pass
        self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(SESSION_NAME, dt_string), 'w')
        EntitePilotage.__init__(self, host, port, name, abonnement)
        # On crée le répertoire CSV_LOG, s'il n'existe pas




    def openCSV(self, file, mode):
        if mode == 'w':
            fopen = open(file, mode, newline='')
            self.writer = csv.DictWriter(fopen, fieldnames=header)
            self.writer.writeheader()
            return fopen
        else:
            pass

    def ecrireCSV(self, message):
        self.writer.writerow(message)

    def service(self):
        print("service")
        while True:
            deserialized_message = self.queue_message_to_process.get()
            print(f"deserialized_message: {deserialized_message}")
            if deserialized_message["type"] == 'LOG':
                del deserialized_message["type"]
                logging.info(deserialized_message)
                self.ecrireCSV(deserialized_message)



def getDateTimeBegin():
    a = datetime.now()
    print("DATE =", a)
    # dd/mm/YY H:M:S
    global dt_string
    dt_string = a.strftime("%d-%m-%Y_%H-%M-%S")
    print("date and time =", dt_string)




if __name__ == '__main__':
    logging.info('starting')
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <name> <session>")
        sys.exit(1)
    name = sys.argv[1]
    SESSION_NAME = sys.argv[2]
    getDateTimeBegin()
    abonnement = ["LOG"]
    logCollect = LogCollector(HOST, PORT, name, abonnement)
