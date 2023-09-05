from PyQt5.Qt import QTextCodec
from PyQt5.QtNetwork import QTcpSocket


class SimSocket(QTcpSocket):
    """
    Класс подключения к эмулятору
    """
    _timeout = 1

    def __init__(self, state_button):
        super().__init__()
        # Очередь команд
        self._queue = []
        # Информация получаемая от имитатора
        self._data = ""
        # Кнопка подключения к имитатору
        # TODO: Исключить изменение текста
        #  в классе сокета
        self._button = state_button
        # Переменная хранящая ссылку на функцию
        # обрабатывающую информацию от имитатора
        self._out = None
        # Задаём таймаут подключения и действия
        # при подключении, получении информации
        # и ошибке подключения
        self.waitForConnected(self._timeout)
        self.readyRead.connect(self.on_ready_read)
        self.connected.connect(self.on_connected)
        self.error.connect(self.on_error)

    def set_out_function(self, func):
        """
        Установка функции для передачи входящей
        информации
        """
        self._out = func

    def open_connection(self, host, port):
        """
        Подключение к имитатору
        """
        self.connectToHost(host, int(port))
        self._button.setText("Attempt...")

    def close(self):
        """
        Отключение от имитатора
        """
        self.disconnectFromHost()
        self._button.setText("Connect")
        self.clear()

    def on_connected(self):
        """
        Функция обработки подключения
        """
        self._button.setText("Disconnect")
        self.clear()

    def on_disconnect(self):
        """
        Функция обработки отключения
        """
        self._button.setText("Connect")
        self.clear()

    def clear(self):
        """
        Функция очистки входящей информации
        и очереди команд
        """
        self._data = ""
        self._queue.clear()

    def send(self, command):
        """
        Функция отправки информации в имитатор
        """
        if self._data:
            # Если от имитатора получена не вся информация
            # после предыдущих команд, то записываем
            # новую команду в очередь
            self._queue.append(command)
        else:
            # Преобразовываем строку к байтам
            # и отправляем в имитатор
            command = command.encode(encoding="utf-8", errors="strict")
            self.write(command)

    def on_error(self):
        """
        Функция обработки ошибки подключения
        """
        self.close()
        self._button.setText("Connect")

    def on_ready_read(self):
        """
        Функция обработки входящей информации
        """
        # Пока доступна информация для чтения
        while self.bytesAvailable():
            # считываем её
            incoming_data = self.readAll()
            # преобразовываем из байтов в строку
            data = QTextCodec.codecForMib(106).toUnicode(incoming_data)
            # сохраняем во временное хранилище
            self._data += data

        if self._data.endswith("* > "):
            # Если была передана вся информация
            # и имитатор готов получать новые команды
            # отправляем полученную информацию в функцию
            # обработчик
            if self._out:
                self._out(self._data)
            # Очищаем временное хранилище информации
            self._data = ""
            # Если в очереди есть команды,
            # отправляем следующую
            if self._queue:
                self.send(self._queue.pop(0))
