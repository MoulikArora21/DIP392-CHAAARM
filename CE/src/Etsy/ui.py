import sys
import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSplitter, QApplication, 
                            QComboBox, QLabel, QVBoxLayout, QPushButton, QFileDialog, 
                            QGridLayout, QDialog, QListWidget, QLineEdit, QFormLayout, QSizePolicy, QMessageBox)
import etsy_to_xml

class ClientEditorDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Clients")
        self.clients = clients.copy()  # Work on a copy to allow canceling
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Client list
        self.client_list = QListWidget()
        self.update_client_list()
        layout.addWidget(self.client_list)

        # Form for adding new client
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.bank_acc_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Bank Account:", self.bank_acc_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Client")
        add_btn.clicked.connect(self.add_client)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_client)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(400)

    def update_client_list(self):
        self.client_list.clear()
        for client in self.clients:
            self.client_list.addItem(f"{client['Name']} ({client['BankAcc']})")

    def add_client(self):
        name = self.name_input.text().strip()
        bank_acc = self.bank_acc_input.text().strip()
        if name and bank_acc:
            self.clients.append({"Name": name, "BankAcc": bank_acc})
            self.update_client_list()
            self.name_input.clear()
            self.bank_acc_input.clear()

    def delete_client(self):
        selected = self.client_list.currentRow()
        if selected >= 0:
            self.clients.pop(selected)
            self.update_client_list()

    def get_clients(self):
        return self.clients

class DragDropLabel(QLabel):
    def __init__(self):
        super().__init__('Drag files here or use "Browse"')
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #aaa;")
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setMinimumHeight(400)  # Ensure sufficient height for file display
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.files = []  # List to store dropped file paths

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            # Add new files to the list, avoiding duplicates
            new_files = [url.toLocalFile() for url in urls if url.toLocalFile() not in self.files]
            self.files.extend(new_files)
            # Update label text with list of files
            self.update_label_text()

    def update_label_text(self):
        if self.files:
            # Generate HTML for each file: numbered, large file name, small path
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
        # Add new files to the list, avoiding duplicates
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
        self.EtsyUI()

    def load_clients(self):
        try:
            with open("clients.json", "r") as f:
                clients = json.load(f)
                # Validate that clients is a list of dictionaries with Name and BankAcc
                if not isinstance(clients, list) or not all(isinstance(c, dict) and "Name" in c and "BankAcc" in c for c in clients):
                    raise ValueError("Invalid client data")
                return clients
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            # Return default client if file doesn't exist or is invalid
            return [{"Name": "MARLE SIA", "BankAcc": "LV81HABA0551052348489"}]

    def save_clients(self):
        with open("clients.json", "w") as f:
            json.dump(self.clients, f, indent=4)

    def EtsyUI(self):
        hbox = QHBoxLayout(self)

        topleft = QFrame(self)
        topleft.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout()
        self.drop_label = DragDropLabel()
        self.drop_label.setMaximumWidth(270)
        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(lambda: self.browse_file(self.drop_label))
        clear_btn = QPushButton("Clear Files")
        clear_btn.clicked.connect(self.drop_label.clear_files)
        label1 = QLabel("Transactions Statement CSV Files:")
        label1.setMaximumHeight(20)  # Limit label height
        label1.setStyleSheet("font-size: 12px;")  # Smaller font for label
        left_layout.addWidget(label1)
        left_layout.addWidget(self.drop_label)
        left_layout.addWidget(browse_btn)
        left_layout.addWidget(clear_btn)
        left_layout.addStretch()  # Push content up, prioritize DragDropLabel
        topleft.setLayout(left_layout)

        # Middle Frame
        topmiddle = QFrame(self)
        topmiddle.setFrameShape(QFrame.Shape.StyledPanel)
        middle_layout = QVBoxLayout()
        self.drop_label2 = DragDropLabel()
        browse_btn2 = QPushButton("Browse Files")
        browse_btn2.clicked.connect(lambda: self.browse_file(self.drop_label2))
        clear_btn2 = QPushButton("Clear Files")
        clear_btn2.clicked.connect(self.drop_label2.clear_files)
        label2 = QLabel("Orders CSV Files:")
        label2.setMaximumHeight(20)  # Limit label height
        label2.setStyleSheet("font-size: 12px;")  # Smaller font for label
        middle_layout.addWidget(label2)
        middle_layout.addWidget(self.drop_label2)
        middle_layout.addWidget(browse_btn2)
        middle_layout.addWidget(clear_btn2)
        middle_layout.addStretch()  # Push content up, prioritize DragDropLabel
        topmiddle.setLayout(middle_layout)

        # Right Frame
        topright = QFrame(self)
        topright.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout()
        self.drop_label3 = DragDropLabel()
        browse_btn3 = QPushButton("Browse Files")
        browse_btn3.clicked.connect(lambda: self.browse_file(self.drop_label3))
        clear_btn3 = QPushButton("Clear Files")
        clear_btn3.clicked.connect(self.drop_label3.clear_files)
        label3 = QLabel("Etsy Invoice PDF Files:")
        label3.setMaximumHeight(20)  # Limit label height
        label3.setStyleSheet("font-size: 12px;")  # Smaller font for label
        right_layout.addWidget(label3)
        right_layout.addWidget(self.drop_label3)
        right_layout.addWidget(browse_btn3)
        right_layout.addWidget(clear_btn3)
        right_layout.addStretch()  # Push content up, prioritize DragDropLabel
        topright.setLayout(right_layout)

        # Bottom Frame
        bottom = QFrame(self)
        bottom.setFrameShape(QFrame.Shape.StyledPanel)
        bottom_layout = QGridLayout()
        bottom_layout.setSpacing(10)
        client_label = QLabel('Select Client:')
        self.combo = QComboBox(self)
        self.update_combo()
        edit_clients_btn = QPushButton("Edit Clients")
        edit_clients_btn.clicked.connect(self.edit_clients)

        process_files_btn = QPushButton("PROCESS")
        process_files_btn.clicked.connect(self.process_files)
        bottom_layout.addWidget(client_label, 1, 0)
        bottom_layout.addWidget(self.combo, 1, 1)
        bottom_layout.addWidget(edit_clients_btn, 1, 2)
        bottom_layout.addWidget(process_files_btn, 2, 0,2,3)
        bottom.setLayout(bottom_layout)

        # Splitters
        splitter1 = QSplitter(Qt.Orientation.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(topmiddle)
        splitter1.addWidget(topright)
        splitter1.setSizes([300, 300, 300]) 

        splitter2 = QSplitter(Qt.Orientation.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(bottom)
        splitter2.setSizes([500, 200])

        hbox.addWidget(splitter2)
        self.setLayout(hbox)

        self.setGeometry(300, 100, 900, 600)
        self.setWindowTitle('QSplitter')
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
            self.save_clients()  # Save updated clients to file
            self.selected_client = min(self.selected_client, len(self.clients) - 1 if self.clients else 0)
            self.update_combo()

    def browse_file(self, label):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files")
        if file_paths:
            label.add_files(file_paths)

    def process_files(self):
            transaction_files = self.drop_label.files
            sales_files = self.drop_label2.files
            pdf_files = self.drop_label3.files

            if not transaction_files or not sales_files:
                QMessageBox.warning(self, "Missing Files", "Please provide at least one Transaction CSV and one Sales CSV file.")
                return

            if len(transaction_files) > 1 or len(sales_files) > 1 or len(pdf_files) > 1:
                QMessageBox.warning(self, "Too Many Files", "Please provide only one file per category.")
                return

            transaction_file = transaction_files[0]
            sales_file = sales_files[0]
            pdf_file = pdf_files[0] if pdf_files else None
            client = self.clients[self.selected_client]

            try:
                etsy_to_xml.process(transaction_file, sales_file, pdf_file, client)
                QMessageBox.information(self, "Success", "XML file generated successfully as 'output.xml'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process files: {str(e)}")


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()