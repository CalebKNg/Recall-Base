import cv2
import numpy as np
import requests
from multiprocessing import Process, Queue

class RecallApp:
    def __init__(self):
        # prob need an auth token as well as a dictionary of the objects that are currently being tracked
        

        # Start process
        self.process = Process(target=self.run)
        self.process.start()


    def run(self):
        # Run this loop in another process
        while True:
            # Main Program Loop
            pass
    
    def terminate(self):
        self.process.terminate()
        self.process.join()


