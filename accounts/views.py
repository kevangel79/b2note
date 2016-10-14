from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import login as django_login, authenticate, logout as django_logout
from django.forms.models import model_to_dict
from accounts.forms import AuthenticationForm, RegistrationForm, ProfileForm
from accounts.models import AnnotatorProfile

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from b2note_devel.settings import DEFAULT_FROM_EMAIL
from django.views.generic import *
from forms.reset_password import PasswordResetRequestForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models.query_utils import Q

# Create your views here.


# http://ruddra.com/2015/09/18/implementation-of-forgot-reset-password-feature-in-django/
class ResetPasswordRequestView(FormView):
    template_name = "account/test_template.html"  # code for template is given below the view's code
    success_url = '/account/login'
    form_class = PasswordResetRequestForm

    @staticmethod
    def validate_email_address(email):
        '''
        This method here validates the if the input is an email address or not. Its return type is boolean, True if the input is a email address or False if its not.
        '''
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False


    def post(self, request, *args, **kwargs):
        '''
        A normal post request which takes input from field "email_or_username" (in ResetPasswordRequestForm).
        '''

        form = self.form_class(request.POST)
        data = None
        if form.is_valid():
            data = form.cleaned_data["email_or_username"]
        if self.validate_email_address(data) is True:  # uses the method written above
            '''
            If the input is an valid email address, then the following code will lookup for users associated with that email address. If found then an email will be sent to the address, else an error message will be printed on the screen.
            '''
            associated_users = User.objects.filter(Q(email=data) | Q(username=data))
            if associated_users.exists():
                for user in associated_users:
                    c = {
                        'email': user.email,
                        'domain': request.META['HTTP_HOST'],
                        'site_name': 'your site',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    subject_template_name = 'registration/password_reset_subject.txt'
                    # copied from django/contrib/admin/templates/registration/password_reset_subject.txt to templates directory
                    email_template_name = 'registration/password_reset_email.html'
                    # copied from django/contrib/admin/templates/registration/password_reset_email.html to templates directory
                    subject = loader.render_to_string(subject_template_name, c)
                    # Email subject *must not* contain newlines
                    subject = ''.join(subject.splitlines())
                    email = loader.render_to_string(email_template_name, c)
                    send_mail(subject, email, DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                result = self.form_valid(form)
                messages.success(request,
                                 'An email has been sent to ' + data + ". Please check its inbox to continue reseting password.")
                return result
            result = self.form_invalid(form)
            messages.error(request, 'No user is associated with this email address')
            return result
        else:
            '''
            If the input is an username, then the following code will lookup for users associated with that user. If found then an email will be sent to the user's address, else an error message will be printed on the screen.
            '''
            associated_users = User.objects.filter(username=data)
            if associated_users.exists():
                for user in associated_users:
                    c = {
                        'email': user.email,
                        'domain': 'example.com',  # or your domain
                        'site_name': 'example',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    subject_template_name = 'registration/password_reset_subject.txt'
                    email_template_name = 'registration/password_reset_email.html'
                    subject = loader.render_to_string(subject_template_name, c)
                    # Email subject *must not* contain newlines
                    subject = ''.join(subject.splitlines())
                    email = loader.render_to_string(email_template_name, c)
                    send_mail(subject, email, DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                result = self.form_valid(form)
                messages.success(request,
                                 'Email has been sent to ' + data + "'s email address. Please check its inbox to continue reseting password.")
                return result
            result = self.form_invalid(form)
            messages.error(request, 'This username does not exist in the system.')
            return result
        messages.error(request, 'Invalid Input')
        return self.form_invalid(form)






def profilepage(request):
    """
    User profile view.
    """
    try:
        if request.session.get("user"):
            userprofile = AnnotatorProfile.objects.using('users').get(pk=request.session.get("user"))
            form = ProfileForm(initial = model_to_dict(userprofile) )
            return render_to_response('accounts/profilepage.html', {'form': form}, context_instance=RequestContext(request))
        else:
            return redirect('/logout')
    except Exception:
        print "Could not load or redirect from profilepage view."
        return False


def login(request):
    """
    Log in view
    """

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(email=request.POST['username'], password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    print type(user), isinstance(user, unicode), user
                    django_login(request, user)
                    print ">>>", user.annotator_id.annotator_id
                    request.session["user"] = user.annotator_id.annotator_id
                    return redirect('/homepage')
    else:
        if request.session.get("user"):
            return redirect('/homepage', context=RequestContext(request))
        else:
            form = AuthenticationForm()

    return render_to_response('accounts/login.html',{'form': form, 'is_console_access': False},
                              context_instance=RequestContext(request, {
                                  "pid_tofeed": request.session.get("pid_tofeed"),
                                  "subject_tofeed": request.session.get("subject_tofeed")
                              }))

def consolelogin(request):
    """
    Log in view
    """

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(email=request.POST['username'], password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    #print type(user), isinstance(user, unicode), user
                    django_login(request, user)
                    #print ">>>", user.annotator_id.annotator_id
                    request.session["user"] = user.annotator_id.annotator_id
                    return redirect('/interface_main')
    else:
        if request.session.get("user"):
            return redirect('/interface_main', context=RequestContext(request))
        else:
            form = AuthenticationForm()

    return render_to_response('accounts/login.html',{'form': form, 'is_console_access': True},
                              context_instance=RequestContext(request, {
                                  "pid_tofeed": request.session.get("pid_tofeed"),
                                  "subject_tofeed": request.session.get("subject_tofeed")
                              }))


def register(request):
    """
    User registration view.
    """
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST)
        #print form
        if form.is_valid():
            user = form.save()
            return redirect('/accounts/logout')
        else:
            print form.errors
    else:
        form = RegistrationForm()
    return render_to_response('accounts/register.html', {'form': form,}, context_instance=RequestContext(request))


def logout(request):
    """
    Log out view
    """
    request.session["is_console_access"] = False
    django_logout(request)
    return redirect('/')