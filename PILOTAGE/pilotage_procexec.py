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
import sys
import socket
import time

from pilotage_lib import NetworkItem, kb_func

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
        """Liste des procédures qui sont à éxécuter en mode FIFO, contient seulement les noms des fichiers"""
        self.proc2exec = []
        """Structure contenant des informations sur la procédure en cours d'éxécution sous forme de dict, None sinon"""
        self.encours = None
        """Répertoire contenant les fichiers de procédures"""
        self.proc_dir = proc_dir
        """Liste des fichiers de procédures disponibles dans le répertoire proc_dir"""
        self.proc_list = self.list_procedures()
        NetworkItem.__init__(self, host, port, name, abonnement)


    """
    Liste l'ensemble des fichiers de procédures disponibles dans le répertoire proc_dir.

    Le nom d'un fichier de procédure est écrit sous la forme:
    “proc*.txt”

    Retourne une liste contenant les noms de tous les fichiers de procédures.
    """
    def list_procedures(self):
        return glob.glob("proc*.txt", root_dir=self.proc_dir)

    
    
    """
    Fonction définissant les actions du ProcEXE

    Entrée:
        self (objet courant)
    Traitement:
        Pour chaque action dans la liste self.proc_list
    Sortie:
        La liste des actions (nom->str et function->callable)
    """
    #TODO tester l'envoie et la validité des actions
    def define_action(self):
        actions = [{"nom":"stop","function": self.stop}]
        
        for proc in self.proc_list:
            actions.append({"nom":'exe_execproc__{}'.format(proc),"function": partial(self.action_execproc, proc)})

        return actions

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

                    self.send_cmd(destinataire= statement['srv'], action = statement['action'], params = statement['params'])
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
                    self.waitfor(id=self.send_cmd(destinataire= statement['srv'], action = statement['action'], params = statement['params']), callback=partial(self.answer_statement, contexte))
               
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


    """
    Lorsque l'on reçoit une réponse qui est attendu, on répond en conséquence,
    Ici on supprime simple la valeur de "wait" dans "contexte"
    """
    def answer_statement(self, contexte, *karg):
        print("Réponse reçue", karg)
        if 'wait' in contexte:
            #Permet de retirer le wait pour passer à l'instruction suivante
            del contexte['wait']
            contexte['position'] += 1

    def traiterCommande(self, commande):
        commande_id = commande.get("id")
        commande_action = commande.get("action")

        if commande_id in self._waitfor: #Si c'est une réponse à un message attendu
            func_callback = self._waitfor[commande_id]["callback"]
            func_callback()
        elif commande_action in self.get_action(): 
            action_callback = self.get_action_callback(commande_action)
            action_callback(commande) 
        else:
            logging.info("Commande non reconnue")

    def traiterData(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type DATA")

    def traiterLog(self, data):
        logging.info(f"Le {self.name} ne traite pas les messages de type LOG")


    """
    Processus principal du procExec
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")

            #Réception
            self.traiterMessage(self.getMessage())
					
                    
            keypress = kb_func()
        logging.info("Service fini")
            
            

            

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "PROCEXEC"
    abonnement = []

   
    proc_exe = ProcExec(host=HOST, port=PORT, name=name, abonnement=abonnement, proc_dir="./Procedures/")
    # class Superviseur qui hérite de NetworkItem, qui redef service
    proc_exe.service()

    proc_exe.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(proc_exe.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(proc_exe.read_thread.name))

    # server.serve_forever()