import os
import sys
from PySide6.QtWidgets import QApplication

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(application_path, '..')))

from gsf.control_center_logic import ControlCenter 
from gsf.main_manager import GADGETS_DIR, CONFIG_DIR 

def main():
    app = QApplication(sys.argv)
    
    window = ControlCenter()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()