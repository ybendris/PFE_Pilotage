import sys
import os
import logging
import csv
from pilotage_lib import NetworkItem, getBeginDateTime

HOST = 'localhost'
PORT = 65432
#SESSION_NAME = ''
#dt_string = ''

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class DataCollect(NetworkItem):
    def __init__(self, host, port, name, abonnement, session, dt_string):
        print(f"{host},{port},{name},{abonnement}")

        self.session = session
        self.dt_string = dt_string

        # On crée le répertoire CSV_DATA, s'il n'existe pas
        try:
            os.mkdir("CSV_DATA")
        except FileExistsError:
            pass

        # self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(SESSION_NAME, dt_string), 'w')

        # clé = expéditeur et valeur = DictWriter
        self.writers = {}

        # clé = expéditeur et valeur = fichier ouvert
        self.fOpens = {}

        NetworkItem.__init__(self, host, port, name, abonnement)

    """def openCSV(self, file, mode):
        if mode == 'w':
            fopen = open(file, mode, newline='')
            self.writer = csv.DictWriter(fopen, fieldnames=header)
            self.writer.writeheader()
            return fopen
        else:
            pass"""

    def ecrireCSV(self, message):
        origine = message["expediteur"]
        print(origine)
        if origine in self.writers:
            #print("existe")
            #print(self.fOpens[origine])
            #print(self.writers[origine])
            logging.info(f"On écrit: {message['msg']}")
            self.writers[origine].writerow(message["msg"])
        else:
            print("existe pas")
            header = list(message["msg"].keys())
            # header=["MESSAGE"]
            #print(type(header))
            self.fOpens[origine] = open('CSV_DATA/DATA_{}_{}_{}.csv'
                                        .format(self.session, origine, self.dt_string), 'w', newline='')
            #print(self.fOpens[origine])
            self.writers[origine] = csv.DictWriter(self.fOpens[origine], fieldnames=header)
            #print(self.writers)
            self.writers[origine].writeheader()
            logging.info(f"On écrit: {message['msg']}")
            self.writers[origine].writerow(message["msg"])
            #print(header)

    def service(self):
        print("service")
        while True:
            deserialized_message = self.queue_message_to_process.get()
            print(f"deserialized_message: {deserialized_message}")
            if deserialized_message["type"] == 'DATA':
                del deserialized_message["type"]
                logging.info(deserialized_message)
                self.ecrireCSV(deserialized_message)


if __name__ == '__main__':
    logging.info('starting')
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <name> <session>")
        sys.exit(1)
    name = sys.argv[1]
    SESSION_NAME = sys.argv[2]
    dt_string = getBeginDateTime()
    abonnement = ["DATA"]
    data_collect = DataCollect(HOST, PORT, name, abonnement, SESSION_NAME, dt_string)
