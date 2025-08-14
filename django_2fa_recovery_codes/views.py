from django.shortcuts import render
from django.http import HttpRequest
# Create your views here.

def recovery_codes_list(request):
    return HttpRequest("I am here")


def recovery_codes_regenerate(request):
    pass


def recovery_codes_verify(request, code):
    pass


def deactivate_recovery_code(request, code):
    pass


def recovery_dashboard(request):
    pass