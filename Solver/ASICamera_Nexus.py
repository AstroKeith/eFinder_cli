from pathlib import Path
from shutil import copyfile
from CameraInterface import CameraInterface
import zwoasi as asi


class ASICamera(CameraInterface):
    """The camera class for ASI cameras.  Implements the CameraInterface interface."""

    def __init__(self) -> None:
        """Initializes the ASI camera

        Parameters:
        handpad (Display): The link to the handpad"""

        self.home_path = str(Path.home())

        # find a camera
        asi.init("/lib/zwoasi/armv8/libASICamera2.so")
        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            print ("Error:", " no camera found", "")
            self.camType = "not found"
            print("camera not found")
            exit()
        else:
            self.camType = "ZWO"
            cameras_found = asi.list_cameras()
            camera_id = 0
            self.initialize()
            print ("ZWO camera found", "", "")
            print("ZWO camera found")

    def initialize(self) -> None:
        """Initializes the camera and set the needed control parameters"""
        global camera
        if self.camType == "not found":
            return
        camera = asi.Camera(0)
        camera.set_control_value(
            asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()["BandWidth"]["MinValue"]
        )
        camera.disable_dark_subtract()
        camera.set_control_value(asi.ASI_WB_B, 99)
        camera.set_control_value(asi.ASI_WB_R, 75)
        camera.set_control_value(asi.ASI_GAMMA, 50)
        camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
        camera.set_control_value(asi.ASI_FLIP, 0)
        camera.set_image_type(asi.ASI_IMG_RAW8)

    def capture(
        self, exposure_time: float, gain: float, m13: bool, polaris: bool, destPath: str) -> None:
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str): The Ra and Dec
        m13 (bool): True if the example image of M13 should be used
        polaris (bool): True if the example image of Polaris should be used
        destPath (str): path to folder to save images, depends on Ramdisk selection
        """
        if self.camType == "not found":
            print ("camera not found", "", "")
            return

        camera.set_control_value(asi.ASI_GAIN, gain)
        camera.set_control_value(asi.ASI_EXPOSURE, exposure_time)  # microseconds

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
            camera.capture(filename=destPath+"capture.png")
        return

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return self.camType
