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


    def recupererNomSession(self,message):
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
            #print(header)

    """
    Processus principal du data_collect
    Reçoit des messages et écrit les données qu'il reçoit dans des fichers CSV spécifique à chaque entité
    """
    def service(self):
        print("service")
        flag_session = False
        while True:
            #Recupère un message dans sa queue
            deserialized_message = self.queue_message_to_process.get()
            print(f"deserialized_message: {deserialized_message}")

            if flag_session == False:
                if deserialized_message["type"]=="CMD":
                    if "session" in deserialized_message["msg"]:
                        print("on recupére le nom de la session")
                        self.recupererNomSession(deserialized_message)
                        flag_session = True
                    else :
                        pass

            #si le message est une DATA
            if deserialized_message["type"] == 'DATA' and flag_session == True:
                #Retire le type du message
                del deserialized_message["type"]
                logging.info(deserialized_message)

                #Écrit la donnée de le bon fichier CSV
                self.ecrireCSV(deserialized_message)
            else :
                print("\naucun nom de session\n")



if __name__ == '__main__':
    logging.info('starting')
    name = "DATA_COLLECT" #sys.argv[1]
    dt_string = getBeginDateTime()
    abonnement = ["DATA"]
    data_collect = DataCollect(HOST, PORT, name, abonnement, dt_string)
    data_collect.service()
