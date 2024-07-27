from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from utils.camera import CameraDevice
from utils.configuration import Configuration
from PIL import Image
from io import BytesIO
from home.views import check_authorized, get_status

camera_device = CameraDevice()

camera_settings = camera_device.get_settings()
camera_settings.restore_default()
camera_settings.from_dict({'resolution': "3280x2464"})
if camera_device.is_available():
    camera_device.reconfigure(camera_settings)

cfg = Configuration()
config = cfg.get_config()

def image(request, data={}):
    data['auto_refresh'] = request.session.get("auto_refresh", False)
    data.update(get_status())
    
    if not camera_device.is_available():
        data['message'] = "Camera not available"
        data['message_type'] = "danger"
        
    return render(request, 'video/image.html', data)

def camera(request):
    response = HttpResponse(content_type='image/jpeg')
    if camera_device.is_available():
        stream = camera_device.get_image()

        if stream is not None:
            stream.seek(0)
            image = Image.open(stream)    
            image.save(response, "JPEG")

    return response  

def stream(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth
    
    streamer_g = streamer()
    return StreamingHttpResponse(streamer_g, content_type="multipart/x-mixed-replace;boundary=frame")
    

def streamer():
    if camera_device.is_available():
        while True:
            stream = camera_device.get_image()
            if stream is None:
                break
                
            image = Image.open(stream)
            stream_jpeg = BytesIO()
            image.save(stream_jpeg, "JPEG")
            stream_jpeg.seek(0)

            yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + stream_jpeg.read() + b'\r\n\r\n')
    yield(b'')

def video(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth
    
    data = get_status()
    
    if not camera_device.is_available():
        data['message'] = "Camera not available"
        data['message_type'] = "danger"

    return render(request, 'video/video.html', data)

def settings(request):
    auth = check_authorized(request)
    if auth is not None:
        return auth
    
    data = get_status()
    
    if camera_device.is_available():    
        data['resolutions'] = camera_device.get_available_resolutions()
        data['rotations'] = camera_device.get_available_rotations()
        data['message'] = ""

        if "changesettings" in request.POST:
            data['message'] = "Changed settings"
            cleaned = {}
            # drop list from each item
            for key, value in request.POST.items():
                if isinstance(value, list):
                    cleaned[key] = value[0]
                else:
                    cleaned[key] = value
            print(cleaned)
            camera_settings.from_dict(cleaned)                     

        data['settings'] = camera_settings.to_dict()
        camera_device.reconfigure(camera_settings)
        return render(request, 'video/settings.html', data)
    
    data['message'] = "Camera not available"
    data['message_type'] = "danger"

    return render(request, 'video/settings.html', data)
    

def autorefresh(request):
    data = get_status()
    status = request.POST.get('auto_refresh', "true")
    if status == "false":
        status = False
    else:
        status = True
    data['auto_refresh'] = status
    request.session["auto_refresh"] = status

    return image(request, data)