#!/usr/bin/env python3


""" Nom du module : Superviseur Sinusoïd"""

""" Description """
""" Version 1 """
""" Date : 04/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import logging
import random
import sys
import socket
import time

import numpy as np
import pandas as pd
from pilotage_lib import NetworkItem, kb_func, Collecteur
from collections import deque

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

class SuperviseurSinus(NetworkItem):
    def __init__(self, host, port, name, abonnement):
        NetworkItem.__init__(self, host, port, name, abonnement)
        self.go()
        self.started = False

    def go(self):
        """
        Initialise les paramètres de données et de génération de données aléatoires
        avec des valeurs aléatoires.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        self.data_params = ['{}.sin'.format(self.name)]
        self.data = {'{}.sin'.format(self.name):deque()}

        self.delta = time.time() - time.perf_counter()
        self.gen_param()
        self.d1 = random.random()*2*np.pi
        self.d2 = random.random()*2*np.pi
        self.d3 = random.random()*2*np.pi
        self.pause_until = 0
        

    def gen_param(self):
        """
        Génère des paramètres aléatoires pour la génération de données aléatoires.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        self.fq=random.randint(1,6)/4
        self.a0=random.randint(0,20)/10
        self.a1=random.randint(5,10)
        self.a2=random.randint(0,20)/random.randint(3,8)
        self.a3=random.randint(0,20)/random.randint(3,5)
		

    def action_regen_param(self, *karg):
        """
        Régénère les paramètres de génération de données aléatoires
        en tenant compte de la dernière valeur générée et en utilisant des valeurs aléatoires.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            *karg (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """
        print(karg)
        fq=random.randint(1,6)/4
        a0=random.randint(0,20)/10*10
        a1=random.randint(5,10)
        a2=random.randint(0,20)/random.randint(3,8)
        a3=random.randint(0,20)/random.randint(3,5)
        
        ytransit = None
        if 'last' in self.__dict__ and self.last is not None:
            #il faut calculer le decalage phi
            x = self.last
            ytransit = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
            
        self.gen_param()
        if ytransit is not None:
            delay = self.next_y(ytransit)
            self.yfix = ytransit
            self.pause_until = self.last+delay


    def next_y(self, y_target):
        """
        Calcule l'instant auquel la génération de données atteindra la valeur cible y_target.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            y_target (float): Valeur cible à atteindre.

        Returns:
            float: Instant auquel la génération de données atteindra la valeur cible.
        """
        x = np.linspace(self.last, self.last+2, 2000)
        y = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
        calc = np.around(np.absolute(y-y_target),1)
        m = np.amin(calc)
        indexs = np.where(calc == m)
        i = indexs[0][0]
        
        return i/1000		


    def action_accelerate(self, *karg):
        """
        Accélère la génération de données.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            *karg (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """
        self.action_accelerate_to(1.2)


    def action_decelerate(self, *karg):
        """
        Ralentit la génération de données.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            *karg (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """
        self.action_accelerate_to(0.6)


    def action_accelerate_to(self, val, *karg):
        """
        Accélère la génération de données à la vitesse spécifiée.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            val (float): Vitesse à laquelle accélérer la génération de données.
            *karg (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """

        x = self.last
        self.d1 -= 2*np.pi*x*self.fq*(val-1)
        self.d2 -= 2*2*np.pi*x*self.fq*(val-1)
        self.d3 -= 3*2*np.pi*x*self.fq*(val-1)
        self.fq *= val


    def action_pause_1(self, *param):
        """
        Met en pause la génération de données pendant 1 unité de temps.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            *param (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """
        self.action_pause(1, *param)
		

    def action_pause(self, delay, *param):
        """
        Met en pause la génération de données pendant un certain délai.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            delay (float): Durée de la pause.
            *param (tuple): Tuples de valeurs supplémentaires passées à la fonction.

        Returns:
            None
        """
        x = self.last
        if self.pause_until < self.last:
            self.pause_until = self.last+delay
            '''
            if y_target is not None:
                self.yfix = y_target
            else:
                self.yfix = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
            '''
            self.yfix = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
        else:
            #on ne change pas yfix
            self.pause_until +=delay
        
        #on recalcule le decalage phi
        self.d1 -= 2*np.pi*self.fq*delay
        self.d2 -= 2*2*np.pi*self.fq*delay
        self.d3 -= 3*2*np.pi*self.fq*delay

    
    def remplit(self):
        """
        Remplit les données de l'objet avec des valeurs générées aléatoirement ou en pause.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        if 'last' not in self.__dict__ or self.last is None:
            self.first = round(time.perf_counter(),3)
            self.last = self.first
            logging.info("cas 1")
        elif self.last < self.pause_until:
            now = time.perf_counter()
            if now > self.pause_until:
                now = self.pause_until
            val0 = int((self.last-self.first)*1000)
            nbval = int((now-self.last)*1000)
            #y = np.full(nbval, self.yfix) (Code LA)
            self.data['{}.sin'.format(self.name)].append({'date':self.last+self.delta, 'counter':val0, 'data':{"time":time.perf_counter(),"test_sinus":self.yfix }})
            self.last = now
            logging.info("cas 2")
        else:
            now = time.perf_counter()
            val0 = int((self.last-self.first)*1000)
            nbval = int((now-self.last)*1000)

            #x = np.linspace(self.last, now, nbval) (Code LA)
            x2 = now

            #y = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3) (Code LA)
            y2 = self.a0+self.a1*np.sin(2*np.pi*self.fq*x2+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x2+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x2+self.d3)
            #y = y*100 (Code LA)
            y2 = y2*100
            
            print(f"y2 {y2}")

            self.data['{}.sin'.format(self.name)].append({'date':self.last+self.delta, 'counter':val0, 'data':{"time":time.perf_counter(),"test_sinus":y2 }})
            self.last = now
 

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
            {"nom":"dem_accelerate", "function": self.action_accelerate},
            {"nom":"dem_decelerate", "function":self.action_decelerate},
            {"nom":"dem_pause", "function":self.action_pause_1},
            {"nom":"dem_change",  "function":self.action_regen_param}
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

            if self.started:
                while self.data['{}.sin'.format(self.name)]:
                    d = self.data['{}.sin'.format(self.name)].popleft()
                    print(d)
                    self.send_data(expediteur=self.name, paquet= "test", dict_message=d['data'])
                    self.send_data(expediteur=self.name, paquet= "PAQUET2", dict_message=d['data'])
                    self.send_log("data sent", 1)
                
                if time.perf_counter() > check_data+0.005: #toute les 5 ms (200hz)
                    self.remplit()
                    check_data = time.perf_counter()

            	
            #time.sleep(1)

            keypress = kb_func()
        logging.info("Service fini")
    
#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
   
    name = "SINUS"
    abonnement = []

    spv = SuperviseurSinus(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class SuperviseurSinus qui hérite de NetworkItem, qui redef service
    
   
    spv.service()

    spv.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(spv.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(spv.read_thread.name))
