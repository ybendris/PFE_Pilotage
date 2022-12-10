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


    def on_send_command(self, command, methods=['GET', 'POST']):
        print('received message: ' + str(command))
        self.socketio.emit("get_data",command)



    """
    fonction principal du ihm_superviseur
    Récupère les messages du central et les envoie
    """
    def service(self):
        print("service API Lancé")
        while True:
            #Récupère un message dans la queue
            deserialized_message = self.queue_message_to_process.get()
            print(f"deserialized_message: {deserialized_message}")
            #si le message est un DATA
            if deserialized_message["type"] == 'DATA':
                #Retirer le type du message
                del deserialized_message["type"]
                print(deserialized_message)
                self.socketio.emit("get_data",deserialized_message)
                # logging.info(deserialized_message)"""
            #si le message est un LOG    
            elif deserialized_message["type"] == 'LOG':
                #Retirer le type du message
                del deserialized_message["type"]
                print(deserialized_message)
                self.socketio.emit("get_log",deserialized_message)
                # logging.info(deserialized_message)"""
        

if __name__ == '__main__':
    logging.info('starting')
    
    name = "IHM"
    abonnement = ["DATA","LOG"]  
    
    app = IhmSupervisor(HOST, PORT, name, abonnement, __name__)
    threadService = app.serviceInDaemonThread()
    app.run()