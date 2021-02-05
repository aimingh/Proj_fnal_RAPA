from django.shortcuts import render

# Create your views here.
def camera_jetbot(request):
    return render(request, "camera_jetbot.html")


#################################################################################################
# Live
#################################################################################################
from django.http import StreamingHttpResponse
from webRTC.utils import VideoCamera

def gen(cam):
    while True:
        frame = cam.get_frame()
        yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

cam = VideoCamera()

def stream(request):
    try:
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:  # This is bad! replace it with proper handling
        pass

def live(request):
    return render(request, 'dcamera_jetbot.html')