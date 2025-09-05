import urllib.request
import urllib.error

urls_to_test = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/transacoes/',
    'http://127.0.0.1:8000/adicionar-transacao/',
    'http://127.0.0.1:8000/adicionar-categoria/',
    'http://127.0.0.1:8000/adicionar-despesa-parcelada/',
    'http://127.0.0.1:8000/despesas-parceladas/',
    'http://127.0.0.1:8000/contas/',
    'http://127.0.0.1:8000/relatorios/'
]

for url in urls_to_test:
    try:
        response = urllib.request.urlopen(url)
        print(f"✅ {url} - Status: {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"❌ {url} - Erro HTTP: {e.code} ({e.reason})")
    except urllib.error.URLError as e:
        print(f"❌ {url} - Erro de URL: {e.reason}")
    except Exception as e:
        print(f"❌ {url} - Erro inesperado: {e}")