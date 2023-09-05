from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QTabWidget
from modeling_classes.connection import SimSocket

# @formatter:off
SIM_ACTIONS = (
    "GO",
    "BS",
    "GOS",
    "GOS5",
    "GOS10",
    "GOC",
    "GOC5",
    "GOC10",
    "GOALL",
    "RF",
    "NR",
    "FF",
)
# @formatter:on


class SimTab(QTabWidget):
    """
    Класс вкладки подключения к имитатору
    """

    def __init__(self):
        super().__init__()
        # Создаём слой сетку, по которой будут
        # выравниваться объекты
        grid = QGridLayout()
        # Добавляем подписи к полям
        grid.addWidget(QLabel("ADDRESS:"), 0, 0, 1, 1)
        grid.addWidget(QLabel("PORT:"), 1, 0, 1, 1)
        grid.addWidget(QLabel("ILS ID:"), 2, 0, 1, 1)

        # Добавляем поля ввода данных для подключения
        # и кнопку подключения
        self._addr = QLineEdit("192.168.0.6")
        self._port = QLineEdit("9090")
        self.connect_button = QPushButton("Connect")

        # Добавляем выбор идентификатора
        # тестируемого объекта.
        self.spin_id = QSpinBox()
        # Диапазон значений может быть от 1 до 8
        self.spin_id.setMinimum(1)
        self.spin_id.setMaximum(8)

        # Добавляем поля и кнопку на слой
        grid.addWidget(self._addr, 0, 1, 1, 1)
        grid.addWidget(self._port, 1, 1, 1, 1)
        grid.addWidget(self.spin_id, 2, 1, 1, 1)
        grid.addWidget(self.connect_button, 4, 0, 1, 2)

        # Для более удобного вида
        # добавляем заполнение пространства
        # под объектами
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        grid.addItem(spacer)
        self.setLayout(grid)

    @property
    def sim_ip(self):
        """
        Метод получение адреса симулятора
        """
        return self._addr.text()

    @property
    def sim_port(self):
        """
        Метод получение порта симулятора
        """
        return int(self._port.text())

    @property
    def sim_id(self):
        """
        Метод идентификатора симулятора
        """
        return self.spin_id.value()


class SimWindow(QMainWindow):
    """
    Класс добавляющий визуальные объекты
    взаимодействия с симулятором
    """

    def __init__(self):
        super().__init__()
        # Добавляем панель для размещения
        # часто используемых действия
        self._sim_tool_bar = self.addToolBar("Simulation tool bar")
        # Идентификатор по умолчанию
        self._site_id = 1
        # Вкладка с подключением к имитатору
        self.simulation = SimTab()
        # Устанавливаем действия на изменения
        # идентификатора и нажатия кнопки подключения
        self.simulation.spin_id.valueChanged.connect(self.set_id)
        self.simulation.connect_button.clicked.connect(self.connect_to_sim)

        # Создаём объект соединения
        self._socket = SimSocket(self.simulation.connect_button)

        # Создаём действия для имитатора
        # и добавляем на панель быстрого доступа
        for name in SIM_ACTIONS:
            action = QAction(name, self)
            action.triggered.connect(self.do_sim_action)
            self._sim_tool_bar.addAction(action)

    def set_id(self):
        """
        Метод связи идентификатора класса и
        значения на кладки имитации
        """
        self._site_id = self.simulation.sim_id

    def do_sim_action(self):
        """
        Метод обработки нажатий на
        действия имитатора
        """
        # Получаем имя объекта вызвавшего функцию
        action_name = self.sender().text()
        string_to_sent = None
        # Убираем лишние символы,
        # получая циклы/секунды
        # для имитации
        new_time = action_name.lstrip("GOSC")
        time_to_sent = new_time if new_time else "1"
        # Если действие в секундах/циклах
        # отправляем соответствующее воздействие
        # с идентификатором
        if action_name.startswith("GOS"):
            string_to_sent = f"{self._site_id}/break seconds {time_to_sent}\n"
        elif action_name.startswith("GOC"):
            string_to_sent = f"{self._site_id}/break after {time_to_sent}\n"
        elif action_name == "GOALL":
            # Если необходимы пересчёты всех
            # данных загруженных в имитатор
            # отправляем команду без идентификатора
            string_to_sent = "go\n"
        elif action_name == "GO":
            string_to_sent = f"{self._site_id}/go\n"
        elif action_name == "BS":
            string_to_sent = f"{self._site_id}/break steady\n"
        elif action_name == "RF":
            # Обновляем данные о всех объектах принудительно
            string_to_sent = f"{self._site_id}/variables *\n"
        elif action_name == "FF":
            # TODO: Добавить загрузку данных из лог файла
            pass
        elif action_name == "NR":
            # TODO: Добавить воздействия для нормализации объектов
            pass
        if string_to_sent:
            # Обрабатываем получившееся воздействие
            self.send_to_sim(string_to_sent)

    def send_to_sim(self, string_to_sent):
        """
        Метод передачи воздействий в объект
        увязки с имитатором
        """
        # Если соединение активно,
        # передаём в него воздействие
        if self._socket.isOpen():
            self._socket.send(string_to_sent)

    def connect_to_sim(self):
        """
        Метод подключения к имитатору
        """
        addr = self.simulation.sim_ip
        port = self.simulation.sim_port
        # С помощью введённых адреса и порта
        # пытаемся подключится к имитатору
        self._socket.open_connection(addr, port)
