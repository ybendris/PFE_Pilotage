""" Nom du module : ProcEXE"""

""" Description """
""" Version 1 """
""" Date : 17/12/2022"""
""" Auteur : Equipe CEIS """

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


    def list_procedures(self):
        """
        Récupère la liste de tous les fichiers de procédures du répertoire 'proc_dir'.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            list: Une liste contenant les noms de tous les fichiers de procédures.
        """
        return glob.glob("proc*.txt", root_dir=self.proc_dir)


    def define_action(self):
        """
        Définit les actions disponibles dans le ProcEXE.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            list: Une liste d'actions sous la forme de dictionnaires contenant un nom (str) et une fonction (callable).
        """
        actions = [{"nom":"stop","function": self.stop}]
            
        for proc in self.proc_list:
            actions.append({"nom":'exe_execproc__{}'.format(proc),"function": partial(self.action_execproc, proc)})
        return actions

    
    def action_execproc(self, proc, *karg):
        """
        Exécute une procédure d'action.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            proc (str): Le nom de la procédure à exécuter.
            *karg: Arguments supplémentaires éventuels.

        Returns:
            None
        """
        if self.encours is not None:
            self.proc2exec.append(proc)
        else:
            self.prepare_proc(proc)


    def prepare_proc(self, maproc):
        """
        Prépare l'exécution d'une procédure.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            maproc (str): Le nom du fichier de procédure.

        Returns:
            None
        """
        #Log.send("EXECUTION DE {}".format(maproc), level=2, direction="PROC")
        #On initialise le contexte: variable représentant l'instruction à éxécuter
        contexte = {'name' : maproc, 'position':0, 'statements':self.charge_proc(maproc)}
        if len(contexte['statements']) != 0:
            #On lance l'execution de la 1ere ligne
            self.encours = contexte
            logging.info("EXECUTION START")
            self.execnextstatement()


    def charge_proc(self, name):
        """
        Charge une procédure à partir d'un fichier de procédure.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            name (str): Nom du fichier de procédure.

        Returns:
            list[str]: Liste des lignes valides (non vides / pas de commentaires) de la procédure.
        """
        statements = [] # Initialise une liste vide pour stocker les statements valides
        try:
            with open(self.proc_dir + name, 'r') as f: # Ouvre le fichier de procédure dans le répertoire self.proc_dir en lecture
                for ligne in f: # Pour chaque ligne du fichier
                    ligne = ligne.strip()  # Supprime les espaces en début et fin de ligne
                    if ligne == '' or ligne.startswith('#'): # Si la ligne est vide ou commence par '#', on l'ignore
                        continue
                    statements.append(ligne) # Sinon, on ajoute la ligne à la liste
        except FileNotFoundError:
            logging.info(f"Le fichier {name} n'a pas été trouvé")

        return statements  # On retourne la liste des lignes valides


    def execnextstatement(self):
        """
        Exécute la prochaine instruction de la procédure en cours d'exécution.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.

        Returns:
            None
        """
        contexte = self.encours
        
        if contexte is not None:
            #Le wait peut être due à deux chose:
            # Une directive pause: on donne un temps de pause à attendre
            # Une directive wait: on attend une réponse
            if contexte.get('wait') and 'wait' in contexte: 
                if isinstance(contexte['wait'], float):
                    t = time.perf_counter()
                    if t >= contexte['wait']:
                        #Log.send("attente terminée".format(t, ctx['wait']), level=3, direction="wait")
                        logging.info("Attente terminée")
                        del contexte['wait']
                        contexte['position'] += 1

            elif contexte["statements"] is not None and contexte["position"] is not None:
                nb_statements = len(contexte["statements"])
                if(contexte["position"] < nb_statements):
                    statement = self.analyse_statement(contexte["statements"][contexte["position"]])
                    #Log.send(ctx['statements'][ctx['position']], level=3, direction="next")
                    if statement is not None and statement['directive']=='pause':
                        t0 = time.perf_counter()
                        delay = float(statement['statement'])
                        contexte['wait'] = t0+delay
                    elif statement is not None and statement['directive']=='send':
                        if 'srv' not in statement or 'action' not in statement:
                            logging.info("on ne comprend pas, on passe au suivant")
                            #Log.send(ctx['statements'][ctx['position']], level=3, direction="error")
                            contexte["position"] += 1
                        else:
                            #on demande l'execution au service via une commande
                            self.ask_action(destinataire= statement['srv'], action = statement['action'], list_params = statement['params'])
                            #self.ask_action(statement['srv'], statement['action'], statement['params'])
                            contexte["position"] += 1
                            #print(f"position_index {contexte['position']}")
                    elif statement is not None and statement['directive']=='wait':
                        if 'srv' not in statement or 'action' not in statement:
                            #on ne comprend pas, on passe au suivant
                            #Log.send(ctx['statements'][ctx['position']], level=3, direction="error")
                            contexte["position"] += 1
                        else:
                            #on demande l'execution au service
                            contexte['wait'] = statement
                            self.waitfor(id=self.ask_action(destinataire= statement['srv'], action = statement['action'], list_params= statement['params']), callback=partial(self.answer_statement, contexte))
                
                if contexte["statements"] and contexte["position"] >= nb_statements:
                    logging.info("EXECUTION OVER")

                    self.encours = None
                    #on prend la prochaine
                    if self.proc2exec:
                        self.prepare_proc(self.proc2exec.pop(0))
    

    def analyse_statement(self, statement):
        """
        Analyse une instruction et en extrait la directive et les paramètres.

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            statement (str): L'instruction à analyser.

        Returns:
            dict: Un dictionnaire contenant la directive, l'instruction, le nom du service (si applicable), l'action (si applicable) et les paramètres (si applicable).
        """
        posdirective = statement.find(":")
        if posdirective>-1:
            directive = statement[:posdirective].lower() #Tout ce qui a avant ":"
            statement = statement[posdirective+1:] #Tout ce qui a après ":"

            posparam = statement.find("(") #index de la parenthèse ouvrante
            posfinparam = statement.rfind(")") #index de la parenthèse fermante
            if posparam>-1 and posfinparam>-1: #Si on a bien les deux parenthèses
                params:str = statement[posparam+1:posfinparam] #Tout ce qui a entre les parenthèses
                ignore = statement[posfinparam+1:] #On veut ignorer ce qui a après les parenthèses
                if len(ignore)!=0:
                    print("statement", statement,"| ignore=[{}]".format(ignore))
                statement = statement[:posparam] #On enlève les parenthèses et les paramètres
                decoup = statement.split('.') #on regarde si on a donnée un service (utilisation de '.')
                if len(decoup) > 1:
                    return {'directive':directive, 'statement':statement, 'srv':decoup[0], 'action':".".join(decoup[1:]), 'params':params.split(sep=',\s*')}
                else:
                    return {'directive':directive, 'statement':statement, 'params':params.split(sep=',\s*')}
            else:
                return {'directive':directive, 'statement':statement}


    def answer_statement(self, contexte, *karg):
        """
        Traite la réponse à une instruction en attente.
        Ici on supprime simple la valeur de "wait" dans "contexte"

        Parameters:
            self (object): L'objet sur lequel est appelée la méthode.
            contexte (dict): Le contexte de l'instruction en attente.
            *karg: Les arguments de la réponse.

        Returns:
            None
        """
        print("Réponse reçue", karg)
        if 'wait' in contexte:
            #Permet de retirer le wait pour passer à l'instruction suivante
            del contexte['wait']
            contexte['position'] += 1


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
        while keypress != 'q' and self.running:			
            ## les commandes claviers
            if keypress and keypress == 'a':
                logging.info("Touche clavier 'a' appuyée")
                self.action_execproc("proc_test.txt")

            if keypress and keypress == 'z':
                logging.info("Touche clavier 'z' appuyée")
                self.action_execproc("proc_test_pause.txt")


            self.execnextstatement()

            time.sleep(0.5)
            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()
        logging.info("Service fini")
            


            
#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "PROCEXEC"
    abonnement = []

   
    proc_exe = ProcExec(host=HOST, port=PORT, name=name, abonnement=abonnement, proc_dir="./Procedures/")
    # class ProcExec qui hérite de NetworkItem, qui redef service
    proc_exe.service()

    proc_exe.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(proc_exe.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(proc_exe.read_thread.name))
