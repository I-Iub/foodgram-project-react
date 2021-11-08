# from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse('This is index')


def profile(request, username):
    pass


def recipe(request):
    pass
