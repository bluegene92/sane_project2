from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# define callback for the speech to text service
class MyRecognizeCallback(RecognizeCallback):

    def __init__(self):
        RecognizeCallback.__init__(self)

    def subscribe(self, callback):
        self.callback = callback

    def on_transcription(self, transcript):
        print(transcript)

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        self.callback(hypothesis)

    def on_data(self, data):
        # print(data)
        pass

    def on_close(self):
        print("Connection closed")
        f.close()