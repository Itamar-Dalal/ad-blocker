from PyQt6.QtWidgets import QApplication
from gui import MainWindow

class Client:
    def __init__(self) -> None:
        """Initialize the Client class."""
        self.app = QApplication([])
        self.window = None

    def __repr__(self) -> str:
        """Return a string representation of the Client."""
        return f"Client()"
    
    @classmethod
    def create_client(cls) -> "Client":
        """Factory method to create and return a Client instance."""
        return cls()
    
    def run(self):
        self.window = MainWindow()
        self.window.show()
        self.app.exec()


if __name__ == "__main__":
    c = Client.create_client()
    c.run()
