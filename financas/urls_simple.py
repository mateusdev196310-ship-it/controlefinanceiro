from django.urls import path
from django.http import HttpResponse

# View simples para teste de deploy
def home_view(request):
    return HttpResponse("<h1>Sistema Financeiro</h1><p>Página inicial simplificada para teste de deploy.</p>")

# URLs simplificadas para teste de deploy
urlpatterns = [
    path('', home_view, name='home'),
]