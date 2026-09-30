# Six hamster emoji drawn as vector art in the mascots' palette: ink outline, flat colour + one cel-shade tone, glossy eyes.
INK='#1b1540'
PAL={'o':dict(base='#fffaf3',shade='#f1e3d6',patch='#f6a04b',patchS='#e08935',ear='#ffc9c4'),
     't':dict(base='#f5cf9c',shade='#e6b67c',patch=None,muz='#fff4e2',ear='#f7b3ab'),
     'g':dict(base='#c3c3cf',shade='#a9a9b8',patch=None,muz='#f7f7fb',ear='#f4b7c0',stripe='#8d8d9f')}
def head(cx,cy,s,k,eyes='open',mouth='smile',rot=0):
    p=PAL[k]; w=58*s; h=58*s; o=[]
    o.append(f'<g transform="rotate({rot} {cx} {cy})">')
    # ears
    for sx in (-1,1):
        ex=cx+sx*40*s; ey=cy-40*s
        o.append(f'<ellipse cx="{ex}" cy="{ey}" rx="{15*s}" ry="{14*s}" fill="{p["base"] if not (k=="o" and sx<0) else p["patch"]}" stroke="{INK}" stroke-width="{4.5*s}"/>')
        o.append(f'<ellipse cx="{ex}" cy="{ey+2*s}" rx="{8*s}" ry="{7.5*s}" fill="{p["ear"]}"/>')
    # head
    o.append(f'<path d="M{cx-w} {cy+6*s} C{cx-w} {cy-h*1.05} {cx+w} {cy-h*1.05} {cx+w} {cy+6*s} C{cx+w} {cy+h*.95} {cx-w} {cy+h*.95} {cx-w} {cy+6*s}Z" fill="{p["base"]}"/>')
    o.append(f'<clipPath id="hc{cx}{cy}{k}"><path d="M{cx-w} {cy+6*s} C{cx-w} {cy-h*1.05} {cx+w} {cy-h*1.05} {cx+w} {cy+6*s} C{cx+w} {cy+h*.95} {cx-w} {cy+h*.95} {cx-w} {cy+6*s}Z"/></clipPath>')
    o.append(f'<g clip-path="url(#hc{cx}{cy}{k})">')
    o.append(f'<ellipse cx="{cx+w*.35}" cy="{cy+h*.7}" rx="{w*1.1}" ry="{h*.5}" fill="{p["shade"]}" opacity=".9"/>')
    if k=='o':
        o.append(f'<path d="M{cx-w-5} {cy-h} C{cx-w*.2} {cy-h*1.1} {cx-w*.05} {cy-h*.3} {cx-w*.35} {cy+h*.05} C{cx-w*.7} {cy+h*.2} {cx-w} {cy} {cx-w-5} {cy}Z" fill="{p["patch"]}"/>')
    if k=='t':
        o.append(f'<ellipse cx="{cx}" cy="{cy+h*.42}" rx="{w*.62}" ry="{h*.42}" fill="{p["muz"]}"/>')
    if k=='g':
        o.append(f'<ellipse cx="{cx}" cy="{cy+h*.45}" rx="{w*.6}" ry="{h*.42}" fill="{p["muz"]}"/>')
        for dx in (-14,0,14):
            o.append(f'<path d="M{cx+dx*s} {cy-h*.95} q{2*s} {10*s} 0 {18*s}" stroke="{p["stripe"]}" stroke-width="{5*s}" fill="none" stroke-linecap="round"/>')
    o.append('</g>')
    o.append(f'<path d="M{cx-w} {cy+6*s} C{cx-w} {cy-h*1.05} {cx+w} {cy-h*1.05} {cx+w} {cy+6*s} C{cx+w} {cy+h*.95} {cx-w} {cy+h*.95} {cx-w} {cy+6*s}Z" fill="none" stroke="{INK}" stroke-width="{5*s}"/>')
    # cheeks
    for sx in (-1,1): o.append(f'<ellipse cx="{cx+sx*36*s}" cy="{cy+14*s}" rx="{8*s}" ry="{5*s}" fill="#ff8fa3" opacity=".55"/>')
    # eyes
    for sx in (-1,1):
        ex=cx+sx*21*s; ey=cy-2*s
        if eyes=='happy':
            o.append(f'<path d="M{ex-9*s} {ey+3*s} Q{ex} {ey-9*s} {ex+9*s} {ey+3*s}" fill="none" stroke="{INK}" stroke-width="{4.5*s}" stroke-linecap="round"/>')
        elif eyes=='sparkle':
            o.append(f'<ellipse cx="{ex}" cy="{ey}" rx="{10*s}" ry="{11*s}" fill="{INK}"/>')
            o.append(f'<path d="M{ex} {ey-7*s} l{2.2*s} {5*s} l{5*s} {2*s} l{-5*s} {2*s} l{-2.2*s} {5*s} l{-2.2*s} {-5*s} l{-5*s} {-2*s} l{5*s} {-2*s}Z" fill="#ffe27a"/>')
            o.append(f'<circle cx="{ex-4*s}" cy="{ey-5*s}" r="{2.2*s}" fill="#fff"/>')
        elif eyes=='wink' and sx>0:
            o.append(f'<path d="M{ex-9*s} {ey} Q{ex} {ey+6*s} {ex+9*s} {ey}" fill="none" stroke="{INK}" stroke-width="{4.5*s}" stroke-linecap="round"/>')
        elif eyes=='determined':
            o.append(f'<ellipse cx="{ex}" cy="{ey+1*s}" rx="{7.5*s}" ry="{8.5*s}" fill="{INK}"/>')
            o.append(f'<circle cx="{ex-2.5*s}" cy="{ey-2*s}" r="{2.6*s}" fill="#fff"/>')
            o.append(f'<path d="M{ex-sx*10*s} {ey-9*s} L{ex+sx*9*s} {ey-15*s}" stroke="{INK}" stroke-width="{4.5*s}" stroke-linecap="round"/>')
        else:
            o.append(f'<ellipse cx="{ex}" cy="{ey}" rx="{9*s}" ry="{10*s}" fill="{INK}"/>')
            o.append(f'<circle cx="{ex-3.5*s}" cy="{ey-4*s}" r="{3.4*s}" fill="#fff"/><circle cx="{ex+3.5*s}" cy="{ey+4*s}" r="{1.6*s}" fill="#fff"/>')
    # nose + mouth
    o.append(f'<ellipse cx="{cx}" cy="{cy+10*s}" rx="{4.5*s}" ry="{3.2*s}" fill="#f47a93" stroke="{INK}" stroke-width="{2*s}"/>')
    if mouth=='open':
        o.append(f'<path d="M{cx-10*s} {cy+16*s} Q{cx} {cy+36*s} {cx+10*s} {cy+16*s} Z" fill="#d9405e" stroke="{INK}" stroke-width="{3.5*s}" stroke-linejoin="round"/>')
        o.append(f'<path d="M{cx-5*s} {cy+27*s} Q{cx} {cy+22*s} {cx+5*s} {cy+27*s}" fill="#ff9fb1"/>')
        o.append(f'<rect x="{cx-4*s}" y="{cy+16*s}" width="{8*s}" height="{5*s}" rx="{1*s}" fill="#fff" stroke="{INK}" stroke-width="{1.6*s}"/>')
    elif mouth=='smile':
        o.append(f'<path d="M{cx-9*s} {cy+15*s} Q{cx-4.5*s} {cy+21*s} {cx} {cy+15*s} Q{cx+4.5*s} {cy+21*s} {cx+9*s} {cy+15*s}" fill="none" stroke="{INK}" stroke-width="{3.5*s}" stroke-linecap="round"/>')
    elif mouth=='o':
        o.append(f'<ellipse cx="{cx}" cy="{cy+21*s}" rx="{5*s}" ry="{6*s}" fill="#d9405e" stroke="{INK}" stroke-width="{3*s}"/>')
    # whiskers
    for sx in (-1,1):
        for dy in (0,6):
            o.append(f'<path d="M{cx+sx*46*s} {cy+(10+dy)*s} l{sx*14*s} {(-2+dy*.6)*s}" stroke="{INK}" stroke-width="{2*s}" stroke-linecap="round"/>')
    o.append('</g>')
    return ''.join(o)
def paw(x,y,s,k,rot=0):
    p=PAL[k]; c=p['base'] if k!='o' else p['base']
    return f'<g transform="rotate({rot} {x} {y})"><ellipse cx="{x}" cy="{y}" rx="{11*s}" ry="{12*s}" fill="{c}" stroke="{INK}" stroke-width="{4*s}"/><path d="M{x-4*s} {y-11*s} v{6*s} M{x+4*s} {y-11*s} v{6*s}" stroke="{INK}" stroke-width="{2.6*s}" stroke-linecap="round"/></g>'
def spark(x,y,r,c='#ffe27a'):
    return f'<path d="M{x} {y-r} L{x+r*.28} {y-r*.28} L{x+r} {y} L{x+r*.28} {y+r*.28} L{x} {y+r} L{x-r*.28} {y+r*.28} L{x-r} {y} L{x-r*.28} {y-r*.28}Z" fill="{c}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
def disc(bg,inner):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="400" height="400">
<defs><clipPath id="d"><circle cx="100" cy="100" r="90"/></clipPath></defs>
<circle cx="100" cy="100" r="96" fill="{INK}"/><circle cx="100" cy="100" r="92" fill="#fff"/><circle cx="100" cy="100" r="86" fill="{bg}"/>
<g clip-path="url(#d)"><ellipse cx="100" cy="190" rx="110" ry="60" fill="#000" opacity=".1"/>{inner}</g></svg>'''
E=[]
# 1 portfolio: gray holds up a blue folder with a star
E.append(disc('#ff8a3d', head(100,82,.95,'g',eyes='sparkle',mouth='open')+
  '<g transform="rotate(-8 100 150)"><rect x="52" y="122" width="96" height="70" rx="8" fill="#2f6fe0" stroke="#1b1540" stroke-width="5"/><path d="M52 132 h36 l8 -10 h44" fill="none" stroke="#1b1540" stroke-width="4"/><rect x="58" y="136" width="84" height="8" rx="3" fill="#5b95f5"/>'+spark(100,166,16)+'</g>'+paw(52,140,.9,'g',-20)+paw(148,134,.9,'g',20)+spark(34,48,9,'#fff')+spark(166,40,7,'#fff')))
# 2 mentor: orange with round glasses, clipboard + thumbs up
g=head(96,88,.95,'o',eyes='wink',mouth='smile')+'<g fill="none" stroke="#1b1540" stroke-width="4.5"><circle cx="76" cy="86" r="14" fill="#ffffff" fill-opacity=".25"/><circle cx="116" cy="86" r="14" fill="#ffffff" fill-opacity=".25"/><path d="M90 86 h12"/></g>'
E.append(disc('#4d9fff', g+'<g transform="rotate(10 150 150)"><rect x="126" y="118" width="46" height="60" rx="5" fill="#b07a4a" stroke="#1b1540" stroke-width="4.5"/><rect x="132" y="128" width="34" height="44" rx="3" fill="#fffaf0"/><rect x="140" y="113" width="18" height="10" rx="3" fill="#c7d0e2" stroke="#1b1540" stroke-width="3.5"/><path d="M137 138 h24 M137 148 h24 M137 158 h16" stroke="#8a8fb0" stroke-width="3.5" stroke-linecap="round"/><path d="M137 138 l4 4 l7 -9" stroke="#2fd08b" stroke-width="4" fill="none" stroke-linecap="round"/></g>'+
  '<g transform="translate(46 150) rotate(-12)"><rect x="-14" y="-6" width="28" height="30" rx="10" fill="#fffaf3" stroke="#1b1540" stroke-width="4.5"/><rect x="-6" y="-28" width="12" height="26" rx="6" fill="#fffaf3" stroke="#1b1540" stroke-width="4.5"/></g>'+spark(30,48,9,'#fff')))
# 3 AI: gray high-fives a little robot
robot='<g transform="translate(148 118)"><path d="M0 -44 v-10" stroke="#1b1540" stroke-width="4"/><circle cx="0" cy="-58" r="6" fill="#ffd23f" stroke="#1b1540" stroke-width="3.5"/><rect x="-30" y="-44" width="60" height="50" rx="18" fill="#f4f7ff" stroke="#1b1540" stroke-width="5"/><rect x="-21" y="-34" width="42" height="28" rx="10" fill="#2a3a8a"/><circle cx="-9" cy="-21" r="5" fill="#8ff0ff"/><circle cx="9" cy="-21" r="5" fill="#8ff0ff"/><path d="M-6 -12 q6 5 12 0" stroke="#8ff0ff" stroke-width="3" fill="none" stroke-linecap="round"/><rect x="-24" y="10" width="48" height="40" rx="12" fill="#f4f7ff" stroke="#1b1540" stroke-width="5"/><circle cx="0" cy="28" r="7" fill="#9b7bff" stroke="#1b1540" stroke-width="3"/></g>'
E.append(disc('#9b7bff', head(72,100,.82,'g',eyes='open',mouth='open',rot=-6)+robot+paw(112,62,.85,'g',25)+'<g transform="translate(126 50)"><circle r="11" fill="#f4f7ff" stroke="#1b1540" stroke-width="4"/></g>'+spark(119,40,11)+spark(96,34,6,'#fff')))
# 4 not alone: three heads squeezed together
E.append(disc('#2fd08b', head(56,112,.58,'o',eyes='happy',mouth='open',rot=-10)+head(144,112,.58,'g',eyes='happy',mouth='open',rot=10)+head(100,98,.64,'t',eyes='happy',mouth='open')+
  '<path d="M100 40 c-6 -10 -20 -4 -14 6 l14 12 l14 -12 c6 -10 -8 -16 -14 -6z" fill="#ff6b8a" stroke="#1b1540" stroke-width="4" stroke-linejoin="round"/>'+paw(26,150,.8,'o',-10)+paw(174,150,.8,'g',10)))
# 5 from zero: tan with a sprout in a pot
E.append(disc('#ff6b8a', head(100,80,.92,'t',eyes='sparkle',mouth='smile')+
  '<path d="M68 142 h64 l-8 46 h-48z" fill="#e0703a" stroke="#1b1540" stroke-width="5" stroke-linejoin="round"/><rect x="62" y="132" width="76" height="16" rx="6" fill="#f08a4f" stroke="#1b1540" stroke-width="5"/>'+
  '<path d="M100 134 c0 -12 0 -18 0 -26" stroke="#2f7d3e" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M100 116 c-4 -14 -22 -16 -26 -8 c8 8 20 10 26 8z" fill="#6cc36b" stroke="#1b1540" stroke-width="4" stroke-linejoin="round"/><path d="M100 110 c4 -14 22 -18 27 -9 c-8 8 -21 11 -27 9z" fill="#6cc36b" stroke="#1b1540" stroke-width="4" stroke-linejoin="round"/>'+
  paw(56,146,.9,'t',-15)+paw(144,146,.9,'t',15)+spark(40,44,8,'#fff')+spark(162,52,7,'#ffe27a')))
# 6 real stage: orange with a mic under a spotlight
E.append(disc('#38b6e8', '<path d="M100 -10 L40 200 H160Z" fill="#fff6c8" opacity=".55"/>'+'<rect x="0" y="166" width="200" height="40" fill="#b07a4a" stroke="#1b1540" stroke-width="5"/><path d="M0 178 h200" stroke="#8a5a34" stroke-width="3"/>'+
  head(96,92,.9,'o',eyes='determined',mouth='open')+
  '<g transform="rotate(-25 142 130)"><rect x="136" y="124" width="12" height="44" rx="5" fill="#2a2f45" stroke="#1b1540" stroke-width="4"/><circle cx="142" cy="120" r="13" fill="#9aa3c0" stroke="#1b1540" stroke-width="4.5"/><path d="M133 116 h18 M133 122 h18" stroke="#6a7290" stroke-width="2.5"/></g>'+paw(134,142,.85,'o',10)+paw(40,68,.85,'o',-30)+spark(34,34,10)+spark(170,40,8,'#fff')+spark(176,96,6,'#ffe27a')))
for i,svg in enumerate(E,1): open(f'e{i}.svg','w').write(svg)
open('all.html','w').write('<body style="margin:0;background:#15172e;display:flex;gap:16px;padding:16px">'+''.join(f'<img src="e{i}.svg" width="200">' for i in range(1,7))+'</body>')
