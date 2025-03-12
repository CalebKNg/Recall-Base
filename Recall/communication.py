import cv2
import numpy as np
import requests
from multiprocessing import Process, Queue
import base64
import config
from collections import deque

class Object:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.x = 0
        self.y = 0
        self.locHistory = deque()
        self.isMoving = True
        

class RecallApp:
    def __init__(self):
        # prob need an auth token as well as a dictionary of the objects that are currently being tracked
        self.trackedObjects = []
        self.historyLength = 10
        # Get Token
        self.bearerToken = self.obtainBearer()

        # Get Initial List
        self.obtainObjects()
        # print("Initial list")
        # print(self.trackedObjects)
        # Start process
        self.process = Process(target=self.run)
        self.process.start()

    def obtainBearer(self):
        url = "https://fydp-backend-production.up.railway.app/api/auth/login/" 
        headers = {"Content-Type": "application/json"}
        data = config.data
        response = requests.post(url, json=data, headers=headers)
        # print(response.status_code)

        if (response.status_code == 200):
            # print(response.json()["access"])
            return response.json()["access"]

    def obtainObjects(self):
        # Ask for a list of objects
        url = "https://fydp-backend-production.up.railway.app/ObjectTracking/" 
        headers = {"Content-Type": "application/json", "Authorization":"Bearer " + self.bearerToken}
        # print("obtain")
        # print(headers)
        response = requests.get(url, headers=headers)
        # print(response.status_code)
        if(response.status_code == 200):
            for item in response.json():
                id = item["id"]
                name = item["name"]
                ob = Object(id, name)
                ob.locHistory.append((0,0))
                self.trackedObjects.append(ob)
            # self.trackedObjects = response.json()

    def updateLocations(self, id, x, y):
        for item in self.trackedObjects:
            if item.id == id:

                # Grab average of the locHistory 
                xsum = 0
                ysum = 0
                for location in item.locHistory:
                    xsum += location[0]
                    ysum += location[1]
                xavg = xsum/len(item.locHistory)
                yavg = ysum/len(item.locHistory)

                # euclidean distance
                dist = np.sqrt((x - xavg)**2 + (y - yavg)**2)
                print(dist)
                
                # # manhattan 
                # dist = np.abs(item.x-x) + np.abs(item.y-y)
                threshold = 2
                if item.isMoving:
                    if dist < threshold:
                        # stopped moving
                        print("Phone moved " + str(dist) + "pixels")
                        item.isMoving = False

                else:   # If not moving
                    if dist >= threshold:
                        item.isMoving = True

                # Update distance
                item.x = x
                item.y = y

                # Update queue
                if(len(item.locHistory) > self.historyLength):
                    item.locHistory.popleft()
                    item.locHistory.append((x, y))
                else:
                    item.locHistory.append((x, y))



    def sendUpdate(self, id, name, image, description):
        url = "fydp-backend-production.up.railway.app/ObjectTracking/" + id
        headers = {"Content-Type": "application/json", "Authorization":"Bearer " +self.bearerToken}

        imageBase64 =base64.b64encode()

        data = {
            "name": name,
            "location_image": image,
            "location_description": description
        }

        response = requests.post(url, json=data, headers=headers)
        print(response.status_code)

    def run(self):
        # Run this loop in another process
        while True:
            # Main Program Loop
            pass
    
    def terminate(self):
        self.process.terminate()
        self.process.join()


