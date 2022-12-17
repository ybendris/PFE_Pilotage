#!/usr/bin/env python3


""" Nom du module : ProcEXE"""

""" Description """
""" Version 1 """
""" Date : 17/12/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import glob
import logging
import queue
import random
import sys
import socket
import time

from pilotage_lib import NetworkItem

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

"""
Elle permet l’exécution séquentielle de commandes issues de fichiers textes.
"""
class ProcExec(NetworkItem):
    def __init__(self, host, port, name, abonnement, proc_dir):
        NetworkItem.__init__(self, host, port, name, abonnement)
        self.proc2exec = []
        self.encours = None
        self.proc_dir = proc_dir
        self.proc_list = self.list_procedures()


    """
    Liste l'ensemble des fichiers de procédures disponibles dans le répertoire proc_dir.

    Le nom d'un fichier de procédure est écrit sous la forme:
    “proc*.txt”

    Retourne une liste contenant les noms de tous les fichiers de procédures.
    """
    def list_procedures(self):
        return glob.glob("proc*.txt", root_dir=self.proc_dir)

    """
    Processus principal du procExec
    """
    def service(self):
        while True:
            commande = self.getCommande()
            if commande is not None:
                logging.info(f"commande reçu :{commande}")

            time.sleep(0.1)

    """
    Essayer de récupérer un élément de la file d'attente. 
    Cet appel va lever une exception queue.Empty si la file est vide.
    """
    def getCommande(self):
        try:
            commande = self.queue_message_to_process.get(block=False)
            return commande
        except queue.Empty:
            print("Queue empty")
            return None

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []
    server = ProcExec(host=HOST, port=PORT, name=name, abonnement=abonnement, proc_dir="./Procedures")
    # class Superviseur qui hérite de NetworkItem, qui redef service
    server.service()

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))

    # server.serve_forever()