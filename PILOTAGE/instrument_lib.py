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


class DecomNano:
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

    def add_sampletrames(self, fic):
        self.samples = {}
        with open(os.path.join(os.path.dirname(__file__), fic), 'r') as samples:
            self.samples = yaml.safe_load(samples)

    def mnemo2code(self, mnemo):
        if mnemo and mnemo in self.mnemos:
            return bytes(self.mnemos[mnemo]['binary'])
        elif mnemo in self.samples:
            return bytes(self.samples[mnemo])
        else:
            print("ERROR", mnemo)

    def compatible_code(self, code_ref, code_test):
        if code_ref is None or code_test is None:
            return False
        lg = min(len(code_ref), len(code_test))

        return (lg > 0 and code_ref[0] & 0x7F == code_test[0] & 0x7F)

    def compatible_mnemo(self, mnemo_ref, mnemo_test):
        if mnemo_ref is None or mnemo_test is None:
            return False
        code_ref = self.mnemo2code(mnemo_ref)
        code_test = self.mnemo2code(mnemo_test)
        return self.compatible_code(code_ref, code_test)

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
        return bytes([DecomNano.cmdgoodtrame(trame)]) + trame[5:]

    def trame2mnemo(self, trame):
        if trame is not None and len(trame) > 4:
            bcmd = DecomNano.cmdgoodtrame(trame)
            nack = True if DecomNano.cmdtrame(trame) != DecomNano.cmdgoodtrame(trame) else False
            msg = DecomNano.msgtrame(trame)
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

class Nano:
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

    def _output(self, elem):
        if self.output is None:
            print(elem, file=sys.stdout)
        elif type(self.output) == list or type(self.output) == deque:
            self.output.append(elem)

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

    def _byte2cmd(self, octet):
        return bytes([octet])

    # gestion de la connexion

    def connect(self, port=None):
        if port is not None:
            self.port = port
            self.serie = serial.Serial(port=self.port, baudrate=115200, timeout=1)
        return self.serie.is_open

    def disconnect(self):
        self.serie.close()
        return not self.serie.is_open

    def _contact(self):
        if self.contact['bool'] and time.perf_counter() > self.contact['last'] + 0.5:
            self.contact['last'] = time.perf_counter()
            self.send_code(self.contact['code'])

    def enable_contact(self, code):
        self.contact['bool'] = True
        self.contact['code'] = code
        self._contact()

    def disable_contact(self):
        self.contact['bool'] = False

    ################
    # Gestion de l'envoi
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

    def send_code(self, octets_cmd):
        trame = self._code2trame(octets_cmd)
        data = {
            'direction': "PC->FINAP",
            'sending-time': time.perf_counter(),
            'binary': trame,
            'cmd': DecomNano.cmdtrame(trame),
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
                'cmd': DecomNano.cmdgoodtrame(trame),
                #						'mnemo':desc,
                'reception-time': trame_read['time'],
                'binary': trame,
                'resp': trame[4:-1],
                'cr': 'OK' if DecomNano.cmdgoodtrame(trame) == DecomNano.cmdtrame(trame) else 'KO',
            }

            return data

    def read_measure(self):
        self.do_staff()
        return self._read_n2()

    def do_staff(self):
        t1 = time.perf_counter()
        self._contact()
        self._read_serial()

        while time.perf_counter() < t1 + 0.2 and len(self.in1) > 2:
            self._read_n1()

        return