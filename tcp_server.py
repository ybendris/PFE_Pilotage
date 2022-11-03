#!/usr/bin/env python3

""" Nom du module : SelectorServer"""
""" Description : Serveur qui accepte les connexions et redirige les messages"""
""" Version 2 """
""" Date : 03/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _________________________________________ IMPORT _________________________________________
import logging
import selectors
import socket
import time
import pickle

#  _________________________________________ CONSTANTES _________________________________________

HOST = 'localhost'
PORT = 65432


#  _________________________________________ DEFINITION DE CLASSES _________________________________________
class SelectorServer:
    """ Nom de la classe : SelectorServer """
    """ Description : Classe représentant un serveur qui accepte les connexions et redirige les messages """
    def __init__(self, host, port):
        # Création du socket principal acceptant les connexions en mode
        # Socket AF_INET (IPV4) / Socket STREAM (TCP)
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Le socket est lié à un hôte et un port
        self.main_socket.bind((host, port))
        # On accepte les connexions
        self.main_socket.listen(5)
        # On place le socket en mode non bloquant, c'est-à-dire qu'elle ne reste pas en attente d'une reception
        self.main_socket.setblocking(False)
        # Dictionnaire qui contiendra les buffers de messages pour chaque socket
        # clé=N°Socket(descripteur de fichier) valeur=buffer de message (dictionnaire)
        self._buffer = {}
        # Dictionnaire qui contiendra la socket de chaque entité
        # clé=index valeur=dictionnaire contenant les informations de la socket
        self._fileno_to_socket = {}
        self._name_to_socket = {}
        # Dictionnaire qui contiendra les abonnements de chaque entité
        # clé=N°Socket(descripteur de fichier) valeur={DATA, LOG, CMD}[N°Socket]
        self._abonnement = {
            'DATA': [],
            'LOG': []
        }
        # Séparateur utilisé pour séparer les messages dans le buffer
        self._separator = b'[...]'

        # Création de l'objet sélector qui distribuera les événements.
        self.selector = selectors.DefaultSelector()
        self.selector.register(fileobj=self.main_socket,
                               events=selectors.EVENT_READ,
                               data=self.on_accept)

        # Dictionnaire qui contiendra les informations de connexion de chaque entité connectée
        # # clé=N°Socket(descripteur de fichier) valeur=peername
        self.current_peers = {}

    # Fonction en charge d'accepter les connexions au serveur
    def on_accept(self, sock, mask):
        # Gestionnaire de connexion
        conn, addr = self.main_socket.accept()

        logging.info('accepted connection from {0}'.format(addr))
        conn.setblocking(False)

        # On initialise le buffer de messages lié à ce socket
        self._buffer[conn.fileno()] = "".encode()

        self.current_peers[conn.fileno()] = conn.getpeername()

        self._fileno_to_socket[conn.fileno()] = conn

        self.on_abonnement(conn=conn)
        # Les évènements de type EVENT_READ sur le socket 'conn' seront transmis à la méthode on_read
        self.selector.register(fileobj=conn, events=selectors.EVENT_READ,
                               data=self.on_read)

    def on_abonnement(self, conn):
        try:
            # On récupère les données reçu et on les stocke dans data
            data = conn.recv(4096)

            # Si des données ont été reçu
            if data:
                peername = conn.getpeername()
                # logging.info('got data from {}: {!r}'.format(peername, data))
                logging.info('got data from {}'.format(peername))

                # on ajoute les données à la suite dans le buffer de la socket correspondante
                self._buffer[conn.fileno()] += data
                # logging.info('ajout dans le buffer {}: {!r}'.format(self._buffer[conn.fileno()], data))

                cpt = 0
                # "fin" correspond à la position du dernier séparateur (= fin du dernier message complet)
                fin = self._buffer[conn.fileno()].find(self._separator)
                # logging.info('fin du message à traiter en position {}.'.format(fin))
                # Si on a un ou plusieurs messages complets dans le buffer
                while fin > -1 and cpt < 30:
                    # le prochain message à decrypter
                    recv_data = self._buffer[conn.fileno()][:fin]
                    # appel obj->receive

                    # logging.info('Traitement de: "{0}"'.format(pickle.loads(recv_data)))

                    deserialized_message = pickle.loads(recv_data)
                    logging.info('Traitement de: "{0}"'.format(deserialized_message))

                    self._name_to_socket[deserialized_message['expediteur']] = conn

                    for type in deserialized_message['msg']:
                        self._abonnement[type].append(conn.fileno())

                    logging.info('Abonnement => "{0}"'.format(self._abonnement))

                    # print('CN/received {}bytes from connection'.format(len(recv_data)), sock.getpeername())
                    # le reste
                    # S'il reste un message incomplet au moment du traitement,
                    # on le stocke, on vide le buffer et on le replace dans celui-ci
                    reste = self._buffer[conn.fileno()][fin + len(self._separator):]
                    self._buffer[conn.fileno()] = reste
                    fin = self._buffer[conn.fileno()].find(self._separator)
                    cpt += 1

                # S'il reste un message complet à la fin de la lecture, cela veut dire qu'il y a un engorgement des messages
                if fin > -1:
                    print("------------------------------engorgement des messages------------------------------")
            else:
                self.close_connection(conn)
        except ConnectionResetError:
            self.close_connection(conn)

    def close_connection(self, conn):
        # On ne peut pas appeler getpeername() ici, car la connexion a été perdu
        # On peut utiliser notre structure de données à la place
        peername = self.current_peers[conn.fileno()]
        logging.info('closing connection to {0}'.format(peername))
        del self.current_peers[conn.fileno()]
        # On supprime les abonnements auquel l'élément déconnecté était abonné
        for abonnement in self._abonnement:
            try:
                self._abonnement[abonnement].remove(conn.fileno())
            except ValueError:
                pass
        #logging.info('Abonnement => "{0}"'.format(self._abonnement))
        self.selector.unregister(conn)
        conn.close()

    def on_read(self, conn, mask):
        # This is a handler for peer sockets - it's called when there's new
        # data.
        print("Read")
        try:
            # On récupère les données reçu et on les stocke dans data
            data = conn.recv(4096)

            # Si des données ont été reçu
            if data:
                peername = conn.getpeername()
                # logging.info('got data from {}: {!r}'.format(peername, data))
                logging.info('got data from {}'.format(peername))

                # on ajoute les données à la suite dans le buffer de la socket correspondante
                self._buffer[conn.fileno()] += data
                # logging.info('ajout dans le buffer {}: {!r}'.format(self._buffer[conn.fileno()], data))

                cpt = 0
                # "fin" correspond à la position du dernier séparateur (= fin du dernier message complet)
                fin = self._buffer[conn.fileno()].find(self._separator)
                # logging.info('fin du message à traiter en position {}.'.format(fin))
                # Si on a un ou plusieurs messages complets dans le buffer
                while fin > -1 and cpt < 30:
                    # le prochain message à decrypter
                    recv_data = self._buffer[conn.fileno()][:fin]
                    # appel obj->receive

                    # logging.info('Traitement de: "{0}"'.format(pickle.loads(recv_data)))
                    # self.nb = self.nb + 1

                    self.rediriger(recv_data, conn)

                    # print('CN/received {}bytes from connection'.format(len(recv_data)), sock.getpeername())
                    # le reste
                    # S'il reste un message incomplet au moment du traitement,
                    # on le stocke, on vide le buffer et on le replace dans celui-ci
                    reste = self._buffer[conn.fileno()][fin + len(self._separator):]
                    self._buffer[conn.fileno()] = reste
                    fin = self._buffer[conn.fileno()].find(self._separator)
                    cpt += 1

                # S'il reste un message complet à la fin de la lecture, cela veut dire qu'il y a un engorgement des messages
                if fin > -1:
                    print("------------------------------engorgement des messages------------------------------")
            else:
                self.close_connection(conn)
                # print(self.nb)
        except ConnectionResetError:
            self.close_connection(conn)
            # print(self.nb)

    # Fonction de fonctionnement continu du serveur
    def serve_forever(self):
        last_report_time = time.time()

        while True:
            # Attente qu'un socket enregistré à l'aide de register soit prêt
            events = self.selector.select(timeout=0)

            # Pour chaque nouvel événement, envoyez un message à son gestionnaire.
            for key, mask in events:
                # fait référence à la fonction on_read dans le
                # self.selector.register(fileobj=conn, events=selectors.EVENT_READ,data=self.on_read)
                # de la fonction on_accept()
                handler = key.data
                socket = key.fileobj
                handler(socket, mask)

            # permet d'éxécuter un rapport du nombre d'éléments connecté toutes les 60 secondes
            cur_time = time.time()
            if cur_time - last_report_time > 60:
                logging.info('Running report...')
                logging.info('Num active peers = {0}'.format(len(self.current_peers)))
                """logging.info('Active peers: {0}'.format(self.current_peers))"""
                last_report_time = cur_time

    def rediriger(self, message, conn):
        deserialized_message = pickle.loads(message)
        if deserialized_message["type"] == 'LOG':
            for numSocket in self._abonnement['LOG']:
                newConn = self._fileno_to_socket[numSocket]
                sent = newConn.send(message + self._separator)
            logging.info('On redirige vers les abonnées LOG de ' + str(conn.fileno()))
        elif deserialized_message["type"] == 'DATA':
            for numSocket in self._abonnement['DATA']:
                newConn = self._fileno_to_socket[numSocket]
                sent = newConn.send(message + self._separator)
            logging.info('On redirige vers les abonnées DATA de ' + str(conn.fileno()))
        elif deserialized_message["type"] == 'CMD':
            if deserialized_message["destinataire"] != '':
                try:
                    newConn = self._name_to_socket[deserialized_message["destinataire"]]
                    sent = newConn.send(message + self._separator)
                    logging.info('On redirige vers les abonnées CMD de ' + str(conn.fileno()))
                except KeyError:
                    print("IL EST PAS CO")
        else:
            logging.info('Y A PAS DE TYPE')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
    logging.info('starting')
    server = SelectorServer(host=HOST, port=PORT)
    server.serve_forever()
