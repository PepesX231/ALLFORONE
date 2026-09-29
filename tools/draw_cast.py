"""Original chibi hamster cast for All for One University (flat 2D, thick outline) -> SVG files."""
import os, math
OUT = '/home/claude/afo-repo/assets/img/cast'
os.makedirs(OUT, exist_ok=True)
INK = '#2b211e'
PAL = {
    'orange': dict(base='#fffaf3', shade='#eadfd1', patch='#f39a3d', belly='#ffffff'),
    'tan':    dict(base='#f2cf9c', shade='#dfb37b', patch=None, belly='#fff4e2'),
    'gray':   dict(base='#cdcad1', shade='#aba7b2', patch=None, belly='#f5f3f7', stripes='#8a8591'),
}
BODY = 'M120 30 C176 30 206 72 204 118 C214 156 208 206 172 226 C146 240 94 240 68 226 C32 206 26 156 36 118 C34 72 64 30 120 30 Z'


def arm(x0, y0, x1, y1, col, big=False, bend=0):
    mx, my = (x0 + x1) / 2 + bend, (y0 + y1) / 2 - abs(bend) * .3
    d = f'M{x0} {y0} Q{mx} {my} {x1} {y1}'
    w = 30 if big else 22
    s = f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w + 12}" stroke-linecap="round"/>'
    s += f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
    return s


def paw(x, y, r=13, rot=0, col='#f7b7b4'):
    s = f'<g transform="translate({x} {y}) rotate({rot})">'
    s += f'<ellipse rx="{r}" ry="{r * .86:.1f}" fill="{col}" stroke="{INK}" stroke-width="5"/>'
    for k in (-1, 0, 1):
        s += f'<line x1="{k * r * .42:.1f}" y1="{-r * .86:.1f}" x2="{k * r * .42:.1f}" y2="{-r * .4:.1f}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    return s + '</g>'


def big_paw(x, y, r=44, col='#f2cf9c', pad='#f7b7b4'):
    """paw thrust toward the viewer: palm up, fingers spread (foreshortened)"""
    s = f'<g transform="translate({x} {y})">'
    for a in (-62, -24, 14, 52):                           # fingers
        fx, fy = math.sin(math.radians(a)) * r * .95, -math.cos(math.radians(a)) * r * .95
        s += f'<ellipse cx="{fx:.1f}" cy="{fy:.1f}" rx="{r * .3:.1f}" ry="{r * .36:.1f}" transform="rotate({a} {fx:.1f} {fy:.1f})" fill="{col}" stroke="{INK}" stroke-width="6"/>'
        s += f'<ellipse cx="{fx * .92:.1f}" cy="{fy * .92:.1f}" rx="{r * .13:.1f}" ry="{r * .16:.1f}" transform="rotate({a} {fx:.1f} {fy:.1f})" fill="{pad}"/>'
    s += f'<ellipse rx="{r}" ry="{r * .86:.1f}" fill="{col}" stroke="{INK}" stroke-width="6"/>'
    s += f'<ellipse cy="{r * .08:.1f}" rx="{r * .52:.1f}" ry="{r * .42:.1f}" fill="{pad}"/>'
    return s + '</g>'


def ham(pal='orange', eyes='happy', mouth='open', pose='chest', scarf=None, extra='', cap=False):
    P = PAL[pal]
    uid = f'{pal}{pose}{eyes}'
    g = f'<defs><clipPath id="b{uid}"><path d="{BODY}"/></clipPath></defs>'
    # ears
    for ex in (60, 180):
        g += f'<ellipse cx="{ex}" cy="54" rx="25" ry="23" fill="{P["base"] if pal != "orange" or ex == 180 else P["patch"]}" stroke="{INK}" stroke-width="6"/>'
        g += f'<ellipse cx="{ex}" cy="56" rx="12" ry="11" fill="#f7a8b3"/>'
    # arms behind the body (raised poses)
    back_arms = ''
    front_arms = ''
    c = P['base']
    if pose == 'cheer':      # both paws thrown up: "yay!"
        back_arms += arm(58, 150, 24, 92, c, bend=-10) + arm(182, 150, 216, 92, c, bend=10)
        front_arms += paw(24, 88, 15, -20) + paw(216, 88, 15, 20)
    elif pose == 'wave':
        back_arms += arm(182, 146, 214, 74, c, bend=14)
        front_arms += paw(214, 70, 15, 20) + paw(104, 170, 12, -10) + paw(136, 170, 12, 10)
    elif pose == 'push':     # both paws pushed out to one side (like the orange-white ref)
        front_arms += arm(62, 150, 40, 126, c) + arm(66, 176, 42, 162, c)
        front_arms += paw(36, 120, 14, -60) + paw(38, 158, 14, -80)
    elif pose == 'give':     # offering with both paws forward-right
        front_arms += arm(148, 176, 168, 160, c) + arm(176, 184, 194, 164, c)
        front_arms += paw(170, 156, 14, 10) + paw(196, 160, 14, 30)
    elif pose == 'receive':  # reaching up-left, eager
        back_arms += arm(72, 150, 30, 96, c, bend=-8) + arm(90, 150, 52, 78, c, bend=-8)
        front_arms += paw(28, 92, 14, -30) + paw(50, 74, 14, -20)
    elif pose == 'reach':    # one paw thrust at the viewer (hero pose)
        front_arms += arm(170, 150, 196, 196, c, big=True) + big_paw(196, 206, 50, c)
        front_arms += paw(84, 196, 13, 10)
    else:                    # paws at the chest
        front_arms += paw(102, 168, 13, -12) + paw(138, 168, 13, 12)
    g += back_arms
    # body
    g += f'<path d="{BODY}" fill="{P["base"]}"/>'
    g += f'<g clip-path="url(#b{uid})">'
    g += f'<path d="M170 30 C220 80 222 190 170 240 L240 240 L240 0Z" fill="{P["shade"]}" opacity=".85"/>'   # cel shade, right side
    if P['patch']:
        g += f'<path d="M20 20 L150 20 C150 60 120 70 100 92 C84 108 60 112 30 110Z" fill="{P["patch"]}"/>'
        g += f'<path d="M200 140 C180 160 176 200 196 226 L240 230 L240 130Z" fill="{P["patch"]}"/>'
    g += f'<ellipse cx="120" cy="184" rx="66" ry="54" fill="{P["belly"]}"/>'
    if pal == 'gray':
        for dx in (-16, 0, 16):
            g += f'<path d="M{120 + dx} 40 q{dx * .2:.1f} 12 0 24" fill="none" stroke="{P["stripes"]}" stroke-width="6" stroke-linecap="round"/>'
        g += f'<path d="M38 100 q14 4 22 0 M38 116 q14 4 22 0 M202 100 q-14 4 -22 0 M202 116 q-14 4 -22 0" fill="none" stroke="{P["stripes"]}" stroke-width="5" stroke-linecap="round"/>'
    g += '</g>'
    g += f'<path d="{BODY}" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
    # feet
    for fx in (90, 150):
        g += f'<ellipse cx="{fx}" cy="236" rx="19" ry="10" fill="#f7b7b4" stroke="{INK}" stroke-width="5"/>'
    # face
    if eyes == 'happy':
        g += f'<path d="M80 110 q13 -17 26 0 M134 110 q13 -17 26 0" fill="none" stroke="{INK}" stroke-width="6.5" stroke-linecap="round"/>'
    elif eyes == 'wow':
        for ex in (93, 147):
            g += f'<circle cx="{ex}" cy="104" r="18" fill="#fff" stroke="{INK}" stroke-width="5"/><circle cx="{ex}" cy="106" r="8" fill="{INK}"/><circle cx="{ex + 3}" cy="102" r="3" fill="#fff"/>'
    elif eyes == 'wink':
        g += f'<ellipse cx="93" cy="106" rx="11" ry="14" fill="{INK}"/><circle cx="97" cy="100" r="4.5" fill="#fff"/><circle cx="89" cy="112" r="2" fill="#fff"/>'
        g += f'<path d="M134 108 q13 -14 26 0" fill="none" stroke="{INK}" stroke-width="6.5" stroke-linecap="round"/>'
    else:   # sparkly open eyes
        for ex in (93, 147):
            g += f'<ellipse cx="{ex}" cy="106" rx="12" ry="15" fill="{INK}"/><circle cx="{ex + 4}" cy="100" r="5" fill="#fff"/><circle cx="{ex - 4}" cy="113" r="2.4" fill="#fff"/>'
    g += '<ellipse cx="72" cy="130" rx="13" ry="7.5" fill="#ff98aa" opacity=".6"/><ellipse cx="168" cy="130" rx="13" ry="7.5" fill="#ff98aa" opacity=".6"/>'
    g += f'<path d="M60 124 L30 118 M60 132 L28 136 M180 124 L210 118 M180 132 L212 136" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    g += f'<ellipse cx="120" cy="121" rx="7" ry="5" fill="{INK}"/>'
    if mouth == 'open':
        g += f'<path d="M103 129 Q120 158 137 129 Q120 136 103 129Z" fill="#6b2a2e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
        g += '<ellipse cx="120" cy="145" rx="9" ry="5.5" fill="#ff8d9c"/>'
        g += f'<rect x="115" y="129" width="10" height="8" rx="1.5" fill="#fff" stroke="{INK}" stroke-width="2"/>'
    elif mouth == 'o':
        g += f'<ellipse cx="120" cy="138" rx="7" ry="9" fill="#6b2a2e" stroke="{INK}" stroke-width="4"/>'
    else:
        g += f'<path d="M108 130 q6 8 12 0 q6 8 12 0" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
    if scarf:
        g += f'<path d="M58 150 Q120 176 182 150 L186 170 Q120 198 54 170Z" fill="{scarf}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        g += f'<path d="M150 170 L170 214 L188 206 L168 164Z" fill="{scarf}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
    if cap:
        g += f'<g transform="translate(120 40) rotate(-10)"><path d="M-30 0 L-30 -14 Q0 -24 30 -14 L30 0Z" fill="#1e2a55" stroke="{INK}" stroke-width="5"/>'
        g += f'<path d="M-62 -18 L0 -40 L62 -18 L0 4Z" fill="#23305e" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        g += f'<path d="M40 -12 L46 18" stroke="#ffd23f" stroke-width="4"/><circle cx="46" cy="22" r="5" fill="#ffd23f" stroke="{INK}" stroke-width="3"/></g>'
    g += front_arms + extra
    return g


def save(name, body, vb='-20 -10 280 262'):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{body}</svg>'
    open(f'{OUT}/{name}.svg', 'w').write(s)
    return s

cast = {
    'h-push':    ham('orange', 'happy', 'open', 'push'),
    'h-chest':   ham('tan', 'happy', 'open', 'chest'),
    'h-wow':     ham('gray', 'wow', 'open', 'wave'),
    'h-cheer':   ham('orange', 'happy', 'open', 'cheer'),
    'h-give':    ham('tan', 'wink', 'open', 'give', scarf='#2f6fe0', cap=True),
    'h-receive': ham('orange', 'sparkle', 'open', 'receive'),
    'h-reach':   ham('tan', 'sparkle', 'open', 'reach', scarf='#2f6fe0'),
    'h-gray-cheer': ham('gray', 'happy', 'open', 'cheer'),
}
for k, v in cast.items():
    save(k, v)
print('ok', list(cast))

# ---- hero: paw thrust at the viewer (bigger, fills the frame)
def hero():
    P = PAL['tan']; c = P['base']
    g = ham('tan', 'sparkle', 'open', 'chest', scarf='#2f6fe0')
    # replace chest paws: draw the reaching arm + a huge foreshortened paw on top
    g = g.replace(paw(102, 168, 13, -12) + paw(138, 168, 13, 12), paw(96, 176, 13, -12))
    g += arm(168, 158, 214, 214, c, big=True) + big_paw(226, 236, 70, c)
    return g
save('h-hero', hero(), vb='-20 -10 340 330')

# ---- cartoon clouds (outlined puffs, flat base)
def cloud(puffs, w, h):
    stroke = ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in puffs)
    base = f'<rect x="{puffs[0][0]}" y="{h - 40}" width="{puffs[-1][0] - puffs[0][0]}" height="30" rx="15"/>'
    shade = ''.join(f'<circle cx="{x}" cy="{y + r * .35:.0f}" r="{r * .8:.0f}"/>' for x, y, r in puffs)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
            f'<g fill="#fff" stroke="#29407e" stroke-width="7" stroke-opacity=".55">{stroke}{base}</g>'
            f'<g fill="#fff">{stroke}{base}</g>'
            f'<clipPath id="cc"><g>{stroke}{base}</g></clipPath><g clip-path="url(#cc)" fill="#dbe8ff">{shade}</g>'
            f'<g fill="#fff">' + ''.join(f'<circle cx="{x - r * .12:.0f}" cy="{y - r * .15:.0f}" r="{r * .78:.0f}"/>' for x, y, r in puffs) + '</g></svg>')
open(f'{OUT}/cloud-a.svg', 'w').write(cloud([(60, 90, 42), (120, 62, 56), (190, 70, 50), (250, 96, 38)], 300, 150))
open(f'{OUT}/cloud-b.svg', 'w').write(cloud([(50, 70, 34), (104, 50, 44), (158, 72, 32)], 200, 120))
open(f'{OUT}/cloud-c.svg', 'w').write(cloud([(60, 100, 44), (130, 64, 64), (210, 58, 58), (282, 86, 46), (340, 106, 30)], 380, 170))
print('hero+clouds')
