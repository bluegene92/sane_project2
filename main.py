import sys
import numpy
import cv2
import time
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui, uic, QtWidgets
from models import VideoThread, Camera

CAMERA_WIDTH = 420
CAMERA_HEIGHT = 300
CAMERA_ID = 0
SCREEN_RATIO = CAMERA_HEIGHT/CAMERA_WIDTH

#calculate from frame.shape width multiply by 3
BYTES_PER_LINE = 1272

def update(frame):
    height, width, channel = frame.shape
    qImg = QtGui.QImage(frame.data, width, height, BYTES_PER_LINE, QtGui.QImage.Format_RGB888)
    qImg = qImg.rgbSwapped()
    coloredFrame = QtGui.QPixmap(qImg)

    scaleX = window.width() / width
    newWidth = width * scaleX
    newHeight = (SCREEN_RATIO) * newWidth
    scaledFrame = coloredFrame.scaled(newWidth, newHeight, Qt.KeepAspectRatio)
    window.videoOutput.setFixedHeight(newHeight)
    window.videoOutput.setPixmap(scaledFrame)

def quitApp():
    print('quit app')
    videoThread.requestInterruption()
    videoThread.wait()
    app.quit()

#app
app = QtWidgets.QApplication([])
window = uic.loadUi("main.ui")
window.layout.setContentsMargins(0,0,0,0)
window.setWindowTitle("Project 2")
window.setLayout(window.layout)
window.show()

#webcam
camera = Camera(CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT)

#thread
videoThread = VideoThread(camera, window)
videoThread.signal.connect(update)
videoThread.start()

#event handler
window.mirrorButton.clicked.connect(videoThread.mirror)
window.closeButton.clicked.connect(quitApp)

#end
sys.exit(app.exec_())