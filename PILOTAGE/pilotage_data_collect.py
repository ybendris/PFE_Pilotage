#!/usr/bin/env python3

""" Nom du module : Data_Collect"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import signal
import socket
import sys
import os
import logging
import csv
from pilotage_lib import NetworkItem, getBeginDateTime, kb_func

HOST = 'localhost'
PORT = 65432
#SESSION_NAME = ''
#dt_string = ''

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class DataCollect(NetworkItem):
    def __init__(self, host, port, name, abonnement, dt_string):
        print(f"{host},{port},{name},{abonnement}")

        self.session = ""

        self.dt_string = dt_string

        # On crée le répertoire CSV_DATA, s'il n'existe pas
        try:
            os.mkdir("CSV_DATA")
        except FileExistsError:
            pass

        # self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(SESSION_NAME, dt_string), 'w')

        # clé = expéditeur_paquet et valeur = DictWriter
        self.writers = {}

        # clé = expéditeur et valeur = fichier ouvert
        self.fOpens = {}

        NetworkItem.__init__(self, host, port, name, abonnement)


    def setNomSession(self, message):
        print(message["msg"]["session"])
        self.session=message["msg"]["session"]
        print("NOM DE LA SESSION : " + self.session)


    """
    Crée, ouvre et écrit dans un fichier CSV

    Paramètre
    ----------
    message : le message contenant la donnée à écrire dans le fichier CSV
    """
    def ecrireCSV(self, message):
        origine = message["expediteur"]
        paquet = message["paquet"]
        separateur = "_"
        cle = origine + separateur + paquet
        print(cle)

        #si le fichier correspondant à l'entité expéditrice est déjà ouvert
        if cle in self.writers:
            #print("existe")
            #print(self.fOpens[cle])
            #print(self.writers[cle])
            logging.info(f"On écrit: {message['msg']}")

            #Écrit la donnée dans le fichier CSV
            self.writers[cle].writerow(message["msg"])

        #Si le fichier n'existe pas
        else:
            print("existe pas")

            #Crée un header basé sur les clés du message
            header = list(message["msg"].keys())

            # header=["MESSAGE"]
            #print(type(header))

            #Crée et ouvre un fichier correspondant au nom de la session, à l'entité expéditrice de données
            #et à la date et heure
            self.fOpens[cle] = open('CSV_DATA/DATA_{}_{}_{}.csv'
                                        .format(self.session, cle, self.dt_string), 'w', newline='')

            #print(self.fOpens[cle])
            #Crée le file writer object correspondant au fichier de l'entité
            self.writers[cle] = csv.DictWriter(self.fOpens[cle], fieldnames=header)

            #print(self.writers)
            #Écrit le header sur la 1er ligne du fichier
            self.writers[cle].writeheader()
            logging.info(f"On écrit: {message['msg']}")

            #Écrit la donnée dans le fichier CSV
            self.writers[cle].writerow(message["msg"])


    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuiyée")
                logging.info(f"Le nom de la session est {self.session}")

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()

        logging.info("Service fini")
        self.queue_message_to_process.put(None) #Envoie d'un message None pour arrêter le thread
        for fopen in self.fOpens: #Fermeture propre des fichiers
            fopen.close()

    
    def traiterData(self, data):
        #si le message est une DATA
        if self.session:
            logging.info(data)
            #Écrit la donnée de le bon fichier CSV
            self.ecrireCSV(data)
        else :
            print("aucun nom de session, valeur par défaut prise en compte")
            self.session = "default_session"


    def traiterLog(self, log):
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")

    def define_action(self):
        actions = [
            {"nom":"setNomSession","function": self.setNomSession},
            {"nom":"stop","function": self.stop}
        ]
        return actions



if __name__ == '__main__':
    logging.info('starting')
    name = "DATA_COLLECT" #sys.argv[1]
    dt_string = getBeginDateTime()
    abonnement = ["DATA"]
    data_collect = DataCollect(HOST, PORT, name, abonnement, dt_string)
    
    data_collect.service()

    data_collect.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(data_collect.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(data_collect.read_thread.name))
