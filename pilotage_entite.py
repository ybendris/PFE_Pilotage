#!/usr/bin/env python3

""" Nom du module : SelectorClient"""
import time
from datetime import datetime

""" Description """
""" Version 2 """
""" Date : 03/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  ______________________________________________________ IMPORT _______________________________________________________
import sys
import logging
import socket
import random
import pickle
import threading
import json
from queue import Queue
from pilotage_lib import NetworkItem, send

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

BUFFER = Queue()


#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class EntitePilotage(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        self.name = name
        self.abonnement = abonnement
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(self.main_socket)
        try:
            self.main_socket.connect((host, port))
        except TimeoutError:
            sys.exit(1)

        NetworkItem.__init__(self, self.main_socket, self.abonnement)

        try:
            self.service()
        except KeyboardInterrupt:
            pass
            #close files

    def envoi_abonnement(self):
        print("envoi_abonnement")
        self.send_log("envoi_abonnement",2)
        message = {}
        print(message)
        try:
            message["expediteur"] = self.name
            message["msg"] = self.abonnement

            print(message)
            send(self.wfile, message)

        except Exception as e:
            print(e)
            # self.selector.unregister(conn)
            """obj.close(sock)"""
            # del self._buffer[self.main_socket]
            return False

    def getCurrentDateTime(self):
        currentDate = datetime.now()
        # dd/mm/YY H:M:S
        dt = currentDate.strftime("%d-%m-%Y %H:%M:%S")
        return dt


    def send_log(self, message, level):
        log = {}
        log["type"] = 'LOG'
        log["date/time"] = self.getCurrentDateTime()
        log["level"] = level
        log["msg"] = message
        self.queue_message_to_send.put(log)

    def service(self):
        pass



#  ________________________________________________ FONCTIONS GLOBALES _________________________________________________
def getBeginDateTime():
    a = datetime.now()
    print("DATE =", a)
    # dd/mm/YY H:M:S
    global dt_string
    dt_string = a.strftime("%d-%m-%Y_%H-%M-%S")
    print("date and time =", dt_string)

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []
    server = EntitePilotage(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class Superviseur qui hérite de EntitePilotage, qui redef service

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))

    # server.serve_forever()
