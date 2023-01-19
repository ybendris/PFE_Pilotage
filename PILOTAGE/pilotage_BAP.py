""" Nom du module : HubSupervisor"""

""" Description Le superviseur du BAP, il peut communiquer avec le central"""
""" Version 1 """
""" Date : 16/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________
import logging
import socket
import serial
import time
import sys
from pilotage_lib import NetworkItem, kb_func

#  ____________________________________________________ CONSTANTES _____________________________________________________
HOST = 'localhost'
PORT = 65432

#  _______________________________________________ FONCTIONS GLOBALES _______________________________________________
#convertit une chaine binaire en hexa
def str_hex(octets):
    chaine = ""
    for o in octets:
        chaine = chaine + "."+hex(o)
    return chaine

#  _______________________________________________ DEFINITION DE CLASSES _______________________________________________


class TonoportDataDesc:
#gere les donnees echangees avec le tonoport
    def __init__(self, desc = None, taille = 0):
        if desc is None:
            desc = [{'nom':'val', 'taille':taille}]
        self.description = desc
        self.taille = 0
        for d in self.description:
            self.taille += d['taille']
        self.taille += 1 + 2 # 1 octets en entete et 2 octets en fin

    #affichage des octets transmis par le BAP
    def to_hex(self, octets):
        chaine = str_hex(octets[0:1]) # initialisation avec l'entete
        deb = 1 #on zappe le caractere d'entete
        fin = len(octets)-2
        for d in self.description:
            if chaine:
                chaine += "\n"
            if deb < fin :
                longueur = d['taille']
                val = octets[deb:deb+longueur]
                chaine += str_hex(val)
                deb += longueur
        chaine += "\n" + str_hex(octets[fin:fin+2])
        return chaine 

    #permet affichage des réponses du BAP, renvoit le dico qui contient toute les données
    def to_dico(self, octets):
        deb = 1
        fin = len(octets)-2
        dico = {}
        for d in self.description:            
            if deb < fin :
                longueur = d['taille']
                nom = d['nom']
                val = octets[deb:deb+longueur]
                if nom == 'heure_tnp':
                    print("test deb")
                    print(deb)
                    print("test val")
                    print(val)
                    val = TonoportDataDesc.data2time(val)
                elif nom != "cr":
                    print(nom,val)
                    val = ord(val)
                    
                if not 'trash' in 'd' or d['trash'] == False:
                    dico[nom] = val
                deb += longueur
        return dico

    #convertit date de l'ordi ou donnée en param en date compréhensible par le BAP
    def time2data(tps = None):
        time_struct = 0
        if tps is None or isinstance(tps, int):
            time_struct = time.localtime(tps)
        elif isinstance(tps, str):
            time_struct = time.strptime(time, "%Y/%m/%d %H:%M:%S")
        
        data = [
                time_struct[5] % 10, time_struct[5] // 10, #sec 
                time_struct[4] % 10, time_struct[4] // 10, #min
                time_struct[3] % 10, time_struct[3] // 10, #heure
                time_struct[2] % 10, time_struct[2] // 10, #jour
                1,                                         #fixe
                time_struct[1] % 10, time_struct[1] // 10, #mois
                0,                                          #fixe
                time_struct[0] % 10, time_struct[0] // 10 % 10, #annee
                ]
        return bytes(data)

    #convertit date au format BAP vers un format classique (AAAA/MM/JJ HH:Min:Sec)
    def data2time(octets):
        temps = (
            2000 + int(octets[10]) + int(octets[11])*10,
            int(octets[8]) + int(octets[9])*10,
            int(octets[6]) + int(octets[7])*10,
            int(octets[4]) + int(octets[5])*10,
            int(octets[2]) + int(octets[3])*10,
            int(octets[0]) + int(octets[1])*10
        )

        return "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(*temps)

    #lecture de la réponse, le nb d'octet lu correspond au champ taille de l'objet DataDesc
    def read(self, serie, attente = True):
        tentative = 10 if attente else 0
        res = serie.read(self.taille)
        #on fait 4 tentatives maximum
        while tentative >0 and len(res) == 0:
            res = serie.read(self.taille)
            tentative -= 1
        return res

    #fonction permettant de traduire les chaines pour les infos patient
    def formatage(chaine,cmd):       
        chainehex=""

        match cmd:
            case "number":
                taille=10 
            case "name":
                taille=28
            case "sex":
                taille=1
            case other:
                return -1

        longueur=len(chaine)
        #Erreur Si la chaine voulue est plus longue que la taille du champs max 
        if longueur>taille:
            return -1
        else: 
            #ajout de caractères pour former une chaine de la bonne longueur  
            if (taille-longueur)>=1:
                trame=" "
                for i in range(taille-longueur-1):
                    trame+=" "
                chaine+=trame

                chainehex=bytes(chaine,'utf-8')
            return chainehex   

#classe permettant l'envoi des commandes au BAP
class TonoportCmd:
#description d'une commande a traiter
    def __init__(self, no, taille, mode = 'get', data_desc = None):
        self.no = no            #octet utilisé dans la trame de la commande
        self.taille = taille    #taille ?
        self.mode = mode        #mode : get, set, abo (abort)
        self.verrou = False
        if data_desc:           #data
            self.data_desc = data_desc
        else:
            self.data_desc = TonoportDataDesc(taille = taille)

    #prépare la trame de commande
    def binary(self, bytes_param = None):
        if self.mode == 'abo':          #trame pour abort la mesure qui a une forme particulière
            return bytes([self.no])
        elif self.mode == 'pat':
            return bytes([0x02,0x10,self.no])
        else:            
            return bytes([0x02,self.no,0x03])

    #envoie la commande a l'equipement
    def send(self, serie, data_val = None, out = sys.stderr):
        print(str(self),"------------------------", file = out)

        #envoi de la demande initiale
        if self.no is not None:
            print("PC->HLTA", str_hex(self.binary()), file = out)
            serie.write(self.binary())
                        
        #mode get : on recupere une reponse du tonoport et on l'affiche
        if self.mode == 'get': 
            res = self.data_desc.read(serie)
            print("debug res :")
            print(res)
            print("fin debug")
            print("HLTA->PC", self.data_desc.to_hex(res).replace("\n","\nHLTA->PC "), file = out)
            print("HLTA->PC", self.data_desc.to_dico(res), file = out)
            return self.data_desc.to_dico(res)
            
        #mode set : 
        elif self.mode == 'set' or self.mode == 'pat':
            hlta_cr = TonoportDataDesc([{'nom':'cr','taille':2}])
            #on récupère le CR pour vérifier la réception de la commande
            res = hlta_cr.read(serie)
            print("HLTA->PC", hlta_cr.to_hex(res).replace("\n","\nHLTA->PC "), file = out)
            #on envoie les données à set
            if data_val is bytes:
                print("PC->HLTA", str_hex(data_val), file = out)
                serie.write(data_val)
            elif isinstance(data_val, list):
                for b in data_val:
                    print("PC->HLTA", str_hex(b), file = out)
                    serie.write(b)
            #on read le CR
            res2 = hlta_cr.read(serie)
            print("HLTA->PC", hlta_cr.to_hex(res2).replace("\n","\nHLTA->PC "), file = out)
            return res2
        else:
            return None 


class SPV_BAP(NetworkItem):
    def __init__(self, host, port, name, abonnement,out = None):
        NetworkItem.__init__(self, host, port, name, abonnement)
        self.verrou = False
        if out:
            self.out = out
        else:
            self.out = open('nul', 'w')

    def traiterData(self, data):
        pass

    def traiterLog(self, log):
        pass


    """
    Fonction définissant les actions du superviseur du BAP
    """
    def define_action(self):
        actions = [{"nom":"stop","function": self.stop},{"nom":"set_date","function":self.set_date},
        {"nom":"extra_meas","function":self.extra_meas},{"nom":"get_measure","function":self.get_measure},
        {"nom":"erase","function":self.erase},{"nom":"get_version","function":self.get_version},
        {"nom":"check_mem","function":self.check_mem},{"nom":"abort","function":self.abort},{"nom":"stop_meas","function":self.stop_meas},{"nom":"set_nb","function":self.set_nb}]
        return actions

    """
    Processus principal du superviseur du BAP
    """
    def service(self):
        logging.info("Service global lancé")
        keypress = kb_func()		
        while keypress != 'q' and self.running:			
            ## les commandes claviers


            #Réception de la part des messages venant du CENTRAL
            self.traiterMessage(self.getMessage())

            keypress = kb_func()
        logging.info("Service fini")

    """
    fonction permettant de se connecter au port série
    param : port le nom du port utilisé (ex : COM3)
    """
    def connect(self, port = None):
        if port is not None:
            self.port = port
        if self.port:
            self.serie = serial.Serial(port = self.port, baudrate = 9600, timeout = 1)
        else:
            print("connexion impossible : aucun port defini", file = self.out) 


    def disconnect(self):
        if self.serie:
            self.serie.close()

    """
    Traitement de la commande à envoyer
    """
    def traite(self, commande:TonoportCmd, data = None, bloquant = True, timeout = 100):
        #on attend aue le verrou soit libre
        decpt = timeout * 5
        while bloquant == True and self.verrou == True and timeout > 0:
            time.sleep(0.2)
            decpt -= 1
            
        if not self.verrou:
            self.verrou = True
            retour = commande.send(self.serie, data, self.out)
            self.verrou = False
            return retour
        else:
            return False

    def set_date(self):
        #on récupère la date à paramétrer (date courante du PC)
        data = TonoportDataDesc.time2data()
        #on prépare la commande
        hlta_set_time = TonoportCmd(0x08, 14, 'set')
        #on envoie la commande
        SPV_BAP.traite(self,hlta_set_time, [data])

    def extra_meas(self):
        data = None
        hlta_bool = TonoportDataDesc([{'nom':'cr','taille':2}])
        hlta_extra_measure = TonoportCmd(0x1c, 2, 'get', data_desc = hlta_bool)
        SPV_BAP.traite(self,hlta_extra_measure,[data])

    def get_measure(self):
        data = None
        hlta_mesure = TonoportDataDesc([
                                {'nom':'heure_tnp','taille':12},
                                {'nom':'sabp','taille':1},
                                {'nom':'dabp','taille':1},
                                {'nom':'mabp','taille':1},
                                {'nom':'hr','taille':1},
                                {'nom':'trigger','taille':1, 'trash':True},
                                ])
        hlta_get_measure = TonoportCmd(0x05, 17, 'get', data_desc = hlta_mesure) 
        
        
        dict_return = SPV_BAP.traite(self,hlta_get_measure,[data])
        #Envoie sous forme de DATA
        #self.send_data(self.name, paquet="measure_BAP",dict_message=dict_return)
        #Envoie sous forme de réponse à une CMD
        return dict_return

        

    def erase(self):
        data = None
        hlta_bool = TonoportDataDesc([{'nom':'cr','taille':2}])
        hlta_erase_data = TonoportCmd(0x07, 2, 'get', data_desc = hlta_bool)
        SPV_BAP.traite(self,hlta_erase_data,[data])

    def get_version(self):
        data = None
        hlta_version = TonoportDataDesc([{'nom':'version','taille':2}])
        hlta_get_version = TonoportCmd(0x03, 2, 'get', data_desc = hlta_version)
        SPV_BAP.traite(self,hlta_get_version,[data])

    def check_mem(self):
        data = None
        hlta_bool = TonoportDataDesc([{'nom':'cr','taille':2}])
        hlta_get_memory_status = TonoportCmd(0x06, 2, 'get', data_desc = hlta_bool)
        SPV_BAP.traite(self,hlta_get_memory_status,[data])

    def abort(self):
        data = None
        hlta_abort = TonoportCmd(0x78, 0, 'abo')
        SPV_BAP.traite(self,hlta_abort,[data])

    def stop_meas(self):
        data = None
        hlta_bool = TonoportDataDesc([{'nom':'cr','taille':2}])
        hlta_stop_measure = TonoportCmd(0x2a, 2, 'get', data_desc = hlta_bool)
        SPV_BAP.traite(self,hlta_stop_measure,[data])

    #Non fonctionnel
    def set_nb(self):
        data = TonoportDataDesc.formatage("test","number")
        hlta_set_nb = TonoportCmd(0x13,14,'pat')
        SPV_BAP.traite(self,hlta_set_nb,[data])

#  ________________________________________________________ MAIN _______________________________________________________
if __name__ == '__main__':
    name = "BAP"
    abonnement = []

   
    BAP = SPV_BAP(host=HOST, port=PORT, name=name, abonnement=abonnement,out = sys.stderr)
    #connexion au port COM
    try:
        BAP.connect('COM3')
        print('equipement trouve')
    except:
        print("equipement non trouve")
        exit(1)
    # class SPV_BAP qui hérite de NetworkItem, qui redef service
    BAP.service()

    #fermeture de la liaison série
    BAP.disconnect()

    #fermeture de la socket après arrêt de service
    BAP.main_socket.shutdown(socket.SHUT_RDWR)

    # server.write_thread.join()
    logging.info("{} joined ended with main thread".format(BAP.write_thread.name))

    # server.read_thread.join()
    logging.info("{} joined ended with main thread".format(BAP.read_thread.name))