from django.shortcuts import render_to_response
from clamopener import settings
from clamopener.forms import RegisterForm
from clamopener.models import CLAMUsers
from django.http import HttpResponse, HttpResponseForbidden,HttpResponseNotFound
from django.core.mail import send_mail


def register(request):    
    if request.method == 'POST': # If the form has been submitted...
        form = RegisterForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            form.save()
            return render_to_response('submitted.html')
    else:
        form = RegisterForm() # An unbound form
        return render_to_response('register.html', {'form': form})


def activate(request, userid):
    if request.method == 'POST':
        if hashlib.md5(request.POST['pw']).hexdigest() == settings.MASTER_PASSWORD:            
            try:
                clamuser = CLAMUsers.objects.get(pk=int(userid))
            except:
                return HttpResponseNotFound("No such user", content_type="text/plain")    
            clamuser.activated = True
            clamuser.save()
            return HttpResponse("Succesfully activated", content_type="text/plain")
        else:
            return HttpResponseForbidden("Invalid password, not activated", content_type="text/plain")
        #send mail
        send_mail('Webservice account on ' + settings.DOMAIN , 'Dear ' + clamuser.fullname + '\n\nYour webservice account on ' + settings.DOMAIN + ' has been reviewed and activated.', 'from@example.com',
    ['to@example.com'], fail_silently=False)
    else:
        return render_to_response('activate.html')
        
