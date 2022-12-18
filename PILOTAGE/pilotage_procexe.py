#!/usr/bin/env python3


""" Nom du module : ProcEXE"""

""" Description """
""" Version 1 """
""" Date : 17/12/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

from functools import partial
import glob
import logging
import queue
import random
import sys
import socket
import time

from pilotage_lib import NetworkItem

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________

"""
Elle permet l’exécution séquentielle de commandes issues de fichiers textes.
"""
class ProcExec(NetworkItem):
    def __init__(self, host, port, name, abonnement, proc_dir):
        NetworkItem.__init__(self, host, port, name, abonnement)
        """Liste des procédures à éxécuter, contient seulement les noms des fichiers"""
        self.proc2exec = []
        self.encours = None
        self.proc_dir = proc_dir
        self.proc_list = []
        self.list_procedures()
        
        self.actions_callback = []
        self.actions_name_list = []
        self.set_actions()


    """
    Liste l'ensemble des fichiers de procédures disponibles dans le répertoire proc_dir.

    Le nom d'un fichier de procédure est écrit sous la forme:
    “proc*.txt”

    Retourne une liste contenant les noms de tous les fichiers de procédures.
    """
    def list_procedures(self):
        return glob.glob("proc*.txt", root_dir=self.proc_dir)

    """
    Fonction d'exécution de procédure d'action

    Entrée:
        self (objet courant)
        proc (nom de la procédure à exécuter)
        *karg (arguments supplémentaires éventuels)
    Traitement:
        Si une procédure est en cours d'éxécution,
        on l'ajoute proc dans la liste proc2exec
    Sortie:
        Aucune
    """
    def action_execproc(self, proc, *karg):
        if self.encours is not None:
            self.proc2exec.append(proc)
        else:
            self.prepare_proc(proc)

    def prepare_proc(self, maproc):
		#Log.send("EXECUTION DE {}".format(maproc), level=2, direction="PROC")
		#On initialise le contexte: variable représentant l'instruction à éxécuter
        contexte = {'name' : maproc, 'position':0, 'statements':self.charge_proc(maproc)}
		#On lance l'execution de la 1ere ligne
        self.encours = contexte
        self.execnextstatement()


    """
    Charge une procédure à partir d'un fichier de procédure.

    Parametres:
    name (str): Nom du fichier de procédure.

    Returns:
    List[str]: Liste des lignes valides (non vides / pas de commentaires) de la procédure.
    """
    def charge_proc(self, name):
        with open(self.proc_dir + name, 'r') as f: # Ouvre le fichier de procédure dans le répertoire self.proc_dir en lecture
            statements = [] # Initialise une liste vide pour stocker les statements valides
            for ligne in f: # Pour chaque ligne du fichier
                ligne = ligne.strip()  # Supprime les espaces en début et fin de ligne
                if ligne == '' or ligne.startswith('#'): # Si la ligne est vide ou commence par '#', on l'ignore
                    continue
            statements.append(ligne) # Sinon, on ajoute la ligne à la liste
        return statements  # On retourne la liste des lignes valides

    def execnextstatement(self):
        contexte = self.encours
        
        #Le wait peut être due à deux chose:
        # Une directive pause: on donne un temps de pause à attendre
        # Une directive wait: on attend une réponse
        if 'wait' in contexte:
            if isinstance(contexte['wait'], float):
                t = time.perf_counter()
                if t >= contexte['wait']:
                    #Log.send("attente terminée".format(t, ctx['wait']), level=3, direction="wait")
                    del contexte['wait']
                    contexte['position'] += 1

        position_index = contexte.get("position")
        statements_list = contexte.get("statements")
        nb_statements = len(statements_list)

        if(position_index < nb_statements):
            statement = self.analyse_statement(statements_list[position_index])

            #Log.send(ctx['statements'][ctx['position']], level=3, direction="next")
            if statement['directive']=='pause':
                t0 = time.perf_counter()
                delay = float(statement['statement'])
                contexte['wait'] = t0+delay
            elif statement['directive']=='send':
                if 'srv' not in statement or 'action' not in statement:
                    #on ne comprend pas, on passe au suivant
                    #Log.send(ctx['statements'][ctx['position']], level=3, direction="error")
                    position_index += 1
                else:
                    #on demande l'execution au service via une commande
                    self.send_command(destinataire= statement['srv'], action = statement['action'], params = statement['params'])
                    #self.ask_action(statement['srv'], statement['action'], statement['params'])
                    position_index += 1
            elif statement['directive']=='wait':
                if 'srv' not in statement or 'action' not in statement:
                    #on ne comprend pas, on passe au suivant
                    #Log.send(ctx['statements'][ctx['position']], level=3, direction="error")
                    position_index += 1
                else:
                    #on demande l'execution au service
                    contexte['wait'] = statement
                    self.waitfor(id=self.send_command(destinataire= statement['srv'], action = statement['action'], params = statement['params']), callback=partial(self.answer_statement, contexte))
               
        if statements_list and position_index >= nb_statements:
            #Log.send("EXECUTION OVER", level=2, direction="PROC")
            self.encours = None
            #on prend la prochaine
            if self.proc2exec:
                self.prepare_proc(self.proc2exec.pop(0))
    
    def analyse_statement(self, statement):
        posdirective = statement.find(":")
        if posdirective>-1:
            directive = statement[:posdirective].lower() #Tout ce qui a avant ":"
            statement = statement[posdirective+1:] #Tout ce qui a après ":"

            posparam = statement.find("(") #index de la parenthèse ouvrante
            posfinparam = statement.rfind(")") #index de la parenthèse fermante
            if posparam>-1 and posfinparam>-1: #Si on a bien les deux parenthèses
                params = statement[posparam+1:posfinparam] #Tout ce qui a entre les parenthèses
                ignore = statement[posfinparam+1:] #On veut ignorer ce qui a après les parenthèses
                if len(ignore)!=0:
                    print("statement", statement,"| ignore=[{}]".format(ignore))
                statement = statement[:posparam] #On enlève les parenthèses et les paramètres
                decoup = statement.split('.') #on regarde si on a donnée un service (utilisation de '.')
                if len(decoup) > 1:
                    return {'directive':directive, 'statement':statement, 'srv':decoup[0], 'action':".".join(decoup[1:]), 'params':params.split(',\s*')}
                else:
                    return {'directive':directive, 'statement':statement, 'params':params.split(',\s*')}
            else:
                return {'directive':directive, 'statement':statement}



    def answer_statement(self, contexte, *karg):
        print("Réponse reçue", karg)
        if 'wait' in contexte:
            #Permet de retirer le wait pour passer à l'instruction suivante
            del contexte['wait']
            contexte['position'] += 1

    #TODO vérifie que l'on envoit bien les actions
    def set_actions(self):
        for proc in self.proc_list:
            self.actions_callback.append({"nom":'exe_execproc__{}'.format(proc), "action": partial(self.action_execproc, proc)})
            self.actions_name_list.append('exe_execproc__{}'.format(proc))

    
    def traiterMessage(self, message):
        message_type = message.get("type")
        if message_type is not None and message_type == "CMD": #On ne traite que les commandes
            #message
            pass


    """
    Essayer de récupérer un message de la file d'attente. 
    Cet appel va lever une exception queue.Empty si la file est vide.
    """
    def getMessage(self):
        try:
            message = self.queue_message_to_process.get(block=False)
            return message
        except queue.Empty:
            #print("Queue empty")
            return None

    def get_action_callback(self,message_action):
        for action_dict in self.actions_callback:
            if action_dict.get("nom") == message_action:
                return action_dict.get("action")


    def traiterMessage(self, message):
        if message is not None and message_type == "CMD": #On ne traite que les commandes
            message_type = message.get("type")
            logging.info(f"message reçu :{message}")
            message_id = message.get("id")
            message_action = message.get("action")

            if message_id in self._waitfor: #Si c'est une réponse à un message attendu
                func_callback = self._waitfor[message_id]["callback"]
                func_callback()
            elif message_action in self.actions_name_list: #demande d'exécution d'une action
                action_callback = self.get_action_callback(message_action)
                pass


            #TODO vérifier 

    """
    Processus principal du procExec
    """
    def service(self):
        #TODO prévoir le kbhit
        while True:
            message = self.getMessage()
            self.traiterMessage(message)
            
            

            



def testPartial(message):
    print(message)

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)
    name = sys.argv[1]
    abonnement = []

   
    server = ProcExec(host=HOST, port=PORT, name=name, abonnement=abonnement, proc_dir="./Procedures/")
    # class Superviseur qui hérite de NetworkItem, qui redef service
    server.service()

    server.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(server.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(server.read_thread.name))

    # server.serve_forever()