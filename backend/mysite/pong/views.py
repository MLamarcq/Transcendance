from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from .models import User, Tournament, Party, Chat, Message, Statistic, Participant, Friendship, BlockedUser

 
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "pong/homepage.html")

def login(request):
    return render(request,"pong/login.html")


def signup(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        avatar = request.POST["avatar"]
        pseudo = request.POST["pseudo"]

        if User.objects.filter(pseudo=pseudo).exists():
            return render(request, 'pong/signup.html', {
                'error_message': "Username already exists. Please choose a different pseudo."
            })

        
        if User.objects.filter(email=email).exists():
            return render(request, 'pong/signup.html', {
                'error_message': "Email already exists. Please choose a different email."
            })
        
        user = User.objects.create_user(email=email, password=password, pseudo=pseudo, avatar=avatar)
        user.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "pong/signup.html")
        
""" 
def signin(request):
    pass
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
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
"""
