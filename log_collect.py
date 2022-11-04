import sys
import logging
from datetime import datetime
import pickle
import csv

from tcp_client import SelectorClient

HOST = 'localhost'
PORT = 65432
SESSION_NAME = ''
dt_string = ''
header = ['date/time','level','msg']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class LogCollector(SelectorClient):
    def __init__(self,host,port,name):
        abo = ["LOG"]
        self.fOpen=self.openCSV('CSV_LOG/LOG_{}_{}.csv'.format(SESSION_NAME,dt_string), 'w')
        SelectorClient.__init__(self,host=host,port=port,name=name,abo=abo)
        self.serve_forever()

    def openCSV(self,file,mode):
        if mode == 'w':
            fopen = open(file,mode,newline='')
            self.writer=csv.DictWriter(fopen,fieldnames=header,delimiter=';')
            #self.ecrireCSV(fopen,header)
            self.writer.writeheader()
            return fopen
        else:
            pass

    def ecrireCSV(self,content):
        self.writer.writerow(content)


    def traitement(self, message):
        deserialized_message = pickle.loads(message)
        if deserialized_message["type"] == 'LOG':
            del deserialized_message["type"]
            logging.info(deserialized_message)
            self.ecrireCSV(deserialized_message)

        elif deserialized_message["type"] == 'CMD':
            pass

        else:
            logging.info('\n############# Type de message inconnu #############\n')


def getDateTimeBegin():
    a = datetime.now()
    print("DATE =", a)
    # dd/mm/YY H:M:S
    global dt_string
    dt_string = a.strftime("%d-%m-%Y_%H-%M-%S")
    print("date and time =", dt_string)

if __name__ == '__main__':
    logging.info('starting')
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <name> <session>")
        sys.exit(1)
    name = sys.argv[1]
    SESSION_NAME = sys.argv[2]
    getDateTimeBegin()
    # datetime object containing current date and time

    '''
    server = SelectorClient(host=HOST, port=PORT, name=name)
    server.serve_forever()
    '''
    logCollect = LogCollector(HOST,PORT,name)
