from PyQt5.QtNetwork import QTcpSocket


class SimSocket(QTcpSocket):
    """
    Класс подключения к эмулятору
    """
    _timeout = 1

    def __init__(self, state_button):
        super().__init__()
        self._queue = []
        self._data = ""
        self._button = state_button
        self._out = None
        self.waitForConnected(self._timeout)
        self.readyRead.connect(self.on_ready_read)
        self.connected.connect(self.on_connected)
        self.error.connect(self.on_error)

    def set_out_function(self, func):
        self._out = func

    def open_connection(self, host, port):
        self.connectToHost(host, int(port))
        self._button.setText("Attempt...")

    def close(self):
        self.disconnectFromHost()
        self._button.setText("Connect")
        self.clear()

    def on_connected(self):
        self._button.setText("Disconnect")
        self.clear()

    def on_disconnect(self):
        self._button.setText("Connect")
        self.clear()

    def clear(self):
        self._data = ""
        self._queue.clear()

    def send(self, command):
        if self._data:
            self._queue.append(command)
        else:
            self.write(bytes(command, "utf-8"))

    def on_error(self):
        self.close()
        self._button.setText("Connect")

    def on_ready_read(self):
        while self.bytesAvailable():
            self._data += str(self.readAll())[2:-1]
        if self._data.endswith("* > "):
            if self._out:
                self._out(self._data)
            self._data = ""
            if self._queue:
                self.send(self._queue.pop())
