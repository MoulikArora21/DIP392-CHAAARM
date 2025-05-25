import sys
import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSplitter, QApplication, 
                            QComboBox, QLabel, QVBoxLayout, QPushButton, QFileDialog, 
                            QGridLayout, QDialog, QListWidget, QLineEdit, QFormLayout, 
                            QSizePolicy, QMessageBox, QMenuBar, QTextEdit)
import etsy_to_xml
import wise_to_xml
import revolut_to_xml
import logging  # Added for debugging

# Set up basic logging to diagnose crashes
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.legal_id_input = QLineEdit()
        self.total_transactions_input = QLineEdit()
        self.total_transactions_input.setValidator(QIntValidator(0, 999999))
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Bank Account:", self.bank_acc_input)
        form_layout.addRow("Legal ID:", self.legal_id_input)
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
        legal_id = self.legal_id_input.text().strip()
        total_transactions = self.total_transactions_input.text().strip()
        total_transactions = int(total_transactions) if total_transactions else 0
        return {
            "Name": name,
            "BankAcc": bank_acc,
            "LegalId": legal_id,
            "total_transactions": total_transactions
        }

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
        self.legal_id_input = QLineEdit(self.client.get("LegalId", ""))
        self.total_transactions_input = QLineEdit(str(self.client["total_transactions"]))
        self.total_transactions_input.setValidator(QIntValidator(0, 999999))
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Bank Account:", self.bank_acc_input)
        form_layout.addRow("Legal ID:", self.legal_id_input)
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
        legal_id = self.legal_id_input.text().strip()
        total_transactions = self.total_transactions_input.text().strip()
        total_transactions = int(total_transactions) if total_transactions else 0
        return {
            "Name": name,
            "BankAcc": bank_acc,
            "LegalId": legal_id,
            "total_transactions": total_transactions
        }

class ClientEditorDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Clients")
        self.clients = clients.copy()
        self.parent = parent
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
        self.setMinimumWidth(600)

    def update_client_list(self):
        self.client_list.clear()
        for i, client in enumerate(self.clients):
            legal_id = client.get("LegalId", "")
            legal_id_display = f", LegalId: {legal_id}" if legal_id else ""
            display_text = (f"{client['Name']}" if client["Name"] == "--NO CLIENT SELECTED--"
                           else f"Client {i}: {client['Name']} ({client['BankAcc']}{legal_id_display}, Transactions: {client['total_transactions']})")
            self.client_list.addItem(display_text)
        # Ensure valid selection
        if self.clients:
            self.client_list.setCurrentRow(0)  # Select first item
        else:
            self.client_list.clearSelection()  # No selection if list is empty
        logging.debug(f"Updated client list, items: {self.client_list.count()}, selected row: {self.client_list.currentRow()}")

    def update_button_states(self):
        selected = self.client_list.currentRow()
        has_selection = selected >= 0
        is_default_client = False
        if has_selection and selected < len(self.clients):  # Bounds check
            is_default_client = self.clients[selected]["Name"] == "--NO CLIENT SELECTED--"
        self.edit_btn.setEnabled(has_selection and not is_default_client)
        self.delete_btn.setEnabled(has_selection and not is_default_client)
        logging.debug(f"Button states: selected={selected}, has_selection={has_selection}, is_default_client={is_default_client}")

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
        if selected >= 0 and selected < len(self.clients) and self.clients[selected]["Name"] != "--NO CLIENT SELECTED--":
            dialog = EditClientDialog(self.clients[selected], self)
            if dialog.exec():
                client_data = dialog.get_client_data()
                if client_data["Name"] and client_data["BankAcc"]:
                    self.clients[selected] = client_data
                    self.update_client_list()
                else:
                    QMessageBox.warning(self, "Invalid Input", "Name and Bank Account cannot be empty.")
        else:
            QMessageBox.warning(self, "Invalid Selection", "Cannot edit the default client.")

    def edit_client_double_click(self):
        selected = self.client_list.currentRow()
        if selected >= 0 and selected < len(self.clients) and self.clients[selected]["Name"] != "--NO CLIENT SELECTED--":
            self.edit_client()

    def delete_client(self):
        selected = self.client_list.currentRow()
        if selected >= 0 and selected < len(self.clients) and self.clients[selected]["Name"] != "--NO CLIENT SELECTED--":
            logging.debug(f"Deleting client at index {selected}, current selected_client: {self.parent.selected_client if self.parent else 'No parent'}")
            if self.parent and hasattr(self.parent, 'selected_client'):
                if selected == self.parent.selected_client:
                    self.parent.selected_client = 0
                elif selected < self.parent.selected_client:
                    self.parent.selected_client -= 1
            self.clients.pop(selected)
            self.update_client_list()
            logging.debug(f"After deletion, clients: {len(self.clients)}, selected_client: {self.parent.selected_client if self.parent else 'No parent'}")
        else:
            QMessageBox.warning(self, "Invalid Selection", "Cannot delete the default client.")

    def accept(self):
        super().accept()

    def get_clients(self):
        return self.clients

class EditXMLDialog(QDialog):
    def __init__(self, xml_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit XML: {os.path.basename(xml_file)}")
        self.xml_file = xml_file
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setFontFamily("Courier New")
        self.text_edit.setMinimumSize(600, 400)
        self.text_edit.setUndoRedoEnabled(True)
        try:
            with open(self.xml_file, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load {os.path.basename(self.xml_file)}: {str(e)}")
            self.reject()
            return
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.text_edit.undo)
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.text_edit.redo)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_xml)
        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self.save_as_xml)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(undo_btn)
        button_layout.addWidget(redo_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(save_as_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save_xml(self):
        try:
            with open(self.xml_file, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save {os.path.basename(self.xml_file)}: {str(e)}")

    def save_as_xml(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save XML As", "", "XML Files (*.xml)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.text_edit.toPlainText())
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save {os.path.basename(file_path)}: {str(e)}")

class SelectXMLDialog(QDialog):
    def __init__(self, xml_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select XML to Edit")
        self.xml_files = xml_files
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.xml_list = QListWidget()
        for xml_file in self.xml_files:
            self.xml_list.addItem(os.path.basename(xml_file))
        self.xml_list.doubleClicked.connect(self.edit_xml)
        layout.addWidget(self.xml_list)

        button_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self.edit_xml)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.xml_list.itemSelectionChanged.connect(self.update_button_state)
        self.edit_btn = edit_btn
        self.update_button_state()

        self.setLayout(layout)
        self.setMinimumWidth(400)

    def update_button_state(self):
        has_selection = self.xml_list.currentRow() >= 0
        self.edit_btn.setEnabled(has_selection)

    def edit_xml(self):
        selected = self.xml_list.currentRow()
        if selected >= 0:
            xml_file = self.xml_files[selected]
            dialog = EditXMLDialog(xml_file, self)
            dialog.exec()

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
        default_client = [{"Name": "--NO CLIENT SELECTED--", "BankAcc": "--NONE SELECTED--", "LegalId": "", "total_transactions": 0}]
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
                    if "LegalId" not in c:
                        c["LegalId"] = ""
                # Ensure default client is first
                if not any(c["Name"] == "--NO CLIENT SELECTED--" for c in clients):
                    clients.insert(0, default_client[0])
                return clients
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return default_client

    def save_clients(self):
        # Save all clients except the default if it's the only one
        clients_to_save = [c for c in self.clients if c["Name"] != "--NO CLIENT SELECTED--"]
        with open("clients.json", "w") as f:
            json.dump(clients_to_save, f, indent=4)

    def set_etsy_mode(self):
        self.mode = "Etsy"
        self.topleft.show()
        self.topmiddle.show()
        self.topright.show()
        self.client_label.show()
        self.combo.show()
        self.edit_clients_btn.show()
        self.drop_label.setText("Drag files here or use 'Browse'")
        self.splitter1.setSizes([300, 300, 300])
        self.update_ui()

    def set_wise_mode(self):
        self.mode = "Wise"
        self.topmiddle.hide()
        self.topright.hide()
        self.client_label.show()
        self.combo.show()
        self.edit_clients_btn.show()
        self.drop_label.setText("Drag Wise CSV files here or use 'Browse'")
        self.drop_label.clear_files()
        self.splitter1.setSizes([900, 0, 0])
        self.update_ui()

    def set_revolut_mode(self):
        self.mode = "Revolut"
        self.topmiddle.hide()
        self.topright.hide()
        self.client_label.show()
        self.combo.show()
        self.edit_clients_btn.show()
        self.drop_label.setText("Drag Revolut CSV files here or use 'Browse'")
        self.drop_label.clear_files()
        self.splitter1.setSizes([900, 0, 0])
        self.update_ui()

    def update_selected_client(self, index):
        if index >= 0 and index < len(self.clients):
            self.selected_client = index

    def EtsyUI(self):
        self.main_layout = QVBoxLayout(self)

        menubar = QMenuBar(self)
        mode_menu = menubar.addMenu("Mode")
        etsy_action = mode_menu.addAction("Etsy Processing")
        wise_action = mode_menu.addAction("Wise Processing")
        revolut_action = mode_menu.addAction("Revolut Processing")
        etsy_action.triggered.connect(self.set_etsy_mode)
        wise_action.triggered.connect(self.set_wise_mode)
        revolut_action.triggered.connect(self.set_revolut_mode)
        self.main_layout.addWidget(menubar)

        hbox = QHBoxLayout()

        self.topleft = QFrame(self)
        self.topleft.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout()
        self.drop_label = DragDropLabel("Drag files here or use 'Browse'")
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
        self.combo.currentIndexChanged.connect(self.update_selected_client)
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
        self.combo.blockSignals(True)
        self.combo.clear()
        for i, client in enumerate(self.clients):
            display_text = (f"{client['Name']}" if client["Name"] == "--NO CLIENT SELECTED--"
                           else f"Client {i}: {client['Name']}")
            self.combo.addItem(display_text)
        self.combo.setCurrentIndex(self.selected_client)
        self.combo.blockSignals(False)

    def edit_clients(self):
        dialog = ClientEditorDialog(self.clients, self)
        if dialog.exec():
            self.clients = dialog.get_clients()
            # Ensure default client is always present
            if not any(c["Name"] == "--NO CLIENT SELECTED--" for c in self.clients):
                self.clients.insert(0, {"Name": "--NO CLIENT SELECTED--", "BankAcc": "--NONE SELECTED--", "LegalId": "", "total_transactions": 0})
            self.save_clients()
            self.selected_client = min(self.selected_client, len(self.clients) - 1 if self.clients else 0)
            self.update_combo()

    def browse_file(self, label):
        if label == self.drop_label3:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open PDF Files", "", "PDF Files (*.pdf)")
        else:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open CSV Files", "", "CSV Files (*.csv)")
        if file_paths:
            label.add_files(file_paths)

    def update_ui(self):
        if self.mode == "Etsy":
            self.topleft.setMaximumWidth(300)
        else:
            self.topleft.setMaximumWidth(16777215)

    def process_files(self):
        generated_files = []
        success = True

        if self.clients[self.selected_client]["Name"] == "--NO CLIENT SELECTED--":
            QMessageBox.warning(self, "No Client Selected", "Please select a valid client before processing files.")
            return

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

        elif self.mode == "Wise":
            wise_files = self.drop_label.files

            if not wise_files:
                QMessageBox.warning(self, "Missing Files", "Please provide at least one Wise CSV file.")
                return

            client = self.clients[self.selected_client]
            for wise_file in wise_files:
                output_xml = os.path.splitext(wise_file)[0] + ".xml"
                try:
                    wise_to_xml.process(wise_file, output_xml, client, self.clients, self.selected_client)
                    generated_files.append(output_xml)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to process {os.path.basename(wise_file)}: {str(e)}")
                    success = False
                    break

        elif self.mode == "Revolut":
            revolut_files = self.drop_label.files

            if not revolut_files:
                QMessageBox.warning(self, "Missing Files", "Please provide at least one Revolut CSV file.")
                return

            client = self.clients[self.selected_client]
            for revolut_file in revolut_files:
                output_xml = os.path.splitext(revolut_file)[0] + ".xml"
                try:
                    revolut_to_xml.process(revolut_file, output_xml, client, self.clients, self.selected_client)
                    generated_files.append(output_xml)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to process {os.path.basename(revolut_file)}: {str(e)}")
                    success = False
                    break

        if success:
            self.save_clients()
            QMessageBox.information(self, "Success", f"XML files generated: {', '.join(os.path.basename(f) for f in generated_files)}.")
            dialog = SelectXMLDialog(generated_files, self)
            dialog.exec()

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()