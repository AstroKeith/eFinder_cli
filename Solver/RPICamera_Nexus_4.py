from pathlib import Path
from picamera2 import Picamera2
import numpy as np
import time

# upadated 18/11/2025 to include buffer = 2, speeds up capture x2
class RPICamera():
    """The camera class for RPI cameras.  Implements the CameraInterface interface."""

    def __init__(self) -> None:
        """Initializes the RPI camera
        Parameters:
        handpad (Display): The link to the handpad"""
        self.home_path = str(Path.home())
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_still_configuration({"size":(960,760),"format":"YUV420"},buffer_count=2)
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

    def capture(
        self, test: bool, offset: bool, hemi):
        """Capture an image with the camera
        Parameters:
        test (bool): True if the example image near M14 should be used
        offset (bool): True if the example image of Polaris should be used
        returns: np.array of Y channel
        """

        if test == True and hemi == 'N':
            return np.load('/home/efinder/Solver/test.npy')
        elif offset == True and hemi == 'N':
            return np.load('/home/efinder/Solver/polaris.npy')
        if test == True and hemi == 'S':
            return np.load('/home/efinder/Solver/testS.npy')
        elif offset == True and hemi == 'S':
            return np.load('/home/efinder/Solver/rigelK.npy')
        else:
            #print(time.time())
            array = np.array(self.picam2.capture_array())
            #print(time.time())
            y = array[0:760,0:960]
            #print(time.time())
            return y

