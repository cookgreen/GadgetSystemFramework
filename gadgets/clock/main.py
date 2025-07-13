import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtCore import QTimer, QTime

# dynamic add GSF core lib into Python dir
from gsf_core.gadget_base import BaseGadget

class ClockGadget(BaseGadget):
    def __init__(self, gadget_path):
        # must call parent class constructor
        super().__init__(gadget_path)

        # --- specific logic ---
        self.resize(200, 200)
        self.setWindowTitle('Clock Gadget')

        timer = QTimer(self)
        timer.timeout.connect(self.update) # update() will trigger paintEvent
        timer.start(1000)

    def paintEvent(self, event):
        """only care about how to paint，other are handled by base-class"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(0, 0, 0, 120))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

        current_time = QTime.currentTime().toString('hh:mm:ss')
        font = QFont('Segoe UI', 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(self.rect(), Qt.AlignCenter, current_time)

if __name__ == '__main__':
    # get gadget_path from command line
    if len(sys.argv) < 2:
        print("Error: need to provide the gadget_path as argument")
        sys.exit(1)
    
    gadget_path_arg = sys.argv[1]

    app = QApplication(sys.argv)
    gadget = ClockGadget(gadget_path=gadget_path_arg)
    gadget.show()
    sys.exit(app.exec())