import cv2
import numpy as np
import requests
from multiprocessing import Process, Queue
import config

class Object:
    def __init__(self, id, name):
        self.id = id
        self.name = name
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
        print("Initial list")
        print(self.trackedObjects)
        # Start process
        self.process = Process(target=self.run)
        self.process.start()

    def obtainBearer(self):
        url = "https://fydp-backend-production.up.railway.app/api/auth/login/" 
        headers = {"Content-Type": "application/json"}
        data = config.data
        response = requests.post(url, json=data, headers=headers)
        print(response.status_code)
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
        print(response.status_code)
        if(response.status_code == 200):
            for item in response.json():
                id = item["id"]
                name = item["name"]
                self.trackedObjects.append(Object(id, name))
            # self.trackedObjects = response.json()

    def updateLocations(self, id, x, y):
        # print("updating "+ str(id))
        for item in self.trackedObjects:
            if item.id == id:
                # calculate distance between last seen location
                # euclidean distance
                dist = np.sqrt((item.x - x)**2 + (item.y - y)**2)
                if(dist > 10):

                    print("Phone moved " + str(dist) + "pixels")

                # Update distance
                item.x = x
                item.y = y



    def sendUpdate(self, id, name, image, description):
        url = "fydp-backend-production.up.railway.app/ObjectTracking/" + id
        headers = {"Content-Type": "application/json", "Authorization":self.bearerToken}

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


