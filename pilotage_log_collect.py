#!/usr/bin/env python3

""" Nom du module : Log_Collect"""

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
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class LogCollector(NetworkItem):
    def __init__(self, host, port, name, abonnement, session, dt_string):

        #print(f"{host},{port},{name},{abonnement}")

        #session name
        self.session = session
        #Date and hour of launch
        self.dt_string = dt_string

        try:
            #Create CSV_LOG directory
            os.mkdir("CSV_LOG")
        except FileExistsError:
            pass
        self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(self.session, self.dt_string), 'w')
        NetworkItem.__init__(self, host, port, name, abonnement)
        # On crée le répertoire CSV_LOG, s'il n'existe pas

    """
    Open a CSV file
    
    Parameters
    ----------
    file : path of the file to open
    mode : mode in which the file is open. Here always WRITE
    
    Return
    ------
    A file object
    """
    def openCSV(self, file, mode):
        #if file open mode is Write
        if mode == 'w':
            #open the file
            fopen = open(file, mode, newline='')

            #Create file writer object
            self.writer = csv.DictWriter(fopen, fieldnames=header)

            #Write header in at the beginning of the file
            self.writer.writeheader()
            return fopen
        else:
            pass

    """
    Write in a CSV file

    Parameters
    ----------
    message : Received log to write in the file
    """
    def ecrireCSV(self, message):
        logging.info(f"On écrit: {message} sur {self.writer}")
        #Write the message using the Writer file object
        self.writer.writerow(message)

    """
    Main process of log_collect
    Receive log and write them in a CSV file
    """
    def service(self):
        print("service")
        while True:
            #Receive a message from the queue
            deserialized_message = self.queue_message_to_process.get()
            # print(f"deserialized_message: {deserialized_message}")

            #if the message is a log
            if deserialized_message["type"] == 'LOG':

                #Remove the type of the message
                del deserialized_message["type"]
                # logging.info(deserialized_message)

                #Write log in a CSV file
                self.ecrireCSV(deserialized_message)


if __name__ == '__main__':
    logging.info('starting')
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <name> <session>")
        sys.exit(1)
    name = sys.argv[1]
    SESSION_NAME = sys.argv[2]
    dt_string = getBeginDateTime()
    abonnement = ["LOG"]
    logCollect = LogCollector(HOST, PORT, name, abonnement, SESSION_NAME , dt_string)
