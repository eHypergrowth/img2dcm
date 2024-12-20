import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QFileDialog, QLineEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from pydicom import Dataset, dcmwrite
from pydicom.uid import generate_uid
from PIL import Image
import numpy as np
import sys
from logging_config import logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertirod de JPG a DICOM y Envio a PACS")
        self.setFixedSize(600, 500)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title label
        title = QLabel("Convertirod de JPG a DICOM y Envio a PACS")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.jpg_path_input = QLineEdit()
        self.jpg_path_input.setPlaceholderText("Seleccionar archivo jpg...")
        self.jpg_path_input.setReadOnly(True)
        layout.addWidget(self.jpg_path_input)

        select_file_button = QPushButton("Seleccionar archivo jpg")
        select_file_button.clicked.connect(self.select_jpg_file)
        layout.addWidget(select_file_button)

        self.patient_id_input = QLineEdit()
        self.patient_id_input.setPlaceholderText("Patient ID (e.g., 123456)")
        self.patient_id_input.textChanged.connect(self.fetch_patient_name)
        layout.addWidget(self.patient_id_input)

        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Patient Name")
        self.patient_name_input.setReadOnly(True)
        layout.addWidget(self.patient_name_input)

        self.study_description_input = QLineEdit()
        self.study_description_input.setPlaceholderText("Study Description (e.g., Ortopantomografia)")
        layout.addWidget(self.study_description_input)

        self.accession_number_input = QLineEdit()
        self.accession_number_input.setPlaceholderText("Accession Number (e.g., ACC12345)")
        layout.addWidget(self.accession_number_input)

        self.study_id_input = QLineEdit()
        self.study_id_input.setPlaceholderText("Study ID (e.g., 78910)")
        layout.addWidget(self.study_id_input)

        convert_button = QPushButton("Converti y enviar a PACS")
        convert_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        convert_button.clicked.connect(self.convert_and_send_to_pacs)
        layout.addWidget(convert_button)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    def select_jpg_file(self):
        file_dialog = QFileDialog()
        jpg_path, _ = file_dialog.getOpenFileName(self, "Select JPG File", "", "Images (*.jpg *.jpeg)")
        if jpg_path:
            self.jpg_path_input.setText(jpg_path)
            logger.info(f"Selected JPG file: {jpg_path}")

    def fetch_patient_name(self):
        patient_id = self.patient_id_input.text()
        if not patient_id:
            self.patient_name_input.clear()
            logger.debug("Patient ID input cleared.")
            return

        try:
            finds_path = os.getenv("FINDSCU_PATH", "/home/skynet/Documentos/GitHub/img2dcm/dcm4che-5.33.1/bin/findscu")
            command = [
                finds_path,
                "-c", "DCM4CHEE@172.17.200.23:11112",
                "-m", f"PatientID={patient_id}",
                "-r", "PatientName"
            ]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            logger.info(f"findscu output: {result.stdout}")
            if result.stderr:
                logger.warning(f"findscu warning: {result.stderr}")

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "(0010,0010)" in line and "PatientName" in line:
                        start_idx = line.find("[")
                        end_idx = line.find("]")
                        if start_idx != -1 and end_idx != -1:
                            raw_name = line[start_idx + 1:end_idx].strip()
                            if raw_name:
                                patient_name = " ".join(raw_name.split("^")).strip()
                                self.patient_name_input.setText(patient_name)
                                logger.info(f"Fetched patient name: {patient_name}")
                                return
                self.patient_name_input.setText("Not Found")
                logger.warning("Patient name not found in the findscu response.")
            else:
                self.patient_name_input.setText("Error Fetching")
                logger.error(f"findscu error: {result.stderr}")
        except Exception as e:
            logger.exception(f"Error fetching patient name: {e}")
            self.patient_name_input.setText(f"Error: {str(e)}")

    def convert_and_send_to_pacs(self):
        jpg_path = self.jpg_path_input.text()
        patient_name = self.patient_name_input.text()
        patient_id = self.patient_id_input.text()
        study_description = self.study_description_input.text()
        accession_number = self.accession_number_input.text()
        study_id = self.study_id_input.text()

        if not all([jpg_path, patient_name, patient_id, study_description, accession_number, study_id]):
            self.status_label.setText("Please fill in all fields.")
            self.status_label.setStyleSheet("color: red;")
            logger.warning("Attempted to convert without all fields filled.")
            return

        try:
            dicom_path = jpg_path.replace(".jpg", ".dcm")
            self.create_dicom(jpg_path, dicom_path, patient_name, patient_id, study_description, accession_number, study_id)
            self.send_to_pacs(dicom_path)
        except Exception as e:
            logger.exception(f"Error during conversion or sending: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def create_dicom(self, jpg_path, dicom_path, patient_name, patient_id, study_description, accession_number, study_id):
        try:
            img = Image.open(jpg_path).convert('L')  # Convertir a escala de grises
            np_img = np.array(img)

            ds = Dataset()
            # Meta information
            ds.file_meta = Dataset()
            ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"  # Secondary Capture Image Storage
            ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()
            ds.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # Implicit VR Little Endian

            # Patient Module
            ds.PatientName = patient_name  # 0010,0010
            ds.PatientID = patient_id  # 0010,0020

            # Study Module
            ds.StudyInstanceUID = generate_uid()  # 0020,000D
            ds.StudyDate = "20241219"  # 0008,0020 - YYYYMMDD (debe generarse dinámicamente si es necesario)
            ds.StudyTime = "164038"  # 0008,0030 - HHMMSS (debe generarse dinámicamente si es necesario)
            ds.AccessionNumber = accession_number  # 0008,0050
            ds.StudyDescription = study_description  # 0008,1030 (opcional, pero útil)

            # Series Module
            ds.SeriesInstanceUID = generate_uid()  # 0020,000E
            ds.SeriesNumber = "1"  # 0020,0011 (puedes ajustar según la lógica de tu aplicación)

            # Image Module
            ds.SOPClassUID = ds.file_meta.MediaStorageSOPClassUID  # 0008,0016
            ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID  # 0008,0018
            ds.InstanceNumber = "1"  # 0020,0013
            ds.Rows, ds.Columns = np_img.shape  # 0028,0010 y 0028,0011
            ds.SamplesPerPixel = 1  # Monocromático
            ds.PhotometricInterpretation = "MONOCHROME2"  # 0028,0004
            ds.BitsAllocated = 8  # 0028,0100
            ds.BitsStored = 8  # 0028,0101
            ds.HighBit = 7  # 0028,0102
            ds.PixelRepresentation = 0  # 0028,0103
            ds.PixelData = np_img.tobytes()  # 7FE0,0010

            # Opcionales
            ds.Modality = "OT"  # Other (puedes ajustar según la modalidad específica)

            # Escribir el archivo DICOM
            dcmwrite(dicom_path, ds)
            logger.info(f"DICOM file created successfully: {dicom_path}")
        except Exception as e:
            logger.exception(f"Error creating DICOM file: {e}")
            raise


    def send_to_pacs(self, dicom_path):
        try:
            stores_path = os.getenv("STORESCU_PATH", "/home/skynet/Documentos/GitHub/img2dcm/dcm4che-5.33.1/bin/storescu")
            command = [
                stores_path,
                "-c", "DCM4CHEE@172.17.200.23:11112",
                dicom_path
            ]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                self.status_label.setText("DICOM sent successfully to PACS.")
                self.status_label.setStyleSheet("color: green;")
                logger.info("DICOM sent successfully to PACS.")
            else:
                self.status_label.setText(f"Failed to send to PACS: {result.stderr}")
                self.status_label.setStyleSheet("color: red;")
                logger.error(f"Failed to send to PACS: {result.stderr}")
        except Exception as e:
            logger.exception(f"Error sending to PACS: {e}")
            self.status_label.setText(f"Error sending to PACS: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

if __name__ == "__main__":
    logger.info("Starting JPG to DICOM Converter & PACS Sender application.")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
