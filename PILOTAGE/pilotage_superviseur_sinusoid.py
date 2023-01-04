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

from pilotage_lib import NetworkItem, kb_func
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

    def go(self):
        self.data_params = ['{}.sin'.format(self.name)]
        self.data = {'{}.sin'.format(self.name):deque()}

        self.delta = time.time() - time.perf_counter()
        self.gen_param()
        self.d1 = random.random()*2*np.pi
        self.d2 = random.random()*2*np.pi
        self.d3 = random.random()*2*np.pi
        self.testdata = deque()
        self.pause_until = 0
        
    def gen_param(self):
        self.fq=random.randint(1,6)/4
        self.a0=random.randint(0,20)/10
        self.a1=random.randint(5,10)
        self.a2=random.randint(0,20)/random.randint(3,8)
        self.a3=random.randint(0,20)/random.randint(3,5)
		
    def action_regen_param(self, *karg):
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
            #self.action_pause(delay)
            
    def next_y(self, y_target):
        x = np.linspace(self.last, self.last+2, 2000)
        y = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
        calc = np.around(np.absolute(y-y_target),1)
        m = np.amin(calc)
        indexs = np.where(calc == m)
        i = indexs[0][0]
        
        return i/1000		

    def action_accelerate(self, *karg):
        self.action_accelerate_to(1.2)

    def action_decelerate(self, *karg):
        self.action_accelerate_to(0.6)

    def action_accelerate_to(self, val, *karg):
        x = self.last
        self.d1 -= 2*np.pi*x*self.fq*(val-1)
        self.d2 -= 2*2*np.pi*x*self.fq*(val-1)
        self.d3 -= 3*2*np.pi*x*self.fq*(val-1)
        self.fq *= val

    def action_pause_1(self, *param):
        self.action_pause(1, *param)
		
    def action_pause(self, delay, *param):
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
        
        if 'last' not in self.__dict__ or self.last is None:
            self.first = round(time.perf_counter(),3)
            self.last = self.first
        elif self.last < self.pause_until:
            now = time.perf_counter()
            if now > self.pause_until:
                now = self.pause_until
            val0 = int((self.last-self.first)*1000)
            nbval = int((now-self.last)*1000)
            x = np.linspace(self.last, now, nbval)
            y = np.full(nbval, self.yfix)
            self.data['{}.sin'.format(self.name)].append({'date':self.last+self.delta, 'counter':val0, 'data':y.tolist()})
            self.last = now
            self.testdata = self.testdata.append(y.tolist())
        else:
            now = time.perf_counter()			
            val0 = int((self.last-self.first)*1000)
            
            nbval = int((now-self.last)*1000)
            x = np.linspace(self.last, now, nbval)
            y = self.a0+self.a1*np.sin(2*np.pi*self.fq*x+self.d1)+self.a2*np.sin(2*2*np.pi*self.fq*x+self.d2)+self.a3*np.sin(3*2*np.pi*self.fq*x+self.d3)
            y = y*100
            self.data['{}.sin'.format(self.name)].append({'date':self.last+self.delta, 'counter':val0, 'data':y.tolist()})
            self.last = now
            self.testdata = self.testdata.append(y.tolist())

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass
    
    """
    Fonction définissant les actions de la classe
    """
    def define_action(self):
        actions = [{"nom":"stop","function": self.stop}]
        return actions
    
    """
    Processus principal du Superviseur de test
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        check_data = time.perf_counter()
        while keypress != 'q' and self.running:			
            ## les commandes claviers

            while self.data['{}.sin'.format(self.name)]:
                d = self.data['{}.sin'.format(self.name)].popleft()
                print(d["counter"],len(d["data"]))
                #self.send_data(expediteur=self.name,paquet= "test", dict_message=d['data'])
                print(self.testdata)

            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())		
                    
            keypress = kb_func()
            
            time.sleep(1)

            if time.perf_counter() > check_data+0.015:
                self.remplit()
                check_data = time.perf_counter()
            

        logging.info("Service fini")
    
    def envoie_data_log_test(self):
        alea = random.randrange(1,6)
        #logging.info('LA VALEUR RANDOM VAUT : ' + str(alea))
        if alea == 1:
            pass
        elif alea == 2:
            self.send_data(expediteur= self.name, paquet = "BEAT", dict_message={"DATA1":"data1","DATA2":"data2","DATA3":"data3"})
        elif alea == 3:
            self.send_data(expediteur= self.name, paquet = "ADVANCED", dict_message={"DATA4":"data4","DATA5":"data5","DATA6":"data6"})
        elif alea == 4:
            self.send_data(expediteur= self.name, paquet = "RECONSTRUCTED", dict_message={"DATA7":"data7","DATA8":"data8","DATA9":"data9"})
        else:
            niveauLogAlea = random.randrange(0, 8)
            self.send_log("Message du LOG", niveauLogAlea)

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []


    spv = SuperviseurSinus(host=HOST, port=PORT, name=name, abonnement=abonnement)
    # class SuperviseurSinus qui hérite de NetworkItem, qui redef service
    
   
    spv.service()

    spv.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(spv.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(spv.read_thread.name))
