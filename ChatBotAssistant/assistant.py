from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.conversation import Statement
from PySide2 import QtCore


class ChatAssistant(QtCore.QObject):

    botResponse = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(ChatAssistant, self).__init__(*args, *kwargs)

        self.chatbot = ChatBot("Bot", logic_adapters=[{
                'import_path': 'chatterbot.logic.BestMatch',
                'default_response': 'I am sorry, but I do not understand.'
            },
            {
                'import_path': 'chatterbot.logic.MathematicalEvaluation',
                'default_response': 'I am sorry, but I do not understand.'
            },

            {
                'import_path': 'chatterbot.logic.TimeLogicAdapter',
                'default_response': 'I am sorry, but I do not understand.'
            }
        ], storage_adapter="chatterbot.storage.SQLStorageAdapter")

        trainer = ChatterBotCorpusTrainer(self.chatbot)

        trainer.train("chatterbot.corpus.english")
        self.thread_alive = False

    def respond(self, message: str, learn: bool = False):

        self.closeChat()

        message = Statement(message)

        self.thread = _ChatThread(self.chatbot, message, learn)
        self.thread.start()
        self.thread.started.connect(self._setThreadStarted)
        self.thread.botResponse.connect(self.botResponse.emit)
        self.thread.finished.connect(self._setThreadFinished)

    def _setThreadStarted(self):
        self.thread_alive = True

    def _setThreadFinished(self):
        self.thread_alive = False

    def closeChat(self):

        if self.thread_alive:
            self.thread.terminate()
            self.thread.wait()


class _ChatThread(QtCore.QThread):

    botResponse = QtCore.Signal(str)

    def __init__(self, bot_instance: ChatBot, message: str, learn_response: bool = False, *args, **kwargs):
        super(_ChatThread, self).__init__(*args, **kwargs)
        self.chat_bot = bot_instance
        self.msg = message
        self.learn = learn_response

    def run(self) -> None:
        if not self.learn:
            response = self.chat_bot.get_response(self.msg)
            self.botResponse.emit(f"{response}")

        else:
            self.chat_bot.learn_response(self.msg)