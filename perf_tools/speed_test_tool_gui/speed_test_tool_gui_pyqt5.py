import psutil
import time
import argparse
import csv
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QFileDialog, QComboBox, QMessageBox
)
from PyQt5.QtCore import QTimer
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="Monitor network bandwidth usage.")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Time interval in seconds between usage checks (default: 1.0)")
    parser.add_argument("-n", "--interface", type=str, default=None, help="Name of the network interface to monitor (e.g., eth0). If not provided, monitors total usage across all interfaces.")
    parser.add_argument("-t", "--threshold", type=float, default=None, help="Threshold in MB above which usage during an interval triggers a warning.")
    parser.add_argument("-o", "--csv-output", type=str, default=None, help="Path to a CSV file where usage data will be logged.")
    return parser.parse_args()

def get_bandwidth_usage(interval, interface=None):
    if interface:
        net_io_before = psutil.net_io_counters(pernic=True).get(interface)
    else:
        net_io_before = psutil.net_io_counters()

    time.sleep(interval)

    if interface:
        net_io_after = psutil.net_io_counters(pernic=True).get(interface)
    else:
        net_io_after = psutil.net_io_counters()

    if not net_io_before or not net_io_after:
        print(f"Error: Interface '{interface}' not found.")
        sys.exit(1)

    sent_bytes = net_io_after.bytes_sent - net_io_before.bytes_sent
    received_bytes = net_io_after.bytes_recv - net_io_before.bytes_recv

    sent_speed = sent_bytes / interval / 1024
    received_speed = received_bytes / interval / 1024

    return sent_speed, received_speed

def log_to_csv(csv_path, upload_speed, download_speed):
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), upload_speed, download_speed])

class BandwidthMonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)

    def init_ui(self):
        self.setWindowTitle("Speed Test Tool")
        layout = QVBoxLayout()

        self.upload_label = QLabel("Upload Speed: 0.00 KB/s")
        self.download_label = QLabel("Download Speed: 0.00 KB/s")
        layout.addWidget(self.upload_label)
        layout.addWidget(self.download_label)

        self.interval_input = QLineEdit("1.0")
        layout.addWidget(QLabel("Interval (seconds):"))
        layout.addWidget(self.interval_input)

        self.interface_dropdown = QComboBox()
        self.interface_dropdown.addItems(psutil.net_if_addrs().keys())
        layout.addWidget(QLabel("Network Interface:"))
        layout.addWidget(self.interface_dropdown)

        self.threshold_input = QLineEdit()
        layout.addWidget(QLabel("Threshold (MB):"))
        layout.addWidget(self.threshold_input)

        self.csv_output_input = QLineEdit(f"speed-test-{datetime.now().strftime('%d-%m-%y')}.csv")
        layout.addWidget(QLabel("CSV Output Path:"))
        layout.addWidget(self.csv_output_input)

        browse_button = QPushButton("Select File")
        browse_button.clicked.connect(self.select_output_file)
        layout.addWidget(browse_button)

        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        layout.addWidget(start_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def select_output_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_path:
            self.csv_output_input.setText(file_path)

    def start_monitoring(self):
        interval = float(self.interval_input.text()) * 1000
        self.timer.start(interval)

    def update_ui(self):
        upload_speed, download_speed = get_bandwidth_usage(float(self.interval_input.text()), self.interface_dropdown.currentText())
        self.upload_label.setText(f"Upload Speed: {upload_speed:.2f} KB/s")
        self.download_label.setText(f"Download Speed: {download_speed:.2f} KB/s")

        threshold = self.threshold_input.text()
        if threshold and (upload_speed / 1024 > float(threshold) or download_speed / 1024 > float(threshold)):
            QMessageBox.warning(self, "Threshold Exceeded", "Bandwidth usage exceeded threshold!")

        csv_path = self.csv_output_input.text()
        if csv_path:
            log_to_csv(csv_path, upload_speed, download_speed)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BandwidthMonitorApp()
    window.show()
    sys.exit(app.exec_())
