from pathlib import Path
from picamera2 import Picamera2
import numpy as np
import time

# upadated 18/11/2025 to include buffer = 2, speeds up capture x2
class RPICamera():
    """The camera class for RPI cameras.  Implements the CameraInterface interface."""

    def __init__(self) -> None:
        """Initializes the RPI camera"""
        self.home_path = str(Path.home())
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_still_configuration({"size":(2028,1520),"format":"YUV420"},buffer_count=2)
        self.picam2.configure(self.camera_config)

    
    def set(self,exposure_time, gain):
        exp = int(exposure_time * 1000000)
        gn = int(float(gain))
        self.picam2.stop()
        self.picam2.set_controls({
            "AeEnable": False,
            "AwbEnable": False,
            "ExposureTime": exp, 
            "AnalogueGain": gn
            })        
        self.picam2.start()

    def capture(self):
        """Capture an image with the camera
        returns: np.array of Y channel
        """
        array = np.array(self.picam2.capture_array())
        y = array[350:1100,500:1500]
        return y

