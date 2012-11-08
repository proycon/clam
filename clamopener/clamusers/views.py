from django.shortcuts import render_to_response
from clamopener import settings
from clamopener.clamusers.forms import RegisterForm
from clamopener.clamusers.models import CLAMUsers
from django.http import HttpResponse, HttpResponseForbidden,HttpResponseNotFound
from django.core.mail import send_mail
from django.core.context_processors import csrf
from django.template import RequestContext
import hashlib

def register(request):    
    if request.method == 'POST': # If the form has been submitted...        
        form = RegisterForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            clamuser = form.save()
            send_mail('[' + settings.DOMAIN + '] Registration request from ' + clamuser.username + ' pending approval' , 'The following new account is pending approval:\n\nUsername: ' + clamuser.username + '\nFull name: '  +clamuser.fullname + '\nInstitution: ' + clamuser.institution + '\nMail: ' + clamuser.mail + '\n\nTo approve this user go to: ' + settings.BASEURL + 'activate/' + str(clamuser.pk), settings.FROMMAIL, [clamuser.mail] + [ x[1] for x in settings.ADMINS ] , fail_silently=False)
            return render_to_response('submitted.html')            
    else:
        c = RequestContext(request)
        c.update(csrf(request))
        form = RegisterForm() # An unbound form
        return render_to_response('register.html', {'form': form},context_instance=c)


def activate(request, userid):
    if request.method == 'POST':
        if hashlib.md5(request.POST['pw']).hexdigest() == settings.MASTER_PASSWORD:            
            try:
                clamuser = CLAMUsers.objects.get(pk=int(userid))
            except:
                return HttpResponseNotFound("No such user", content_type="text/plain")    
            clamuser.activated = True
            clamuser.save()
            send_mail('Webservice account on ' + settings.DOMAIN , 'Dear ' + clamuser.fullname + '\n\nYour webservice account on ' + settings.DOMAIN + ' has been reviewed and activated.', settings.FROMMAIL, [clamuser.mail] + [ x[1] for x in settings.ADMINS ] , fail_silently=False)
            return HttpResponse("Succesfully activated", content_type="text/plain")
        else:
            return HttpResponseForbidden("Invalid password, not activated", content_type="text/plain")
    
    else:
        c = RequestContext(request)
        c.update(csrf(request))
        return render_to_response('activate.html',{'userid': userid},context_instance=c)
        
def report(request):
    s = "The following accounts are pending approval:\n\n"
    report = []             
    for clamuser in CLAMUsers.objects.filter(active=0):
        report.append('Username: ' + clamuser.username + '\nFull name: '  +clamuser.fullname + '\nInstitution: ' + clamuser.institution + '\nMail: ' + clamuser.mail + '\n\nTo approve this user go to: ' + settings.BASEURL + 'activate/' + str(clamuser.pk))
    
    if report:
        s = "\n\n".join(report)
    else:
        s = "(no pending accounts found)"
        
    send_mail('[' + settings.DOMAIN + '] Report of pending accounts' , s , settings.FROMMAIL, [ x[1] for x in settings.ADMINS ] , fail_silently=False)








