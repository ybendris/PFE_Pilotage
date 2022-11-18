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

        #Nom de la session
        self.session = session
        #Date et heure de lancement du log_collect
        self.dt_string = dt_string

        try:
            # On crée le répertoire CSV_LOG dans le répertoire courant, s'il n'existe pas
            os.mkdir("CSV_LOG")
        except FileExistsError:
            pass
        #On crée et ouvre le fichier CSV, où les logs sont stockés
        #Le fichier est nommé selon le nom de la session et de la date et l'heure de lancement du log_collect
        self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(self.session, self.dt_string), 'w')
        NetworkItem.__init__(self, host, port, name, abonnement)


    """
    Ouvrir un fichier CSV
    
    Paramètres
    ----------
    file : chemin du fichier à ouvrir
    mode : mode d'ouverture du fichier, ici 'écriture'
    
    Return
    ------
    Un file object
    """
    def openCSV(self, file, mode):
        #si le mode d'ouverture est 'écriture'
        if mode == 'w':
            #ouvrir le fichier
            fopen = open(file, mode, newline='')

            #Créer le file writer object
            self.writer = csv.DictWriter(fopen, fieldnames=header)

            #Écrire le header sur la première ligne du fichier
            self.writer.writeheader()
            return fopen
        else:
            pass

    """
    Écrire dans un fichier CSV

    Paramètre
    ----------
    message : le message reçu contenant le log à enregistrer 
    """
    def ecrireCSV(self, message):
        logging.info(f"On écrit: {message} sur {self.writer}")
        #Écrire le message dans le fichier
        self.writer.writerow(message)

    """
    Processus principal du log_collect
    Reçoit des messages et écrit les logs dans un fichier CSV
    """
    def service(self):
        print("service")
        while True:
            #Récupère un message dans la queue
            deserialized_message = self.queue_message_to_process.get()
            # print(f"deserialized_message: {deserialized_message}")

            #si le message est un log
            if deserialized_message["type"] == 'LOG':

                #Retirer le type du message
                del deserialized_message["type"]
                # logging.info(deserialized_message)

                #Écrire le log dans le fichier CSV
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
