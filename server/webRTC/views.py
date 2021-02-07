from django.shortcuts import render
from django.shortcuts import redirect

# Create your views here.
# def camera_jetbot(request):
#     return render(request, "camera_jetbot.html")


#################################################################################################
# Live
#################################################################################################
import time
from django.http import StreamingHttpResponse
from webRTC.utils import VideoCamera
from django.views.decorators.csrf import csrf_exempt

# streaming cam
cam = VideoCamera()
def gen(cam):
    while True:
        time.sleep(0.083)
        frame = cam.get_frame()
        yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def stream(request):
    try:
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        print("error streaming camera")

# change moving status
def moving(request, move):
    if move ==0:
        cam.move = False
    else:
        cam.move = True
    return redirect("live")

# live 
def live(request):
    return render(request, 'webRTC/camera_jetbot.html')
