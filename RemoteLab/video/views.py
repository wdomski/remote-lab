from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from utils.camera import CameraDevice
from utils.configuration import Configuration
from home.views import check_authorized, get_status

camera_device = CameraDevice()

camera_settings = camera_device.get_settings()
camera_settings.restore_default()
camera_settings.from_dict({"resolution": "3280x2464"})
if camera_device.is_available():
    camera_device.reconfigure(camera_settings)

cfg = Configuration()
config = cfg.get_config()


def image(request, data={}):
    data["auto_refresh"] = request.session.get("auto_refresh", False)
    data.update(get_status())

    if not camera_device.is_available():
        data["message"] = "Camera not available"
        data["message_type"] = "danger"
    else:
        camera_device.stop_stream()
    return render(request, "video/image.html", data)


def jpeg_compression(stream):
    if camera_device.compression_enabled():
        stream = camera_device.compress_image(stream)
        stream.seek(0)
        size_in_kB = stream.getbuffer().nbytes / 1024
        print(f"Compressed image to {size_in_kB:.2f} kB")
    return stream


def camera(request):
    response = HttpResponse(content_type="image/jpeg")
    if not camera_device.is_available():
        return response

    stream = camera_device.get_image()

    stream.seek(0)
    stream = jpeg_compression(stream)
    response.write(stream.read())

    return response


def stream_jpeg(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth
    streamer = camera_device.streamer("jpeg")
    return StreamingHttpResponse(
        streamer, content_type="multipart/x-mixed-replace;boundary=frame"
    )


def video_jpeg(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth

    data = get_status()

    if not camera_device.is_available():
        data["message"] = "Camera not available"
        data["message_type"] = "danger"

    return render(request, "video/video_jpeg.html", data)


def settings(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth

    data = get_status()

    if camera_device.is_available():
        data["resolutions"] = camera_device.get_available_resolutions()
        data["rotations"] = camera_device.get_available_rotations()
        data["message"] = ""

        if "changesettings" in request.POST:
            data["message"] = "Changed settings"
            cleaned = {}
            # drop list from each item
            for key, value in request.POST.items():
                if isinstance(value, list):
                    cleaned[key] = value[0]
                else:
                    cleaned[key] = value
            print(cleaned)
            camera_settings.from_dict(cleaned)

        data["settings"] = camera_settings.to_dict()
        camera_device.reconfigure(camera_settings)
        return render(request, "video/settings.html", data)

    data["message"] = "Camera not available"
    data["message_type"] = "danger"

    return render(request, "video/settings.html", data)


def autorefresh(request):
    data = get_status()
    status = request.POST.get("auto_refresh", "true")
    if status == "false":
        status = False
    else:
        status = True
    data["auto_refresh"] = status
    request.session["auto_refresh"] = status

    return image(request, data)
