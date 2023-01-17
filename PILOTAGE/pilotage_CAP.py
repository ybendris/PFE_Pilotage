#!/usr/bin/env python3

""" Nom du module : SPV_CAP"""
from collections import deque
from datetime import datetime
from functools import partial
import msvcrt
import sys
import time


""" Description """
""" Version 1.2 """
""" Date : 17/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import socket
import logging
from pilotage_lib import NetworkItem, getBeginDateTime, kb_func
from instrument_lib import DecomNano, Nano

HOST = 'localhost'
PORT = 65432

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


def _str_hex(octets):
	chaine = ""
	if octets:
		for o in octets:
			if chaine:
				chaine += "|"+"0x{:02x}".format(o)
			else:
				chaine = "0x{:02x}".format(o)
	return chaine


class SPV_CAP(NetworkItem):
    def __init__(self, host, port, name, abonnement, instrument, decom, mode_quiet = False, stdout = None):
        self.retrieveCom()
        self.decomdata = {}
        self.quiet = mode_quiet
        self.device:Nano = instrument
        self.decom = decom
        self.en_attente = None
        self.filters_only = []
        self.filters_mask = []
        self.log = sys.stdout
        
        self.process()        
        NetworkItem.__init__(self, host, port, name, abonnement)

    def retrieveCom(self):
        #Récupère le port com sur lequel l'instrument est co (développement par les indus)
        pass

    def process(self):
        self.device.connect()

    def print_mnemo_filters(self, only=None, mask=None, reset=False):
        if reset:
            self.filters_only = []
            self.filters_mask = []
        if only:
            if isinstance(only, list):
                self.filters_only.extend(only)
            else:
                self.filters_only.append(only)
        if mask:
            if isinstance(mask, list):
                self.filters_mask.extend(mask)
            else:
                self.filters_mask.append(mask)

	#NON			
    def print_mnemo_ok(self, mnemo):
        if mnemo is None \
            or self.filters_only and mnemo not in self.filters_only \
            or self.filters_mask and mnemo in self.filters_mask:
            return False
        else:			 
            return True

    def print(self, *args, **kwargs):
        if 'file' not in kwargs:
            kwargs['file'] = self.log
            
        if kwargs['file'] != sys.stdout:
            pass
            return print(*args, **kwargs)
        
    def print2(self, *args, **kwargs):
        #on affiche dans la sortie standard
        if self.quiet == False:
            print(*args)
        
        #on enregistre dans le log
        if 'file' not in kwargs:
            kwargs['file'] = self.log

        #return print(*args, **kwargs)	
                
    def print_ascii(self, mnemo, data):
        len_head = len(self.decom.mnemo2code(mnemo))
        self.print("ASCII="+data['resp'][len_head:].decode())
        
    def print_decimal(self, mnemo, data):
        len_head = len(self.decom.mnemo2code(mnemo))
        utile = data['resp'][len_head:]
        for i in range(int(len(utile)/4)):
            g32 = utile[i*4] +utile[i*4 +1]*256 + utile[i*4 +2]*256*256 + utile[i*4 +3]*256*256*256
            g16a = utile[i*4] +utile[i*4 +1]*256
            g16b = utile[i*4 +2] +utile[i*4 +3]*256
            self.print("DECIMAL=",str(g32),'['+str(g16a)+','+str(g16b)+']')
                                            
    def send_code_and_wait(self, code, mnemo_retour=None, timeout=1):
        cmd=self.send_code(code)
        if cmd and mnemo_retour is None:
            mnemo_retour = cmd['mnemo']
        if cmd:
            self.print_log(cmd)
            return self.wait_mnemo(mnemo_retour)			 

    def send_mnemo(self, mnemo):	
        print(self.decom.mnemo2code(mnemo))	
        cmd = self.device.send_code(self.decom.mnemo2code(mnemo) )
        cmd['mnemo']=mnemo

        if cmd:
            self.print_log(cmd)
        return cmd

    def send_mnemo_bad_crc(self, mnemo):	
        cmd = self.device.send_badcode(self.decom.mnemo2code(mnemo))
        if cmd:
            self.print_log(cmd)
        return cmd
        
    def send_mnemo_and_wait(self, mnemo, mnemo_retour=None):
        """envoie une commande et attend timeout secondes le mnemo de retour"""
        cmd = self.send_mnemo(mnemo)
        
        if cmd :
            if mnemo_retour is None:
                mnemo_retour=mnemo

            return self.wait_mnemo(mnemo_retour)
            
    def wait_mnemo(self, mnemo_retour):
        self.en_attente=self.decom.mnemo2code(mnemo_retour)
        
    def read_next(self):
        #print("stack {} / {}".format(len(self.device.in1), len(self.device.in2)))
        
        data = self.device.read_measure()
        #print("data dans read_next", data)
        if data:
            self.decom.completedata(data)
            
            self.add_decom(data)

            
            cond_wait = self.en_attente and self.decom.compatible_code(DecomNano.msgtrame(data['binary']), self.en_attente)					
            cond_verb = (not self.quiet or cond_wait or data['mnemo'] in self.filters_only) and data['mnemo'] not in self.filters_mask
                
            #self.print_log(data, not cond_verb)
            
            if cond_wait:
                self.en_attente = None
			
				
    def wait_timeout(self, timeout=0):
        t_max = time.perf_counter() + timeout
        cond = True
        
        while cond:
            self.read_next()
            cond = time.perf_counter() < t_max

    #pour consigner la donnee et pouvoir l'enregistrer
    def add_decom(self, data):
        if data:
            mnemo = data['mnemo']
            decom = self.decom.decomdata(data)
            decom["time"] = round(datetime.now().timestamp()*1000)
            mnemo_masked = []
            mnemo_masked.append("alive")
            mnemo_masked.append("execute")

            if mnemo not in mnemo_masked:
                if mnemo not in self.decomdata:
                    self.decomdata[mnemo] = deque()
                self.decomdata[mnemo].append(decom)
        

    """def print_decom(self, data, quiet=False):
        if data:				
            sortie = "XXXXXX"
            sortie += ";"+"mnenmo:"+mnemo
            if 'timestamp' in decom:
                sortie += ";"+"time:"+"{0:0.03f}".format(decom['timestamp'])
            for param in decom.keys():
                if param != 'mnemo' and param != 'timestamp':
                    if isinstance(decom[param], int):
                        sortie += ";"+param+":"+str(decom[param])
                        #sortie += ";"+param+":"+"0x{:02x}".format(decom[param])
                    else:
                        sortie += ";"+param+":"+str(decom[param])
            #on marque dans le log
            self.print(sortie)
            #on affiche dans la sortie standard
            if not quiet:
                print(sortie)"""

    def print_log(self, data, quiet=False):
        if data:		
            commentaire = ""
            
            if 'mnemo' in data:
                mnemo = data['mnemo']+" ("+data['cr']+")" if 'cr' in data else data['mnemo']
                
                if 'sending-time' in data:
                    commentaire = "{} {:0.03f}s : {} : {} [{}]".format(data['direction'], data['sending-time'], mnemo, _str_hex(data['binary']), "OK" if data['return'] else "KO")
                elif 'reception-time' in data:
                    if 'time' in data:				  
                        commentaire = "{} {:0.03f}s : {} : {} (delta={:+0.04f}s) : {}".format(data['direction'], data['reception-time'], mnemo,
                                        data['time'], data['time'] - data['reception-time'] +data['offset'], _str_hex(data['binary']))
                    else:
                        commentaire = "{} {:0.03f}s : {} :  : {}".format(data['direction'], data['reception-time'], mnemo, _str_hex(data['binary']))
                else:
                    commentaire = "{} error {}".format(data['direction'], data)
                    
            else:				
                #erreur donc
                message = "{}".format(data['return'])
                if 'comment' in data:
                    message+="({})".format(data['comment'])

                if 'sending-time' in data:
                    #commande
                    commentaire = "{} {:0.03f}s : {} : {}".format(data['direction'], data['sending-time'], message, _str_hex(data['binary']))
                elif 'reception-time' in data:
                    commentaire = "{} {:0.03f}s : {} :  : {}".format(data['direction'], data['reception-time'], message, _str_hex(data['binary']))
                else:
                    commentaire = "{} error {}".format(data['direction'], data)

            self.print(commentaire)
            if not quiet:
                print(commentaire)
                
                
    def interactive(self, commands=None, data=None):	
        #propose l'envoi de commande ou l'affichage de data
        #commands est une liste de commandes potentielles et data une liste de donnees
        #si commands ou data ne sont pas donn�s, on propose ceux de la bds
        print("interactive")
        mode_quiet = self.quiet
        self.quiet = True
        definitions = {}
        prop = ord('a')
        b_fin = False
        
        if commands is None:
            commands = []
            for item in self.decom.mnemos:
                if 'send' in self.decom.mnemos[item] and self.decom.mnemos[item]['send']:
                    if item[:7]!='service':
                        commands.append(item)
            for item in self.decom.samples:
                if item[:7]!='service':
                    commands.append(item)

        print(commands)


                    
        if data is None:
            data = []
            for item in self.decom.mnemos:
                if 'receive' not in self.decom.mnemos[item] or self.decom.mnemos[item]['receive']:
                    if item[:7]!='service':
                        data.append(item)
        print(data)
            
        if commands is not None:
            prop = ord('a')
            for item in commands:
                definitions[chr(prop)] = {'command':item}
                prop +=1
                
        if data is not None:
            prop = ord('A')
            for item in data:
                definitions[chr(prop)] = {'data':item}
                prop +=1
                
        input = '?'

        print(definitions)
        msvcrt.getch()
        
        while not b_fin:
            print("bfin")
            if input == ' ' or input == '?':
                #on r�-affiche les commandes ?
                for prop in definitions:
                    if 'command' in definitions[prop]:
                        print(prop,":", "command", definitions[prop]['command'])
                    elif 'data' in definitions[prop]:
                        print(prop,":", "data", definitions[prop]['data'])
                print()
                print(0, ":", "EXIT")
                
            elif input in definitions:
                print("input", input)
                if 'command' in definitions[input]:

                    mnemo = definitions[input]['command']
                    print(mnemo)
                    cmd = self.send_mnemo_and_wait(mnemo) 
                    #if cmd:
                    #	self.wait_mnemo(mnemo)
                elif 'data' in definitions[input]:
                    mnemo = definitions[input]['data']
                    if mnemo in self.decomdata:
                        print(self.decomdata[mnemo][-1])
                    else:
                        print(mnemo, 'no data')

            #on attend le prochain touche
            while not msvcrt.kbhit():
                self.wait_timeout(0.2)

            tap = msvcrt.getch()
            input = tap.decode('ASCII')
            if input == '0':
                b_fin = True
            elif input == '1' or input==1:
                self.device.enable_contact(self.decom.mnemo2code('alive'))
            elif input == '2':
                self.device.disable_contact()
                            
        self.quiet = mode_quiet
				

    def batch(self, progfile):
        with open(progfile,"r") as prog :
            for line in prog:
                #on enleve le retour ligne
                line=line.strip()
                #on decoupe par espace
                args = line.split()
                #ligne blanche
                self.print2("")
                self.print2("************************************", line, "************************************")
                self.print2("")
                if not line or line.isspace():
                    self.print2(line)
                    pass
                #commentaire
                elif len(line)>0 and str(line[0])=='#':
                    self.print2(line)
                elif args[0] == "send_bad_crc" and len(args) == 2:
                    mnemo = args[1]
                    cmd = self.send_mnemo_bad_crc(mnemo) 
                    if cmd:
                        self.wait_mnemo(mnemo)
                elif args[0] == "send_and_wait" and len(args) == 2:
                    mnemo = args[1]
                    cmd = self.send_mnemo(mnemo) 
                    if cmd:
                        self.wait_mnemo(mnemo)					  
                elif args[0] == "send_and_wait" and len(args) == 3:
                    mnemo = args[1]
                    mnemo_retour = args[2]
                    cmd = self.send_mnemo(mnemo) 
                    if cmd:
                        self.wait_mnemo(mnemo_retour)					 
                elif args[0] == "send_and_wait" and len(args) == 4:
                    mnemo = args[1]
                    mnemo_retour = args[2]
                    delay = int(args[3])
                    cmd = self.send_mnemo(mnemo) 
                    if cmd:
                        self.wait_mnemo(mnemo_retour, delay)					
                elif args[0] == "send_and_wait_ascii" and len(args) == 2:
                    mnemo = args[1]
                    mnemo_retour = mnemo
                    cmd = self.send_mnemo(mnemo) 
                    if cmd:
                        retour=self.wait_mnemo(mnemo_retour)
                        self.print_ascii(mnemo_retour, retour)
                elif args[0] == "interactive" and len(args) == 2:
                    liste_commandes = args[1].split(',')
                    self.interactive(liste_commandes)
                elif args[0] == "interactive" and len(args) == 3:
                    liste_commandes = args[1].split(',')
                    liste_data = args[2].split(',')
                    self.interactive(liste_commandes, liste_data)
                elif args[0] == "maintenance_unit" and len(args) == 3:
                    mnemo = args[1]
                    mnemo_result = args[2]
                    cmd = self.send_mnemo(mnemo) 
                    if cmd:
                        retour=self.wait_mnemo(mnemo)
                        t = time.perf_counter()
                        timeout = 120
                        while time.perf_counter() < t+timeout:
                            self.wait_timeout(5)
                            self.send_mnemo('serviceStatus')
                            cr=self.wait_mnemo('serviceStatus')
                            if cr['resp'][-1]==0:
                                break
                        self.send_mnemo('serviceStop')
                        self.send_mnemo('serviceStatus')
                        self.wait_mnemo('serviceStatus')
                        self.send_mnemo(mnemo_result)
                        retour = self.wait_mnemo(mnemo_result)
                        self.print_decimal(mnemo_result, retour)
                elif args[0] == "maintenance_cuff" and len(args) == 4:
                    mnemo = args[1]
                    mnemo_retour = args[2]
                    mnemo_result = args[3]
                    if mnemo in self.decom.samples:
                        cmd = self.send_code(bytes(self.samples[mnemo])) 
                    if cmd:
                        retour=self.wait_mnemo(mnemo_retour)
                        t = time.perf_counter()
                        timeout = 30
                        while time.perf_counter() < t+timeout:
                            self.wait_timeout(5)
                            self.send_mnemo('serviceStatus')
                            cr=self.wait_mnemo('serviceStatus')
                            if cr['resp'][-1]==0:
                                break
                        self.send_mnemo('serviceStop')
                        self.send_mnemo('serviceStatus')
                        self.wait_mnemo('serviceStatus')
                        self.send_mnemo(mnemo_result)
                        retour = self.wait_mnemo(mnemo_result)
                        self.print_decimal(mnemo_result, retour)
                elif args[0] == "wait" and len(args)==2 and args[1].isdecimal:
                    temps = float(args[1])
                    self.wait_timeout(temps)
                elif args[0] == "enable_contact" and len(args) == 1:
                    self.device.enable_contact()
                elif args[0] == "disable_contact" and len(args) == 1:
                    self.device.disable_contact()
                elif args[0] == "pause":
                    instruction = ["======="]+args[1:]+["======="]
                    print("")
                    print(*instruction)
                    print("")
                    while not msvcrt.kbhit():
                        self.wait_timeout()
                    msvcrt.getch()
                elif args[0] == "input" and len(args) > 2:
                    instruction = args[1:]
                    print(">>>>>>>>", instruction, "<<<<<<<<")
                    while not msvcrt.kbhit():
                        self.wait_timeout()
                    msvcrt.getch()
                elif args[0] == "mask" and len(args) == 2:
                    mnemo = args[1]
                    self.print_mnemo_filters(mask=mnemo)
                elif args[0] == "mask_reset" and len(args) == 1:
                    self.print_mnemo_filters(reset=True)
                elif args[0] == "abort" and len(args) ==1:
                    #on sort
                    return
                else:
                    print("error", line[0], line, file=sys.stderr)


    def send_buffered_data(self):
        #On crée une copie de self.decomdata
        data_to_send = self.decomdata
        #On vide self.decomdata
        self.decomdata = {}
        #On envoie les données enregistrée dans data_to_send par mnemo
        for mnemo in data_to_send:
            self.send_data(expediteur=self.name, paquet=mnemo, dict_message=list(data_to_send[mnemo]))


    """
    Processus principal du superviseur CAP
    Reçoit et envoie des messages, traduit les commandes en trame et les trames en message
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()
        check_data = time.perf_counter()
        self.device.enable_contact(self.decom.mnemo2code('alive'))

        while keypress != 'q' and self.running:
            ## les commandes claviers
            if keypress and keypress == 'e':
                logging.info("Touche clavier 'e' appuyée")
                self.send_mnemo_and_wait("executeStart") 

            elif keypress and keypress == '1':
                logging.info("Touche clavier '1' appuyée")
                self.device.enable_contact(self.decom.mnemo2code('alive'))

            elif keypress and keypress == 'f':
                logging.info("Touche clavier 'f' appuyée")
                self.send_mnemo_and_wait("executeStop")

            elif keypress and keypress == 's':
                logging.info("Touche clavier 's' appuyée")
                self.send_mnemo_and_wait("patient_female")

            elif keypress and keypress == 'p':
                logging.info("Touche clavier 'p' appuyée")
                
                print(self.decomdata["measure"][-1])

            # Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            self.read_next()
            if time.perf_counter() > check_data+0.5: 
                self.send_buffered_data()
                check_data = time.perf_counter()



            keypress = kb_func()

        logging.info("Service fini")
        

    def print_action(self, action):
        print(action)

    def bds_command(self,mnemo):
        cmd = self.send_mnemo_and_wait(mnemo)

    def bds_data(self, mnemo):
        if mnemo in self.decomdata:
            print(self.decomdata[mnemo][-1])
        else:
            print(mnemo, 'no data')

    def define_action(self):
        actions = [{"nom": "stop", "function": self.stop}]
        liste = []

        for item in self.decom.mnemos:
            if 'send' in self.decom.mnemos[item] and self.decom.mnemos[item]['send']:
                if item[:7]!='service':
                    actions.append({"nom": item, "function": partial(self.bds_command, item)})

        for item in self.decom.samples:
            if item[:7]!='service':
                actions.append({"nom": item, "function": partial(self.bds_command, item)})

        for item in self.decom.mnemos:
            if 'receive' not in self.decom.mnemos[item] or self.decom.mnemos[item]['receive']:
                if item[:7]!='service':
                    actions.append({"nom": item, "function": partial(self.bds_data, item)})

       
        return actions


    def traiterData(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")

    def traiterLog(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")


if __name__ == '__main__':
    logging.info('starting')
    name = "CAP"
    abonnement = []
    nano = Nano("COM6")
    decom = DecomNano()
    decom.add_sampletrames("nano_samples.yml")
    CAP_spv = SPV_CAP(HOST, PORT, name, abonnement, nano, decom)
    CAP_spv.service()

    CAP_spv.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(CAP_spv.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(CAP_spv.read_thread.name))




