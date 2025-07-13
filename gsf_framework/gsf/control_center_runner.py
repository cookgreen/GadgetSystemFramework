import sys
from PySide6.QtWidgets import QApplication
from control_center_logic import ControlCenter 
from main_manager import GADGETS_DIR, CONFIG_DIR 

def main():
    app = QApplication(sys.argv)
    
    window = ControlCenter()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()