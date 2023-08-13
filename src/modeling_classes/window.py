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
    def __init__(self):
        super().__init__()

        grid = QGridLayout()
        grid.addWidget(QLabel("ADDRESS:"), 0, 0, 1, 1)
        grid.addWidget(QLabel("PORT:"), 1, 0, 1, 1)
        grid.addWidget(QLabel("ILS ID:"), 2, 0, 1, 1)

        self._addr = QLineEdit("192.168.0.6")
        self._port = QLineEdit("9090")
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_sim)

        self.spin_id = QSpinBox()
        self.spin_id.setMinimum(1)

        grid.addWidget(self._addr, 0, 1, 1, 1)
        grid.addWidget(self._port, 1, 1, 1, 1)
        grid.addWidget(self.spin_id, 2, 1, 1, 1)
        grid.addWidget(self.connect_button, 4, 0, 1, 2)
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        grid.addItem(spacer)
        self.setLayout(grid)

    def connect_to_sim(self):
        pass

    @property
    def sim_id(self):
        return self.spin_id.value()


class SimWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._sim_tool_bar = self.addToolBar("Simulation tool bar")
        self._site_id = 1
        self.simulation = SimTab()
        self.simulation.spin_id.valueChanged.connect(self.set_id)

        for name in SIM_ACTIONS:
            action = QAction(name, self)
            action.triggered.connect(self.do_sim_action)
            self._sim_tool_bar.addAction(action)

    def set_id(self):
        self._site_id = self.simulation.sim_id

    def do_sim_action(self):
        action_name = self.sender().text()
        string_to_sent = None
        new_time = action_name.lstrip("GOSC")
        time_to_sent = new_time if new_time else "1"
        if action_name.startswith("GOS"):
            string_to_sent = f"{self._site_id}/break seconds {time_to_sent}\n"
        elif action_name.startswith("GOC"):
            string_to_sent = f"{self._site_id}/break after {time_to_sent}\n"
        elif action_name == "GOALL":
            string_to_sent = "go\n"
        elif action_name == "GO":
            string_to_sent = f"{self._site_id}/go\n"
        elif action_name == "BS":
            string_to_sent = f"{self._site_id}/break steady\n"
        elif action_name == "RF":
            string_to_sent = f"{self._site_id}/variables *\n"
        elif action_name == "FF":
            # TODO: Добавить загрузку данных из лог файла
            pass
        elif action_name == "NR":
            # TODO: Добавить воздействия для нормализации объектов
            pass
        if string_to_sent:
            self.send_to_sim(string_to_sent)

    def send_to_sim(self, string_to_sent):
        pass
