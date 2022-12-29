""" Nom du module : IhmSupervisor"""

""" Description Le superviseur de l'IHM, il peut communiquer avec le central"""
""" Version 2 """
""" Date : 01/122022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import sys
import os
import logging
import csv
from pilotage_lib import NetworkItem, getBeginDateTime

import time
from flask import Flask, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, Namespace

HOST = 'localhost'
PORT = 65432
#SESSION_NAME = ''
#dt_string = ''
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class IhmSupervisor(NetworkItem, Flask):
    def __init__(self, host, port, name, abonnement,import_name):
        NetworkItem.__init__(self, host, port, name, abonnement)
        Flask.__init__(self, import_name)
        
        # Initialise Flask-CORS
        self.cors = CORS(self)

        # Initialise Flask-SocketIO
        self.socketio = SocketIO(self, cors_allowed_origins="*")

        self.socketio.on("send_command")(self.on_send_command)

    """
    Fonction qui gère la réception de data de la part du central
    #TODO à compléter
    """
    def traiterData(self, data):
        pass

    """
    Fonction qui gère la réception de log de la part du central
    #TODO à compléter
    """
    def traiterLog(self, log):
        pass

    """
    Fonction définissant les actions de la classe
    #TODO à compléter
    """
    def define_action(self):
        actions = [
            {"nom":"stop","function": self.stop},
        ]

        return actions

    """
    La fonction on_send_command() est un gestionnaire d'événement enregistré avec Flask-SocketIO. 
    Elle est appelée lorsqu'un événement "send_command" est reçu via WebSocket.
    Elle est chargé de transmettre la commande au central 
    
    Le paramètre command est un dict
    #TODO à compléter avec les nouvelles fonctions send
    """
    def on_send_command(self, command):
        print('received message: ' + str(command))
        self.queue_message_to_send.put(command)
        

    """
    fonction principal du ihm_superviseur
    Récupère les messages du central et les envoie
    #TODO à refactoriser
    """
    def service(self):
        logging.info("service API Lancé")
        while True:
            deserialized_message = self.queue_message_to_process.get() #Récupère un message dans la queue

            message_type = deserialized_message.get("type")
            #print(f"deserialized_message: {deserialized_message}")
            if message_type == 'DATA':
                self.socketio.emit("get_data",deserialized_message)
                # logging.info(deserialized_message)
    
            elif deserialized_message["type"] == 'LOG':
                self.socketio.emit("get_log",deserialized_message)
                # logging.info(deserialized_message)

            elif deserialized_message["type"] == 'CMD':
                self.socketio.emit("get_cmd", deserialized_message)
                # logging.info(deserialized_message)
        

if __name__ == '__main__':
    logging.info('starting')
    
    name = "IHM"
    abonnement = ["DATA","LOG"]  
    
    app = IhmSupervisor(HOST, PORT, name, abonnement, __name__)
    #TODO vérifier si l'on a toujour besoin de lancer la fonction service dans un thread à cause du processus run qui est bloquant
    threadService = app.serviceInDaemonThread()
    app.run()