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


class IhmSupervisor(NetworkItem):
    def __init__(self, host, port, name, abonnement, app: Flask, socketio: SocketIO):
        #print(f"{host},{port},{name},{abonnement}")*
        self.app = app
        self.socketio = socketio
        NetworkItem.__init__(self, host, port, name, abonnement)
      
        
        


    """
    Processus principal du ihm_superviseur
    Définie l'api entre la partie IHM et le processus courrant
    """
    def service(self):
        print("service API Lancé")

        @socketio.on('send_command')
        def on_send_command(command, methods=['GET', 'POST']):
            print('received message: ' + str(command))
            
            self.socketio.emit("get_data",command)
                
        self.socketio.start_background_task(target=self.communicateWithCentral)
        self.socketio.run(self.app)



    def communicateWithCentral(self):
        print("communicateWithCentral")
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
    abonnement = ["DATA"]
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = ["DATA","LOG"]


    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")
    CORS(app)

    
    
    IhmSupervisor(HOST, PORT, name, abonnement, app, socketio)

   
   
    
   

