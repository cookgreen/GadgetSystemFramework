import os
import shutil
import zipfile
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

APP_ICON = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')

class ControlCenter(QWidget):
    # --- defination signals ---
    # parameters: gadget_path, gadget_id
    request_launch_gadget = Signal(str, str)
    # parameters: gadget_id
    request_terminate_gadget = Signal(str)

    def __init__(self, gadgets_dir, running_gadgets_info):
        super().__init__()
        self.gadgets_dir = gadgets_dir
        # running_gadgets_info is a dic such as {'clock': process_object}
        self.running_gadgets_info = running_gadgets_info
        
        self.init_ui()
        self.populate_table()

    def init_ui(self):
        self.setWindowIcon(QIcon(APP_ICON))
        self.setWindowTitle("GSF Control Center")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Grid
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Version", "Description", "Status", "Tool"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive) # Adjustable colum for description
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # Cannot edit
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # Full-Row Select

        # Bottom Buttoms
        button_layout = QHBoxLayout()
        self.install_button = QPushButton("Install Gadget...")
        self.uninstall_button = QPushButton("Uninstall Selected")
        self.refresh_button = QPushButton("Refresh")

        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.uninstall_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        # Connect signal to slot
        self.install_button.clicked.connect(self.install_gadget)
        self.uninstall_button.clicked.connect(self.uninstall_gadget)
        self.refresh_button.clicked.connect(self.populate_table)

    def populate_table(self):
        """use information contains in gadgets_dir fill the grid"""
        self.table.setRowCount(0) # Cleanup grid
        
        # Discover gadgets
        for name in sorted(os.listdir(self.gadgets_dir)):
            gadget_path = os.path.join(self.gadgets_dir, name)
            manifest_path = os.path.join(gadget_path, 'gadget.json')

            if os.path.isdir(gadget_path) and os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = __import__('json').load(f)

                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                
                # set data
                self.table.setItem(row_position, 0, QTableWidgetItem(manifest.get('name', 'N/A')))
                self.table.setItem(row_position, 1, QTableWidgetItem(manifest.get('version', 'N/A')))
                self.table.setItem(row_position, 2, QTableWidgetItem(manifest.get('description', '')))
                
                # status and tool button
                is_running = name in self.running_gadgets_info and self.running_gadgets_info[name].poll() is None
                
                status_item = QTableWidgetItem("Running" if is_running else "Stopped")
                status_item.setForeground(Qt.green if is_running else Qt.red)
                self.table.setItem(row_position, 3, status_item)

                # tool button
                action_button = QPushButton("停止" if is_running else "Start")
                action_button.setProperty("gadget_id", name)
                action_button.setProperty("gadget_path", gadget_path)
                
                if is_running:
                    action_button.clicked.connect(self.on_terminate_clicked)
                else:
                    action_button.clicked.connect(self.on_launch_clicked)
                
                self.table.setCellWidget(row_position, 4, action_button)
    
    def on_launch_clicked(self):
        button = self.sender()
        gadget_id = button.property("gadget_id")
        gadget_path = button.property("gadget_path")
        self.request_launch_gadget.emit(gadget_path, gadget_id)

    def on_terminate_clicked(self):
        button = self.sender()
        gadget_id = button.property("gadget_id")
        self.request_terminate_gadget.emit(gadget_id)

    def install_gadget(self):
        """open file dialog to install .zip format gadget tool"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select gadget package", "", "Zip Files (*.zip)")
        if not file_path:
            return

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # the folder name is the zip package root dir
                gadget_name = os.path.splitext(os.path.basename(file_path))[0]
                target_path = os.path.join(self.gadgets_dir, gadget_name)
                
                if os.path.exists(target_path):
                    # can add a confirm dialog
                    print(f"Error: {gadget_name} has existed, please uninstall firstly")
                    return
                    
                zip_ref.extractall(self.gadgets_dir)
                print(f"Install {gadget_name} sucessfully!")
                self.populate_table() # refresh list
        except Exception as e:
            print(f"Install FAILED: {e}")

    def uninstall_gadget(self):
        """Uninstall the selected gadget"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            # can add a prompt
            print("Please select a gadget which need to be uninstall.")
            return
            
        row = selected_rows[0].row()
        gadget_id_item = self.table.cellWidget(row, 4).property("gadget_id")
        
        # Make sure gadget has stopped
        if gadget_id_item in self.running_gadgets_info and self.running_gadgets_info[gadget_id_item].poll() is None:
            print(f"Error: Please stop {gadget_id_item} firstly and then uninstall.")
            return

        # There should be a confirm dialog
        target_path = os.path.join(self.gadgets_dir, gadget_id_item)
        try:
            shutil.rmtree(target_path)
            print(f"Unistall {gadget_id_item} sucessfully")
            self.populate_table()
        except Exception as e:
            print(f"Uninstall Failed: {e}")

    def update_status(self, running_gadgets_info):
        """External callable func, for updating the running status"""
        self.running_gadgets_info = running_gadgets_info
        self.populate_table()