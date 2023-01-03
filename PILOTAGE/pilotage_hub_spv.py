""" Nom du module : HubSupervisor"""

""" Description Le superviseur du Hub, il peut communiquer avec le central"""
""" Version 1 """
""" Date : 03/01/2023"""
""" Auteur : Equipe CEIS """
""""""


#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import socket
import serial.tools.list_ports
from pilotage_lib import NetworkItem, kb_func

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

"""
Elle permet l’identification des instruments connectés et la mémorisation des adresses
"""
class HubSPV(NetworkItem):
    def __init__(self, host, port, name, abonnement, proc_dir):
        NetworkItem.__init__(self, host, port, name, abonnement)

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass

    """
    TODO
    Fonction permettant de récupérer les instruments connectés
    Entrée:
        self (objet courant)
    Traitement:
        Récupère tout les périphériques connecté en série et utilise les id pour reconnaitre les instruments
    Sortie:
        La liste des instruments connectés avec leur adresse
    """
    def getConnect(self):
        port_data = []
        for port in serial.tools.list_ports.comports():
            info = dict({"Name": port.name, "Description": port.description, "Manufacturer": port.manufacturer,
                 "Hwid": port.hwid})
            port_data.append(info)
        print (port_data)

    """
    Fonction définissant les actions du superviseur du Hub
    """
    def define_action(self):
        actions = [{"nom":"getConnect","function": self.getConnect},{"nom":"stop","function": self.stop}]
        return actions



    """
    Processus principal du superviseur du Hub
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()
        logging.info("Service fini")


#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "HUB_SPV"
    abonnement = []

   
    hub_spv = HubSPV(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class HubSPV qui hérite de NetworkItem, qui redef service
    HubSPV.service()

    HubSPV.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(HubSPV.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(HubSPV.read_thread.name))