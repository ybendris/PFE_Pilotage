#!/usr/bin/env python3


""" Nom du module : TestSendCommand"""

""" Description """
""" Version 1 """
""" Date : 28/12/2022"""
""" Auteur : Yannis """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import random
import sys
import socket
import time

from pilotage_lib import NetworkItem, kb_func

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class TestSendCommand(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)

    def traiterCommande(self, commande):
        pass

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass



    """
    Processus principal du TestSendCommand
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                self.send_cmd(destinataire='PROCEXEC', action="stop")

            if keypress and keypress == 'z':
                logging.info("Touche clavier 'z' appuyée")
                self.send_cmd(destinataire='DATA_COLLECT', action="stop")

            if keypress and keypress == 'e':
                logging.info("Touche clavier 'e' appuyée")
                self.send_cmd(destinataire='LOG_COLLECT', action="stop")

            if keypress and keypress == 'w':
                logging.info("Touche clavier 'e' appuyée")
                self.send_cmd(destinataire='LOG_COLLECT', action="stop")

            #Réception
            self.traiterMessage(self.getMessage())
					
                    
            keypress = kb_func()
        logging.info("Service fini")


#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "TestSendCommand"
    abonnement = []
    test = TestSendCommand(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class TestSendCommand qui hérite de NetworkItem, qui redef service
    test.service()

    test.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(test.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(test.read_thread.name))

    # server.serve_forever()