import threading
from queue import Queue, Empty
import logging
import json

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class NetworkItem():
    def __init__(self, socket, abonnement):
        self.main_socket = socket
        self.wfile = self.main_socket.makefile("wb", 0)
        self.rfile = self.main_socket.makefile("rb", -1)
        self.abonnement = abonnement

        self.envoi_abonnement()

        self.queue_message_to_send = Queue()
        self.queue_message_to_process = Queue()

        self.write_thread = ThreadEcriture(self.wfile, "ThreadEcriture", self.queue_message_to_send)
        self.write_thread.start()

        self.read_thread = ThreadLecture(self.rfile, "ThreadLecture", self.queue_message_to_process)
        self.read_thread.start()

    def envoi_abonnement(self):
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
                message_received = receive(self.rfile) #object json
                if message_received:
                    logging.info("Received: {}".format(message_received))
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
                logging.info("Sent: {}".format(message_to_send))


            except Empty as e:
                logging.info("{} ended with exception: {}".format(self.name, e))
                break


def receive(rfile):
    abonnement_encoded = rfile.readline().strip()
    abonnement_str = abonnement_encoded.decode("utf-8")
    abonnement_decoded = json.loads(abonnement_str)
    return abonnement_decoded


def send(wfile, message):
    print("send")
    if message:
        str_message = json.dumps(message)
        bytes_message = bytes(str_message, encoding="utf-8")
        wfile.write(bytes_message + b"\n")
