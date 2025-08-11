from pathlib import Path
from picamera2 import Picamera2
import numpy as np

class RPICamera():
    """The camera class for RPI cameras.  Implements the CameraInterface interface."""

    def __init__(self) -> None:
        """Initializes the RPI camera
        Parameters:
        handpad (Display): The link to the handpad"""
        self.home_path = str(Path.home())
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_still_configuration({"size":(960,760),"format":"YUV420"},)
        self.picam2.configure(self.camera_config)

    
    def set(self,exposure_time, gain):
        exp = int(exposure_time * 1000000)
        gn = int(float(gain))
        self.picam2.stop()
        self.picam2.set_controls({"ExposureTime": exp, "AnalogueGain": gn})
        self.picam2.start()

    def capture(
        self, m13: bool, polaris: bool):
        """Capture an image with the camera
        Parameters:
        m13 (bool): True if the example image of M13 should be used
        polaris (bool): True if the example image of Polaris should be used
        returns: nparray of Y channel
        """

        if m13 == True:
            return np.load('/home/efinder/Solver/test.npy')
        elif polaris == True:
            return np.load('/home/efinder/Solver/polaris.npy')
        else:
            array = np.array(self.picam2.capture_array())
            y = array[0:760,0:960]
            return y

