import cv2
import numpy as np
import requests
from multiprocessing import Process, Queue
import config

class Object:
    def __init__(self, id):
        self.id = id
        self.x = 0
        self.y = 0

class RecallApp:
    def __init__(self):
        # prob need an auth token as well as a dictionary of the objects that are currently being tracked
        self.trackedObjects = []

        # Get Token
        self.bearerToken = self.obtainBearer()

        # Get Initial List
        self.obtainObjects()

        # Start process
        self.process = Process(target=self.run)
        self.process.start()

    def obtainBearer(self):
        url = "https://fydp-backend-production.up.railway.app/api/auth/login/" 
        headers = {"Content-Type": "application/json"}
        data = config.data
        response = requests.post(url, json=data, headers=headers)

        if (response.status_code == 200):
            return response.json()["access"]

    def obtainObjects(self):
        # Ask for a list of objects
        url = "https://fydp-backend-production.up.railway.app/ObjectTracking/" 
        headers = {"Content-Type": "application/json", "Authorization":self.bearerToken}

        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            self.trackedObjects = response.json()

    def updateLocations(self, ID):
        pass

    def run(self):
        # Run this loop in another process
        while True:
            # Main Program Loop
            pass
    
    def terminate(self):
        self.process.terminate()
        self.process.join()


