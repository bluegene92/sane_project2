import speech_recognition as sr
import os
import re
from subprocess import Popen
from pocketsphinx import LiveSpeech, get_model_path

import sys
import numpy
import cv2
import time
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui, uic, QtWidgets
from models import VideoThread, Camera, MicrophoneThread

CAMERA_WIDTH = 420
CAMERA_HEIGHT = 300
CAMERA_ID = 0
SCREEN_RATIO = CAMERA_HEIGHT/CAMERA_WIDTH

#calculate from frame.shape width multiply by 3
BYTES_PER_LINE = 1272

#speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

model_path = get_model_path()

#speech dictionary and language model paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DIC_PATH = DIR_PATH + "/dic/2714.dic"
LM_PATH = DIR_PATH + "/lm/2714.lm"
MODEL_PATH = DIR_PATH + "/model/en-us"
TEMP_PATH = DIR_PATH + "/temp/output.log"
launchSphinx = "pocketsphinx_continuous " + "-inmic yes " + "-dict " + DIC_PATH + " -lm " + LM_PATH + " -hmm " + MODEL_PATH + " -logfn " + TEMP_PATH + " -backtrace yes"


# proc = Popen("gnome-terminal -e '" + launchSphinx + "'", shell = True)
# time.sleep(5)
# idx = 0
# flag = 0

# while True:
#     with open(TEMP_PATH) as f:
#         for i, line in enumerate(f):
#             if line.startswith("INFO: pocketsphinx.c") and (i>idx):
#                 cmd = check(line, window)
#                 print(cmd)
#         idx = i
#         if flag == 1:
#             break
#     if flag == 1:
#         break
# proc.terminate()
# proc.kill()

fillerCount = 0

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

def updateFillerWordsCount(c):
    window.fillerWordsCountLabel.setText(str(c))

def record_audio():
    with microphone as source:
        audio = recognizer.listen(source)
        print('Sphinx thinks you said ' + recognizer.recognize_sphinx(audio))

def countdown(t):
    while (t):
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(imer, end='\r')
        t -= 1

def quitApp():
    print('quit app')
    videoThread.requestInterruption()
    videoThread.wait()
    app.quit()

#app
app = QtWidgets.QApplication([])
window = uic.loadUi("main.ui")
window.setWindowTitle("Final Project")
window.show()

#webcam
camera = Camera(CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT)

#video thread
videoThread = VideoThread(camera, window)
videoThread.signal.connect(update)
videoThread.start()

#microphone thread
microphoneThread = MicrophoneThread(window)
microphoneThread.signal.connect(updateFillerWordsCount)
microphoneThread.start()

#record speech
print('say something')
# record_audio()
# time.sleep(1)
# print('Start talking')
# while 1:
#     voiceData = record_audio()
#     print(voiceData)
# voiceData = record_audio()
# print(voiceData)

#event handler
window.closeButton.clicked.connect(quitApp)

#end
sys.exit(app.exec_())