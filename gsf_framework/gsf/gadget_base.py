import sys
import os
import json
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import QMouseEvent, QAction
from PySide6.QtCore import Qt, QPoint, QSettings

class BaseGadget(QWidget):
    def __init__(self, gadget_path):
        super().__init__()
        self.gadget_path = gadget_path
        self.settings_file = os.path.join(self.gadget_path, 'config.ini')

        self.init_ui()
        self.load_position()

        # for window dragging
        self.drag_position = QPoint()

    def init_ui(self):
        """initizing the window standard style"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |          # no border
            Qt.WindowStaysOnTopHint |          # always top
            Qt.Tool                            # don't show on taskba
        )
        self.setAttribute(Qt.WA_TranslucentBackground) # background transparent

    def load_position(self):
        """load window pos from setting file"""
        settings = QSettings(self.settings_file, QSettings.IniFormat)
        pos = settings.value("geometry/pos")
        if pos is not None:
            self.move(pos)

    def save_position(self):
        """save current pos into setting file"""
        settings = QSettings(self.settings_file, QSettings.IniFormat)
        settings.setValue("geometry/pos", self.pos())

    def closeEvent(self, event):
        """auto-save pos into setting file"""
        self.save_position()
        event.accept()

    # --- standard dragging logic ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    # --- standard right-click menu ---
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # allow sub-class add its own menu items
        self.populate_context_menu(menu)
        
        menu.addSeparator()
        close_action = menu.addAction("close gadget")
        
        action = menu.exec(self.mapToGlobal(event.pos()))
        
        if action == close_action:
            self.close()

    def populate_context_menu(self, menu):
        """
        sub-class can re-write this func to add custom menu items
        e.g. menu.addAction("setting...")
        """
        pass