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
import socket
from threading import *
import numpy as np
import rdp as rdp

import pandas as pd
from pilotage_lib import NetworkItem, getBeginDateTime, kb_func

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

        self.reduce = True
        
        # Initialise Flask-CORS
        self.cors = CORS(self)

        # Initialise Flask-SocketIO
        self.socketio = SocketIO(self, cors_allowed_origins="*")

        # On défini les évênement sur lesquels on réagit ainsi que la fonction éxécutée
        self.socketio.on("send_command")(self.on_send_command)

        #Crée le thread daemon lançant le serveur
        self.thread_application = Thread(target=self.run_server, daemon=True)
        self.thread_application.start()

    def run_server(self):
        self.run()

    """
    Fonction qui gère la réception de data de la part du central
    """
    def traiterData(self, data):
        if self.reduce:
            data_to_reduce = data["msg"]
            points_reformed = np.array([[point['time'], point['data']] for point in data_to_reduce])
            df2 = pd.DataFrame(rdp.rdp(points_reformed, 1), columns=['time', 'data'])
            df2.to_dict(orient='records')

            data["msg"] = df2.to_dict(orient='records')
            self.socketio.emit("get_data",data)
        else:
            self.socketio.emit("get_data",data)

    """
    Fonction qui gère la réception de log de la part du central
    """
    def traiterLog(self, log):
        self.socketio.emit("get_log",log)

    """
    Fonction définissant les actions de la classe
    #TODO à compléter
    """
    def define_action(self):
        actions = [
            {"nom":"stop","function": self.stop},
            {"nom":"toggle_reduce","function": self.toggle_reduce}
        ]

        return actions

    """
    La fonction on_send_command() est un gestionnaire d'événement enregistré avec Flask-SocketIO. 
    Elle est appelée lorsqu'un événement "send_command" est reçu via WebSocket.
    Elle est chargé de transmettre la commande au central 
    
    Le paramètre command est un dict
    """
    def on_send_command(self, command):
        print('received message (send_command): ' , command)
        self.waitfor(id=self.ask_action(destinataire= command['destinataire'], action = command['action'], list_params=command['params']), callback=self.send_response_to_ihm)
       

    def send_response_to_ihm(self, response):
        print(response)
        self.socketio.emit("response", response)

   
    def toggle_reduce(self, message = None):
        self.reduce = not self.reduce

    """
    Processus principal du procExec
    """
    def service(self):
        
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                self.ask_action(action="recup_action",destinataire="CENTRAL")
                

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())
					
                    
            keypress = kb_func()
        logging.info("Service fini")


if __name__ == '__main__':
    logging.info('starting')
    
    name = "IHM"
    abonnement = ["DATA","LOG"]  
    
    app = IhmSupervisor(HOST, PORT, name, abonnement, __name__)
    
    app.service()
    app.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(app.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(app.read_thread.name))
    