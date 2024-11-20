from PyQt6.QtWidgets import QApplication
from gui import MainWindow

class Client:
    def __init__(self):
        """Initialize the Client class."""
        self.app = QApplication([])
        self.window = None

    def __repr__(self):
        """Return a string representation of the Client."""
        return f"Client()"

    def init_gui(self):
        """Initialize and show the GUI."""
        self.window = MainWindow()
        self.window.show()
        self.app.exec()


if __name__ == "__main__":
    c = Client()
    c.init_gui()
