#!/usr/bin/env python3


""" Nom du module : Superviseur"""

""" Description """
""" Version 1 """
""" Date : 10/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import random
import sys
import socket

from pilotage_lib import NetworkItem

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class Superviseur(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)


    """
    Processus principal du superviseur
    Utilisé pour réalsier des tests
    """
    def service(self):
        print("SERVICE")
        i = 0
        while True:
            i+=1
            print(f"--------------{i}")
            try:
                message = {}
                alea = random.randrange(2, 6)
                #logging.info('LA VALEUR RANDOM VAUT : ' + str(alea))
                if alea == 1:
                    message["type"] = "CMD"
                    message["destinataire"] = "CAP"
                    message["msg"] = "Flux CMD"
                elif alea == 2:
                    message["type"] = 'DATA'
                    message["expediteur"] = self.name
                    message["paquet"] = "BEAT"
                    message["msg"] = {"DATA1":"data1","DATA2":"data2","DATA3":"data3"}
                elif alea == 3:
                    message["type"] = 'DATA'
                    message["expediteur"] = self.name
                    message["paquet"] = "ADVANCED"
                    message["msg"] = {"DATA4":"data4","DATA5":"data5","DATA6":"data6"}
                elif alea == 4:
                    message["type"] = 'DATA'
                    message["expediteur"] = self.name
                    message["paquet"] = "RECONSTRUCTED"
                    message["msg"] = {"DATA7":"data7","DATA8":"data8","DATA9":"data9"}
                else:
                    niveauLogAlea = random.randrange(0, 8)
                    self.send_log("Message du LOG", niveauLogAlea)
                self.queue_message_to_send.put(message)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                break


#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []
    server = Superviseur(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class Superviseur qui hérite de NetworkItem, qui redef service

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))

    # server.serve_forever()