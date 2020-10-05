import sys
import numpy
import cv2
import time
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui, uic, QtWidgets
from models import VideoThread, Camera

def update(frame):
    height, width, channel = frame.shape
    bytesPerLine = 3 * width
    qImg = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
    qImg = qImg.rgbSwapped()
    coloredFrame = QtGui.QPixmap(qImg)

    ratio = cameraHeight/cameraWidth
    scaleX = window.width() / width
    newWidth = width * scaleX
    newHeight = (cameraHeight/cameraWidth) * newWidth
    scaledFrame = coloredFrame.scaled(newWidth, newHeight, Qt.KeepAspectRatio)
    window.videoOutput.setPixmap(scaledFrame)
    window.videoOutput.resize(newWidth, newHeight)
    window.videoOutput.setMinimumSize(cameraWidth,cameraHeight)



def quitApp():
    print('quit app')
    videoThread.requestInterruption()
    videoThread.wait()
    app.quit()

#app
app = QtWidgets.QApplication([])
window = uic.loadUi("main.ui")
window.layout.setContentsMargins(0,0,0,0)
window.setLayout(window.layout)
window.show()

#webcam
cameraNumber = 0
cameraWidth = 420
cameraHeight = 300
camera = Camera(cameraNumber, cameraWidth, cameraHeight)

#thread
videoThread = VideoThread(camera, window)
videoThread.signal.connect(update)
videoThread.start()

#event handler
window.mirrorButton.clicked.connect(videoThread.mirror)
window.closeButton.clicked.connect(quitApp)

#end
sys.exit(app.exec_())