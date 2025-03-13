import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import sys
import numpy as np
import cv2
import hailo

from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    app_callback_class,
    get_numpy_from_buffer,
)

from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp, GStreamerApp

# Import recall app
from communication import RecallApp

# Initialization
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        # Create recall app instance
        self.recallapp = RecallApp()

def app_callback(pad, info, user_data):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Using the user_data to count the number of frames
    user_data.increment()



    string_to_print = f"Frame count: {user_data.get_count()}\n"

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if format is not None and width is not None and height is not None:
        # Get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)
    user_data.set_frame(frame)

    # Also count frames through the app
    count = user_data.recallapp.getCount()
    if count == user_data.recallapp.updateSurroundingsEvery:
        user_data.recallapp.MLFrameQueue.put(frame)
        user_data.recallapp.resetCount()
    user_data.recallapp.increment()
    # print(count)
    
    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    

    # Parse the detections
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        # Object ID 14
        if label == "cell phone" and confidence > 0.6:
            ## assume only one cell phone
            x = bbox.xmin()+bbox.width()/2
            y = bbox.ymin()+bbox.height()/2

            cv2.rectangle(frame, (int(bbox.xmin()), int(bbox.ymin())), (int(bbox.xmin())+int(bbox.width()), int(bbox.ymin())+int(bbox.height())), (255, 0, 255), 3)
            user_data.recallapp.updateLocations(14, x, y, frame)
            
    # Do something with the detection that updates the recall app
    #user_data.recallapp.
    user_data.recallapp.increment()
    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()