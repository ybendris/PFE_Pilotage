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

    

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass

    """
    Fonction définissant les actions de la classe
    """
    def define_action(self):
        actions = [
            {"nom":"stop","function": self.stop},
            {"nom":"print_list","function": self.print_list},
            {"nom":"print_dict","function": self.print_dict},
            {"nom":"print_else","function": self.print_else},
            {"nom":"test_return_value","function": self.test_return_value},
            {"nom":"test_return_list","function": self.test_return_list},
            {"nom":"test_return_dict","function": self.test_return_dict}
            
        ]

        return actions

    def print_list(self, list):
        logging.info("print_list début")
        print(list["params"])
        logging.info("print_list fin")

    def print_dict(self, dict):
        logging.info("print_dict début")
        print(dict)
        logging.info("print_dict fin")
    
    def print_else(self, something):
        logging.info("print_else début")
        print(something)
        time.sleep(2)
        logging.info("print_else fin")

    def test_return_value(self):
        return 55

    def test_return_list(self):
        return ["test1", "test2"]

    def test_return_dict(self):
        return {"data1": "oui", "data2": "toto"}

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
                self.ask_action(destinataire='PROCEXEC', action="stop")

            if keypress and keypress == 'z':
                logging.info("Touche clavier 'z' appuyée")
                self.ask_action(destinataire='DATA_COLLECT', action="stop")

            if keypress and keypress == 'e':
                logging.info("Touche clavier 'e' appuyée")
                self.ask_action(destinataire='LOG_COLLECT', action="stop")

            if keypress and keypress == 'r':
                logging.info("Touche clavier 'r' appuyée")
                self.ask_action(destinataire='LOG_COLLECT', action="stop")

            if keypress and keypress == 't':
                logging.info("Touche clavier 't' appuyée")
                self.ask_action(destinataire='TEST2', action="stop")

            if keypress and keypress == 'y':
                logging.info("Touche clavier 'y' appuyée")
                self.ask_action(destinataire='TEST2', action="print_list", list_params=["wow"])

            if keypress and keypress == 'u':
                logging.info("Touche clavier 'u' appuyée")
                self.ask_action(destinataire='TEST2', action="print_dict")

            if keypress and keypress == 'i':
                logging.info("Touche clavier 'i' appuyée")
                self.ask_action(destinataire='TEST2', action="print_else")

            if keypress and keypress == 'o':
                logging.info("Touche clavier 'o' appuyée")
                self.waitfor(self.ask_action(destinataire='TEST2', action="print_else"),callback=self.stop)

            if keypress and keypress == 'p':
                logging.info("Touche clavier 'p' appuyée")
                self.ask_action(destinataire='HUB_SPV', action="getConnected")  

            if keypress and keypress == 's':
                logging.info("Touche clavier 's' appuyée")
                self.ask_action(destinataire='SINUS', action="dem_accelerate")  

            if keypress and keypress == 'd':
                logging.info("Touche clavier 's' appuyée")
                self.ask_action(destinataire='SINUS', action="dem_decelerate")  

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())
					
                    
            keypress = kb_func()
        logging.info("Service fini")


#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "TEST"
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