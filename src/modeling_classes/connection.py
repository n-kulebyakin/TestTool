from PyQt5.QtNetwork import QTcpSocket


class SimSocket(QTcpSocket):
    """
    Класс подключения к эмулятору
    """
    _timeout = 1

    def __init__(self, out_function, state_button):
        super().__init__()
        self._queue = []
        self._data = ""
        self._button = state_button
        self._out = out_function
        self.waitForConnected(self._timeout)
        self.readyRead.connect(self.on_ready_read)
        self.connected.connect(self.on_connected)
        self.error.connect(self.on_error)

    def open_connection(self, host, port):
        self.connectToHost(host, int(port))
        self._button.setText("Attempt...")
        print('OPEN')

    def close(self):
        self.disconnectFromHost()
        self._button.setText("Connect")
        print('CLOSE')



    def on_connected(self):
        self._button.setText("Disconnect")

    def on_disconnect(self):
        self._button.setText("Connect")


    def send(self, command):
        if self._data:
            self._queue.append(command)
        else:
            self.write(bytes(command, "utf-8"))

    def on_error(self):
        self.close()
        self._button.setText("Connect")
        print('ERROR')


    def on_ready_read(self):
        while self.bytesAvailable():
            self._data += str(self.readAll())[2:-1]
        if self._data.endswith("* > "):
            self._out(self._data)
            self._data = ""
            if self._queue:
                self.send(self._queue.pop())
