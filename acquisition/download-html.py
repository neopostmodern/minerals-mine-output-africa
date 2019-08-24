import urllib.request
import urllib.error
import config

req = urllib.request.Request(url=config.ENTRY_POINT)

try:
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8')

        with open(config.HTML_FILE_NAME, 'w') as html_file:
            html_file.write(html)


except urllib.error.URLError as error:
    print("Error!", error)
