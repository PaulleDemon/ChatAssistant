import datetime
import os.path
import sys
import textwrap
import speech_recognition as sr

from PySide2 import QtWidgets, QtCore, QtGui
from typing import Tuple
from settings import Settings
from ChatBotAssistant import ChatAssistant


class MessageWidget(QtWidgets.QWidget):
    """ Creates Message area, settings"""

    def __init__(self, *args, **kwargs):
        super(MessageWidget, self).__init__(*args, **kwargs)

        self.microphone_index = 0
        self.transcript_path = ""
        self.listening = False
        self.learning_mode = False

        self.chat_bot = ChatAssistant()
        self.chat_bot.botResponse.connect(self.receiveMessage)

        grid_layout = QtWidgets.QGridLayout()

        self.setLayout(grid_layout)

        widget = QtWidgets.QWidget()
        self.v_box = QtWidgets.QVBoxLayout(widget)

        self.scroll_widget = QtWidgets.QScrollArea()
        self.scroll_widget.setWidget(widget)
        self.scroll_widget.setWidgetResizable(True)
        scrollbar = self.scroll_widget.verticalScrollBar()
        scrollbar.rangeChanged.connect(lambda: scrollbar.setValue(scrollbar.maximum()))

        self.settings_btn = QtWidgets.QPushButton(text="Settings", clicked=self.openSettings)

        self.text_box = QtWidgets.QLineEdit()
        self.text_box.setLayout(QtWidgets.QVBoxLayout())
        self.text_box.textChanged.connect(self.updateWordCount)
        self.text_box.returnPressed.connect(self.sendMessage)

        self.char_count = QtWidgets.QLabel()
        self.text_box.layout().addWidget(self.char_count, alignment= QtCore.Qt.AlignRight)

        self.speech_btn = QtWidgets.QPushButton(text="Speech", clicked=self.audioToText)
        self.send_btn = QtWidgets.QPushButton(text="send", clicked=self.sendMessage)

        grid_layout.addWidget(self.settings_btn, 0, 0, 1, 1)
        grid_layout.addWidget(self.scroll_widget, 1, 0, 1, 4)
        grid_layout.addWidget(self.text_box, 2, 0, 2, 1)
        grid_layout.addWidget(self.speech_btn, 3, 2, 1, 1)
        grid_layout.addWidget(self.send_btn, 3, 3, 1, 1)

    def sendMessage(self, trainingmsg: str = ""):
        text = ""
        if trainingmsg:
            text = trainingmsg

        elif self.text_box.text():
            text = self.text_box.text()
            time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            msg = MessageLabel("You", time, text)

            self.v_box.addWidget(msg, alignment=QtCore.Qt.AlignRight)
            self.text_box.clear()

        if text:
            self.chat_bot.respond(text, bool(trainingmsg))


    def receiveMessage(self, msg: str):

        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        msg_lbl = MessageLabel("Bot", time, msg, bot_training=self.learning_mode)
        msg_lbl.correctResponse.connect(self.sendMessage)

        self.v_box.addWidget(msg_lbl, alignment=QtCore.Qt.AlignLeft)

    def updateWordCount(self):
        self.char_count.setText(f"{len(self.text_box.text())}")

    def openSettings(self):
        settings = Settings(parent=self)
        settings.setFolderPath(self.transcript_path)

        if settings.exec_():
            print(settings.getSettings())

            index, clear_chat, learning_mode, (create_transcript, path) = settings.getSettings()

            self.transcript_path = path

            if create_transcript:
                self.createTranscript(path)

            if clear_chat:
                self.clearChar()

            if index != self.microphone_index:
                self.microphone_index = index

            self.learning_mode = learning_mode

    def createTranscript(self, path):

        with open(os.path.join(path, "Transcript.txt"), 'w') as file:
            x = 0
            while x < self.v_box.count():
                child = self.v_box.itemAt(x)
                widget = child.widget()

                if widget:
                    text = "name: {0} \ntime: {1} \nmessage: {2}\n\n".format(*widget.getInfo())
                    file.write(text)

                x += 1

    def clearChar(self):
        while self.v_box.count():
            child = self.v_box.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def audioToText(self):

        self.speech_btn.setText("Listening...")
        self.speech_btn.setDisabled(True)

        self.speech = SpeechRecognition(self.microphone_index)
        self.speech.messageAdded.connect(self.setSpeechText)
        self.speech.start()
        self.listening = True
        self.speech.finished.connect(self.enableSpeechBtn)

    def enableSpeechBtn(self):
        self.speech_btn.setText("Speech")
        self.speech_btn.setDisabled(False)
        self.listening = False

    def setSpeechText(self, text):
        self.text_box.moveCursor(QtGui.QTextCursor.End)
        self.text_box.insertPlainText(f" {text}")
        self.text_box.moveCursor(QtGui.QTextCursor.End)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:

        # self.chat_bot.closeChat()

        if self.listening:
            # self.speech.quit()
            self.speech.terminate()
            self.speech.wait()

        super(MessageWidget, self).closeEvent(event)


class SpeechRecognition(QtCore.QThread):
    messageAdded = QtCore.Signal(str)

    def __init__(self, device_id=0, sample_rate=48000, chunk_size=2048, *args, **kwargs):
        super(SpeechRecognition, self).__init__(*args, **kwargs)

        self.device_id = device_id
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # self.start()

    def run(self) -> None:

        r = sr.Recognizer()
        # while not self.isInterruptionRequested():
        with sr.Microphone(device_index=self.device_id, sample_rate=self.sample_rate,
                           chunk_size=self.chunk_size) as source:
            # wait for a second to let the recognizer adjust the
            # energy threshold based on the surrounding noise level
            r.adjust_for_ambient_noise(source)
            print("Say Something")

            # listens for the user's input
            audio = r.listen(source)

            try:
                text = r.recognize_google(audio)
                self.messageAdded.emit(text)

            # error occurs when google could not understand what was said

            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")

            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service;{0}".format(e))


class MessageLabel(QtWidgets.QFrame):
    """ formats messages in a way that ame is displayed at top, message at center and time at bottom.
        set bot_training=True to get yes/no option. This can be useful when training a bot.
    """
    iscorrectResponse = QtCore.Signal(bool)  # yes or no button
    correctResponse = QtCore.Signal(str)  # emits correct response

    def __init__(self, name: str, time: str, message: str, wrap_len: int = 70, bot_training: bool = False,
                 *args, **kwargs):
        super(MessageLabel, self).__init__(*args, **kwargs)

        self.setLayout(QtWidgets.QVBoxLayout())

        self.message_label = QtWidgets.QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.wrap_len = wrap_len

        self.name, self.time, self.message = "", "", ""

        if name and time and message:
            self.setText(name, time, message)

        self.layout().addWidget(self.message_label)

        self.correct_response = ""

        if bot_training:
            self.question_frame = QtWidgets.QFrame()
            question_lbl = QtWidgets.QLabel(text="Is this a correct response?")

            self.yes_btn = QtWidgets.QPushButton("Yes", clicked=self.responseCorrectness)
            self.no_btn = QtWidgets.QPushButton("No", clicked=self.responseCorrectness)

            self.correct_responseEdit = QtWidgets.QLineEdit()
            self.correct_responseEdit.setPlaceholderText("Enter what should be a correct response")
            self.correct_responseEdit.returnPressed.connect(self.acceptInput)
            self.correct_responseEdit.hide()

            question_layout = QtWidgets.QFormLayout(self.question_frame)
            question_layout.addRow(question_lbl)
            question_layout.addRow(self.yes_btn, self.no_btn)
            question_layout.addRow(self.correct_responseEdit)

            self.layout().addWidget(self.question_frame)

    def responseCorrectness(self):

        widget = self.sender()
        if widget == self.yes_btn:
            self.iscorrectResponse.emit(True)
            self.question_frame.deleteLater()

        else:
            self.correct_responseEdit.show()
            self.iscorrectResponse.emit(False)

    def acceptInput(self):
        self.question_frame.deleteLater()
        self.correct_response = self.correct_responseEdit.text()
        self.correctResponse.emit(self.correct_response)

    def setText(self, name: str, time: str, message: str) -> None:
        self.name, self.time, self.message = name, time, message

        text = self.format(name, time, message)
        self.message_label.setText(text)

    def format(self, name: str, time: str, msg: str) -> str:
        wrapped_text = textwrap.fill(text=msg, width=self.wrap_len).replace("\n", "<br>").strip()

        formatted_str = f"<p style='text-align:right;'>{name}</p><br>{wrapped_text}<br>" \
                        f"<p style='text-align:right;'>{time}</p>"

        return formatted_str

    def getInfo(self) -> Tuple[str, str, str]:
        """ returns name, time, message"""
        return self.name, self.time, self.message


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    win = MessageWidget()
    win.show()

    sys.exit(app.exec_())
