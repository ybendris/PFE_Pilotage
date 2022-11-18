#!/usr/bin/env python3

""" Nom du module : Librairie"""

""" Description """
""" Version 1 """
""" Date : 12/11/2022"""
""" Auteur : Equipe CEIS """
""""""

#  _______________________________________________________ IMPORT ______________________________________________________

import threading
from datetime import datetime
from queue import Queue, Empty
import logging
import json
import socket
import sys

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class NetworkItem():
    def __init__(self, host, port, name, abonnement):
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wfile = self.main_socket.makefile("wb", 0)
        self.rfile = self.main_socket.makefile("rb", -1)
        self.abonnement = abonnement
        self.name = name

        self.queue_message_to_send = Queue()
        self.queue_message_to_process = Queue()

        try:
            self.main_socket.connect((host, port))
        except TimeoutError:
            sys.exit(1)

        self.envoi_abonnement()

        self.write_thread = ThreadEcriture(self.wfile, "ThreadEcriture", self.queue_message_to_send)
        self.write_thread.start()

        self.read_thread = ThreadLecture(self.rfile, "ThreadLecture", self.queue_message_to_process)
        self.read_thread.start()

        try:
            self.service()
        except KeyboardInterrupt:
            pass
            # close files

    def envoi_abonnement(self):
        print("envoi_abonnement")
        self.send_log("envoi_abonnement", 2)
        message = {}
        print(message)
        try:
            message["expediteur"] = self.name
            message["msg"] = self.abonnement

            print(message)
            send(self.wfile, message)

        except Exception as e:
            print(e)
            # self.selector.unregister(conn)
            """obj.close(sock)"""
            # del self._buffer[self.main_socket]
            return False

    def getCurrentDateTime(self):
        currentDate = datetime.now()
        # dd/mm/YY H:M:S
        dt = currentDate.strftime("%d-%m-%Y %H:%M:%S")
        return dt

    def send_log(self, message, level):
        log = {}
        log["type"] = 'LOG'
        log["date/time"] = self.getCurrentDateTime()
        log["level"] = level
        log["msg"] = message
        self.queue_message_to_send.put(log)

    def service(self):
        pass


class ThreadLecture(threading.Thread):
    def __init__(self, rfile, name, queue):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.rfile = rfile
        self.queue_message_to_process = queue

    def run(self):

        logging.info("{} started".format(self.name))
        while True:

            try:
                message_received = receive(self.rfile)  # object json
                if message_received:
                    #logging.info("Received: {}".format(message_received))
                    self.queue_message_to_process.put(message_received)
            except Exception as e:
                logging.info("{} ended with exception: {}".format(self.name, e))
                break


class ThreadEcriture(threading.Thread):
    def __init__(self, wfile, name, queue):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.wfile = wfile
        self.queue_message_to_send = queue

    # Everything inside of run is executed in a seperate thread
    def run(self):
        logging.info("{} started".format(self.name))
        while True:
            try:

                message_to_send = self.queue_message_to_send.get()
                send(self.wfile, message_to_send)
                #logging.info("Sent: {}".format(message_to_send))


            except Empty as e:
                logging.info("{} ended with exception: {}".format(self.name, e))
                break



#  ________________________________________________ FONCTIONS GLOBALES _________________________________________________
def getBeginDateTime():
    a = datetime.now()
    print("DATE =", a)
    # dd/mm/YY H:M:S
    dt_string = a.strftime("%d-%m-%Y_%H-%M-%S")
    print("date and time =", dt_string)
    return dt_string


def receive(rfile):
    abonnement_encoded = rfile.readline().strip()
    abonnement_str = abonnement_encoded.decode("utf-8")
    abonnement_decoded = json.loads(abonnement_str)
    return abonnement_decoded


def send(wfile, message):
    #print("send")
    if message:
        str_message = json.dumps(message)
        bytes_message = bytes(str_message, encoding="utf-8")
        wfile.write(bytes_message + b"\n")
