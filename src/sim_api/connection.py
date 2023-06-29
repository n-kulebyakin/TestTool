#!/usr/bin/env python
from PyQt5.QtNetwork import QTcpSocket


class SimSocket(QTcpSocket):
    def __init__(self, out_function):
        QTcpSocket.__init__(self)
        self.state_button = None
        self.connected.connect(self.on_connected)
        self.disconnected.connect(self.on_disconnect)
        self.error.connect(self.on_error)
        self.readyRead.connect(self.on_ready_read)
        self.output = out_function
        self.waitForConnected(10000)

    def connectToHost(self, host, port):
        QTcpSocket.connectToHost(self, host, int(port))
        print(self.SocketError())

    def close(self):
        self.disconnectFromHost()

    def send(self, data):
        self.write(bytes(data, 'utf-8'))

    def on_error(self):
        print('Error connection:', self.errorString())
        self.close()

    def on_connected(self):
        print('Connected to HOST')
        if self.state_button:
            self.state_button.setText('Disconnect')

    def on_disconnect(self):
        print('Disconnected')
        if self.state_button:
            self.state_button.setText('Connect')

    def on_ready_read(self):
        data = ''
        while self.bytesAvailable():
            data += str(self.readAll())[2:-1]
        self.output(data)


def send_to_sim(sock, data):
    sock.send(data)
