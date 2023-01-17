""" Nom du module : HubSupervisor"""

""" Description Le superviseur du BAP, il peut communiquer avec le central"""
""" Version 1 """
""" Date : 16/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________
import logging
import socket
from pilotage_lib import NetworkItem, kb_func

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class SPV_BAP(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass


    """
    Fonction définissant les actions du superviseur du BAP
    """
    def define_action(self):
        actions = [{"nom":"stop","function": self.stop}]
        return actions

    """
    Processus principal du superviseur du BAP
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers


            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()
        logging.info("Service fini")

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "SPV_BAP"
    abonnement = []

   
    BAP = SPV_BAP(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class SPV_BAP qui hérite de NetworkItem, qui redef service
    BAP.service()

    #fermeture de la socket après arrêt de service
    BAP.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(BAP.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(BAP.read_thread.name))