import logging
import selectors
import socket
import time
import pickle

HOST = 'localhost'
PORT = 65432

# print améliorer
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(messagee)s')

#class du serveur
class SelectorServer:
    
    def __init__(self, host, port):
        # Create the main socket that accepts incoming connections and start
        # listening. The socket is nonblocking.
        # création de la socket
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # la socket est liée à un hôte et un port
        self.main_socket.bind((host, port))
        # On accepte les connexions
        self.main_socket.listen(1)
        # On place la socket en mode non bloquant, c'est-à-dire qu'elle ne reste pas en attente d'une reception
        self.main_socket.setblocking(False)
        # Dictionnaire qui contiendra les buffers de messages pour chaque socket
        # clé=N°Socket valeur=buffer de message (dictionnaire)
        self._buffer = {}
        # Dictionnaire qui contiendra la socket de chaque entité
        # clé=index valeur=dictionnaire contenant les informations de la socket
        self._fileno_to_socket = {}
        self._name_to_socket = {}
        # Dictionnaire qui contiendra les abonnements de chaque entité
        # clé=N°Socket valeur={DATA, LOG, CMD}[N°Socket]
        self._abonnement = {
            'DATA' : [],
            'LOG' : []
        }
        # Séparateur pour séparer les messages dans le buffer
        self._separator = b'[...]'
        #self.nb = 0

        # Create the selector object that will dispatch events. Register
        # interest in read events, that include incoming connections.
        # The handler method is passed in data so we can fetch it in
        # serve_forever.
        self.selector = selectors.DefaultSelector()
        self.selector.register(fileobj=self.main_socket,
                               events=selectors.EVENT_READ,
                               data=self.on_accept)

        # Keeps track of the peers currently connected. Maps socket fd to
        # peer name.
        self.current_peers = {}

    # Fonction en charge d'accepter les connexions au serveur
    def on_accept(self, sock, mask):
        # This is a handler for the main_socket which is now listening, so we
        # know it's ready to accept a new connection.
        conn, addr = self.main_socket.accept()

        logging.info('accepted connection from {0}'.format(addr))
        conn.setblocking(False)
        # logging.info('Socket: {0}'.format(sock))

        #On initialise le buffer
        self._buffer[conn.fileno()]="".encode()

        # On stocke le nom du port de connection dans le dictionnaire de buffers
        self.current_peers[conn.fileno()] = conn.getpeername()

        self._fileno_to_socket[conn.fileno()] = conn

        self.on_abonnement(conn=conn)
        # Register interest in read events on the new socket, dispatching to
        # self.on_read
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
                # Assume for simplicity that send won't block
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

                    #logging.info('Traitement de: "{0}"'.format(pickle.loads(recv_data)))
                    # self.nb = self.nb + 1

                    deserialized_message=pickle.loads(recv_data)
                    logging.info('Traitement de: "{0}"'.format(deserialized_message))

                    self._name_to_socket[deserialized_message['expediteur']]=conn

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
        # We can't ask conn for getpeername() here, because the peer may no
        # longer exist (hung up); instead we use our own mapping of socket
        # fds to peer names - our socket fd is still open.
        peername = self.current_peers[conn.fileno()]
        logging.info('closing connection to {0}'.format(peername))
        del self.current_peers[conn.fileno()]
        self.selector.unregister(conn)
        conn.close()
        # TODO : Supprimer les abonnements de conn.fileno()

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
                #logging.info('got data from {}: {!r}'.format(peername, data))
                logging.info('got data from {}'.format(peername))
                # Assume for simplicity that send won't block
                # on ajoute les données à la suite dans le buffer de la socket correspondante
                self._buffer[conn.fileno()] += data
                # logging.info('ajout dans le buffer {}: {!r}'.format(self._buffer[conn.fileno()], data))

                cpt = 0
                # "fin" correspond à la position du dernier séparateur (= fin du dernier message complet)
                fin = self._buffer[conn.fileno()].find(self._separator)
                # logging.info('fin du message à traiter en position {}.'.format(fin))
                # Si on a un ou plusieurs messages complets dans le buffer
                while fin > -1 and cpt < 30:
                    #le prochain message à decrypter
                    recv_data = self._buffer[conn.fileno()][:fin]
                    #appel obj->receive

                    #logging.info('Traitement de: "{0}"'.format(pickle.loads(recv_data)))
                    #self.nb = self.nb + 1

                    self.rediriger(recv_data,conn)

                    #print('CN/received {}bytes from connection'.format(len(recv_data)), sock.getpeername())
                    #le reste
                    # S'il reste un message incomplet au moment du traitement,
                    # on le stocke, on vide le buffer et on le replace dans celui-ci
                    reste = self._buffer[conn.fileno()][fin+len(self._separator):]
                    self._buffer[conn.fileno()] = reste
                    fin = self._buffer[conn.fileno()].find(self._separator)
                    cpt+=1

                # S'il reste un message complet à la fin de la lecture, cela veut dire qu'il y a un engorgement des messages
                if fin > -1:
                    print("------------------------------engorgement des messages------------------------------")
            else:
                self.close_connection(conn)
                #print(self.nb)
        except ConnectionResetError:
            self.close_connection(conn)
            #print(self.nb)

        
    # Fonction de fonctionnement continu du serveur
    def serve_forever(self):
        last_report_time = time.time()

        while True:
            # Wait until some registered socket becomes ready. This will block
            # for 0 ms.
            events = self.selector.select(timeout=0)

            # For each new event, dispatch to its handler
            for key, mask in events:
                # fait référence à la fonction on_read dans le
                # self.selector.register(fileobj=conn, events=selectors.EVENT_READ,data=self.on_read)
                # de la fonction on_accept()
                handler = key.data
                socket = key.fileobj
                handler(socket, mask)

            # This part happens roughly every second.
            cur_time = time.time()
            if cur_time - last_report_time > 60:
                logging.info('Running report...')
                logging.info('Num active peers = {0}'.format(len(self.current_peers)))
                """logging.info('Active peers: {0}'.format(self.current_peers))"""
                last_report_time = cur_time

    def rediriger(self,message,conn):
        deserialized_message=pickle.loads(message)
        if deserialized_message["type"] == 'LOG':
            for numSocket in self._abonnement['LOG']:
                newConn = self._fileno_to_socket[numSocket]
                sent = newConn.send(message + self._separator)  # Should be ready to write
            logging.info('On redirige vers les abonnées LOG de '+str(conn.fileno()))
        elif deserialized_message["type"] == 'DATA':
            for numSocket in self._abonnement['DATA']:
                newConn = self._fileno_to_socket[numSocket]
                sent = newConn.send(message + self._separator)  # Should be ready to write
            logging.info('On redirige vers les abonnées DATA de '+str(conn.fileno()))
        elif deserialized_message["type"] == 'CMD':
            if deserialized_message["destinataire"] != '':
                try:
                    newConn = self._name_to_socket[deserialized_message["destinataire"]]
                    sent = newConn.send(message + self._separator)  # Should be ready to write
                    logging.info('On redirige vers les abonnées CMD de '+ str(conn.fileno()))
                except KeyError:
                    print("IL EST PAS CO")
        else:
            logging.info('Y A PAS DE TYPE')


if __name__ == '__main__':
    logging.info('starting')
    server = SelectorServer(host=HOST, port=PORT)
    server.serve_forever()