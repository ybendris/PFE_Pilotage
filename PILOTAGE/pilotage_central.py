""" Nom du module : Centrale"""

""" Description """
""" Version 2 """
""" Date : 03/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import pprint
import socket
import socketserver
import threading
import json
from queue import Queue
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
event = threading.Event()


class Central(socketserver.ThreadingMixIn, socketserver.TCPServer):
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingMixIn.daemon_threads = True


    def __init__(self, server_address, request_handler_class):
        socketserver.TCPServer.__init__(self, server_address, request_handler_class)
        self.name = "CENTRAL"
        self._abonnement = {
            'DATA': [],
            'LOG': []
        }
        self._actions = {}
        self._wfile = {}
        self.daemon_threads = True
        self.current_peers = []
        self.messageQueue= Queue()
        self.name_to_fillno = {}
        self.consumer_thread = threading.Thread(target=self.redirect_message, daemon=True, args=(self.messageQueue,))
        self.consumer_thread.start()

    def server_bind(self):
        """Called by constructor to bind the socket.
            overridded.
        """
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        #logging.info("Socket binded")
        self.server_address = self.socket.getsockname()

    """
    Enregistre les abonnements d'une entité
    """
    def setAbonnements(self, fillno, type):
        self._abonnement[type].append(fillno)
        self.send_log("{} : Subcriptions = {} ".format(self.name,self._abonnement), 6)

    """
    Enregistre les actions d'une entité
    """
    def setActions(self, expediteur, action):
        self._actions[expediteur]= action
        self.send_log("{} : Actions = {} ".format(self.name, self._actions), 6)

    """
    Enregistre le file writer de l'entité qui s'est connectée
    """
    def setWFile(self, fileno, wfile):
        self._wfile[fileno] = wfile
        self.send_log("{} : file writer add for {}".format(self.name, self.fileno), 6)
        #print(self._wfile)

    """
    Récupère les abonnements de toutes entités connectées
    """
    def getAbonnements(self):
        return self._abonnement

    """
    Récupère les actions de toutes entités connectées
    """
    def getActions(self):
        return self._actions

    def server_activate(self):
        """Called by constructor to activate the server.
            overridded
        """
        logging.info("Server is listening...")
        """request_queue_size = nombre de connexion en attente possible"""
        self.socket.listen(self.request_queue_size)

    """
    Ajoute un client à la liste self.current_peers et envoie des logs de l'ajout et de la taille de la liste.
    
    Ajoute un client à la liste self.current_peers et envoie des logs annonçant l'ajout et la taille actuelle de la liste des clients.
    
    Parameters:
    client_to_add (object): le client à ajouter à la liste self.current_peers.
    
    Returns:
    None
    """

    def add_client(self, client_to_add):
        self.current_peers.append(client_to_add)
        self.send_log("{} : client added ".format(self.name), 6)
        self.send_log("{} : Amount of clients : {}".format(self.name, len(self.current_peers)), 6)
        #logging.info("Nb connecté :{}".format(len(self.current_peers)))

    """
    Supprime un client de la liste des clients connectés et de ses abonnements.

    Les données associées au client, telles que ses abonnements et ses actions, sont également supprimées.
    Envoie un log pour signaler la suppression du client.

    Parameters:
    client_to_delete (Client): le client à supprimer.

    Returns:
    None
    """
    def delete_client(self, client_to_delete):
        # On supprime le client de la liste des clients connectés
        self.current_peers.remove(client_to_delete)
        # On supprime également ses abonnements
        for abonnement in self._abonnement:
            try:
                self._abonnement[abonnement].remove(client_to_delete.fileno())
            except ValueError:
                pass

        del self._wfile[client_to_delete.fileno()]
        # On supprime aussi ses actions
        for key, value in self.name_to_fillno.items():
            if value == client_to_delete.fileno():
                del self._actions[key]

        self.send_log("{} : {} removed".format(self.name, client_to_delete), 6)


    """
    Redirige le message vers un client spécifique ou vers tous les clients concernés.

    La fonction reçoit une file d'attente de messages, met le message en file d'attente, le sérialise 
    et l'envoie au destinataire.
    Le message peut être de type LOG, DATA ou CMD.

    Pour les types LOG et DATA, le message est envoyé à tous les clients abonnés à ces types.
    Pour le type CMD, le message est envoyé au destinataire spécifique mentionné dans le message, 
    ou une réponse est envoyée à l'expéditeur si le destinataire est le serveur central.

    Si le destinataire n'est pas connecté, un message de journal est envoyé au serveur. S'il y a une exception, 
    le message d'exception est également enregistré.

    Parameters :
    queue (queue) : La file d'attente de messages à partir de laquelle le message doit être retiré de la file d'attente.
    """
    def redirect_message(self, queue):
        #print("consumer")
        while True:
            deserialized_message = queue.get()
            message_type = deserialized_message.get("type")

            #logging.info(f"- dequeued message: {deserialized_message}")

            str_message = json.dumps(deserialized_message)
            bytes_message = bytes(str_message, encoding="utf-8")

            if message_type == 'LOG' or message_type == 'DATA':
                for numSocket in self._abonnement[message_type]:
                    self._wfile[numSocket].write(bytes_message + b"\n")
            
            elif message_type == 'CMD':
                destinataire = deserialized_message["destinataire"]
                expediteur = deserialized_message["expediteur"]
                if destinataire != '':
                    try:
                        #Traitement particulier quand on demande des information au CENTRAL
                        if destinataire == self.name:
                            if deserialized_message["action"] == "recup_action":
                                deserialized_message["msg"] = self.getActions()
                                #On lui répond
                                destinataire = expediteur
                                deserialized_message["action"] = "answer"
                                str_message = json.dumps(deserialized_message)
                                bytes_message = bytes(str_message, encoding="utf-8")
                        
                        fillno = self.name_to_fillno[destinataire]
                        logging.info('On redirige vers {} : {}'.format(destinataire,fillno))
                        self._wfile[fillno].write(bytes_message + b"\n")
                        self.send_log("{} sent to {} : {}".format(self.name, destinataire,str_message), 6)
                    except KeyError:
                        self.send_log("{} : Consumer isn't connected".format(self.name), 3)
                        #logging.info("Le client n'est pas connecté")

                    except Exception as e:
                        self.send_log("{} : {} ".format(self.name, e), 3)
                        #logging.info(e)
            else:
                logging.info('No TYPE in message found')
                self.send_log("{} : Le message envoyé n\'a pas de type ".format(self.name), 3)

    """
        Récupère la requête et l'adresse du client à partir de la socket.overridden.

        Returns:
            conn : Une connexion
            address : une adresse.
    """
    def get_request(self):
        #  Get the request and client address from the socket.overridden.

        (conn, address) = self.socket.accept()
        logging.info("Connection accepted from: {}".format(address))
        conn.setblocking(True)

        return conn, address


    def recup_action(self):
        """
        Cette fonction retourne la liste des actions enregistrées.

        Returns:
            dict: Les actions enregistrées.
        """
        return self._actions

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
        #logging.info(f"Log envoyé :{log}")
        self.messageQueue.put(log)


    def getCurrentDateTime(self):
        currentDate = datetime.now()
        # dd/mm/YY H:M:S
        #On formate la date et l'heure
        dt = currentDate.strftime("%d-%m-%Y %H:%M:%S")
        return dt


class MyThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server :Central):
        self.queue = server.messageQueue
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)

    """
    Cette méthode effectue les opérations suivantes :
        1. Définit l'auteur de la socket
        2. Ajoute la connexion au serveur `Central`.
        3. Enregistre le démarrage du service
        4. Reçoit les informations d'abonnement et les enregistre
        5. Définit les abonnements pour la connexion
        6. Reçoit les informations sur les actions et les enregistre
        7. Définit les actions
        8. Reçoit continuellement des messages et les ajoute à la file d'attente des messages du serveur.
        9. S'il y a une erreur EOFError ou ConnectionError, l'enregistre et sort de la boucle.

        Return : 
        None
        """
    def handle(self):
        #logging.info("Handle")
        self.setSocketWriter()
        self.server: Central
        self.server.add_client(self.connection)

        #logging.info("Service Started")
        self.server.send_log("{} : Service Started".format(self.server.name), 7)
        abonnements_dict = self.receive()
        #logging.info("abonnement de {} : {}".format(abonnements_dict["expediteur"], abonnements_dict))
        self.server.send_log("{} : Subcriptions of {} : {}".format(self.server.name,abonnements_dict["expediteur"], abonnements_dict), 7)

        self.setAbonnements(self.connection, abonnements_dict)
        #logging.info("name to fillno {} ".format(self.server.name_to_fillno))
        self.server.send_log("{} : name to fillno {}".format(self.server.name,self.server.name_to_fillno), 7)

        actions_dict = self.receive()
        #logging.info("actions de {} : {}".format(actions_dict["expediteur"], actions_dict))
        self.server.send_log("{} : actions of {} : {}".format(self.server.name, self.server.name_to_fillno,actions_dict["expediteur"], actions_dict), 7)
        self.setActions(actions_dict)

        


        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        while True:
            try:
                # logging.info("Will Receive...")
                message_dict = self.receive()
                
                #logging.info("Received: {}".format(message_dict))
                if not message_dict:
                    break

                # self.server.messageQueue.put(message_dict)

                # self.send(message_dict)

                # logging.info("Sent: {}".format(data.upper()+b"\n"))

                if event.is_set():
                    break

                #print("+ enqueued message: ", message_dict)
                self.server.messageQueue.put(message_dict)
            except EOFError:
                print("EOFError")
                self.server.send_log("{} : EOFError".format(self.server.name), 3)
                break
            except (ConnectionAbortedError, ConnectionResetError):
                print("ConnectionError")
                self.server.send_log("{} : ConnectionError".format(self.server.name), 3)
                break
            """except json.decoder.JSONDecodeError:
                print("json.decoder.JSONDecodeError")
                break
            
            except Exception as e:
                print(f"Exception {e}")"""

    """
    Reçoit et décode un message reçu à partir de la connexion client.

    Le message est lu à partir de l'objet rfile, décodé en UTF-8 et converti en objet Python à l'aide de json.loads. 
    Si le message est vide, une dict vide est retourné.
    Le message reçu est logué avec la méthode send_log de self.server.

    Return :
    msg_decoded (dict) : Le message décodé en objet Python
    """
    def receive(self):
        message = self.rfile.readline().strip()
        print(f"message:  {message}")
        message_str = message.decode("utf-8")
        print(f"abonnement_str:  {message_str}")
        self.server.send_log("{} received {}".format(self.server.name, message_str),6)
        if message_str:
            message_decoded = json.loads(message_str)
            # print(f"abonnement_decoded:  {message_decoded}")
            return message_decoded
        msg_encoded = self.rfile.readline().strip()
        # print(f"msg_encoded:  {msg_encoded}")
        msg_str = msg_encoded.decode("utf-8")
        # print(f"msg_str:  {msg_str}")
        if msg_str:
            msg_decoded = json.loads(msg_str)
            # print(f"msg_decoded:  {msg_decoded}")
            return msg_decoded
        else:
            return {}

    """
    Fonction d'émission de message

    Paramètres
    ----------
    message : le message à envoyer
    """
    def send(self, message):
        str_message = json.dumps(message)
        bytes_message = bytes(str_message, encoding="utf-8")
        self.wfile.write(bytes_message + b"\n")


    """
    Supprime la connexion avec le client, ses abonnements et ses actions quand celui-ci se déconnecte du Central
    Termine proprement le Thread fils spécifique à ce client
    
    Return:
    None
    """
    def finish(self):
        logging.info("finish")
        # print(self.connection)
        self.server.delete_client(self.connection)
        print(self.server.getAbonnements())
        print(self.server.getActions())
        super().finish()

    """
    Enregistre les abonnements d'un client dans une liste de 2 dictionnaires (DATA et LOG)
    
    Parameters:
    connection : le client
    abonnement_dict : les abonnements du client
    """
    def setAbonnements(self, connection, abonnement_dict):
        self.server.name_to_fillno[abonnement_dict["expediteur"]] = connection.fileno()
        for type in abonnement_dict['msg']:
            self.server.setAbonnements(connection.fileno(), type)

        print(self.server.getAbonnements())

    """
        Enregistre les actions d'un client dans un dictionnaire 

        Parameters:
        actions_dict : les actions du client
        """
    def setActions(self, actions_dict):
        self.server.setActions(actions_dict["expediteur"], actions_dict["msg"])

        print(self.server.getActions())
    def setSocketWriter(self):
        self.server.setWFile(self.connection.fileno(), self.wfile)

    def __str__(self) -> str:
        return pprint.pformat(self.__dict__)

if __name__ == "__main__":
    HOST, PORT = "localhost", 65432
    logger = logging.getLogger('__main__')
    central = Central((HOST, PORT), MyThreadedTCPRequestHandler)

    # create printing thread
    """printer_thread = threading.Thread(target=printer, args=(queue,), daemon=True, name='Printer')
    printer_thread.start()"""

    try:
        central.serve_forever()
    except KeyboardInterrupt:
        print("Terminating...")
        event.set()
        central.server_close()

    print("FIN")
