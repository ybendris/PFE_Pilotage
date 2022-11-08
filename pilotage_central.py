#!/usr/bin/env python3

""" Nom du module : SelectorClient"""
import time

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
import pickle
import json
from queue import Queue
from pilotage_lib import NetworkItem

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
event = threading.Event()


class MyThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.queue = server.messageQueue
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)


    def setup(self):
        # print("setup")
        super().setup()

    def handle(self):
        logging.info("Handle")
        self.server.add_client(self.connection)

        logging.info("Serviced Started")
        abonnements_dict = self.receive()
        logging.info("abonnement de {} : {}".format(abonnements_dict["expediteur"], abonnements_dict))
        self.setAbonnements(self.connection, abonnements_dict)
        self.setSocketWriter()


        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        while True:
            # print("while ture")
            try:
                # logging.info("Will Receive...")
                message_dict = self.receive()
                logging.info("Received: {}".format(message_dict))
                if not message_dict:
                    break

                # self.server.messageQueue.put(message_dict)

                # self.send(message_dict)
                # logging.info("Sent: {}".format(data.upper()+b"\n"))

                if event.is_set():
                    logging.info("coucou")
                    break

                print("+ enqueued message: ", message_dict)
                self.server.messageQueue.put(message_dict)
            except EOFError:
                print("EOFError")
                break
            except (ConnectionAbortedError, ConnectionResetError):
                print("ConnectionError")
                break
            """except json.decoder.JSONDecodeError:
                print("json.decoder.JSONDecodeError")
                break
            
            except Exception as e:
                print(f"Exception {e}")"""

    def receive(self):
        abonnement_encoded = self.rfile.readline().strip()
        # print(f"abonnement_encoded:  {abonnement_encoded}")
        abonnement_str = abonnement_encoded.decode("utf-8")
        # print(f"abonnement_str:  {abonnement_str}")
        if abonnement_str:
            abonnement_decoded = json.loads(abonnement_str)
            # print(f"abonnement_decoded:  {abonnement_decoded}")
            return abonnement_decoded
        else:
            return {}

    def send(self, message):
        str_message = json.dumps(message)
        bytes_message = bytes(str_message, encoding="utf-8")
        self.wfile.write(bytes_message + b"\n")

    def finish(self):
        logging.info("finish")
        # print(self.connection)
        self.server.delete_client(self.connection)
        super().finish()

    def setAbonnements(self, connection, abonnement_dict):
        for type in abonnement_dict['msg']:
            self.server.setAbonnements(connection.fileno(), type)

        print(self.server.getAbonnements())

    def setSocketWriter(self):
        self.server.setWFile(self.connection.fileno(), self.wfile)

    def __str__(self) -> str:
        return pprint.pformat(self.__dict__)


class Central(socketserver.ThreadingMixIn, socketserver.TCPServer):
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingMixIn.daemon_threads = True

    def __init__(self, server_address, request_handler_class):
        socketserver.TCPServer.__init__(self, server_address, request_handler_class)
        self._abonnement = {
            'DATA': [],
            'LOG': []
        }
        self._wfile = {}
        self.daemon_threads = True
        self.current_peers = []
        self.messageQueue= Queue()
        self.consumer_thread = threading.Thread(target=self.consumer, daemon=True, args=(self.messageQueue,))
        self.consumer_thread.start()

    def server_bind(self):
        """Called by constructor to bind the socket.
            overridded.
        """
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        logging.info("Socket binded")
        self.server_address = self.socket.getsockname()

    def setAbonnements(self, fillno, type):
        self._abonnement[type].append(fillno)

    def setWFile(self, fileno, wfile):
        self._wfile[fileno] = wfile
        print(self._wfile)

    def getAbonnements(self):
        return self._abonnement

    def server_activate(self):
        """Called by constructor to activate the server.
            overridded
        """
        logging.info("Server is listening...")
        self.socket.listen(self.request_queue_size)

    def add_client(self, client_to_add):
        self.current_peers.append(client_to_add)
        logging.info("Nb connecté :{}".format(len(self.current_peers)))

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


    def consumer(self, queue):
        print("consumer")
        while True:
            # retrieve an item
            # time.sleep(1)

            deserialized_message = queue.get()
            logging.info(f"- dequeued message: {deserialized_message}")

            str_message = json.dumps(deserialized_message)
            bytes_message = bytes(str_message, encoding="utf-8")

            if deserialized_message["type"] == 'LOG':
                for numSocket in self._abonnement['LOG']:
                    newConn = self._wfile[numSocket].write(bytes_message + b"\n")
            elif deserialized_message["type"] == 'DATA':
                for numSocket in self._abonnement['DATA']:
                    newConn = self._wfile[numSocket].write(bytes_message + b"\n")
            elif deserialized_message["type"] == 'CMD':
                """if deserialized_message["destinataire"] != '':
                    try:
                        newConn = self._name_to_socket[deserialized_message["destinataire"]]
                        sent = newConn.send(message + self._separator)
                        logging.info('On redirige vers les abonnées CMD de ' + str(conn.fileno()))
                    except KeyError:
                        print("IL EST PAS CO")"""
            else:
                logging.info('Y A PAS DE TYPE')

            # process the item in some way
            # ...

            """if deserialized_message["type"] == 'LOG':
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
"""

    def get_request(self):
        #  Get the request and client address from the socket.overridden.

        (conn, address) = self.socket.accept()
        logging.info("Connection accepted from: {}".format(address))
        conn.setblocking(1)

        return conn, address


"""def printer(queue):
    logging.info("Printer launched")
    while True:
        # get messages
        message = queue.get()
        # print the message
        logging.info(message)"""

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
