#!/usr/bin/env python3

""" Nom du module : Client_exemple """
""" Description : Exemple d'un client se connectant au Central  """
""" Version : 0 """
""" Date : 17/10/2022 """
""" Auteur : Équipe CEIS """
""" Nom du module : Client_exemple """

# ________________________________IMPORT_________________________________
import socket

# ______________________________CONSTANTES_______________________________
LOCALHOST = "127.0.0.1"
PORT = 65432


# ________________________DEFINITION DE LA CLASS_________________________

# __________________________FONCTIONS GLOBALES___________________________
def client_exemple():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((LOCALHOST, PORT))
    client.sendall(bytes("SPV_CAP", 'UTF-8'))  # Envoi de son identifiant au central

    while True:
        in_data = client.recv(1024)
        print("From Server :", in_data.decode())
        out_data = input()
        client.sendall(bytes(out_data, 'UTF-8'))
        if out_data == 'bye':
            break
    client.close()


# _________________________________MAIN__________________________________
if __name__ == '__main__':
    client_exemple()
