from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from base64 import b64encode
from django.core.files.base import ContentFile

from .models import NewUser, Tournament, Party, Chat, Message, Statistic, Participant, Friendship, BlockedUser
from django.http import HttpResponse, HttpResponseRedirect


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return (render(request, "pong/homepage.html"))


def login_view(request):
    if not request.user.is_authenticated:
        return render(request,"pong/login.html")
    else:
        #ça serait bien de rajouter une notification "vous êtes déjà connecté"
        return HttpResponseRedirect(reverse("index"))

def signup(request):
    if request.user.is_authenticated:
        #ça serait bien de rajouter une notification "vous êtes déjà connecté"
        return HttpResponseRedirect(reverse("index"))
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        avatar = request.FILES.get("avatar")
        pseudo = request.POST.get("pseudo")

        if (confirm_password.casefold() != password.casefold()) :
            return render(request, 'pong/signup.html', {
                'error_message': "Password don't match, please try again."
            })
        
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
        print(user.id)
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
            return render(request, "pong/signin.html", {
                "message": "Invalid credentials."
            })
    else:
        return render(request, "pong/signin.html")

def statistics(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    user = request.user
    statistics = user.statistic
    return render(request, "pong/statistics.html", {'user' : user, 'statistics' : statistics})

def chat(request):
    return render(request, "pong/chat.html")

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login')

def profil_view(request) :
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    return (render(request, "pong/profil.html"))
