from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def index(request):
    return render(request, "pong/index.html")

def statistics(request):
    # return HttpResponseRedirect(reverse("pong:chat.html"))
    return render(request, "pong/statistics.html")

def chat(request):
    return render(request, "pong/chat.html")
