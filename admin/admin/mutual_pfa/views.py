from django.shortcuts import render

def home(request):  # ← Cambiar 'view' por 'request'
    return render(request, 'home.html')