import time
from flask import Flask, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)


@socketio.on('get_data')
def send_data():
    socketio.emit('data', 'DATA')
    print("Emit DATA: ", 'DATA')


@socketio.on('send_command')
def messaging(command, methods=['GET', 'POST']):
    print('received message: ' + str(command))
    

if __name__ == '__main__':
    socketio.run(app)   
    socketio.emit('data1', 'DATA1')
    socketio.emit('data2', 'DATA2')
    socketio.emit('data3', 'DATA3')
    socketio.emit('data4', 'DATA4')
    socketio.emit('data5', 'DATA5')

    
    
    