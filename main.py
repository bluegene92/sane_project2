import sys
import numpy
import cv2
import time
import pyaudio
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui, uic, QtWidgets
from models import VideoThread, Camera
from speech_timer import TimerThread
from threading import Thread
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from translate import Translator
from datetime import datetime

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

#translator
translator = Translator(to_lang="spanish")

#report file
REPORT_FILENAME = "report.txt"

#global
disfluencyCount = 0
captureText = ''
translatedText = ''
realtimeText = ''
grade = 100
isStarted = False
mood = ''

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
    global captureText
    window.captureTextLabel.setText(captureText)

    global translatedText
    window.translatedTextLabel.setText(translatedText)

    global disfluencyCount
    window.disfluencyCountLabel.setText(str(disfluencyCount))

    global realtimeText
    window.realtimeTextLabel.setText(realtimeText)


mc = 0
def getMood(m):
    global mood
    global mc
    #grab mood every 10 frame
    mc = mc + 1
    if (mc >= 10):
        mood = m
        mc = 0

def stopTimer():
    global isStarted
    isStarted = False
    timer_thread.pause()

def startTimer():
    global disfluencyCount
    global isStarted
    disfluencyCount = 0
    isStarted = True
    duration = window.durationLineEdit.text()
    threshold = window.thresholdLineEdit.text()
    timer_thread.setThreshold(int(threshold))
    timer_thread.resume(int(duration))

    with open(REPORT_FILENAME, "a") as myfile:
        myfile.write("********************************\n")
        myfile.write("********* TRANSCRIPT ***********\n")
        myfile.write("********************************\n\n")
        myfile.close()
    
def quitApp():
    print('quit app')
    videoThread.requestInterruption()
    videoThread.wait()
    app.quit()

def clearReport():
    raw = open(REPORT_FILENAME, "r+")
    contents = raw.read().split("\n")
    raw.seek(0)
    raw.truncate()
    raw.close()

def report():
    stopTimer()
    global disfluencyCount
    duration = window.durationLineEdit.text()
    threshold = window.thresholdLineEdit.text()

    global grade
    gradeLetter = ''
    if (grade >= 90 and grade <= 100):
        gradeLetter = 'A'
    elif (grade >= 80 and grade <= 89):
        gradeLetter = 'B'
    elif (grade >= 70 and grade <= 79):
        gradeLetter = 'C'
    elif (grade >= 60 and grade <=69):
        gradeLetter = 'D'
    else:
        gradeLetter = 'F'
    
    global isStarted
    if  not isStarted:
        with open(REPORT_FILENAME, "a") as myfile:
            myfile.write("\n********************************\n")
            myfile.write("********* Report ***************\n")
            myfile.write("********************************\n\n")
            myfile.write("Time: " + duration + " seconds \n")
            myfile.write("Threshold: " + threshold + " seconds \n")
            myfile.write("Disfluency Count: " + str(disfluencyCount) + "\n")
            myfile.write("Grade score: " + str(grade) + "\n")
            myfile.write("Grade: " + gradeLetter + "\n")

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


# define callback for the speech to text service
class MyRecognizeCallback(RecognizeCallback):

    def __init__(self):
        RecognizeCallback.__init__(self)

    def on_transcription(self, transcript):
        global captureText
        global translatedText
        global disfluencyCount
        global grade

        text = transcript[0]['transcript']
        captureText = text
        translatedText = translator.translate(text)

        #detect disfluency
        if "%HESITATION" in text or "mmhm" in text:
            disfluencyCount = disfluencyCount + 1

            if (grade >= 0):
                grade = grade - 2


        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        global isStarted
        global mood

        #write transcript to report file
        if (isStarted):
            with open(REPORT_FILENAME, "a") as myfile:
                myfile.write("English["+ current_time +" Mood("+ mood +")]: " + text + "\n")
                myfile.write("Spanish["+ current_time +" Mood("+ mood +")]: " + translatedText + "\n")

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        global realtimeText
        realtimeText = hypothesis
        
    def on_data(self, data):
        pass

    def on_close(self):
        print("Connection closed")

    def setWindow(self, window):
        self._window = window

class SpeechThread(QThread):
    def __init__(self, window):
        super().__init__()
        self._window = window

    def recognize_using_websocket(self, *args):
        global captureText
        mycallback = MyRecognizeCallback()
        mycallback.setWindow(window)
        speech_to_text.recognize_using_websocket(audio=audio_source,
                                                content_type='audio/l16; rate=44100',
                                                recognize_callback=mycallback,
                                                interim_results=True)

    def run(self):
        self.recognize_using_websocket([])

#app
app = QtWidgets.QApplication([])
window = uic.loadUi("main.ui")
window.setWindowTitle("Final Project")
window.show()

#timer
timer_thread = TimerThread(window)
timer_thread.start()
timer_thread.pause()

#webcam
camera = Camera(CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT)

#video thread
videoThread = VideoThread(camera, window)
videoThread.signal.connect(update)
videoThread.signalMood.connect(getMood)
videoThread.start()

#microphone thread
recognize_thread = SpeechThread(window)
recognize_thread.start()
window.durationLineEdit.setText(str(DEFAULT_DURATION))
window.thresholdLineEdit.setText(str(DEFAULT_THRESHOLD))
window.captureTextLabel.setText("Captured text...")
window.translatedTextLabel.setText("Translated text...")
window.disfluencyCountLabel.setText("0")

clearReport()

#timer thread
window.recordButton.clicked.connect(startTimer)
window.stopButton.clicked.connect(stopTimer)

#event handler
window.closeButton.clicked.connect(quitApp)

#report
window.reportButton.clicked.connect(report)

#end
sys.exit(app.exec_())