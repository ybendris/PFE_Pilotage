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
from pilotage_lib import NetworkItem, getBeginDateTime, kb_func
import signal
import time

HOST = 'localhost'
PORT = 65432
#SESSION_NAME = ''
#dt_string = ''
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class LogCollector(NetworkItem):
    def __init__(self, host, port, name, abonnement, dt_string):
        #Nom de la session
        self.session = ""
        #Date et heure de lancement du log_collect
        self.dt_string = dt_string

        # clé = expéditeur_paquet et valeur = DictWriter
        self.writers = {}

        # clé = expéditeur et valeur = fichier ouvert
        self.fOpens = {}

        try:
            # On crée le répertoire CSV_LOG dans le répertoire courant, s'il n'existe pas
            os.mkdir("CSV_LOG")
        except FileExistsError:
            pass
        """
        #On crée et ouvre le fichier CSV, où les logs sont stockés
        #Le fichier est nommé selon le nom de la session et de la date et l'heure de lancement du log_collect
        self.fOpen = self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(self.session, self.dt_string), 'w')"""
        NetworkItem.__init__(self, host, port, name, abonnement)


    def setNomSession(self, message):
        print(message["msg"]["session"])
        self.session=message["msg"]["session"]
        print("NOM DE LA SESSION : " + self.session)


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
    """def openCSV(self, file, mode):
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
            pass"""

    """
    Écrire dans un fichier CSV

    Paramètre
    ----------
    message : le message reçu contenant le log à enregistrer 
    """
    """def ecrireCSV(self, message):
        logging.info(f"On écrit: {message} sur {self.writer}")
        #Écrire le message dans le fichier
        self.writer.writerow(message)"""

    def ecrireCSV(self, message):
        """origine = message["expediteur"]
        paquet = message["paquet"]
        separateur = "_"
        """
        cle = self.session
        print(cle)

        #si le fichier correspondant à l'entité expéditrice est déjà ouvert
        if cle in self.writers:
            #print("existe")
            #print(self.fOpens[cle])
            #print(self.writers[cle])
            logging.info(f"On écrit: {message}")

            #Écrit la donnée dans le fichier CSV
            self.writers[cle].writerow(message)

        #Si le fichier n'existe pas
        else:
            print("existe pas")

            #Crée un header basé sur les clés du message
            header = list(message.keys())
             #On sait que l'on a des logs, on supprime la colonne type
            
            # header=["MESSAGE"]
            #print(type(header))

            #Crée et ouvre un fichier correspondant au nom de la session, à l'entité expéditrice de données
            #et à la date et heure
            self.fOpens[cle] = open('CSV_LOG/LOG_{}_{}.csv'
                                        .format(self.session, self.dt_string), 'w', newline='')

            #print(self.fOpens[cle])
            #Crée le file writer object correspondant au fichier de l'entité
            self.writers[cle] = csv.DictWriter(self.fOpens[cle], fieldnames=header)

            #print(self.writers)
            #Écrit le header sur la 1er ligne du fichier
            self.writers[cle].writeheader()
            logging.info(f"On écrit: {message}")

            #Écrit la donnée dans le fichier CSV
            self.writers[cle].writerow(message)
            #print(header)

    """
    Processus principal du log_collect
    Reçoit des messages et écrit les logs dans un fichier CSV
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuiyée")
                logging.info(f"Le nom de la session est {self.session}")

            #Réception
            self.traiterMessage(self.getMessage())

            keypress = kb_func()

        logging.info("Service fini")
        self.queue_message_to_process.put(None) #Envoie d'un message None pour arrêter le thread
        for fopen in self.fOpens: #Fermeture propre des fichiers
            fopen.close()


    def traiterData(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")

    def traiterLog(self, log):
        if self.session:
            logging.info(log)
            #Écrit la donnée de le bon fichier des logs de la session
            self.ecrireCSV(log)
        else :
            print("aucun nom de session, valeur par défaut prise en compte")
            self.session = "default_session"


    def define_action(self):
        actions = [
            {"nom":"setNomSession","function": self.setNomSession},
            {"nom":"stop","function": self.stop}
        ]
        return actions

if __name__ == '__main__':
    logging.info('starting')
    name = "LOG_COLLECT" #sys.argv[1]
    #SESSION_NAME = sys.argv[2]
    dt_string = getBeginDateTime()
    abonnement = ["LOG"]
    logCollect = LogCollector(HOST, PORT, name, abonnement, dt_string)
    logCollect.service()
    

    
