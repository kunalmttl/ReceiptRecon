import urllib.request
import urllib.error

urls = [
    'https://receiptrecon-backendnode.onrender.com/health',
    'https://receiptrecon-backendflask.onrender.com/health',
    'https://receiptrecon.vercel.app'
]

for url in urls:
    try:
        response = urllib.request.urlopen(url, timeout=30)
        print(f"{url} -> {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"{url} -> {e.code}")
    except urllib.error.URLError as e:
        print(f"{url} -> Error: {e.reason}")
    except Exception as e:
        print(f"{url} -> Error: {str(e)}")
