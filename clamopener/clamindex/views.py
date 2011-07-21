# Create your views here.
from clamopener import settings
from django.shortcuts import render_to_response

def index(request):    
    return render_to_response('index.html', {'services': settings.SERVICES})
