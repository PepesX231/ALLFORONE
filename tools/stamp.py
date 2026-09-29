"""Cache-bust: append ?v=<content hash> to the local CSS/JS links in index.html (run before committing)."""
import hashlib, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'index.html'); s = open(p, encoding='utf-8').read()
def v(m):
    path = m.group(2); h = hashlib.md5(open(os.path.join(ROOT, path), 'rb').read()).hexdigest()[:8]
    return m.group(1) + path + '?v=' + h + m.group(4)
s = re.sub(r'((?:href|src)=")(assets/(?:css|js)/[\w.-]+\.(?:css|js))(\?v=\w+)?(")', v, s)
open(p, 'w', encoding='utf-8').write(s); print('stamped')
