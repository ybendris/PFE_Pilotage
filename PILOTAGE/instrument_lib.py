#!/usr/bin/env python3

""" Nom du module : Librairie"""


""" Description """
""" Version 1 """
""" Date : 07/01/2023"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________


import logging
import sys
import time
from collections import deque
import serial
import crcmod
import os
import yaml


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


crc_func = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim');



def _str_hex(octets):
	chaine = ""
	for o in octets:
		if chaine:
			chaine += "|"+"0x{:02x}".format(o)
		else:
			chaine = "0x{:02x}".format(o)
	return chaine


class DecomFinap:
    def __init__(self):
        # variables pour le ctrl du temps
        self.inittps()

        # variables pour la definition des mnemos
        self.binaries = {}
        # on ouvre le fichier de bds nano
        with open(os.path.join(os.path.dirname(__file__), "bds_nano.yml"), 'r') as bdsnano:
            self.mnemos = yaml.safe_load(bdsnano)

        for cmd in self.mnemos.keys():
            binary = bytes(self.mnemos[cmd]['binary'])
            self.binaries[binary] = cmd

    """
    Récupère des trames spécifiques issues du fichier yaml passé en argument
    """
    def add_sampletrames(self, fic):
        self.samples = {}
        with open(os.path.join(os.path.dirname(__file__), fic), 'r') as samples:
            self.samples = yaml.safe_load(samples)

    """
    Convertit une instruction mnémonique en sa représentation en code binaire.

    Parameters :
    mnemo (str) : L'instruction mnémonique.

    Return :
    octets : La représentation binaire de l'instruction, ou un objet octet vide si le mnémonique ne correspond à aucun code connu.

    Imprime un message "ERROR" si le mnémonique n'est pas trouvé dans les mnémoniques ou échantillons connus.
    """
    def mnemo2code(self, mnemo):
        if mnemo and mnemo in self.mnemos:
            return bytes(self.mnemos[mnemo]['binary'])
        elif mnemo in self.samples:
            return bytes(self.samples[mnemo])
        else:
            print("ERROR", mnemo)

    """
    Retourne si le code code_test est compatible avec le code de référence code_ref.

    Les codes sont considérés compatibles si leur longueur est supérieure à zéro et leur première valeur (masquée par 0x7F) est identique.

    Parameters : 
    code_ref (bytes) : Code de référence.
    code_test (bytes) : Code à tester.
    
    Return: 
    bool : Vrai si les codes sont compatibles, faux sinon.
    """
    def compatible_code(self, code_ref, code_test):
        if code_ref is None or code_test is None:
            return False
        lg = min(len(code_ref), len(code_test))

        return (lg > 0 and code_ref[0] & 0x7F == code_test[0] & 0x7F)

    """
    Verifie la compatibilité entre deux mnémoniques

    Parameters:
    mnemo_ref (str) : mnémonique de référence
    mnemo_test (str) : mnémonique à tester

    Return:
    (bool) : True si les deux mnémoniques sont compatibles, False sinon
    """
    def compatible_mnemo(self, mnemo_ref, mnemo_test):
        if mnemo_ref is None or mnemo_test is None:
            return False
        code_ref = self.mnemo2code(mnemo_ref)
        code_test = self.mnemo2code(mnemo_test)
        return self.compatible_code(code_ref, code_test)

    """
    Renvoie l'horodatage de la trame binaire dans le paramètre trame.

    Parameters :
    trame (octets) : trame binaire dont il faut récupérer l'horodatage

    Return :
    float : horodatage de la trame binaire ou None s'il n'y a pas de mnémonique correspondant
    """
    def timetrame(self, trame):
        mnemo = self.trame2mnemo(trame)
        if mnemo and mnemo in self.mnemos and 'time_position' in self.mnemos[mnemo]:
            pos = self.mnemos[mnemo]['time_position']
            temps_trame = (trame[pos + 4] + trame[pos + 5] * 256) / 200

            return temps_trame

    def cmdtrame(trame):
        return trame[4]

    def cmdgoodtrame(trame):
        return trame[4] & 0x7F

    def msgtrame(trame):
        return bytes([DecomFinap.cmdgoodtrame(trame)]) + trame[5:]

    """
    Convertit une trame binaire en mnémonique

    Parameters:
    trame (bytes) : trame binaire à convertir

    Return:
    (str) : mnémonique correspondant à la trame binaire ou une représentation hexadécimale du contenu 
    de la trame si aucun mnémonique ne correspond
    """
    def trame2mnemo(self, trame):
        if trame is not None and len(trame) > 4:
            bcmd = DecomFinap.cmdgoodtrame(trame)
            nack = True if DecomFinap.cmdtrame(trame) != DecomFinap.cmdgoodtrame(trame) else False
            msg = DecomFinap.msgtrame(trame)
            maxi = min(4, len(msg))
            for i in range(maxi, -1, -1):
                cmd = bytes(msg[:i])
                if cmd in self.binaries:
                    # print("CAS {} {}".format(i, self.binaries[cmd]))
                    return self.binaries[cmd]

        #		print("HEXA {} == {}".format(hex(msg[0]),_str_hex(trame)))
        return _str_hex(msg)

    def inittps(self):
        self.offset = 0
        self.delta = 0
        self.previous = 0
        self.max_interval = 0

    ##########
    # Gestion du temps
    """
    Calcule et met à jour le décalage entre l'heure actuelle et l'heure représentée dans la trame binaire.

    Parameters :
    temps (float) : Le temps représenté dans la trame binaire.
    temps_courant (float, optional) : Le temps actuel, la valeur par défaut est time.perf_counter().

    Return :
    float : Le décalage mis à jour.
    """
    def calc_offset(self, temps, temps_courant=time.perf_counter()):
        # on initialise l'offset
        if not self.offset or self.offset == 0:
            self.offset = temps_courant - temps
        elif self.previous > temps:
            self.offset += 256 * 256 / 200

        self.previous = temps

        # on calcule le delta courant, et son max
        self.delta = self.offset - (temps_courant - temps)
        delta_abs = self.delta if self.delta > 0 else -self.delta
        if delta_abs > self.max_interval:
            self.max_interval = delta_abs

        return self.offset

    """
    Complète la trame binaire avec des données mnémoniques et d'horodatage.
    
    Parameters :
    data (dict) : dictionnaire contenant les données de la trame binaire (doit inclure la clé 'binary')
    
    Return :
    (dict) : dictionnaire de données complet, avec les clés 'mnemo', 'tps', 'tps-re' ajoutées si nécessaire.
    """
    def completedata(self, data):
        if data:
            trame = data['binary']
            mnemo = self.trame2mnemo(trame)
            if mnemo:
                data['mnemo'] = mnemo
            tps = self.timetrame(trame)
            if tps:
                data['tps'] = tps
                offset = self.calc_offset(data['tps'], data['reception-time'])
                data['tps-re'] = round(tps + offset, 3)

        return data

    """
        Décode les données binaires en mnémonique.

        Parameters :
        data (dict) : données à décoder, doivent comporter les clés 'binary' et 'mnemo'.

        Return :
        (dict) : dictionnaire des valeurs décodées. Les clés sont les noms de paramètre 
        et les valeurs sont les valeurs correspondantes.
        """
    def decomdata(self, data):
        decommutation = None

        if data is not None and 'binary' in data:
            decommutation = {}
            if 'mnemo' not in data:
                self.completedata(data)

            mnemo = data['mnemo']
            trame = data['binary']

            if mnemo and mnemo in self.mnemos and 'decom' in self.mnemos[mnemo]:
                start = len(self.mnemos[mnemo]['binary'])
                # pos donne la position des parametres. Au depart on 4 octets entete + signature
                pos = 4 + start
                for param in self.mnemos[mnemo]['decom'].keys():
                    lg = self.mnemos[mnemo]['decom'][param]
                    if type(lg) == int:
                        if lg == 1:
                            decommutation[param] = trame[pos]
                        elif lg == 2:
                            decommutation[param] = trame[pos] + trame[pos + 1] * 256
                        elif lg == 4:
                            decommutation[param] = trame[pos] + trame[pos + 1] * 256 + trame[pos + 2] * 256 * 256 + \
                                                   trame[pos + 3] * 256 * 256 * 256
                        if param == 'timestamp':
                            decommutation[param] /= 200
                    elif type(lg) == dict:
                        # ss structure avec des bits
                        bits = lg
                        lg = 1
                        decommutation[param] = trame[pos]
                        copy = trame[pos]
                        for ssparam in bits:
                            lgss = self.mnemos[mnemo]['decom'][param][ssparam]
                            decommutation[ssparam] = copy & (0xFF >> 8 - lgss)
                            copy = copy >> lgss
                    if type(lg) != int:
                        print("LG??", self.mnemos[mnemo]['decom'])
                    pos += lg

        return decommutation

class Finap:
    def __init__(self, port, output=None):
        self.port = port
        self.serie = None
        self.output = output
        self.in1 = deque()
        self.tm1 = deque()
        self.in2 = deque()
        self.params = {}  # stockage des données

        self.contact = {'last': 0, 'bool': False}

    #############
    # gestion des sorties et des formatages
    """
    Sortir l'élément soit vers stdout soit vers une liste/deque

    Parameters :
    elem (Any) -- L'élément à sortir
    """
    def _output(self, elem):
        if self.output is None:
            print(elem, file=sys.stdout)
        elif type(self.output) == list or type(self.output) == deque:
            self.output.append(elem)

    """
    Génère une trame à partir de l'octet de commande.

    Paramètres :
    octets_cmd (bytes) : octet de commande

    Return :
    trame (bytes) : trame générée à partir de l'octet de commande
    """
    def _code2trame(self, octets_cmd):
        crc = crc_func(octets_cmd)
        taille = len(octets_cmd)
        trame = bytes([0xD4, taille, taille, 0xD4]) + octets_cmd + bytes([crc])
        return trame

    def _code2badtrame(self, octets_cmd):
        crc = ~crc_func(octets_cmd) & 0xFF
        taille = len(octets_cmd)
        trame = bytes([0xD4, taille, taille, 0xD4]) + octets_cmd + bytes([crc])
        return trame

    "Convertit un octet en commande en utilisant le format de données binaire."
    def _byte2cmd(self, octet):
        return bytes([octet])

    # gestion de la connexion

    """
    Connecte à un port série.

    Parameters: 
    port (str) : Port série à connecter (optionnel).
    Return: 
    self.serie.is_open (bool) : État de la connexion (True si réussite, False sinon).
    """
    def connect(self, port=None):
        if port is not None:
            self.port = port
            self.serie = serial.Serial(port=self.port, baudrate=115200, timeout=1)
        return self.serie.is_open

    """
    Ferme la connexion série et renvoie son état.

    Retourne :
    bool : False si la connexion est fermée, True sinon.
    """
    def disconnect(self):
        self.serie.close()
        return not self.serie.is_open

    """
    Cette fonction gère le contact entre le client et le serveur.

    Si `self.contact['bool']`est `True` et que le temps écoulé depuis le dernier contact est supérieur à 0.5 secondes,
    la fonction mettra à jour `self.contact['last']` à l'heure actuelle et appellera `self.send_code()` avec 
    avec `self.contact['code']` comme argument.

    """
    def _contact(self):
        if self.contact['bool'] and time.perf_counter() > self.contact['last'] + 0.5:
            self.contact['last'] = time.perf_counter()
            self.send_code(self.contact['code'])

    """
   Active la fonction de contact pour envoyer un code spécifique au dispositif série.

   Paramètres
   ----------
   code : int
       Le code à envoyer au dispositif série.
   """
    def enable_contact(self, code):
        self.contact['bool'] = True
        self.contact['code'] = code
        self._contact()

    """
    Désactive le contact.

    Le contact est un mécanisme utilisé pour envoyer un code spécifique de manière répétée. Cette fonction le désactive.
    """
    def disable_contact(self):
        self.contact['bool'] = False

    ################
    # Gestion de l'envoi
    """
    Tente d'envoyer une trame représentée par une séquence d'octets sur la connexion série.

    Parameters
    ----------
    suite_octets : bytes-like
        La trame à envoyer sur la connexion série.

    Return
    -------
    bool
        `True` si la trame a été envoyée avec succès, `False` sinon.
    """
    def _send_trame(self, suite_octets):
        try:
            self.serie.write(suite_octets)
            return True
        except:
            print('error in sending', _str_hex(suite_octets), file=sys.stderr)
            return False

    def _check_return(self, sent, received):
        cmd = sent[4]
        okcmd = bytes([0xD4, cmd])  # 0xD4 suivi de la commande
        kocmd = bytes([0xD4, cmd | 0x80])
        if okcmd in received:
            pos = received.index(okcmd) - 3
            sz = received[pos + 1] + 4 + 1
            if received[pos] == 0xD4 and received[pos + 2] == received[pos + 1]:
                if cmd != 0x61:
                    print("TROUVE OK {}".format(_str_hex(received[pos:pos + sz])))
                return True
            else:
                print("OUPS {} {} {}".format(received[pos] != 0xD4, received[pos + 1], received[pos + 2]))
        if kocmd in received:
            pos = received.index(kocmd) - 3
            sz = received[pos + 1] + 4 + 1
            if received[pos] == 0xD4 and received[pos + 2] == received[pos + 1]:
                print("TROUVE KO {}".format(_str_hex(received[pos:pos + sz])))
                return False

    """
    Envoie le code de commande donné et renvoie les données d'envoi

    Parameters :
    octets_cmd : liste d'octets représentant la commande à envoyer

    Return :
    dict : données d'envoi comprenant la direction, l'heure d'envoi, la forme binaire de la trame envoyée, cmd, valeur de retour.

    """
    def send_code(self, octets_cmd):
        trame = self._code2trame(octets_cmd)
        data = {
            'direction': "PC->FINAP",
            'sending-time': time.perf_counter(),
            'binary': trame,
            'cmd': DecomFinap.cmdtrame(trame),
            #				'mnemo':self._str_cmd(trame),
            'return': None
        }
        # on purge la file de reception
        self._read_serial()
        t1 = time.perf_counter()
        if not self._send_trame(trame):
            data['cr'] = 'KO'
        # on recupere la trame de retour
        while data['return'] is None and time.perf_counter() < t1 + 0.6:
            time.sleep(0.1)
            data['return'] = self._check_return(trame, self._read_serial())
        if data['return'] is None:
            print("PB with {} {}".format(_str_hex(trame), trame))

        return data

    def send_badcode(self, octets_cmd):
        trame = self._code2badtrame(octets_cmd)
        data = {
            'direction': "PC->FINAP",
            'sending-time': time.perf_counter(),
            'binary': trame,
            'cmd': self.cmdtrame(trame),
            #				'mnemo':self._str_cmd(trame)
        }
        if not self._send_trame(trame):
            data['cr'] = 'KO'
        return data

    ####################
    # gestion de la reception
    """
    lit les données depuis le tampon du port série et les ajoute à 'self.in1' avec l'heure actuelle.

    La fonction initialise un tableau d'octets 'readbuff' vide et vérifie s'il y a des données dans le tampon 
    du port série. 
    S'il y en a, elle lit toutes les données et les assigne à 'readbuff'. 
    Ensuite, elle recherche l'octet de synchronisation '0xD4' dans le tampon, 
    le divise à l'octet de synchronisation en paquets séparés et ajoute chaque 
    paquet avec l'heure actuelle à la liste 'self.in1'.

    Return :
    readbuff (octets) : les données lues depuis le tampon du port série.
    """
    def _read_serial(self):
        sync = bytes([0xD4])

        tps = time.perf_counter()

        readbuff = bytes()
        if self.serie and self.serie.in_waiting > 0:
            readbuff = self.serie.read(self.serie.in_waiting)
            buff = readbuff

            #########
            while sync in buff[1:]:
                sep = buff[1:].index(sync) + 1
                self.in1.append(buff[:sep])
                self.tm1.append(tps)
                buff = buff[sep:]
            self.in1.append(buff)
            self.tm1.append(tps)

        return readbuff

    """
    Lit les valeurs N1 et vérifie les erreurs d'en-tête, de taille et de crc.

    Return :
    Aucun si le message ne contient pas assez de données.
    sortie (dict) : Le dictionnaire avec l'en-tête, le message binaire, le contrôle crc et l'horodatage 
    si le message est complet et passe les contrôles d'en-tête, de taille et de crc.
    """
    def _read_n1(self):
        sortie = {'head': "", 'binary': "", 'cr': False}

        entete = bytes()
        tps = 0
        while len(entete) < 3:
            entete += self.in1.popleft()
            tps = self.tm1.popleft()

        if len(entete) != 3 or entete[1] != entete[2]:
            # pb d'entete, on purge
            sortie = {'head': entete, 'cr': False, 'info': 'HEAD ERROR {}'.format(_str_hex(entete)), 'time': tps}
            self.in2.append(sortie)
            print(sortie)
        else:
            sz = entete[1] + 2  # 0xD4 termine l'entete => non present // CRC termine le message
            message = bytes()
            while len(message) < sz and self.in1:
                if self.in1:
                    message += self.in1.popleft()
                    # on purge le tps
                    self.tm1.popleft()
            if len(message) < sz:
                # on remet le buff
                if len(message) > 0:
                    self.in1.appendleft(message)
                    self.tm1.appendleft(tps)
                self.in1.appendleft(entete)
                self.tm1.appendleft(tps)
                return
            elif len(message) > sz:
                # on remet un partie du buff
                print("+++BIZZARE {} {} {}".format(_str_hex(entete), len(message), _str_hex(message)))
                self.in1.appendleft(message[sz:])
                self.tm1.appendleft(tps)
                message = message[:sz]

            if sz > 0:
                crc = message[-1]
                crc_calc = crc_func(message[1:-1])
                if crc != crc_calc:
                    # crc incorrect
                    sortie = {'binary': entete + message, 'cr': False, 'time': tps,
                              'info': 'CRC ERROR {}|{} crc{}!={}'.format(_str_hex(entete), _str_hex(message[:-1]),
                                                                         hex(crc), hex(crc_calc))}
                    self.in2.append(sortie)
                    print(sortie)
                else:
                    sortie = {'binary': entete + message, 'cr': True, 'time': tps}
                    self.in2.append(sortie)

    """
   Lit les données de la file d'attente in2, les décode et renvoie la trame résultante.

   Return :
       dict : Trame de données incluse :
           - direction (str) : La direction de la trame (FINAP -> PC)
           - cmd (str) : La commande de la trame
           - reception-time (float) : L'heure de réception de la trame
           - binary (bytes) : La représentation binaire de la trame
           - resp (octets) : La réponse de la trame
           - cr (str) : OK ou KO selon que le cmd est valide ou non.

   """
    def _read_n2(self):
        while self.in2:
            trame_read = self.in2.popleft()
            if not trame_read['cr']:
                self._output(trame_read)
                continue

            # on decode
            trame = trame_read['binary']
            data = {
                'direction': "FINAP->PC",
                'cmd': DecomFinap.cmdgoodtrame(trame),
                #						'mnemo':desc,
                'reception-time': trame_read['time'],
                'binary': trame,
                'resp': trame[4:-1],
                'cr': 'OK' if DecomFinap.cmdgoodtrame(trame) == DecomFinap.cmdtrame(trame) else 'KO',
            }

            return data

    """
    Lit et décode les données de mesure FINAP à partir du port série.

    La méthode `do_staff` est appelée pour traiter les données, et la méthode `_read_n2` 
    est appelée pour retourner les données décodées.

    Retourne :
        dict : Un dictionnaire contenant les données de mesure FINAP, 
        y compris la direction, la commande, le temps de réception, 
        les données binaires, la réponse et la confirmation du décodage correct.
    """
    def read_measure(self):
        self.do_staff()
        return self._read_n2()

    """
    Effectue une communication avec le dispositif.

    Cette méthode exécute les étapes suivantes :
    1. Démarrer le timer en utilisant time.perf_counter()
    2. Appelez la méthode `_contact` pour initier la communication avec le périphérique.
    3. Appelez la méthode `_read_serial` pour lire les données entrantes du périphérique.
    4. Continuez à appeler `_read_n1` tant que `time.perf_counter()` est inférieur à t1 + 0.2 secondes
       et que la longueur de `self.in1` est supérieure à 2.
    """
    def do_staff(self):
        t1 = time.perf_counter()
        self._contact()
        self._read_serial()

        while time.perf_counter() < t1 + 0.2 and len(self.in1) > 2:
            self._read_n1()

        return