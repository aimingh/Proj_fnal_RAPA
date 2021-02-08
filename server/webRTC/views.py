from django.shortcuts import render
from django.shortcuts import redirect

# Create your views here.
#################################################################################################
# Live
#################################################################################################

import time
from django.http import StreamingHttpResponse, HttpResponse
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

@csrf_exempt
def avoidance(request):
    if (request.method == 'POST'):  # ajax에서 정보를 받는다.
        avoidance_status = request.POST.get('avoidance_status')
        cam.avoidance_status = True if avoidance_status=='1' else False
        print(cam.avoidance_status)
        return HttpResponse("receive")

@csrf_exempt
def cruise(request):
    if (request.method == 'POST'):  # ajax에서 정보를 받는다.
        cruise_status = request.POST.get('cruise_status')
        cam.cruise_status = True if cruise_status=='1' else False
        print(cam.cruise_status)
        return HttpResponse("receive")

@csrf_exempt
def move_arrow(request):
    if (request.method == 'POST'):  # ajax에서 정보를 받는다.
        move_arrow = request.POST.get('move_arrow')
        cam.move_arrow = move_arrow
        print(move_arrow)
        return HttpResponse("receive")

# live 
def live(request):
    return render(request, 'webRTC/camera_jetbot.html')


# Record video
import threading
import cv2
recording_flag = False

def record_video(cam):
    print('Recording start')
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter('static/videos/output.mp4', fourcc, 30.0, (640,720))
    while (recording_flag):
        frame = cam.result
        out.write(frame)
    print('Recording end')
    out.release()

@csrf_exempt
def record(request):
    global recording_flag
    global cam
    if (request.method == 'POST'):  # ajax에서 정보를 받는다.
        recording_flag = not recording_flag
        if recording_flag:
            threading.Thread(target=record_video, args=(cam,)).start()
        return HttpResponse("receive")
