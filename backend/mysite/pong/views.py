from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from base64 import b64encode
from django.core.files.base import ContentFile

from .models import NewUser, Tournament, Party, Chat, Message, Statistic, Participant, Friendship, BlockedUser

 
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "pong/homepage.html")

def login_view(request):
    return render(request,"pong/login.html")


def signup(request):
    if request.user.is_authenticated:
        #ça serait bien de rajouter une notification "vous êtes déjà connecté"
        return HttpResponseRedirect(reverse("index"))
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        avatar = request.FILES.get("avatar")
        pseudo = request.POST.get("pseudo")

        if NewUser.objects.filter(pseudo=pseudo).exists():
            return render(request, 'pong/signup.html', {
                'error_message': "Username already exists. Please choose a different pseudo."
            })

        
        if NewUser.objects.filter(email=email).exists():
            return render(request, 'pong/signup.html', {
                'error_message': "Email already exists. Please choose a different email."
            })
        binary_data = b64encode(avatar.read())

        user = NewUser.objects.create_user(email=email, password=password, pseudo=pseudo, avatar=binary_data)
        user.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "pong/signup.html")
        

def signin(request):
    if request.user.is_authenticated:
        #ça serait bien de rajouter une notification "vous êtes déjà connecté"
        return HttpResponseRedirect(reverse("index"))
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "users/login.html", {
                "message": "Invalid credentials."
            })
    else:
        return render(request, "pong/signin.html")

