import cv2
import numpy
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

HORIZONTAL = 1

class Camera():
    def __init__(self, cameraNumber, width, height):
        self.cameraNumber = cameraNumber
        self.width = width
        self.height = height
        self.isMirror = False

        #webcam
        self._video = cv2.VideoCapture(cameraNumber)
        self._video.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._video.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    @property
    def frame(self):
        return self._video.read()


class VideoThread(QThread):
    signal = pyqtSignal(numpy.ndarray)

    def __init__(self, camera, window):
        super().__init__()
        self.camera = camera
        self.isMirror = False
        self.window = window
        self.frame_nums = 120

    def run(self):
        print('thread running')
        frameCount = 0
        start = time.time()

        while True:
            if self.isInterruptionRequested():
                self.camera._video.release()
                return
            else:
                ret, frame = self.camera.frame

                #when frame count get to 120 calculate the fps and reset time
                frameCount = frameCount + 1
                if (frameCount >= self.frame_nums):
                    end = time.time()
                    seconds = end - start
                    fps = self.frame_nums / seconds
                    fps = int(round(fps))
                    self.window.fps.setText("FPS: {}".format(fps))
                    print("fps: {}".format(fps))
                    frameCount = 0 #reset frame count
                    start = time.time() #reset time

                #flip the frame horizontally
                if (self.isMirror):
                    frame = cv2.flip(frame, HORIZONTAL)
                if ret:
                    self.signal.emit(frame)

    def mirror(self):
        self.isMirror = False if self.isMirror else True

