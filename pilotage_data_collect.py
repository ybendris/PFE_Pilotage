#!/usr/bin/env python3

""" Nom du module : Data_Collect"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

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

    """
    Create, Open and Write in a CSV file
    Else open the file and write the message

    Parameters
    ----------
    message : Received log to write in the file
    """
    def ecrireCSV(self, message):
        origine = message["expediteur"]
        print(origine)

        #if the file is already open and have file writer object
        if origine in self.writers:
            #print("existe")
            #print(self.fOpens[origine])
            #print(self.writers[origine])
            logging.info(f"On écrit: {message['msg']}")

            #Write the message in a CSV file related to the right entity
            self.writers[origine].writerow(message["msg"])

        #Else the file doesn't exist
        else:
            print("existe pas")

            #Create a header base on the message's keys
            header = list(message["msg"].keys())
            # header=["MESSAGE"]
            #print(type(header))

            #Create and open the file according to the name of the sessionn the entity related, and date/time
            self.fOpens[origine] = open('CSV_DATA/DATA_{}_{}_{}.csv'
                                        .format(self.session, origine, self.dt_string), 'w', newline='')

            #print(self.fOpens[origine])
            #Create the file writer file related to the right entity
            self.writers[origine] = csv.DictWriter(self.fOpens[origine], fieldnames=header)

            #print(self.writers)
            #Write the header at first line of the file
            self.writers[origine].writeheader()
            logging.info(f"On écrit: {message['msg']}")

            #Write the message in the CSV file using file writer
            self.writers[origine].writerow(message["msg"])
            #print(header)

    """
    Main process of data_collect
    Receive data from a specific entity and write them in the related CSV file
    """
    def service(self):
        print("service")
        while True:
            #Receive a message from the queue
            deserialized_message = self.queue_message_to_process.get()
            print(f"deserialized_message: {deserialized_message}")

            #if the message is a DATA
            if deserialized_message["type"] == 'DATA':
                #Remove message's type from the message
                del deserialized_message["type"]
                logging.info(deserialized_message)

                #Write the data in a CSV file
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
