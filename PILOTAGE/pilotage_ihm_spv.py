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
            {"nom":"stop","function": self.stop}
        ]

        return actions

    """
    La fonction on_send_command() est un gestionnaire d'événement enregistré avec Flask-SocketIO. 
    Elle est appelée lorsqu'un événement "send_command" est reçu via WebSocket.
    Elle est chargé de transmettre la commande au central 
    
    Le paramètre command est un dict
    """
    def on_send_command(self, command):
        print('received message: ' + str(command))
        print(f'Running in thread {current_thread().name}')

        #TODO à compléter
        self.waitfor(id=self.ask_action(destinataire= command["destinataire"], action = command["action"], dict_message=command["msg"]), callback=self.test)
        

    def test(self, commande):
        print("REPONSE")  
        self.socketio.emit("command_response", commande)

    """
    Processus principal du procExec
    """
    def service(self):
        
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                print(f'Running in thread {current_thread().name}')

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
