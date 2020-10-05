import sys
import cv2
import numpy
from PyQt5 import QtWidgets,QtGui,uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

class VideoThread(QThread):
    new_frame_signal = pyqtSignal(numpy.ndarray)

    def run(self):
        
        # Capture from Webcam
        width = 320
        height = 240
        video_capture_device = cv2.VideoCapture(0)
        video_capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        video_capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        while True:
            if self.isInterruptionRequested():
                video_capture_device.release()
                return
            else:
                ret, frame = video_capture_device.read()
                if ret:
                    self.new_frame_signal.emit(frame)

def Update_Image(frame):
    height, width, channel = frame.shape
    bytesPerLine = 3 * width
    qImg = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
    qImg = qImg.rgbSwapped()
    UI.lblOutput.setPixmap(QtGui.QPixmap(qImg))

def Quit():
    thread.requestInterruption()
    thread.wait()
    App.quit()


App = QtWidgets.QApplication([])
UI=uic.loadUi("demo_webcam.ui")

UI.actionQuit.triggered.connect(Quit)

UI.show()

thread = VideoThread()
thread.new_frame_signal.connect(Update_Image)
thread.start()

sys.exit(App.exec_())