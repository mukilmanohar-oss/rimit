import urllib.request
import urllib.error
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/auth/token')
    print(response.getcode())
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode('utf-8'))
