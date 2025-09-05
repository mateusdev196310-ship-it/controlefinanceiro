import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/adicionar-transacao/')
    print(f"Status Code: {response.getcode()}")
    if response.getcode() == 200:
        print("URL está funcionando!")
        print("Conteúdo encontrado (primeiros 200 caracteres):")
        content = response.read().decode('utf-8')
        print(content[:200])
    else:
        print(f"Erro: {response.getcode()}")
except urllib.error.HTTPError as e:
    print(f"Erro HTTP: {e.code}")
    print(f"Mensagem: {e.reason}")
except urllib.error.URLError as e:
    print(f"Erro de URL: {e.reason}")
except Exception as e:
    print(f"Erro inesperado: {e}")