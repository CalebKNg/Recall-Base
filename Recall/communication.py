import cv2
import numpy as np
import requests
from multiprocessing import Process, Queue
import torch
import base64
import config
import heapq
from collections import deque

classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]

relational_words = [
        "the right of", "above", "to the left of", "below", 
    ]

class Object:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.x = 0
        self.y = 0
        self.locHistory = deque()
        self.isMoving = True
        self.lastLocationImage = ""

class RecallApp:
    def __init__(self):
        # prob need an auth token as well as a dictionary of the objects that are currently being tracked
        
        self.historyLength = 60
        self.avgLength = 10
        self.updateSurroundingsEvery = 9000
        self.count = self.updateSurroundingsEvery
        self.sector_size = 360/90

        # Tracked objects list
        self.trackedObjects = []
        
        # Queues
        self.MLFrameQueue = Queue()
        self.detectionQueue = Queue()

        # Surroundings list
        self.surroundings = []
        
        # Get Token
        self.bearerToken = self.obtainBearer()

        # Get Initial List
        self.obtainObjects()

        # Initiate Relational Model
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s")
        self.model.verbose = True
        self.model.to("cpu")

        # Start process
        self.process = Process(target=self.run)
        self.process.start()

    def increment(self):
        self.count += 1

    def getCount(self):
        return self.count

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
                for i in range(self.avgLength): 
                    ob.locHistory.append((0,0))
                self.trackedObjects.append(ob)
            # self.trackedObjects = response.json()

    def updateLocations(self, id, x, y, frame):
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

                # Grab average of the last 5 
                xrec = 0
                yrec = 0
                for i in range(self.avgLength):
                    xrec += item.locHistory[i][0]
                    yrec += item.locHistory[i][1]
                xrec = xrec/self.avgLength
                yrec = yrec/self.avgLength
                # euclidean distance
                # dist = np.sqrt((x - xavg)**2 + (y - yavg)**2)
                dist = np.sqrt((xrec - xavg)**2 + (yrec - yavg)**2)

                threshold = 0.01
                if item.isMoving:
                    if dist < threshold:
                        # stopped moving
                        
                        # print("Phone moved " + str(dist) + "pixels")
                        item.isMoving = False
                        output = self.toB64(frame)

                        pts = self.findKNearestPoints(x, y)
                        outputString = self.relationalString(x, y, pts)
                        print(outputString)
                        # make request
                        # self.sendUpdate(item.id, output, outputString)

                else:   # If not moving
                    if dist >= threshold:
                        item.isMoving = True
                        # print("Phone is moving")

                # print(item.isMoving)
                # Update distance
                item.x = x
                item.y = y
                item.lastLocationImage = self.toB64(frame)

                # Update queue
                if(len(item.locHistory) > self.historyLength):
                    item.locHistory.pop()
                    item.locHistory.appendleft((x, y))
                else:
                    item.locHistory.appendleft((x, y))


    def sendUpdate(self, id, name, image, description):
        url = "fydp-backend-production.up.railway.app/ObjectTracking/" + str(id)
        headers = {"Content-Type": "application/json", "Authorization":"Bearer " + self.bearerToken}

        data = {
            "name": name,
            "location_image": image,
            "location_description": description
        }

        response = requests.patch(url, json=data, headers=headers)
        print(response.status_code)


    def resetCount(self):
        self.count = 0

    def obtainSurroundings(self, frame):
        print("obtained")

        # results = self.model(frame)
        try:
            results = self.model(frame)
            print("Model inference completed")
        except Exception as e:
            print("Error during model inference:", str(e))
            return

        r = results.xyxy[0].numpy()

        for row in r:
            xmin, ymin, xmax, ymax, confidence, cls = row
            if classNames[cls] != "person" and classNames[cls] != "cell phone" and confidence > 0.6:
                xmin, ymin, xmax, ymax, cls = int(xmin), int(ymin), int(xmax), int(ymax), int(cls)
                x = xmin+(xmax-xmin)/2
                y = ymin+(ymax-ymin)/2
                self.surroundings.append((x, y, classNames[cls]))
        # print("surroundings")
        # print(self.surroundings)

    def findKNearestPoints(self, x, y):
        k = 3
        heap = []
        for px, py, s in self.surroundings:
            distance = np.sqrt((px - x) ** 2 + (py - y) ** 2)
            heapq.heappush(heap, (distance, (px, py, s)))
        return [heapq.heappop(heap)[1] for _ in range(min(k, len(heap)))]

    def relationalString(self, x, y, points):
        string = "Check "
        for px, py, s in points:
            angle = self.angleBetween(x, y, px, py)
            string = string + relational_words[int(angle//(self.sector_size))]
            string = string + " " + s + ", "

        return string

    def angleBetween(x, y, x2, y2):
        xdiff = x2 - x
        ydiff = y2 - y
        return np.arctan(ydiff/xdiff)*180/np.pi


    def toB64(self, img):
        _, buffer = cv2.imencode('.jpg', img)
        im_bytes = buffer.tobytes()
        b64 = base64.b64encode(im_bytes)
        return b64.decode("utf-8")


    def grabNewPictures(self, id):
        url= "fydp-backend-production.up.railway.app/ObjectImage/?tracking_object_id=" +str(id)
        headers = {"Content-Type": "application/json", "Authorization":"Bearer " +self.bearerToken}

    def run(self):
        # Run this loop in another process
        while True:
            # Main Program Loop

            # Update Surroundings
            if not self.MLFrameQueue.empty():
                
                frame = self.MLFrameQueue.get()
                self.obtainSurroundings(frame)
    
    def terminate(self):
        self.process.terminate()
        self.process.join()


