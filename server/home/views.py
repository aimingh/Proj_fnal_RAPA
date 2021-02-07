from django.shortcuts import render

# Create your views here.

# home 
def live(request):
    return render(request, 'home/home.html')