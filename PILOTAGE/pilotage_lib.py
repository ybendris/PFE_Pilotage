""" Nom du module : Librairie"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import msvcrt
import os
import queue
import threading
from datetime import datetime
from queue import Queue, Empty
import logging
import json
import socket
import sys
import pandas as pd

from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class NetworkItem(ABC):
    def __init__(self, host, port, name, abonnement):
        """Socket TCP permettant la connexion avec le Central."""
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """File object dans lequel la réponse est lue."""
        self.rfile = self.main_socket.makefile("rb", -1)
        """File object à partir duquel la requête est envoyée."""
        self.wfile = self.main_socket.makefile("wb", 0)
        """Liste des abonnements du client actuel à envoyer au central"""
        self.abonnement = abonnement
        """Flag permettant de stopper la fonction de service"""
        self.running = True
        """Nom sous forme de chaîne de caractère à communiquer au Central pour qu’il puisse rediriger les commandes."""
        self.name = name
        """Liste des actions, chaque action est un dictionnaire contenant le nom et l'object callable"""
        self.actions = [] #Initialisation d'une liste vide
        self.actions = self.define_action()
        """Dictionnaire contenant les fonctions de callback à éxécuter lors de la réception d’une réponse"""
        self._waitfor = {}
        """Entier permettant de générer les ID des messages"""
        self.no_msg = 0
        """Queue “ThreadSafe” servant de buffer de message à envoyer au Central."""
        self.queue_message_to_send = Queue()
        """Queue “ThreadSafe” servant de buffer de message à reçu de la part du Centra"""
        self.queue_message_to_process = Queue()

        try:
            self.main_socket.connect((host, port))
        except TimeoutError:
            sys.exit(1)

        #Envoie des abonnements dans l'init
        self.envoi_abonnement()

        #Envoie des actions dans l'init
        self.envoi_actions()

        #Crée le thread d'écriture
        self.write_thread = ThreadEcriture(self.wfile, "ThreadEcriture", self.queue_message_to_send)
        self.write_thread.start()

        # Crée le thread de lecture
        self.read_thread = ThreadLecture(self.rfile, "ThreadLecture", self.queue_message_to_process)
        self.read_thread.start()


    """
    Cette fonction est à redéfinir pour chaque processus héritant de NetworkItem
    """
    @abstractmethod
    def traiterData(self, data):
        pass


    """
    Cette fonction est à redéfinir pour chaque processus héritant de NetworkItem
    """
    @abstractmethod
    def traiterLog(self, log):
        pass


    """
    Cette fonction est à redéfinir pour chaque processus héritant de NetworkItem
    """
    @abstractmethod
    def service(self):
        pass


    """
    Cette fonction doit être redéfini pour chaque processus héritant de NetworkItem
    """
    @abstractmethod
    def define_action(self):
        pass


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

    
    """
    Cette fonction est conçue pour traiter les messages reçus de type CMD. 
    En fonction de la clé 'action' dans l'attribut commande_dict on sait si on a une réponse ou une requête
    Cette fonction traite les réponses comme ceci:
        Si on a un compte rendu (cr) à faux, on envoit un LOG
        Si on a une réponse attendu valide, on éxécute la fonction de callback que l'élément à spécifié dans self.waitfor
        Sinon on ne sait pas ce que c'est, on envoit un LOG

    Cette fonction traite les commandes de cette façon:
        Vérifie que l'on a une action valide (action dans la liste des actions), si c'est le cas on 
        éxécute la fonction de callback que l'élément à spécifié dans self.define_action
    """
    def traiterCommande(self, commande_dict):
        commande_id = commande_dict.get("id")
        commande_action = commande_dict.get("action")
        commande_msg = commande_dict.get("msg")
        commande_params = commande_dict.get("params")

        #Traitement des commandes identifiées comme des réponses
        if commande_action == "answer":
            if 'cr' in commande_dict and commande_dict['cr']==False: #On a une réponse attendu mais avec un compte rendu faux
                del self._waitfor[commande_id] #On n'attend plus de réponse avec cet id
                logging.info("Erreur dans l'éxécution de la commande")

            if commande_id in self._waitfor: #Si c'est une réponse attendue, on éxécute la fonction de callback que l'élément courant a précisé
                logging.info(f"La commande ID: {commande_id} attendait une réponse, elle est arrivée")
                wait = self._waitfor[commande_id]
                #logging.info(f"wait: {wait}")
                del self._waitfor[commande_id] #On n'attend plus de réponse avec cet id
                func_callback = wait["callback"] 
                logging.info(f"commande_msg: {commande_msg}")  
                
                #TODO tester les différents cas (à savoir que commande_msg est déjà un dict vide par défaut )

                if isinstance(commande_msg, dict):
                    logging.info("isinstance(commande_msg, dict)")
                    func_callback(**commande_msg)
                elif isinstance(commande_msg, list):
                    logging.info("isinstance(commande_msg, list)")
                    func_callback(*commande_msg)
                else:
                    logging.info("ELSE")
                    func_callback(commande_msg)

        #Traitement des commandes identifiées comme des requêtes valides (dans les actions)
        elif commande_action in self.get_action():
            action_callable = self.get_action_callback(commande_action)
            if action_callable is not None:
                self.reply(request=commande_dict, answer=action_callable(*commande_params))

        #Traitement des commandes non identifiées arrivant
        else:
            logging.info("Commande non reconnue")
        
    
    """
    Fonction permettant d'envoyer la réponse 'answer' à la requête 'request'
    via la fonction d'envoie de commande 'sens_cmd'
    La réponse envoyée possède le même ID que la requête pour que le destinataire puisse reconnaitre la réponse à sa requête
    """
    def reply(self, request, answer):
        logging.info(f"reply to = {request}")
        if answer is not None:
            return self.send_cmd(id = request["id"], destinataire = request["expediteur"], action='answer', message=answer)
        else:
            return self.send_cmd(id = request["id"], destinataire = request["expediteur"], action='answer')
    

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
        log["expediteur"] = self.name
        log["msg"] = message
        logging.info(f"Log envoyé :{log}")
        self.queue_message_to_send.put(log)


    """
    Créer un identifiant sous forme de chaine de caractère:
    Il s'agit d'un nombre entier avec un minimum de 4 chiffres (si le nombre est inférieur à 4 chiffres, il est complété avec des zéros).
    La valeur de self.no_msg est utilisé pour ce formatage.
    Le nom self.name est concaté à cette chaine    
    """
    def idauto(self):
        self.no_msg += 1
        return "{:04d}{}".format(self.no_msg, self.name)


    """
    Fonction permettant d'envoyer la réponse 'answer' à la requête 'request'
    via la fonction d'envoie de commande 'send_cmd'
    La requête envoyée possède un ID généré via la fonction self.idauto
    """
    def ask_action(self, destinataire, action, list_params = [], dict_message = {}):
        id = self.idauto()
        self.send_cmd(destinataire, action, id, list_params, dict_message)
        return id	


    """
    Fonction permettant d'envoyer une commande en précisant:
        le destinataire
        l'action
        l'id,
        les paramètres #TODO à vérifier
        Le message en lui même sous forme de dictionnaire
    """
    def send_cmd(self, destinataire, action, id, list_params = [], message = None):
        commande = {}
        commande["id"] = id
        commande["type"] = "CMD"
        commande["action"] = action
        commande["expediteur"] = self.name
        commande["destinataire"] = destinataire
        commande["params"] = list_params
        commande["msg"] = message

        #logging.info(f"Commande envoyée :{commande}")
        self.queue_message_to_send.put(commande)
        return id


    """
    Fonction permettant d'envoyer des données en présisant
        l'expéditeur
        le nom du paquet
        Le message en lui même sous forme de dictionnaire contenant les données
    """
    def send_data(self, expediteur, paquet, dict_message):
        data = {}
        data["type"] = 'DATA'
        data["expediteur"] = expediteur
        data["paquet"] = paquet
        data["msg"] = dict_message
        #logging.info(f"Data envoyée :{data}")
        self.queue_message_to_send.put(data)


    """
    Fonction permettant de définir une fonction de callback à éxécuter quand la réponse à une précédente requête envoyée arrive
    Chaque fonction est enregistrée dans un dictionnaire à la clé 'callback'
    Chaque dictionnaire comprenant une fonction est rangé dans un dictionnaire à la clé 'id'
    """
    def waitfor(self, id, callback):
        self._waitfor[id] = {'callback':callback}
    

    """
    Renvoie la liste des actions de l'entité courrante, envoie seulement l'attribut 'nom'
    """
    def get_action(self):
        if self.actions is None:
            return []

        list_actions = []
        for action in self.actions:
            #print(action)
            list_actions.append(action['nom'])

        return list_actions


    """
    Récupère l'object de type callable, dans la structure de données self.actions
    Si le message_action n'est pas référencé dans le dictionnaire des actions en renvoie None
    """
    def get_action_callback(self,message_action):
        if self.actions is None:
            return None

        for action_dict in self.actions:
            if action_dict.get("nom") == message_action:
                return action_dict.get("function")
        return None

    """
    Fonction permettant de mettre le flag 'running' à False,
    """
    def stop(self, commande):
        self.running = False
        return "STOP"


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


class Collecteur:
    def __init__(self, repertoire, date, typeDonnees, session="default"):
        self.repertoire = repertoire
        try:
            os.mkdir(self.repertoire)
        except FileExistsError:
            pass

        self.datetime = date
        self.session = session
        self.data_dict = {}
        self.typeDonnees = typeDonnees


    def setNomSession(self, param):
        self.session=param
        print("NOM DE LA SESSION : " + self.session)

    
    def write_to_csv(self, param):
        for cles in self.data_dict.keys():
            attributs = self.data_dict[cles][0].keys()
            dataframe = pd.DataFrame(self.data_dict[cles], columns=attributs)
           
            if self.typeDonnees == "DATA":
                format_string = "{}/{}_{}{}{}_{}.csv"
                filename = format_string.format(self.repertoire, self.typeDonnees, self.session, '-' if self.session else '', cles, self.datetime)
            elif self.typeDonnees == "LOG":
                format_string = "{}/{}_{}{}{}.csv"
                filename = format_string.format(self.repertoire, self.typeDonnees, self.session, '-' if self.session else '', self.datetime)

            dataframe.to_csv(filename, sep=';', decimal=',', index=False)



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
