#!/usr/bin/env python3

""" Nom du module : Central """
""" Description : Le central est l'élément  """
""" Version : 0 """
""" Date : 17/10/2022 """
""" Auteur : Équipe CEIS """
""" Nom du module : Central """

# ________________________________IMPORT_________________________________
import socket
import threading


# ______________________________CONSTANTES_______________________________
LOCALHOST = "127.0.0.1"
PORT = 65432
clients_connected = {}


# ________________________DEFINITION DE LA CLASS_________________________
class ClientThread(threading.Thread):
    """Classe représentant le thread qui gère la communication avec un autre élément de la partie pilotage"""

    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        print("New connection added: ", client_address)

    def run(self):
        """Surcharge de la méthode run() de la classe mère Thread"""

        identifiant_client = ""
        """Cette chaine de caractères prendra le nom du client connecté"""

        print("Connection from : ", self.client_address)
        identifiant_client = self.client_socket.recv(2048).decode()
        clients_connected[identifiant_client] = self.client_socket

        while True:
            """Boucle infinie écoutant les messages du client arrivant sur la socket associée"""
            data = self.client_socket.recv(2048)  # Recevoir des données venant du socket (octets)
            msg = data.decode()  # Décode les octets donnés, et le renvoie sous forme d'une chaîne de caractères
            print("from client", msg)

            # Traiter le message reçu

            if msg == 'bye':
                break

        print("Client at ", self.client_address, " disconnected...")
        clients_connected.pop(identifiant_client, None)  # On enlève le client dans le dict des clients connectés


# __________________________FONCTIONS GLOBALES___________________________
def nb_client_connected():
    """Renvoie le nombre de clients connectés"""
    return len(clients_connected)


def central():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, PORT))

    print("Server started")
    print("Waiting for client request..")
    while True:
        server.listen(1)

        client_sock, client_address = server.accept()

        new_thread = ClientThread(client_sock, client_address)
        new_thread.start()
        print(nb_client_connected())


# _________________________________MAIN__________________________________
if __name__ == '__main__':
    central()
