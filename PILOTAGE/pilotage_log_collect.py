""" Nom du module : Log_Collect"""

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
header = ['date/time', 'level', 'msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class LogCollector(NetworkItem, Collecteur):
    def __init__(self, host, port, name, abonnement, dt_string):
        Collecteur.__init__(self, repertoire="CSV_LOG", date=dt_string, typeDonnees="LOG")
        NetworkItem.__init__(self, host, port, name, abonnement)
   
    
    def service(self):
        """
        Fonction principal du log_collect
        Reçoit les messages (LOG ou CMD) et enregistre les logs dans une structure de données
        """
        logging.info("Service global lancé")
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
        logging.info("Service fini")


    def traiterData(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")

    def traiterLog(self, log):
        cle = self.datetime
        
        if cle not in self.data_dict:
            self.data_dict[cle] = deque()

        self.data_dict[cle].append(log)


    def define_action(self):
        actions = [
            {"nom":"setNomSession","function": self.setNomSession},
            {"nom":"writeDataCSV", "function": self.write_to_csv},
            {"nom":"stop","function": self.stop}
        ]
        return actions

if __name__ == '__main__':
    logging.info('starting')
    name = "LOG_COLLECT" #sys.argv[1]
    #SESSION_NAME = sys.argv[2]
    dt_string = getBeginDateTime()
    abonnement = ["LOG"]
    logCollect = LogCollector(HOST, PORT, name, abonnement, dt_string)
    
    logCollect.service()
    logCollect.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(logCollect.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(logCollect.read_thread.name))

    
