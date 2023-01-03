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
import time

from pilotage_lib import NetworkItem, kb_func

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class Superviseur(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)
    
    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass
    
    """
    Fonction définissant les actions de la classe
    """
    def define_action(self):
        actions = [{"nom":"stop","function": self.stop}]
        return actions
    
    """
    Processus principal du Superviseur de test
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
           
            self.envoie_data_log_test()

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())		
                    
            keypress = kb_func()
        logging.info("Service fini")

    
    def envoie_data_log_test(self):
        alea = random.randrange(1,6)
        #logging.info('LA VALEUR RANDOM VAUT : ' + str(alea))
        if alea == 1:
            pass
        elif alea == 2:
            self.send_data(expediteur= self.name, paquet = "BEAT", dict_message={"DATA1":"data1","DATA2":"data2","DATA3":"data3"})
        elif alea == 3:
            self.send_data(expediteur= self.name, paquet = "ADVANCED", dict_message={"DATA4":"data4","DATA5":"data5","DATA6":"data6"})
        elif alea == 4:
            self.send_data(expediteur= self.name, paquet = "RECONSTRUCTED", dict_message={"DATA7":"data7","DATA8":"data8","DATA9":"data9"})
        else:
            niveauLogAlea = random.randrange(0, 8)
            self.send_log("Message du LOG", niveauLogAlea)

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []
    server = Superviseur(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class Superviseur qui hérite de NetworkItem, qui redef service
    server.service()

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))
