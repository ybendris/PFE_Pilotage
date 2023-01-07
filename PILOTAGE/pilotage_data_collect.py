""" Nom du module : Data_Collect"""

""" Description """
""" Version 2 """
""" Date : 07/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

from collections import deque
import socket
import logging

from pilotage_lib import NetworkItem, getBeginDateTime, kb_func, Collecteur

HOST = 'localhost'
PORT = 65432
#SESSION_NAME = ''
#dt_string = ''

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class DataCollect(NetworkItem, Collecteur):
    def __init__(self, host, port, name, abonnement, dt_string):
        Collecteur.__init__(self, repertoire="CSV_DATA", date=dt_string, typeDonnees="DATA")     
        NetworkItem.__init__(self, host, port, name, abonnement)
         

    def service(self):
        """
        Exécute le service principal du DataCollect.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        logging.info("Service DataCollect lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                logging.info(f"Le nom de la session est {self.session}")
            
            if keypress and keypress == 'z':
                logging.info("Touche clavier 'z' appuyée")
                logging.info(self.data_dict)

            if keypress and keypress == 'e':
                logging.info("Touche clavier 'e' appuyée")
                self.write_to_csv()

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()
        
        self.write_to_csv()
        logging.info("Service fini")
       
    
    def traiterData(self, data):
        """
        Traite les données reçues.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            data (dict): Les données à traiter.

        Returns:
            None
        """
        origine = data["expediteur"]
        paquet = data["paquet"]
        separateur = "_"
        cle = origine + separateur + paquet
        
        if cle not in self.data_dict:
            self.data_dict[cle] = deque()
        self.data_dict[cle].append(data["msg"])

      
    def traiterLog(self, log):
        """
        Traite les log reçues.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            log (dict): Les log à traiter.

        Returns:
            None
        """
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")

    def define_action(self):
        actions = [
            {"nom":"setNomSession", "function": self.setNomSession},
            {"nom":"writeDataCSV", "function": self.write_to_csv},
            {"nom":"stop","function": self.stop}
        ]
        return actions



if __name__ == '__main__':
    logging.info('starting')
    name = "DATA_COLLECT"
    dt_string = getBeginDateTime()
    abonnement = ["DATA"]
    data_collect = DataCollect(HOST, PORT, name, abonnement, dt_string)

    data_collect.service()
    data_collect.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(data_collect.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(data_collect.read_thread.name))
