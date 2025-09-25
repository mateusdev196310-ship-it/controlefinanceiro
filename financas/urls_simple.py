from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect

# View simples para teste de deploy que redireciona para login
def home_view(request):
    return redirect('login')

# View de login simplificada
def login_view(request):
    return HttpResponse("<h1>Sistema Financeiro</h1><p>Página de login simplificada para teste de deploy.</p>")

# URLs simplificadas para teste de deploy
urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
]