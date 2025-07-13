import sys
import os
import shutil
import zipfile
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon

from gsf.main_manager import *

APP_ICON = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')

class ControlCenter(QWidget):
    def __init__(self):
        super().__init__()
        
        self.logic = GadgetManagerLogic()
        
        self.init_ui()
        
        self.populate_table()

        self.logic.set_status_change_callback(
            lambda: QMetaObject.invokeMethod(self, "populate_table", Qt.QueuedConnection)
        )

    def init_ui(self):
        self.setWindowIcon(QIcon(APP_ICON))
        self.setWindowTitle("GSF Control Center")
        self.setMinimumSize(650, 400)
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Version", "Status", "Description", "Tool"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)

        button_layout = QHBoxLayout()
        self.install_button = QPushButton("Install Gadget...")
        self.uninstall_button = QPushButton("Uninstall Selected")
        
        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.uninstall_button)
        button_layout.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.install_button.clicked.connect(self.install_gadget)
        self.uninstall_button.clicked.connect(self.uninstall_gadget)

    @Slot()
    def populate_table(self):
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        
        current_selection_id = None
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            button = self.table.cellWidget(selected_rows[0].row(), 4)
            if button:
                current_selection_id = button.property("gadget_id")

        self.table.clearContents()
        self.table.setRowCount(0)
        
        all_gadgets = self.logic.discover_gadgets()
        running_info = self.logic.get_running_gadgets_info()
        
        for gadget_data in all_gadgets:
            gadget_id = gadget_data['id']
            manifest = gadget_data['manifest']
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            self.table.setItem(row_position, 0, QTableWidgetItem(manifest.get('name', 'N/A')))
            self.table.setItem(row_position, 1, QTableWidgetItem(manifest.get('version', 'N/A')))
            
            is_running = gadget_id in running_info
            status_text = "Running" if is_running else "Stopped"
            status_color = Qt.green if is_running else Qt.red
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.table.setItem(row_position, 2, status_item)

            self.table.setItem(row_position, 3, QTableWidgetItem(manifest.get('description', '')))

            action_button = QPushButton("Stop" if is_running else "Start")
            action_button.setProperty("gadget_id", gadget_id)
            action_button.setProperty("gadget_path", gadget_data['path'])
            
            if is_running:
                action_button.clicked.connect(lambda checked=False, gid=gadget_id: self.logic.terminate_gadget(gid))
            else:
                action_button.clicked.connect(lambda checked=False, gpath=gadget_data['path'], gid=gadget_id: self.logic.launch_gadget(gpath, gid))
            
            self.table.setCellWidget(row_position, 4, action_button)
            
            if gadget_id == current_selection_id:
                self.table.selectRow(row_position)
        
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)

    def install_gadget(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Gadget Package", "", "Zip Files (*.zip)")
        if not file_path:
            return

        try:
            target_path = os.path.join(self.logic.gadgets_dir, os.path.splitext(os.path.basename(file_path))[0])
            if os.path.exists(target_path):
                QMessageBox.warning(self, "Install FAILED", f"The gadget named {os.path.basename(target_path)} has aleady existed, please uninstall firstly!")
                return
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.logic.gadgets_dir)
            
            QMessageBox.information(self, "Success", "Install Gadget successfully！")
            self.populate_table()
        except Exception as e:
            QMessageBox.critical(self, "Install FAILED", f"Install FAILED: {e}")

    def uninstall_gadget(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Notice", "Please select a gadget which need to be uninstall.")
            return
            
        row = selected_rows[0].row()
        button_widget = self.table.cellWidget(row, 4)
        if not button_widget: return
        
        gadget_id = button_widget.property("gadget_id")
        
        if gadget_id in self.logic.get_running_gadgets_info():
            QMessageBox.warning(self, "Unistall FAILED", "Please stop the gadget before uninstall it!")
            return

        reply = QMessageBox.question(self, "Confirm Uninstall", 
                                     f"Are you sure uninstall '{gadget_id}' forever? This operation cannot be undo!",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            target_path = os.path.join(self.logic.gadgets_dir, gadget_id)
            try:
                shutil.rmtree(target_path)
                QMessageBox.information(self, "Success", f"'{gadget_id}' has been uninstalled!")
                self.populate_table()
            except Exception as e:
                QMessageBox.critical(self, "Uninstall FAILED", f"Occur error when uninstall the gadget: {e}")

    def closeEvent(self, event):
        print("Control Center is closing, cancelling its logic poller.")
        if self.logic and self.logic.status_poll_timer:
            self.logic.status_poll_timer.cancel()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = ControlCenter()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()