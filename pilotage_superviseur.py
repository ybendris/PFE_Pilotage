#!/usr/bin/env python3


""" Nom du module : SelectorClient"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import random
import sys
import socket

from pilotage_entite import EntitePilotage

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class Superviseur(EntitePilotage):
    def service(self):
        print("SERVICE")
        while True:
            try:
                message = {}
                alea = random.randrange(2, 4)
                logging.info('LA VALEUR RANDOM VAUT : ' + str(alea))
                if alea == 1:
                    message["type"] = "CMD"
                    message["destinataire"] = "CAP"
                    message["msg"] = "Flux CMD"
                elif alea == 2:
                    message["type"] = 'DATA'
                    message["expediteur"] = self.name
                    message["msg"] = {"DATA1":"data1","DATA2":"data2","DATA3":"data3"}
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
    # class Superviseur qui hérite de EntitePilotage, qui redef service

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))

    # server.serve_forever()