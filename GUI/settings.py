import os
from PySide2 import QtWidgets, QtCore
from typing import Tuple
import speech_recognition as sr


class Settings(QtWidgets.QDialog):

    """ settings related to microphone selection, clear chat, create transcript, transcript path"""

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)

        self.setModal(True)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.index = 0
        self.clear_chat = False
        self.create_transcript = False
        self.transcriptPath = ""
        self.learning_mode = False

        self.err_lbl = QtWidgets.QLabel()

        self.microphone_lst = QtWidgets.QComboBox()
        microphone_lst = sr.Microphone.list_microphone_names()

        self.microphone_lst.addItems(microphone_lst)
        self.microphone_lst.currentIndexChanged.connect(self.getIndex)

        self.ok_btn = QtWidgets.QPushButton(text="ok", clicked=self.checkPath)
        self.clear_btn = QtWidgets.QCheckBox(text="Clear Chat")
        self.clear_btn.stateChanged.connect(self.clearChat)

        self.create_btn = QtWidgets.QCheckBox(text="Create chat transcript")
        self.create_btn.stateChanged.connect(self.createTranscript)

        self.learning_mode_btn = QtWidgets.QCheckBox(text="Learning mode")
        self.learning_mode_btn.stateChanged.connect(self.setLearningMode)

        hbox = QtWidgets.QHBoxLayout()
        self.transcriptPath_edit = QtWidgets.QLineEdit()
        self.transcriptPath_edit.setPlaceholderText("Enter transcript path")
        self.folder_btn = QtWidgets.QPushButton(text="Select folder", clicked=self.selectPath)

        hbox.addWidget(self.transcriptPath_edit)
        hbox.addWidget(self.folder_btn)

        self.layout().addWidget(self.err_lbl)
        self.layout().addWidget(self.microphone_lst)
        self.layout().addWidget(self.clear_btn)
        self.layout().addWidget(self.create_btn)
        self.layout().addWidget(self.learning_mode_btn)

        self.layout().addLayout(hbox)
        self.layout().addWidget(self.ok_btn)
        self.layout().addStretch()

    def getIndex(self, index):
        self.index = index

    def clearChat(self, clear: bool):
        self.clear_chat = bool(clear)

    def createTranscript(self, create: bool):
        self.create_transcript = bool(create)

    def selectPath(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "select directory")

        if folder:
            self.setFolderPath(folder)
            self.err_lbl.setText("")

    def setFolderPath(self, path):
        self.transcriptPath = path
        self.transcriptPath_edit.setText(path)

    def getSettings(self) -> Tuple[int, bool, bool, Tuple[bool, str]]:
        """ returns a tuple of (microphone_index, clear_chat, learning_mode, (create_transcript, transcriptPath))"""
        print(self.index, self.clear_chat, self.create_transcript)
        return self.index, self.clear_chat, self.learning_mode, (self.create_transcript, self.transcriptPath)

    def checkPath(self):

        if os.path.exists(self.transcriptPath):
            self.accept()

        else:
            self.err_lbl.setText("Error in path")

    def setLearningMode(self, checked: bool):
        self.learning_mode = bool(checked)
