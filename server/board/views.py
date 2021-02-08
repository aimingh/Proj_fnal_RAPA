from django.shortcuts import render

# Create your views here.

# show video
def show_video(request):
    return render(request, 'board/show_video.html')