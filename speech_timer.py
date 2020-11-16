import asyncio
import time
import threading

DEFAULT_DURATION = 0

class TimerThread(threading.Thread):
    def __init__(self, window, *args, **kwargs):
        super(TimerThread, self).__init__(*args, **kwargs)
        self._flag = threading.Event() #flag use to pause thread
        self._flag.set() 
        self._running = threading.Event() #used to stop the thread identification
        self._running.set()
        self._countdown = DEFAULT_DURATION
        self._window = window
        self._threshold = 0

    def setThreshold(self, threshold):
        self._threshold = threshold


    def run(self):
        while (self._running.isSet()):
            self._flag.wait()
            mins, secs = divmod(self._countdown, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            
            #if countdown less than thresold change label color to red
            if (self._countdown <= self._threshold):
                self._window.countdownLabel.setStyleSheet("color: red")
            elif self._countdown > self._threshold:
                self._window.countdownLabel.setStyleSheet("color: black")

            if (self._countdown <= 0):
                self.pause()
                self._window.countdownLabel.setStyleSheet("color: black")


            self._window.countdownLabel.setText(timeformat)

            time.sleep(1)
            self._countdown -= 1

    def pause(self):
        self._flag.clear()

    def resume(self, time):
        self._countdown = time
        self._flag.set()

    def stop(self):
        self._flag.set()
        self._running.clear()



        

