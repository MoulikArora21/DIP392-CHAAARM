import sys
import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSplitter, QApplication, 
                            QComboBox, QLabel, QVBoxLayout, QPushButton, QFileDialog, 
                            QGridLayout, QDialog, QListWidget, QLineEdit, QFormLayout, 
                            QSizePolicy, QMessageBox, QMenuBar)
import etsy_to_xml
import wise_to_xml

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Client")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.bank_acc_input = QLineEdit()
        self.total_transactions_input = QLineEdit()
        self.total_transactions_input.setValidator(QIntValidator(0, 999999))
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Bank Account:", self.bank_acc_input)
        form_layout.addRow("Total Transactions:", self.total_transactions_input)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def get_client_data(self):
        name = self.name_input.text().strip()
        bank_acc = self.bank_acc_input.text().strip()
        total_transactions = self.total_transactions_input.text().strip()
        total_transactions = int(total_transactions) if total_transactions else 0
        return {"Name": name, "BankAcc": bank_acc, "total_transactions": total_transactions}

class EditClientDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Client")
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit(self.client["Name"])
        self.bank_acc_input = QLineEdit(self.client["BankAcc"])
        self.total_transactions_input = QLineEdit(str(self.client["total_transactions"]))
        self.total_transactions_input.setValidator(QIntValidator(0, 999999))
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Bank Account:", self.bank_acc_input)
        form_layout.addRow("Total Transactions:", self.total_transactions_input)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def get_client_data(self):
        name = self.name_input.text().strip()
        bank_acc = self.bank_acc_input.text().strip()
        total_transactions = self.total_transactions_input.text().strip()
        total_transactions = int(total_transactions) if total_transactions else 0
        return {"Name": name, "BankAcc": bank_acc, "total_transactions": total_transactions}

class ClientEditorDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Clients")
        self.clients = clients.copy()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.client_list = QListWidget()
        self.update_client_list()
        self.client_list.doubleClicked.connect(self.edit_client_double_click)
        layout.addWidget(self.client_list)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Client")
        add_btn.clicked.connect(self.add_client)
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_client)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_client)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.client_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()

        self.setLayout(layout)
        self.setMinimumWidth(400)

    def update_client_list(self):
        self.client_list.clear()
        for client in self.clients:
            self.client_list.addItem(f"{client['Name']} ({client['BankAcc']}, Transactions: {client['total_transactions']})")

    def update_button_states(self):
        has_selection = self.client_list.currentRow() >= 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def add_client(self):
        dialog = AddClientDialog(self)
        if dialog.exec():
            client_data = dialog.get_client_data()
            if client_data["Name"] and client_data["BankAcc"]:
                self.clients.append(client_data)
                self.update_client_list()
            else:
                QMessageBox.warning(self, "Invalid Input", "Name and Bank Account cannot be empty.")

    def edit_client(self):
        selected = self.client_list.currentRow()
        if selected >= 0:
            dialog = EditClientDialog(self.clients[selected], self)
            if dialog.exec():
                client_data = dialog.get_client_data()
                if client_data["Name"] and client_data["BankAcc"]:
                    self.clients[selected] = client_data
                    self.update_client_list()
                else:
                    QMessageBox.warning(self, "Invalid Input", "Name and Bank Account cannot be empty.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a client to edit.")

    def edit_client_double_click(self):
        selected = self.client_list.currentRow()
        if selected >= 0:
            self.edit_client()

    def delete_client(self):
        selected = self.client_list.currentRow()
        if selected >= 0:
            self.clients.pop(selected)
            self.update_client_list()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a client to delete.")

    def accept(self):
        super().accept()

    def get_clients(self):
        return self.clients

class DragDropLabel(QLabel):
    def __init__(self, text='Drag files here or use "Browse"'):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #aaa;")
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.files = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            new_files = [url.toLocalFile() for url in urls if url.toLocalFile() not in self.files]
            self.files.extend(new_files)
            self.update_label_text()

    def update_label_text(self):
        if self.files:
            file_entries = [
                f'<div style="margin-bottom: 10px;">'
                f'<span style="font-size: 14px; font-weight: bold;">{i+1}. {os.path.basename(file)}</span><br>'
                f'<span style="font-size: 10px; color: #666;">{file}</span>'
                f'</div>'
                for i, file in enumerate(self.files)
            ]
            self.setText(''.join(file_entries))
        else:
            self.setText('<span style="color: #888; font-size: 12px;">Drag files here or use "Browse"</span>')

    def add_files(self, file_paths):
        new_files = [path for path in file_paths if path not in self.files]
        self.files.extend(new_files)
        self.update_label_text()

    def clear_files(self):
        self.files = []
        self.update_label_text()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.clients = self.load_clients()
        self.selected_client = 0
        self.mode = "Etsy"
        self.EtsyUI()

    def load_clients(self):
        try:
            with open("clients.json", "r") as f:
                clients = json.load(f)
                if not isinstance(clients, list):
                    raise ValueError("Invalid client data")
                for c in clients:
                    if not (isinstance(c, dict) and "Name" in c and "BankAcc" in c):
                        raise ValueError("Invalid client data")
                    if "total_transactions" not in c:
                        c["total_transactions"] = 0
                return clients
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return [{"Name": "MARLE SIA", "BankAcc": "LV81HABA0551052348489", "total_transactions": 0}]

    def save_clients(self):
        with open("clients.json", "w") as f:
            json.dump(self.clients, f, indent=4)

    def set_etsy_mode(self):
        self.mode = "Etsy"
        self.topleft.show()
        self.topmiddle.show()
        self.topright.show()
        self.client_label.show()
        self.combo.show()
        self.edit_clients_btn.show()
        self.drop_label.setText("Drag Transaction CSV files here or use 'Browse'")
        self.splitter1.setSizes([300, 300, 300])
        self.update_ui()

    def set_wise_mode(self):
        self.mode = "Wise"
        self.topmiddle.hide()
        self.topright.hide()
        self.client_label.hide()
        self.combo.hide()
        self.edit_clients_btn.hide()
        self.drop_label.setText("Drag Wise CSV file here or use 'Browse'")
        self.drop_label.clear_files()
        self.splitter1.setSizes([900, 0, 0])
        self.update_ui()

    def EtsyUI(self):
        self.main_layout = QVBoxLayout(self)

        menubar = QMenuBar(self)
        mode_menu = menubar.addMenu("Mode")
        etsy_action = mode_menu.addAction("Etsy Processing")
        wise_action = mode_menu.addAction("Wise Processing")
        etsy_action.triggered.connect(self.set_etsy_mode)
        wise_action.triggered.connect(self.set_wise_mode)
        self.main_layout.addWidget(menubar)

        hbox = QHBoxLayout()

        self.topleft = QFrame(self)
        self.topleft.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout()
        self.drop_label = DragDropLabel("Drag Transaction CSV files here or use 'Browse'")
        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(lambda: self.browse_file(self.drop_label))
        clear_btn = QPushButton("Clear Files")
        clear_btn.clicked.connect(self.drop_label.clear_files)
        label1 = QLabel("Transactions Statement CSV Files:")
        label1.setMaximumHeight(20)
        label1.setStyleSheet("font-size: 12px;")
        left_layout.addWidget(label1)
        left_layout.addWidget(self.drop_label)
        left_layout.addWidget(browse_btn)
        left_layout.addWidget(clear_btn)
        left_layout.addStretch()
        self.topleft.setLayout(left_layout)

        self.topmiddle = QFrame(self)
        self.topmiddle.setFrameShape(QFrame.Shape.StyledPanel)
        middle_layout = QVBoxLayout()
        self.drop_label2 = DragDropLabel()
        browse_btn2 = QPushButton("Browse Files")
        browse_btn2.clicked.connect(lambda: self.browse_file(self.drop_label2))
        clear_btn2 = QPushButton("Clear Files")
        clear_btn2.clicked.connect(self.drop_label2.clear_files)
        label2 = QLabel("Orders CSV Files:")
        label2.setMaximumHeight(20)
        label2.setStyleSheet("font-size: 12px;")
        middle_layout.addWidget(label2)
        middle_layout.addWidget(self.drop_label2)
        middle_layout.addWidget(browse_btn2)
        middle_layout.addWidget(clear_btn2)
        middle_layout.addStretch()
        self.topmiddle.setLayout(middle_layout)

        self.topright = QFrame(self)
        self.topright.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout()
        self.drop_label3 = DragDropLabel()
        browse_btn3 = QPushButton("Browse Files")
        browse_btn3.clicked.connect(lambda: self.browse_file(self.drop_label3))
        clear_btn3 = QPushButton("Clear Files")
        clear_btn3.clicked.connect(self.drop_label3.clear_files)
        label3 = QLabel("Etsy Invoice PDF Files:")
        label3.setMaximumHeight(20)
        label3.setStyleSheet("font-size: 12px;")
        right_layout.addWidget(label3)
        right_layout.addWidget(self.drop_label3)
        right_layout.addWidget(browse_btn3)
        right_layout.addWidget(clear_btn3)
        right_layout.addStretch()
        self.topright.setLayout(right_layout)

        bottom = QFrame(self)
        bottom.setFrameShape(QFrame.Shape.StyledPanel)
        bottom_layout = QGridLayout()
        bottom_layout.setSpacing(10)
        self.client_label = QLabel('Select Client:')
        self.combo = QComboBox(self)
        self.update_combo()
        self.edit_clients_btn = QPushButton("Edit Clients")
        self.edit_clients_btn.clicked.connect(self.edit_clients)

        process_files_btn = QPushButton("PROCESS")
        process_files_btn.clicked.connect(self.process_files)
        bottom_layout.addWidget(self.client_label, 1, 0)
        bottom_layout.addWidget(self.combo, 1, 1)
        bottom_layout.addWidget(self.edit_clients_btn, 1, 2)
        bottom_layout.addWidget(process_files_btn, 2, 0, 1, 3)
        bottom.setLayout(bottom_layout)

        self.splitter1 = QSplitter(Qt.Orientation.Horizontal)
        self.splitter1.addWidget(self.topleft)
        self.splitter1.addWidget(self.topmiddle)
        self.splitter1.addWidget(self.topright)
        self.splitter1.setSizes([300, 300, 300])

        splitter2 = QSplitter(Qt.Orientation.Vertical)
        splitter2.addWidget(self.splitter1)
        splitter2.addWidget(bottom)
        splitter2.setSizes([500, 200])

        hbox.addWidget(splitter2)
        self.main_layout.addLayout(hbox)
        self.setLayout(self.main_layout)

        self.setGeometry(300, 100, 900, 600)
        self.setWindowTitle('CSV to XML Converter')
        self.show()

    def update_combo(self):
        self.combo.clear()
        for client in self.clients:
            self.combo.addItem(client["Name"])
        if self.clients and self.selected_client < len(self.clients):
            self.combo.setCurrentIndex(self.selected_client)
        else:
            self.selected_client = 0
            self.combo.setCurrentIndex(0)

    def edit_clients(self):
        dialog = ClientEditorDialog(self.clients, self)
        if dialog.exec():
            self.clients = dialog.get_clients()
            self.save_clients()
            self.selected_client = min(self.selected_client, len(self.clients) - 1 if self.clients else 0)
            self.update_combo()

    def browse_file(self, label):
        if self.mode == "Wise":
            file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
            if file_path:
                label.add_files([file_path])
        else:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files")
            if file_paths:
                label.add_files(file_paths)

    def update_ui(self):
        if self.mode == "Etsy":
            self.topleft.setMaximumWidth(270)
        else:
            self.topleft.setMaximumWidth(16777215)  # Max int to allow full expansion

    def process_files(self):
        generated_files = []
        success = True

        if self.mode == "Etsy":
            transaction_files = self.drop_label.files
            sales_files = self.drop_label2.files
            pdf_files = self.drop_label3.files

            if not transaction_files:
                QMessageBox.warning(self, "Missing Files", "Please provide at least one Transaction CSV file.")
                return

            if not sales_files:
                QMessageBox.warning(self, "Missing Files", "Please provide at least one Orders CSV file.")
                return

            client = self.clients[self.selected_client]
            for transaction_file in transaction_files:
                output_xml = os.path.splitext(transaction_file)[0] + ".xml"
                try:
                    etsy_to_xml.process(transaction_file, sales_files, pdf_files, client, self.clients, self.selected_client, output_xml)
                    generated_files.append(output_xml)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to process {os.path.basename(transaction_file)}: {str(e)}")
                    success = False
                    break

            if success:
                self.save_clients()

        else:  # Wise mode
            wise_files = self.drop_label.files

            if not wise_files:
                QMessageBox.warning(self, "Missing Files", "Please provide one Wise CSV file.")
                return

            if len(wise_files) > 1:
                QMessageBox.warning(self, "Too Many Files", "Please provide exactly one Wise CSV file.")
                return

            wise_file = wise_files[0]
            output_xml = os.path.splitext(wise_file)[0] + ".xml"
            try:
                wise_to_xml.process(wise_file, output_xml)
                generated_files.append(output_xml)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process {os.path.basename(wise_file)}: {str(e)}")
                success = False

        if success:
            QMessageBox.information(self, "Success", f"XML files generated: {', '.join(os.path.basename(f) for f in generated_files)}.")

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()