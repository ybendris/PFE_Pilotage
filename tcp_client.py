import sys
import logging
import selectors
import socket
import time
import random
import pickle

HOST = 'localhost'
PORT = 65432

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(messagee)s')

class SelectorClient:
    def __init__(self, host, port, name):
        self.name = name
        # création de la socket
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # On connecte la socket à un serveur existant
        self.connected = self.main_socket.connect_ex((host, port))
        # Séparateur pour séparer les messages dans le buffer
        self._separator = b'[...]'
        # Dictionnaire qui contiendra les buffers de messages pour chaque socket
        # clé=N°Socket valeur=buffer de message (dictionnaire)
        self._buffer = {}
        # On initialise le buffer
        self._buffer[self.main_socket.fileno()]="".encode()
        # Create the selector object that will dispatch events. Register
        # interest in read events, that include incoming connections.
        # The handler method is passed in data so we can fetch it in
        # serve_forever.
        self.selector = selectors.DefaultSelector()
        self.envoi_abonnement()
        self.selector.register(fileobj=self.main_socket,
                               events=selectors.EVENT_READ | selectors.EVENT_WRITE,
                               data=self.test)
        

    def envoi_abonnement(self):
        conn = self.main_socket
        message = {}
        try:
            message["expediteur"] = self.name
            message["msg"] = ["DATA", "LOG"]

            serialized_message = pickle.dumps(message)

            sent = conn.send(serialized_message + self._separator)  # Should be ready to write

        except:  # TODO à voir
            print("CN/socket fermée/sent W", """self._closed""")
            #self.selector.unregister(conn)
            """obj.close(sock)"""
            del self._buffer[conn]
            return False

    def test(self,conn, mask):
        if mask & selectors.EVENT_READ:
            print("\nREAD\n")
            try:
                # On récupère les données reçu et on les stocke dans data
                data = conn.recv(1024)

                if data:
                    peername = conn.getpeername()
                    #logging.info('got data from {}: {!r}'.format(peername, data))
                    # Assume for simplicity that send won't block
                    # on ajoute les données à la suite dans le buffer de la socket correspondante
                    self._buffer[conn.fileno()] += data
                    #logging.info('ajout dans le buffer {}: {!r}'.format(self._buffer[conn.fileno()], data))

                    cpt = 0
                    # "fin" correspond à la position du dernier séparateur (= fin du dernier message complet)
                    fin = self._buffer[conn.fileno()].find(self._separator)
                    logging.info('fin du message à traiter en position {}.'.format(fin))
                    # Si on a un ou plusieurs messages complets dans le buffer
                    while fin > -1 and cpt < 30:
                        #le prochain message à decrypter
                        recv_data = self._buffer[conn.fileno()][:fin]
                        #appel obj->receive
                        logging.info('Reçu de: {}.'.format(pickle.loads(recv_data)))
                        #conn.send(data)

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
                        print("engorgement des messages")
                else:
                    self.close_connection(conn)
            except ConnectionResetError:
                self.close_connection(conn)
        if mask & selectors.EVENT_WRITE:
            print("WRITE")
            message = {}
            try:
                alea = random.randrange(1, 4)
                logging.info('LA VALEUR RANDOM VAUT : '+ str(alea))
                if alea == 1:
                    message["type"]="CMD"
                    message["destinataire"]="CAP"
                    message["msg"] = "Flux CMD"
                elif alea == 2:
                    message["type"]='DATA'
                    message["msg"] = "Flux DATA"
                else:
                    message["type"]='LOG'
                    message["msg"] = "Flux LOG" #"Flux LOG"

                serialized_message = pickle.dumps(message)

                sent = conn.send(serialized_message+self._separator)	 # Should be ready to write

            except: #TODO à voir
                print("CN/socket fermée/sent W", """self._closed""")
                self.selector.unregister(conn)
                """obj.close(sock)"""
                del self._buffer[conn]
                return False
            
            

    def serve_forever(self):
        while True:
            
            # Wait until some registered socket becomes ready. This will block
            # for 0 ms. (en seconde)
            events = self.selector.select(timeout=0)
            time.sleep(2)
            # For each new event, dispatch to its handler
            for key, mask in events:
                handler = key.data
                handler(key.fileobj, mask)



if __name__ == '__main__':
    logging.info('starting')
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    server = SelectorClient(host=HOST, port=PORT, name=name)
    server.serve_forever()