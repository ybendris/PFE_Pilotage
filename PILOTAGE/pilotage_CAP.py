#!/usr/bin/env python3

""" Nom du module : Log_Collect"""
from functools import partial

import yaml

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import socket
import os
import logging
import csv
from pilotage_lib import NetworkItem, getBeginDateTime, kb_func
from instrument_lib import DecomNano, Nano

HOST = 'localhost'
PORT = 65432
# SESSION_NAME = ''
# dt_string = ''
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')





class SPV_CAP(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        self.retrieveCom()
        self.nano = Nano("COM3") #None
        self.decom = DecomNano()
        self.process()
        NetworkItem.__init__(self, host, port, name, abonnement)

    def retrieveCom(self):
        #Récupère le port com sur lequel l'instrument est co (développement par les indus)
        pass

    def process(self):
        self.decom.add_sampletrames("nano_samples.yml")
        self.nano.connect()
        self.nano.send_code(self.decom.mnemo2code('statusUpdate1s'))

    def doTrame(self,action,*kargs):
        print("wola ça marche" + action)
        self.nano.send_code(self.decom.mnemo2code(action))

    """
    Processus principal du superviseur CAP
    Reçoit et envoie des messages, traduit les commandes en trame et les trames en message
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()
        while keypress != 'q' and self.running:
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                logging.info(f"Le nom de la session est {self.session}")

            # Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()

        logging.info("Service fini")
        self.queue_message_to_process.put(None)  # Envoie d'un message None pour arrêter le thread
        for fopen in self.fOpens:  # Fermeture propre des fichiers
            fopen.close()

    def define_action(self):
        actions = [{"nom": "stop", "function": self.stop}]

        for action in self.decom.mnemos:
            actions.append({"nom": action, "function": partial(self.doTrame, action)})
        return actions


    def traiterData(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")

    def traiterLog(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")


if __name__ == '__main__':
    logging.info('starting')
    name = "CAP"
    dt_string = getBeginDateTime()
    abonnement = []
    CAP = SPV_CAP(HOST, PORT, name, abonnement)
    CAP.service()

    CAP.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(CAP.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(CAP.read_thread.name))




