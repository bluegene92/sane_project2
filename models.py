import cv2
import numpy
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from tensorflow.keras.models import model_from_json, load_model
from tensorflow.keras.preprocessing import image


#files
faceDetectionModelFile = "haarcascade_frontalface_default.xml"
emotionPredictionModelFile = "fer2013_mini_XCEPTION.102-0.66.hdf5"

#models
face_model = cv2.CascadeClassifier(faceDetectionModelFile)
model = load_model(emotionPredictionModelFile, compile=False)

#variables
HORIZONTAL = 1
CROP_SIZE = 64
BLUE = (255, 0, 0)
RED = (0, 0, 255)
BORDER_WIDTH = 2
FRAMES_MAX = 120
emotionLabels = {
    0: 'angry',
    1: 'digust',
    2: 'fear',
    3: 'happy',
    4: 'sad',
    5: 'surprise',
    6: 'neutral'
}

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
        self.frame_nums = FRAMES_MAX

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

                #flip the frame horizontally
                if (self.isMirror):
                    frame = cv2.flip(frame, HORIZONTAL)

                #turn image to gray scale
                grayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_model.detectMultiScale(grayImage, 1.1, 4)
                for (x, y, w, h) in faces:

                    #draw rectangle around face
                    cv2.rectangle(frame, (x,y), (x+w, y+h), BLUE, thickness=BORDER_WIDTH)

                    #crop image to predict emotion
                    roi_gray = grayImage[y:y+h, x:x+h]
                    roi_gray = cv2.resize(roi_gray, (CROP_SIZE,CROP_SIZE))
                    imgPixels = image.img_to_array(roi_gray)
                    imgPixels = numpy.expand_dims(imgPixels, axis = 0)
                    imgPixels /= 255

                    #mood prediction
                    predictions = model.predict(imgPixels)
                    moodIndex = numpy.argmax(predictions)
                    probability = numpy.max(predictions)
                    probability = str(round(probability, 2))
                    moodText = "{} ({})".format(emotionLabels[moodIndex], probability)

                    #write emotion prediction on screen
                    cv2.putText(frame, moodText, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED)

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
                    if ret:
                        self.signal.emit(frame)

    def mirror(self):
        self.isMirror = False if self.isMirror else True