from multiprocessing import Lock
from io import BytesIO, BufferedIOBase
from dataclasses import dataclass, field
from typing import Literal, Union, List
from PIL import Image
import subprocess
import time
import os
import threading
from enum import StrEnum

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
        from picamera2.encoders import H264Encoder, MJPEGEncoder
        from picamera2.outputs import FileOutput
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


class CameraSettingsAfModes(StrEnum):
    Manual = "Manual"
    Auto = "Auto"
    Continuous = "Continuous"


CameraSettingsAfModesList = [e.value for e in CameraSettingsAfModes]


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
    sharpness: float = 1.0
    framerate: int = 24
    bitrate: int = 10000000
    autofocus_mode: str = CameraSettingsAfModes.Auto
    autofocus_lens_position: float = 0.0
    exposure_value: float = 0.0
    # following settings are only used for images or image stream in JPEG fromat
    jpeg_quality: int = (
        0  # desired JPEG qualit, if 0 then it is disabled, no compression is done
    )
    jpeg_quality_auto: bool = (
        False  # if True then the jpeg_quality is automatically adjusted
    )
    jpeg_quality_auto_goal: float = (
        150.0  # value given in kB of output file size, this is the maximum size the image can have after compression
    )

    def restore_default(self):
        self.from_dict({})

    def to_dict(self) -> dict:
        settings = {}
        settings["resolution"] = f"{self.resolution[0]}x{self.resolution[1]}"
        settings["hflip"] = self.hflip
        settings["vflip"] = self.vflip
        settings["rotation"] = self.rotation
        settings["brightness"] = self.brightness
        settings["contrast"] = self.contrast
        settings["saturation"] = self.saturation
        settings["sharpness"] = self.sharpness
        settings["framerate"] = self.framerate
        settings["bitrate"] = self.bitrate
        settings["jpeg_quality"] = self.jpeg_quality
        settings["jpeg_quality_auto"] = self.jpeg_quality_auto
        settings["jpeg_quality_auto_goal"] = self.jpeg_quality_auto_goal

        if self.camera_type == "picamera":
            ranges = {
                "brightness": (0, 100, 1),
                "contrast": (-100, 100, 1),
                "saturation": (-100, 100, 1),
                "sharpness": (-100, 100, 1),
                "framerate": (1, 120, 1),
                "bitrate": (1000, 17000000, 1000),
            }
        elif self.camera_type == "picamera2":
            ranges = {
                "brightness": (-1.0, 1.0, 0.01),
                "contrast": (0.0, 32.0, 0.1),
                "saturation": (0.0, 32.0, 0.1),
                "sharpness": (0.0, 16.0, 0.1),
                "framerate": (1, 120, 1),
                "bitrate": (1000, 10000000, 1000),
                "autofocus_lens_position": (0.0, 10.0, 0.01),
                "exposure_value": (-8.0, 8.0, 0.01),
            }
            settings["autofocus_mode"] = self.autofocus_mode
            settings["autofocus_lens_position"] = self.autofocus_lens_position
            settings["exposure_value"] = self.exposure_value

        ranges["jpeg_quality"] = (0, 100, 1)
        ranges["jpeg_quality_auto_goal"] = (50, 10000, 20)

        for param, range in ranges.items():
            settings[f"min_{param}"] = range[0]
            settings[f"max_{param}"] = range[1]
            settings[f"step_{param}"] = range[2]

        return settings

    def from_dict(self, settings: dict):
        try:
            self.resolution = tuple(map(int, settings["resolution"].split("x")))
        except:
            self.resolution = (640, 480)
        try:
            self.hflip = bool(settings["hflip"])
        except:
            self.hflip = False
        try:
            self.vflip = bool(settings["vflip"])
        except:
            self.vflip = False
        try:
            self.rotation = int(settings["rotation"])
        except:
            self.rotation = 180
        try:
            self.framerate = int(settings["framerate"])
        except:
            self.framerate = 24
        try:
            self.jpeg_quality = max(min(int(settings["jpeg_quality"]), 100), 0)
        except:
            self.jpeg_quality = 0
        try:
            self.jpeg_quality_auto = bool(settings["jpeg_quality_auto"])
        except:
            self.jpeg_quality_auto = False
        try:
            self.jpeg_quality_auto_goal = max(
                min(int(settings["jpeg_quality_auto_goal"]), 50000), 50
            )
        except:
            self.jpeg_quality_auto_goal = 150

        if self.camera_type == "picamera":
            self._from_dict_picamera(settings)
        elif self.camera_type == "picamera2":
            self._from_dict_picamera2(settings)

    def _from_dict_picamera(self, settings: dict):
        try:
            self.brightness = max(min(int(settings["brightness"]), 100), 0)
        except:
            self.brightness = 50
        try:
            self.contrast = max(min(int(settings["contrast"]), 100), -100)
        except:
            self.contrast = 0
        try:
            self.saturation = max(min(int(settings["saturation"]), 100), -100)
        except:
            self.saturation = 0
        try:
            self.sharpness = max(min(int(settings["sharpness"]), 100), -100)
        except:
            self.sharpness = 1.0
        try:
            self.bitrate = max(min(int(settings["bitrate"]), 17000000), 1000)
        except:
            self.bitrate = 17000000

    def _from_dict_picamera2(self, settings: dict):
        try:
            self.brightness = max(min(float(settings["brightness"]), 1.0), -1.0)
        except:
            self.brightness = 0.0
        try:
            self.contrast = max(min(float(settings["contrast"]), 32.0), 0.0)
        except:
            self.contrast = 1.0
        try:
            self.saturation = max(min(float(settings["saturation"]), 32.0), 0.0)
        except:
            self.saturation = 1.0
        try:
            self.sharpness = max(min(float(settings["sharpness"]), 16.0), 0.0)
        except:
            self.sharpness = 1.0
        try:
            self.bitrate = max(min(int(settings["bitrate"]), 10000000), 1000)
        except:
            self.bitrate = 10000000

        af_mode = settings.get("autofocus_mode", "Auto")
        if af_mode in CameraSettingsAfModesList:
            self.autofocus_mode = af_mode
        else:
            self.autofocus_mode = "auto"

        try:
            self.autofocus_lens_position = max(
                min(float(settings["autofocus_lens_position"]), 10.0), 0.0
            )
        except:
            self.autofocus_lens_position = 0.0

        try:
            self.exposure_value = max(min(float(settings["exposure_value"]), 8.0), -8.0)
        except:
            self.exposure_value = 0.0


class CameraDevice:

    def _reinitialize(self):
        print("Reinitializing camera device")
        try:
            if self._device:
                self._device.stop()
                self._device.close()
        except:
            print("Not able to stop camera device")

        try:
            self._device = PiCamera()
        except:
            self._device = None
            print("Not able to create camera device")
            return False

        self._settings = CameraSettings(camera_type=self._camera_lib)

        if self._camera_lib == "picamera2":
            print("Creating still configuration")
            self._config = self._device.create_still_configuration(
                main={"size": self._settings.resolution}
            )

        return True

    def __init__(self):
        self._camera_lib = camera_module_available
        self._lock = None
        self._device = None

        initialized = self._reinitialize()
        if initialized:
            self._lock = Lock()
            self._configured_for_streaming = False
            self._stream = None
            self._stream_buffer = None
            self._streaming = False
            print("Camera device initialized")

    def is_available(self) -> bool:
        return self._device is not None

    def get_available_resolutions(self) -> List:
        if self._camera_lib == "picamera":
            return [
                "320x240",
                "640x480",
                "1280x720",
                "1640x922",
                "1640x1232",
                "1920x1080",
                "3280x2464",
            ]
        elif self._camera_lib == "picamera2":
            return ["320x240", "640x480", "1280x720", "1920x1080", "3280x2464"]

    def get_autofocus_modes(self) -> List:
        return CameraSettingsAfModesList

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
        if self._lock is None:
            return

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
                self._device.framerate = self._settings.framerate
            elif self._camera_lib == "picamera2":
                controls = {
                    "Brightness": self._settings.brightness,
                    "Contrast": self._settings.contrast,
                    "Saturation": self._settings.saturation,
                    "Sharpness": self._settings.sharpness,
                    "ExposureValue": self._settings.exposure_value,
                }
                af_modes_translation = {
                    CameraSettingsAfModes.Manual.value: libcamera.controls.AfModeEnum.Manual,
                    CameraSettingsAfModes.Auto.value: libcamera.controls.AfModeEnum.Auto,
                    CameraSettingsAfModes.Continuous.value: libcamera.controls.AfModeEnum.Continuous,
                }
                controls_additional = {}
                controls_additional["AfMode"] = af_modes_translation.get(
                    self._settings.autofocus_mode, "Auto"
                )
                controls_additional["LensPosition"] = (
                    self._settings.autofocus_lens_position
                )
                transform = libcamera.Transform(
                    hflip=self._settings.hflip, vflip=self._settings.vflip
                )
                self._config = self._device.create_still_configuration(
                    main={"size": self._settings.resolution},
                    controls=controls,
                    transform=transform,
                )
                self._device.stop()
                self._device.configure(self._config)
                for name, value in controls_additional.items():
                    try:
                        self._device.set_control(name, value)
                    except:
                        print(f"Error setting control {name} to {value}")

            self._configured_for_streaming = False

    def configure_for_streaming(self):
        if self._configured_for_streaming:
            return

        if self._camera_lib == "picamera":
            self._configured_for_streaming = True
        elif self._camera_lib == "picamera2":
            FrameDelay = int(1000000 / self._settings.framerate)
            FrameDurationLimits = (FrameDelay, FrameDelay)

            controls = {
                "Brightness": self._settings.brightness,
                "Contrast": self._settings.contrast,
                "Saturation": self._settings.saturation,
                "Sharpness": self._settings.sharpness,
                "FrameDurationLimits": FrameDurationLimits,
            }
            transform = libcamera.Transform(
                hflip=self._settings.hflip, vflip=self._settings.vflip
            )
            video_config = self._device.create_video_configuration(
                {"size": self._settings.resolution},
                controls=controls,
                transform=transform,
            )
            if self._device.is_open:
                self._device.stop()
            self._device.configure(video_config)

            self._configured_for_streaming = True

    def init_stream(self, format: Literal["mjpeg", "h264", "mp4"] = "h264"):
        if not self._configured_for_streaming:
            self.configure_for_streaming()

        if self._camera_lib == "picamera":
            if format not in ["mjpeg", "h264"]:
                print("Unsupported format for video streaming, changing to mjpeg")
                format = "mjpeg"
            self.stop_stream()
            self._stream = BytesIO()
            self._device.start_recording(
                self._stream, format=format, bitrate=self._settings.bitrate
            )
            self._streaming = True
        elif self._camera_lib == "picamera2":
            self.stop_stream()
            if format == "mjpeg":
                self._encoder = MJPEGEncoder(self._settings.bitrate)
            elif format == "h264" or format == "mp4":
                self._encoder = H264Encoder(self._settings.bitrate)
            self._stream = BytesIO()
            self._stream_output = FileOutput(self._stream)
            self._device.start_recording(self._encoder, self._stream_output)
            self._streaming = True

        return self._stream

    def streamer(
        self,
        format: Literal["jpeg", "mjpeg", "h264", "mp4"],
        delay: float = 0.1,
        timeout: float = 0.0,
    ):
        if not self._configured_for_streaming:
            self.configure_for_streaming()

        if self._camera_lib == "picamera":
            if format == "jpeg":
                # mime type: multipart/x-mixed-replace;boundary=frame
                while True:
                    try:
                        stream = self.get_image()
                        if stream is None:
                            break

                        stream.seek(0)
                        if self.compression_enabled():
                            stream = self.compress_image(stream)
                            stream.seek(0)

                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + stream.read()
                            + b"\r\n\r\n"
                        )
                    except Exception as e:
                        print("Video jpeg streaming stopped")
            elif format == "mjpeg":
                # mime type: multipart/x-mixed-replace;boundary=frame
                self.init_stream(format="mjpeg")
                try:
                    while True:
                        self._device.wait_recording(delay)
                        self._stream.seek(0)
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + self._stream.read()
                            + b"\r\n\r\n"
                        )
                        self._stream.seek(0)
                        self._stream.truncate()
                except Exception as e:
                    print("Video mjpeg streaming stopped")
            elif format == "h264":
                # mime type: video/h264
                self.init_stream(format="h264")
                try:
                    while True:
                        self._device.wait_recording(delay)
                        self._stream.seek(0)
                        yield self._stream.read()
                        self._stream.seek(0)
                        self._stream.truncate()
                except Exception as e:
                    print("Video h264 streaming stopped")
            elif format == "mp4":
                # mime type: video/mp4
                self.init_stream(format="h264")
                ffmpeg_process, t_event = self._ffmpeg_stream(delay, timeout)

                tStart = time.time()

                try:
                    while True:
                        self._device.wait_recording(delay)
                        self._stream.seek(0)
                        data = self._stream.read()
                        self._stream.seek(0)
                        self._stream.truncate()
                        if len(data) == 0:
                            continue
                        ffmpeg_process.stdin.write(data)
                        ffmpeg_process.stdin.flush()
                        data = ffmpeg_process.stdout.read()
                        if data:
                            yield data
                        if timeout > 0.0:
                            if time.time() - tStart > timeout:
                                break
                except Exception as e:
                    print("Video mp4 streaming stopped")

                print("Terminating ffmpeg process")
                t_event.set()
                ffmpeg_process.terminate()
                print("Terminated ffmpeg process")

        elif self._camera_lib == "picamera2":
            if format == "jpeg":
                # mime type: multipart/x-mixed-replace;boundary=frame
                while True:
                    try:
                        stream = self.get_image()
                        if stream is None:
                            break

                        stream.seek(0)
                        if self.compression_enabled():
                            stream = self.compress_image(stream)
                            stream.seek(0)

                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + stream.read()
                            + b"\r\n\r\n"
                        )
                    except Exception as e:
                        print("Video jpeg streaming stopped")
            elif format == "mjpeg":
                # mime type: multipart/x-mixed-replace;boundary=frame
                self.init_stream(format="mjpeg")
                try:
                    while True:
                        time.sleep(delay)
                        self._stream.seek(0)
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + self._stream.read()
                            + b"\r\n\r\n"
                        )
                        self._stream.seek(0)
                        self._stream.truncate()
                except Exception as e:
                    print("Video mjpeg streaming stopped")
            elif format == "h264":
                # mime type: video/h264
                self.init_stream(format="h264")
                try:
                    while True:
                        time.sleep(delay)
                        self._stream.seek(0)
                        yield self._stream.read()
                        self._stream.seek(0)
                        self._stream.truncate()
                except Exception as e:
                    print("Video h264 streaming stopped")
            elif format == "mp4":
                # mime type: video/mp4
                self.init_stream(format="h264")
                ffmpeg_process, t_event = self._ffmpeg_stream(delay, timeout)

                tStart = time.time()

                try:
                    while True:
                        time.sleep(delay)
                        self._stream.seek(0)
                        data = self._stream.read()
                        self._stream.seek(0)
                        self._stream.truncate()
                        if len(data) == 0:
                            continue
                        ffmpeg_process.stdin.write(data)
                        ffmpeg_process.stdin.flush()
                        data = ffmpeg_process.stdout.read()
                        if data:
                            yield data
                        if timeout > 0.0:
                            if time.time() - tStart > timeout:
                                break
                except Exception as e:
                    print("Video mp4 streaming stopped")

                print("Terminating ffmpeg process")
                t_event.set()
                ffmpeg_process.terminate()
                print("Terminated ffmpeg process")

    def _ffmpeg_stream(self, delay: float = 0.1, timeout: float = 0.0):
        ffmpeg_cmd = [
            "ffmpeg",
            # "-fflags", "nobuffer",
            "-f",
            "h264",  # Input format: H.264
            "-i",
            "pipe:0",  # Input from standard input (pipe:0)
            "-f",
            "mp4",  # Output format: MP4
            "-movflags",
            "frag_keyframe+empty_moov",  # Fragment MP4 for streaming
            "-vcodec",
            "copy",  # Copy codec (no re-encoding)
            "pipe:1",  # Output to standard output (pipe:1)
        ]
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        fd = ffmpeg_process.stdout.fileno()
        os.set_blocking(fd, False)  # Make stdout non-blocking
        fd = ffmpeg_process.stderr.fileno()
        os.set_blocking(fd, False)  # Make stderr non-blocking

        def drain_stderr(stderr, event):
            while True:
                stderr.readline()
                if event.is_set():
                    break

        t_event = threading.Event()
        t = threading.Thread(
            target=drain_stderr,
            args=(
                ffmpeg_process.stderr,
                t_event,
            ),
        )
        t.start()

        return ffmpeg_process, t_event

    def stop_stream(self):
        if self._streaming:
            if self._camera_lib == "picamera":
                try:
                    if self._device.recording:
                        print("Stopping video stream")
                        self._device.stop_recording()
                except Exception as e:
                    print(
                        "Error stopping recording, already in progress in init stream"
                    )
                self._streaming = False
            elif self._camera_lib == "picamera2":
                try:
                    print("Stopping video stream")
                    self._device.stop_recording()
                except Exception as e:
                    print(
                        "Error stopping recording, already in progress in init stream"
                    )
                # self._stream_output.stop()
                self._stream_output = None
                self._stream = None
                self._configured_for_streaming = False
                self._streaming = False

    def get_image(self):
        if self._camera_lib == "":
            return None
        stream = BytesIO()

        with self._lock:
            if self._camera_lib == "picamera":
                self._device.start_preview()
                self._device.capture(stream, format="jpeg")
                self._device.stop_preview()
            elif self._camera_lib == "picamera2":
                reintialize = False
                try:
                    self._device.start()
                    self._device.capture_file(stream, format="jpeg")
                    self._device.stop()
                except Exception as e:
                    print("Error capturing image")
                    reintialize = True
                    return None

                if reintialize:
                    self._reinitialize()

        return stream

    def show_image(self, stream: BytesIO = None):
        if not stream:
            stream = self.get_image()
        img = mpimg.imread(stream, format="jpeg")
        plt.imshow(img)
        plt.show()

    def compression_enabled(self):
        return self._settings.jpeg_quality > 0 or self._settings.jpeg_quality_auto

    def compress_image(self, stream: BytesIO) -> BytesIO:
        if self._settings.jpeg_quality_auto:
            stream = self._compress_image_auto(stream)
        else:
            stream = self._compress_image(stream, self._settings.jpeg_quality)
        return stream

    def _compress_image_auto(self, stream: BytesIO, threshold: float = 0.1) -> BytesIO:
        change = (100 - 5) / 2
        quality = change
        goal = self._settings.jpeg_quality_auto_goal * 1024
        threshold_size = goal * threshold
        output = BytesIO(stream.getbuffer())
        # binary search for the optimal quality
        while change > 1:
            stream.seek(0)
            output = self._compress_image(stream, quality)
            image_size = output.getbuffer().nbytes
            # early stop if within threshold
            if abs(image_size - goal) <= threshold_size:
                break
            change = change / 2
            quality = quality + change if image_size < goal else quality - change
        return output

    def _compress_image(self, stream: BytesIO, quality: int = 0) -> BytesIO:
        if quality == 0:
            return stream
        stream.seek(0)
        img = Image.open(stream)
        output = BytesIO()
        img.save(output, format="jpeg", quality=int(quality), optimize=True)
        return output
