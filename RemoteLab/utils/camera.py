from multiprocessing import Lock
from io import BytesIO
from dataclasses import dataclass, field
from typing import Literal, Union, List

# using camera module picamera
camera_module_available = ""
try:
    from picamera import PiCamera
    camera_module_available = "picamera"
    print("Loaded picamera")
except:
    print("Was not able to load PiCamera package")

# using camera module picamera2
try:
    if not camera_module_available:
        from picamera2 import Picamera2 as PiCamera
        import libcamera
        print("Loaded picamera2")
        camera_module_available = "picamera2"
except:
    print("Was not able to load PiCamera2 package")

# try to import matplotlib
matplotlib_imported = False
try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    matplotlib_imported = True
except:
    print("Was not able to load matplotlib package")

@dataclass
class CameraSettings:
    camera_type: str = field(init=True, default="picamera")
    resolution: tuple = (640, 480)
    hflip: bool = False
    vflip: bool = False
    rotation: int = 180
    brightness: float = 50
    contrast: float = 0
    saturation: float = 0
    sharpness: float = 0

    def restore_default(self):
        self.from_dict({})

    def to_dict(self) -> dict:
        settings = {}
        settings['resolution'] = f"{self.resolution[0]}x{self.resolution[1]}"
        settings['hflip'] = self.hflip
        settings['vflip'] = self.vflip
        settings['rotation'] = self.rotation
        settings['brightness'] = self.brightness
        settings['contrast'] = self.contrast
        settings['saturation'] = self.saturation
        settings['sharpness'] = self.sharpness
        
        if self.camera_type == "picamera":
            ranges = {'brightness': (0, 100, 1), 
                      'contrast': (-100, 100, 1), 
                      'saturation': (-100, 100, 1), 
                      'sharpness': (-100, 100, 1)}
        elif self.camera_type == "picamera2":
            ranges = {'brightness': (-1.0, 1.0, 0.01), 
                      'contrast': (0.0, 32.0, 0.1), 
                      'saturation': (0.0, 32.0, 0.1), 
                      'sharpness': (0.0, 16.0, 0.1)}
            
        for param, range in ranges.items():
            settings[f"min_{param}"] = range[0]
            settings[f"max_{param}"] = range[1]
            settings[f"step_{param}"] = range[2]         
        
        return settings

    def from_dict(self, settings: dict):
        try:
            self.resolution = tuple(map(int, settings['resolution'].split('x')))
        except:
            self.resolution = (640, 480)
        try:
            self.hflip = bool(settings['hflip'])
        except:
            self.hflip = False
        try:
            self.vflip = bool(settings['vflip'])
        except:
            self.vflip = False
        try:
            self.rotation = int(settings['rotation'])
        except:
            self.rotation = 180

        if self.camera_type == "picamera":
            self._from_dict_picamera(settings)
        elif self.camera_type == "picamera2":
            self._from_dict_picamera2(settings)

    def _from_dict_picamera(self, settings: dict):
        try:
            self.brightness = max(min(int(settings['brightness']), 100), 0)
        except:
            self.brightness = 50
        try:
            self.contrast = max(min(int(settings['contrast']), 100), -100)
        except:
            self.contrast = 0
        try:
            self.saturation = max(min(int(settings['saturation']), 100), -100)
        except:
            self.saturation = 0
        try:
            self.sharpness = max(min(int(settings['sharpness']), 100), -100)
        except:
            self.sharpness = 0

    def _from_dict_picamera2(self, settings: dict):
        try:
            self.brightness = max(min(float(settings['brightness']), 1.0), -1.0)
        except:
            self.brightness = 0.0
        try:
            self.contrast = max(min(float(settings['contrast']), 32.0), 0.0)
        except:
            self.contrast = 1.0
        try:
            self.saturation = max(min(float(settings['saturation']), 32.0), 0.0)
        except:
            self.saturation = 1.0
        try:
            self.sharpness = max(min(float(settings['sharpness']), 16.0), 0.0)
        except:
            self.sharpness = 1.0


class CameraDevice():
    def __init__(self):
        self._camera_lib = camera_module_available
        self._settings = CameraSettings(camera_type=self._camera_lib)
        self._lock = Lock()
        try:
            self._device = PiCamera()
        except:
            self._device = None
            print("Not able to create camera device")
            return
        
        if self._camera_lib == "picamera2":
            self._config = self._device.create_still_configuration(main={'size': self._settings.resolution})

        print("Camera device initialized")
        
    def is_available(self) -> bool:
        return self._device is not None
        
    def get_available_resolutions(self) -> List:
        if self._camera_lib == "picamera":
            return ["320x240", "640x480", "1280x720", "1640x922", "1640x1232", "1920x1080", "3280x2464"]
        elif self._camera_lib == "picamera2":
            return ["320x240", "640x480", "1280x720", "1920x1080", "3280x2464"]
        
    def get_available_rotations(self) -> List:
        if self._camera_lib == "picamera":
            return [0, 90, 180, 270]
        elif self._camera_lib == "picamera2":
            return [0]        

    def get_settings(self) -> CameraSettings:
        if self._device:
            return self._settings
        return CameraSettings()

    def reconfigure(self, camera_settings: Union[CameraSettings, dict]):
        with self._lock:
            if self._device is None:
                return

            if isinstance(camera_settings, dict):
                self._settings.from_dict(camera_settings)
            else:
                self._settings = camera_settings

            if self._camera_lib == "picamera":
                self._device.resolution = self._settings.resolution
                self._device.hflip = self._settings.hflip
                self._device.vflip = self._settings.vflip
                self._device.rotation = int(self._settings.rotation)
                self._device.brightness = int(self._settings.brightness)
                self._device.contrast = int(self._settings.contrast)
                self._device.saturation = int(self._settings.saturation)
                self._device.sharpness = int(self._settings.sharpness)
            elif self._camera_lib == "picamera2":
                controls = {'Brightness': self._settings.brightness, 
                            'Contrast': self._settings.contrast, 
                            'Saturation': self._settings.saturation, 
                            'Sharpness': self._settings.sharpness}
                transform = libcamera.Transform(hflip=self._settings.hflip, 
                                                vflip=self._settings.vflip)
                self._config = self._device.create_still_configuration(main={'size': self._settings.resolution},
                                                                       controls=controls,
                                                                       transform=transform
                                                                       )
                self._device.stop()
                self._device.configure(self._config)

    def get_image(self):
        if self._camera_lib == "":
            return None
        stream = BytesIO()

        with self._lock:
            if self._camera_lib == "picamera":
                self._device.start_preview()
                self._device.capture(stream, format='jpeg')
                self._device.stop_preview()
            elif self._camera_lib == "picamera2":
                self._device.start()
                self._device.capture_file(stream, format='jpeg')
                
        return stream

    def show_image(self, stream: BytesIO = None):
        if not stream:
            stream = self.get_image()
        img = mpimg.imread(stream, format='jpeg')            
        plt.imshow(img)
        plt.show()
