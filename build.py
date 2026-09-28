#!/usr/bin/env python3
"""Bundle the site into ONE self-contained HTML file (CSS, JS and local images inlined).
   Usage:  python3 build.py [output]      default output: dist/index.html
   Use the normal folder (index.html + assets/) for real hosting such as GitHub Pages;
   the single file is handy for previews, sending over chat, or hosts that only take one file."""
import base64, mimetypes, os, re, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'index.html')
read = lambda p: open(os.path.join(ROOT, p), encoding='utf-8').read()
html = read('index.html')
html = re.sub(r'<link rel="stylesheet" href="(assets/[^"]+\.css)">', lambda m: '<style>\n' + read(m.group(1)) + '\n</style>', html)
html = re.sub(r'<script src="(assets/[^"]+\.js)" defer></script>', '', html)          # moved to end of body
scripts = re.findall(r'assets/js/[\w.-]+\.js', read('index.html'))
body_js = ''.join('<script>\n' + read(s) + '\n</script>\n' for s in scripts)
html = html.replace('</body>', body_js + '</body>')
cache = {}
def data_uri(path):
    if path not in cache:
        mime = mimetypes.guess_type(path)[0] or ('image/webp' if path.endswith('.webp') else 'application/octet-stream')
        cache[path] = 'data:%s;base64,%s' % (mime, base64.b64encode(open(os.path.join(ROOT, path), 'rb').read()).decode())
    return cache[path]
html = re.sub(r'(src|href)="(assets/img/[^"]+)"', lambda m: '%s="%s"' % (m.group(1), data_uri(m.group(2))), html)
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print('built', out, round(len(html.encode()) / 1024), 'KB')
