import sys
import numpy
import cv2
import time
import pyaudio
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui, uic, QtWidgets
from models import VideoThread, Camera, MicrophoneThread
from speech_timer import TimerThread
from threading import Thread
from speech_to_text import MyRecognizeCallback
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from threading import Thread
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from translate import Translator

try:
    from Queue import Queue, Full
except ImportError:
    from queue import Queue, Full


CAMERA_WIDTH = 420
CAMERA_HEIGHT = 300
CAMERA_ID = 0
SCREEN_RATIO = CAMERA_HEIGHT/CAMERA_WIDTH
DEFAULT_DURATION = 180
DEFAULT_THRESHOLD = 0

#calculate from frame.shape width multiply by 3
BYTES_PER_LINE = 1272

# initialize speech to text service
API_KEY = 'd_vI7npJhICly_5HOdyLYJYVlXU0QnCQOiSxjNil6qdl'
API_URL = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/eb505cb9-2feb-484c-ba93-7af0539d6dd7'
authenticator = IAMAuthenticator(API_KEY)
speech_to_text = SpeechToTextV1(authenticator=authenticator)

#initalize queue to store the recordings ##
CHUNK = 1024
#Note: It will discard if the websocket client can't consumme fast enough
#So, increase the max size as per your choice
BUF_MAX_SIZE = CHUNK * 10
#buffer to store audio
q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK)))

#create an instance of AudioSource
audio_source = AudioSource(q, True, True)

disfluencyCount = 0

#translator
translator = Translator(to_lang="spanish")


def update(frame):
    height, width, channel = frame.shape
    qImg = QtGui.QImage(frame.data, width, height, BYTES_PER_LINE, QtGui.QImage.Format_RGB888)
    qImg = qImg.rgbSwapped()
    coloredFrame = QtGui.QPixmap(qImg)

    scaleX = window.width() / width
    newWidth = width * scaleX
    newHeight = (SCREEN_RATIO) * newWidth
    scaledFrame = coloredFrame.scaled(newWidth, newHeight, Qt.KeepAspectRatio)
    window.resize(newWidth, newHeight)
    window.videoOutput.setPixmap(scaledFrame)

def stopTimer():
    timer_thread.pause()

def startTimer():
    duration = window.durationLineEdit.text()
    threshold = window.thresholdLineEdit.text()
    timer_thread.setThreshold(int(threshold))
    timer_thread.resume(int(duration))
    
def quitApp():
    print('quit app')
    videoThread.requestInterruption()
    videoThread.wait()
    app.quit()

def report():
    print('final report: ' + disfluencyCount)

#Variables for recording the speech
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

#define callback for pyaudio to store the recording in queue
def pyaudio_callback(in_data, frame_count, time_info, status):
    try:
        q.put(in_data)
    except Full:
        pass # discard
    return (None, pyaudio.paContinue)

audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    stream_callback=pyaudio_callback,
    start=False
)

print("Enter CTRL+C to end recording...")
stream.start_stream()

class Store:
    def __init__(self, window):
        self._window = window

    def getSpeech(self, data):
        self._window.captureTextLabel.setText(data)
        global disfluencyCount
        print(data)

        #translate to spanish
        translated_text = translator.translate(data)
        self._window.translatedTextLabel.setText(translated_text)
        if "%HESITATION" in data or "mmhm" in data:
            disfluencyCount = disfluencyCount + 1
            print(disfluencyCount)
            self._window.disfluencyCountLabel.setText(str(disfluencyCount))


#app
app = QtWidgets.QApplication([])
window = uic.loadUi("main.ui")
window.setWindowTitle("Final Project")
window.show()

def recognize_using_websocket(*args):
    mycallback = MyRecognizeCallback()
    store = Store(window)
    mycallback.subscribe(store.getSpeech)
    speech_to_text.recognize_using_websocket(audio=audio_source,
                                            content_type='audio/l16; rate=44100',
                                            recognize_callback=mycallback,
                                            interim_results=True)

#timer
timer_thread = TimerThread(window)
timer_thread.start()
timer_thread.pause()

#webcam
camera = Camera(CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT)

#video thread
videoThread = VideoThread(camera, window)
videoThread.signal.connect(update)
videoThread.start()

#microphone thread
recognize_thread = Thread(target=recognize_using_websocket, args=())
recognize_thread.start()
window.captureTextLabel.setText("Captured text...")
window.translatedTextLabel.setText("Translated text...")
window.disfluencyCountLabel.setText("0")

#timer thread
window.recordButton.clicked.connect(startTimer)
window.stopButton.clicked.connect(stopTimer)

#event handler
window.closeButton.clicked.connect(quitApp)

#report
window.reportButton.clicked.connect(report)

#end
sys.exit(app.exec_())