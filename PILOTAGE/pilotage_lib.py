#!/usr/bin/env python3

""" Nom du module : Librairie"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import msvcrt
import queue
import threading
from datetime import datetime
from queue import Queue, Empty
import logging
import json
import socket
import sys
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class NetworkItem(ABC):
    def __init__(self, host, port, name, abonnement):
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wfile = self.main_socket.makefile("wb", 0)
        self.rfile = self.main_socket.makefile("rb", -1)
        self.abonnement = abonnement
        self.running = True
        self.name = name
        self.actions = self.define_action()

        self._waitfor = {}
        self.no_msg = 0

        self.queue_message_to_send = Queue()
        self.queue_message_to_process = Queue()

        try:
            self.main_socket.connect((host, port))
        except TimeoutError:
            sys.exit(1)

        self.envoi_abonnement()

        self.envoi_actions()

        #Crée le thread d'écriture
        self.write_thread = ThreadEcriture(self.wfile, "ThreadEcriture", self.queue_message_to_send)
        self.write_thread.start()

        # Crée le thread de lecture
        self.read_thread = ThreadLecture(self.rfile, "ThreadLecture", self.queue_message_to_process)
        self.read_thread.start()

        """try:
            self.service()
        except KeyboardInterrupt:
            pass"""
            
    """
    Envoie les abonnements d'une entité lorsque celle-ci se connecte au central
    """
    def envoi_abonnement(self):
        print("envoi_abonnement")
        self.send_log("envoi_abonnement", 2)
        message = {}
        print(message)
        try:
            message["expediteur"] = self.name
            message["msg"] = self.abonnement

            print(message)
            send(self.wfile, message)

        except Exception as e:
            print(e)
            # self.selector.unregister(conn)
            """obj.close(sock)"""
            # del self._buffer[self.main_socket]
            return False

    """
    Envoie les actions d'une entité lorsque celle-ci se connecte au central
    """
    def envoi_actions(self):
        print("envoi_actions")
        self.send_log("envoi_actions", 2)
        message = {}
        print(message)
        try:
            message["expediteur"] = self.name
            message["msg"] = self.get_action()

            print(message)
            send(self.wfile, message)

        except Exception as e:
            print(e)
            # self.selector.unregister(conn)
            """obj.close(sock)"""
            # del self._buffer[self.main_socket]
            return False


    """
    Récupère la date et l'heure actuelle
    
    Return
    ------
    
    la date et l'heure
    """
    def getCurrentDateTime(self):
        currentDate = datetime.now()
        # dd/mm/YY H:M:S
        #On formate la date et l'heure
        dt = currentDate.strftime("%d-%m-%Y %H:%M:%S")
        return dt


    """
    Essayer de récupérer un message de la file d'attente. 
    Cet appel va lever une exception queue.Empty si la file est vide.
    Cette fonction est non bloquante,
    """
    def getMessage(self):
        try:
            message = self.queue_message_to_process.get(block=False)
            return message
        except queue.Empty:
            #print("Queue empty")
            return None

    """
    Cette fonction est conçue pour traiter différents types de messages reçus par un élément Client de la partie pilotage. 
    Selon le type de message, la fonction appelle une autre fonction spécifique pour traiter le message.
    TODO, Ces fonctions sont redéfinies dans les Classes héritant de NetworkItem
    """
    def traiterMessage(self, message):
        if message is not None:
            logging.info(f"Message reçu :{message}")
            message_type = message.get("type")
            if message_type == "CMD":
                self.traiterCommande(message)
            elif message_type == "LOG":
                self.traiterLog(message)
            elif message_type == "DATA":
                self.traiterData(message)

    
    def traiterCommande(self, commande):
        commande_id = commande.get("id")
        commande_action = commande.get("action")

        if commande_id in self._waitfor: #Si c'est une réponse à un message attendu
            func_callback = self._waitfor[commande_id]["callback"]
            func_callback()
        elif commande_action in self.get_action(): 
            action_callback = self.get_action_callback(commande_action)
            action_callback(commande) 
        else:
            logging.info("Commande non reconnue")

    @abstractmethod
    def traiterData(self, data):
        pass

    @abstractmethod
    def traiterLog(self, log):
        pass
       

    """
    Fonction d'envoie de log
    
    Paramètres
    ----------
    message : le message du log
    level : le niveau du log
    """
    def send_log(self, message, level):
        log = {}
        log["type"] = 'LOG'
        log["date/time"] = self.getCurrentDateTime()
        log["level"] = level
        log["msg"] = message
        print(log)
        self.queue_message_to_send.put(log)

    """
    Crée un identifiant sous forme de chaine de caractère:
    Il s'agit d'un nombre entier avec un minimum de 4 chiffres (si le nombre est inférieur à 4 chiffres, il est complété avec des zéros).
    La valeur de self.no_msg est utilisé pour ce formatage.
    Le nom self.name est concaté à cette chaine    
    """
    def idauto(self):
        self.no_msg += 1
        return "{:04d}{}".format(self.no_msg, self.name)

    def send_cmd(self, destinataire, action, list_params = [], dict_message = {}):
        id = self.idauto()
        commande = {}
        commande["type"] = "CMD"
        commande["action"] = action
        commande["destinataire"] = destinataire
        commande["params"] = list_params
        commande["msg"] = dict_message

        print(commande)
        self.queue_message_to_send.put(commande)
        return id

    def send_data(self, expediteur, paquet, dict_message):
        data = {}
        data["type"] = 'DATA'
        data["expediteur"] = expediteur
        data["paquet"] = paquet
        data["msg"] = dict_message
        print(data)
        self.queue_message_to_send.put(data)

    def waitfor(self, id, callback):
        self._waitfor[id] = {'callback':callback}
    

    """
    Cette fonction est redéfini pour chaque processus
    """
    @abstractmethod
    def service(self):
        pass



    def define_action(self):
        return []

    """
    Renvoie la liste des actions de l'entité courrante, envoie seulement l'attribut 'nom'
    """
    def get_action(self):
        list_actions = []
        for action in self.actions:
            #print(action)
            list_actions.append(action['nom'])

        return list_actions


    """
    Récupère l'object de type callable, dans la structure de données self.actions
    """
    def get_action_callback(self,message_action):
        for action_dict in self.actions:
            if action_dict.get("nom") == message_action:
                return action_dict.get("function")


    


    def stop(self, commande):
        self.running = False

    """
    Fonction permettant de lancer la fonction de service dans un thread daemon
    Utilisé lorsque le thread principal est maintenu actif par un autre traitement que la fonction de service
    """
    def serviceInDaemonThread(self):
        threadService = threading.Thread(target=self.service,daemon=True)
        threadService.start()
        return threadService

class ThreadLecture(threading.Thread):
    def __init__(self, rfile, name, queue):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.rfile = rfile
        self.queue_message_to_process = queue

    def run(self):

        logging.info("{} started".format(self.name))
        while True:

            try:
                message_received = receive(self.rfile)  # object json
                if message_received:
                    #logging.info("Received: {}".format(message_received))
                    self.queue_message_to_process.put(message_received)
            except Exception as e:
                logging.info("{} ended with exception: {}".format(self.name, e))
                break


class ThreadEcriture(threading.Thread):
    def __init__(self, wfile, name, queue):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.wfile = wfile
        self.queue_message_to_send = queue

    # Everything inside of run is executed in a seperate thread
    def run(self):
        logging.info("{} started".format(self.name))
        while True:
            try:

                message_to_send = self.queue_message_to_send.get()
                send(self.wfile, message_to_send)
                #logging.info("Sent: {}".format(message_to_send))


            except Empty as e:
                logging.info("{} ended with exception: {}".format(self.name, e))
                break



#  ________________________________________________ FONCTIONS GLOBALES _________________________________________________
def getBeginDateTime():
    a = datetime.now()
    print("DATE =", a)
    # dd/mm/YY H:M:S
    dt_string = a.strftime("%d-%m-%Y_%H-%M-%S")
    print("date and time =", dt_string)
    return dt_string

"""
La fonction vérifie si une touche a été appuyée en utilisant la fonction kbhit de l'interface msvcrt. 
Si c'est le cas, la fonction essaie de décoder la touche appuyée en utilisant la fonction getch de l'interface msvcrt et de la renvoyer sous forme de chaîne de caractères. 
Si une exception est levée lors de la décodage, elle est simplement ignorée et la fonction ne renvoie rien.
Notez que cette fonction ne sera probablement pas compatible avec d'autres interfaces de terminal ou sur des systèmes d'exploitation différents de Windows.
"""
def kb_func():
    if msvcrt.kbhit():
        try:
            ret = msvcrt.getch().decode()
            return ret
        except:
            pass

"""
Fonction de réception de message

Paramètre
---------
rfile : fichier de lecture de la socket
"""
def receive(rfile):
    msg_encoded = rfile.readline().strip()
    msg_str = msg_encoded.decode("utf-8")
    msg_decoded = json.loads(msg_str)
    return msg_decoded

"""
Fonction d'émission de message

Paramètres
----------
wfile : fichier d'écriture de la socket
message : le message à envoyer
"""
def send(wfile, message):
    #print("send")
    if message:
        str_message = json.dumps(message)
        bytes_message = bytes(str_message, encoding="utf-8")
        wfile.write(bytes_message + b"\n")
