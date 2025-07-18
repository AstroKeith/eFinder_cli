from pathlib import Path
from shutil import copyfile
import time
from picamera2 import Picamera2

class RPICamera():
    """The camera class for RPI cameras.  Implements the CameraInterface interface."""

    def __init__(self) -> None:
        """Initializes the RPI camera

        Parameters:
        handpad (Display): The link to the handpad"""

        self.home_path = str(Path.home())
        self.camType = "RPI"
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_still_configuration({"size":(960,760)})
        self.picam2.configure(self.camera_config)

    
    def set(self,exposure_time, gain):
        exp = int(exposure_time * 1000000)
        gn = int(float(gain))
        self.picam2.stop()
        self.picam2.set_controls({"ExposureTime": exp, "AnalogueGain": gn}) # ,"AeEnable": False})
        self.picam2.start()

    def capture(
        self, m13: bool, polaris: bool, destPath: str) -> None:
        """Capture an image with the camera
        Parameters:
        m13 (bool): True if the example image of M13 should be used
        polaris (bool): True if the example image of Polaris should be used
        destPath (str): path to folder to save images, depends on Ramdisk selection
        """
        if self.camType == "not found":
            print ("camera not found", "", "")
            exit()
        
        if m13 == True:
            print(self.home_path + "/Solver/test.png", destPath+"capture.png")
            copyfile(
                self.home_path + "/Solver/test.png",
                destPath+"capture.png",
            )
        elif polaris == True:
            copyfile(
                self.home_path + "/Solver/polaris.png",
                destPath+"capture.png",
            )
            print("using Polaris")
        else:
            filename=destPath+"capture.png"
            self.picam2.capture_file(filename)
        return

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return self.camType
