#!/usr/bin/env python3


""" Nom du module : Superviseur Readfile"""


""" Description : Ce superviseur lit un fichier avec DATA et envoit ces données au central """
""" Version 1 : La version 1 permet de lire les fichiers que LA à envoyé"""
""" Date : 14/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import socket
import sys
import getopt
import msvcrt

import time

#import csv
import pandas as pd
import numpy as np
from pilotage_lib import NetworkItem, kb_func
from collections import deque
from datetime import datetime
from scipy import signal


#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________
class SuperviseurReadfile(NetworkItem):
    def __init__(self, host, port, name, abonnement, filename):
        NetworkItem.__init__(self, host, port, name, abonnement)
        with open(filename,'r') as fp:
            line = fp.readline()
            lparams = line.rstrip().split("\t")
            line = fp.readline()
            lunits = line.rstrip().split("\t")
            line = fp.readline()
            start = float(line.rstrip().split("\t")[0])
            
        self.last = 0
        self.started = False
        params = []
        self.data = {}
        for p in lparams[1:]:
            params.append("{}.{}".format(name, p))
            self.data["{}.{}".format(name, p)]=deque()
        print(params)
        
        self.df = pd.read_csv(filename, header=None, skiprows=2, delimiter='\t', decimal=".", names=lparams)
        print(self.df)
        self.start = start
        self.action_raz_courbe()

    def traiterData(self, data):
        """
        Traite les données reçues.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            data (dict): Les données à traiter.

        Returns:
            None
        """
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")


    def traiterLog(self, log):
        """
        Traite les log reçues.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            log (dict): Les log à traiter.

        Returns:
            None
        """
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")
    

    def start_mesure(self, message=None):
        logging.info("start_mesure")
        self.started = True


    def define_action(self):
        """
        Définit les actions disponibles dans le Superviseur Sinusoïde.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            list: Une liste d'actions sous la forme de dictionnaires contenant un nom (str) et une fonction (callable).
        """
        actions = [
            {"nom":"stop","function": self.stop},
            {"nom":"start_mesure","function": self.start_mesure},
        ]
        
        return actions

    def service(self):
        """
        Exécute le service principal de l'objet.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        logging.info("Service global lancé")
        keypress = kb_func()		
        check_data = time.perf_counter()
        while keypress != 'q' and self.running:			
            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())	

            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                self.start_mesure()

            if self.started ==False:
                for dname in self.data:
                    while self.data[dname]:
                        d = self.data[dname].popleft()	
                        print(d)
                        self.send_data(expediteur=self.name, paquet= self.name, dict_message=d['data'])
            
                if time.perf_counter() > check_data+0.015: 
                    self.remplit()
                    check_data = time.perf_counter()

                
            #time.sleep(1)

            keypress = kb_func()
        logging.info("Service fini")


    def action_raz_courbe(self, *args, **kargs):
        self.tref = self.start-time.perf_counter()
        self.last = self.tref
        self.delta = time.time() -self.start		

		
    def remplit(self):
        if 'lasttest' not in self.__dict__ or self.lasttest is None:
            print("not")
            self.first = round(datetime.now().timestamp()*1000)
            self.lasttest = self.first
        else:
            tnow = time.perf_counter()+self.tref
            
            nowtest = round(datetime.now().timestamp()*1000)
            
            ssdf = self.df[(self.df['t']>self.last)&(self.df['t']<=tnow)]
            if len(ssdf)>15:
                t = ssdf['t']
                for dname in self.data:
                    d = dname[len(self.name)+1:]
                    val = ssdf[d].tolist()

                    x = np.linspace(self.lasttest, nowtest, len(val))

                    datatest = [{'time': key, 'data': value} for key, value in zip(x, val)]


                                    
                    self.data[dname].append({'date':t.iloc[0]+self.delta, 'counter':0, 'data':datatest})
                self.last = tnow
                self.lasttest = nowtest
		

if __name__ == '__main__':
   
    name = "READFILE"
    filename="CDS_FINAP.BP.tab"
    abonnement = []

    spv = SuperviseurReadfile(host=HOST, port=PORT, name=name, abonnement=abonnement, filename=filename)
    # class SuperviseurSinus qui hérite de NetworkItem, qui redef service
    
   
    spv.service()

    spv.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(spv.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(spv.read_thread.name))
