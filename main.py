#!/usr/bin/python3

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
import sys, subprocess, os, copy, threading, re

#sys.path.append('LIBS')

IMAGE: str = "c0deinblack/yt-dlp-at"
IMAGE_VERSION: str = "v2.2"

class MainUI(QMainWindow,):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # loadUi(os.path.join(sys._MEIPASS, 'mainWindow.ui')) # Pyinstaller tmp path
        uic.loadUi('mainWindow_bak.ui', self)
        # Qt::AlignHCenter -> Replace in the ui file
         
        self.path_button.clicked.connect(self.browse_path)
        self.file_checkbox.stateChanged.connect(self.use_file)
        self.run_button.clicked.connect(self.run)
        self.sections_checkbox.stateChanged.connect(self.use_sections)
        self.st_checkbox.stateChanged.connect(self.use_default_section_title)
        self.status_button.clicked.connect(self.status)
        self.cancel_button.clicked.connect(self.cancel_process)

        self.image: str = IMAGE
        self.version: str = IMAGE_VERSION
        self.path: str = ''
        self.file: str = ''
        self.url: str = ''
        self.metadata: str = ''
        self.sections_file: str = ''
        self.default_sections: bool = False
        
        self.command: list[str] = '' 
        self.status: str = ''    
        
        self.available_msg_box: bool = True

    def browse_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path: self.path_browser.setText(path); self.path = path

    def search_file(self, text_browser: str, attribute: str) -> None:
        """
        Spawn file dialog
        Check if the attribute 'text_browser' exist, which is a Qtextbrowser
        and if 'attribute' exist which is a attribute of the class (variable),
        set the filename text value to the Qtextbrowser and 
        the filename text value to the attribute of the class
        """
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select a txt file", os.getcwd(), "TXT Files (*.txt)", options=options
        )
        if filename:
            if hasattr(self, text_browser) and hasattr(self, attribute):
                browser = getattr(self, text_browser)
                browser.clear(); browser.setText(filename)
                attr = getattr(self, attribute); attr = filename

    def disable_useURL(self, disable: bool) -> None:
        if disable:
            self.url_edit.setEnabled(False); self.url_edit.clear()
        else:
            self.url_edit.setEnabled(True)

    def disable_useFile(self, disable: bool) -> None:
        if disable:
            self.file_checkbox.setEnabled(False); self.file_checkbox.setChecked(False)
            self.file_browser.clear()
        else:
            self.file_checkbox.setEnabled(True)
    
    def disable_useSections(self, disable: bool) -> None:
        if disable:
            self.sections_checkbox.setEnabled(False); self.sections_checkbox.setChecked(False)
            self.sf_browser.clear()
            self.st_checkbox.setEnabled(False); self.st_checkbox.setChecked(False)
        else:
            self.sections_checkbox.setEnabled(True)

    def use_file(self, value) -> None:
        state = Qt.CheckState(value)
        if state == Qt.CheckState.Checked:
            self.search_file('file_browser', 'file')
            self.disable_useFile(False); self.disable_useSections(True); self.disable_useURL(True)
        
        elif state == Qt.CheckState.Unchecked:
            self.disable_useURL(False); self.disable_useFile(False); self.disable_useSections(False); self.file_browser.clear()

    def use_sections(self, value) -> None:
        state = Qt.CheckState(value)
        if state == Qt.CheckState.Checked:
            self.search_file('sf_browser', 'sections_file')
            self.disable_useSections(False); self.disable_useFile(True); self.disable_useURL(True)
            self.st_checkbox.setEnabled(True)
        
        elif state == Qt.CheckState.Unchecked:
            self.disable_useURL(False); self.disable_useFile(False); self.disable_useSections(False)
            self.st_checkbox.setEnabled(False); self.sf_browser.clear(); self.st_checkbox.setChecked(False)

    def use_default_section_title(self, value) -> None:
        state = Qt.CheckState(value)
        if state == Qt.CheckState.Checked: self.default_sections = True
        elif state == Qt.CheckState.Unchecked: self.default_sections = False

    def message_box(self, info: str, type_: str) -> None:
        if self.available_msg_box:
            self.available_msg_box = False
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning) if type_ == "warning" else msg.setIcon(QMessageBox.Information) 
            msg.setText(info)
            msg.setWindowTitle("Warning") if type_ == "warning" else msg.setWindowTitle("Finished")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            revtal = msg.exec_()
            self.available_msg_box = True 

    def run(self) -> None:
        self.url = self.url_edit.text() # URL Qline edit
        self.metadata = self.metadata_edit.text() # Metadata Qline edit
        self.sections_file = self.sf_browser.toPlainText() # Retrieve text from Qtextbrowser 
        self.file = self.file_browser.toPlainText()

        if not self.path: self.message_box("Select a Path", "warning")
        
        elif not self.url and not self.file and not self.sections_file: self.message_box("Use on the following:\nURL\nFile\nSections", "warning")
        
        elif not self.metadata: self.message_box("Write the Metadata", "warning")
        
        elif self.url and not self.file and not self.sections_file:
            self.run_button.setEnabled(False); self.update = True
       
            self.run_button.setEnabled(True); self.update = False
       
        elif self.file and not self.url and not self.sections_file:
            self.run_button.setEnabled(False); self.update = True 
       
            self.run_button.setEnabled(True); self.update = False

        elif self.sections_file and not self.url and not self.file: 
            self.run_button.setEnabled(False); self.update = True 

            self.run_button.setEnabled(True); self.update = False

        command: list[str] = ["docker", "run", "-it", "--rm", "--name", "yt2music"]
        parameters: list[str] = []
 
        if self.path: command.append("-v"); command.append(f"{self.path}:/app/data")
        if self.metadata: parameters.append("-m"); parameters.append(self.metadata)
        if self.file:
            command.append("-v"); command.append(f"{self.file}:/app/{os.path.basename(self.file)}")
            parameters.append("-f"); parameters.append(os.path.basename(self.file))
        if self.url: parameters.append("-u"); parameters.append(self.url)
        if self.sections_file:
            parameters.append("-s"); parameters.append("true")
            command.append("-v"); command.append(f"{self.sections_file}:/app/{os.path.basename(self.sections_file)}")
            parameters.append("-sf"); parameters.append(os.path.basename(self.sections_file))
        if self.default_sections: parameters.append("-st"); parameters.append("true")

        command.append(f"{self.image}:{self.version}")

        command.extend(parameters)
        self.command = copy.deepcopy(command)

        self.docker_cmd(self.command)

    def docker_cmd(self, command: list[str]) -> None:
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet("background-color: rgb(125, 125, 125); color: rgb(0, 0, 0)")
        self.docker = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        thread = threading.Thread(target=self.read_stdout); thread.start() 

    def read_stdout(self) -> None:
        while True:
            stdout = self.docker.stdout.readline()
            if stdout: self.status = re.findall(r'Downloading \d{1,2} of \d{1,2}', stdout)[0] if re.findall(r'Downloading \d{1,2} of \d{1,2}', stdout) else "Waiting"
            if re.findall(r'Finished', stdout): self.message_box("Download Finished", "info")
            if self.docker.poll() is not None: break 
        
        self.run_button.setEnabled(True)
        self.status = "Finished"
        self.run_button.setStyleSheet("background-color: rgb(85, 255, 127); color: rgb(0, 0, 0)")

    def status(self) -> None:
        text: str = ''
        if not self.command: self.message_box("No process running", "warning")
        else:
            for i in self.command: text+=f' {i}'
            self.message_box(f'COMMAND:\n\n{text}\n\nSTATUS:\n\n{self.status}', "info")

    def cancel_process(self) -> None:
        cmd = subprocess.Popen(["docker", "stop", "yt2music"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if not cmd.stderr.readline():
            self.message_box("Canceled", "warning")
        else: self.message_box("No process running", "warning")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    app.exec_() 

