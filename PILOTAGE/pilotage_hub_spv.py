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
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass

    """
    Fonction permettant de récupérer les instruments connectés et leur adresse pour communiquer
    Entrée:
        self (objet courant)
    Traitement:
        Récupère tout les périphériques connecté en série et utilise les id pour reconnaitre les instruments
    Sortie:
        La liste des instruments connectés avec leur adresse
    """
    def getConnected(self,message):
        #tableau qui contiendra les adresses et noms des instruments connectés
        port_data = []
        #On parcourt tout les périphériques connectés en série (COM)
        for port in serial.tools.list_ports.comports():
            info=""
            #Si l'hardware Id correspond à celui de l'adaptateur du CAP on l'ajoute au tableau
            if port.hwid == "USB VID:PID=0403:6001 SER=A104GC9LA":
                info = dict({"Name": "CAP", "Adresse": port.name})
                print("CAP")
            #Si l'hardware Id correspond à celui de l'adaptateur du BAP on l'ajoute au tableau
            elif port.hwid == "USB VID:PID=0403:6001 SER=A100TL08A":
                info = dict({"Name": "BAP", "Adresse": port.name})
            if info != "":
                port_data.append(info)
        #TODO ajouter la récupération des périphériques USB
        #affichage du tableau obtenu pour débuggage
        print (port_data)
        return port_data

    """
    Fonction définissant les actions du superviseur du Hub
    """
    def define_action(self):
        actions = [{"nom":"getConnected","function": self.getConnected},{"nom":"stop","function": self.stop}]
        return actions



    """
    Processus principal du superviseur du Hub
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
    name = "HUB_SPV"
    abonnement = []

   
    hub_spv = HubSPV(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class HubSPV qui hérite de NetworkItem, qui redef service
    hub_spv.service()

    hub_spv.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(hub_spv.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(hub_spv.read_thread.name))