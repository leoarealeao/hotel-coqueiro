# Planta de situação (prancha A-00): mapa da Praia do Coqueiro desenhado a partir do OpenStreetMap
# (tools/osm_coqueiro.json, © OpenStreetMap contributors, ODbL). Gera o SVG e o injeta em index.html entre
# <!--SIT--> e <!--/SIT-->. O SVG fica em metros, com a origem no centro da planta do térreo (o ponto para onde o
# zoom converge); js/main.js anima viewBox, giro e marcadores.
import json, math, re
D = json.load(open('tools/osm_coqueiro.json', encoding='utf8'))
# o terreno: frente na ponta da Travessa Vicente Vaz, lado norte paralelo à R. Francisco Gomes
A = math.radians(30.9); UX = (math.cos(A), math.sin(A)); UZ = (math.sin(A), -math.cos(A))   # frente->fundo, mar->terra (x leste, y norte)
E = (-70, -33)                                                                                # ponta da travessa (OSM)
O = (E[0] - 3.2 * UX[0] - 20 * UZ[0], E[1] - 3.2 * UX[1] - 20 * UZ[1])                         # canto frente/mar do lote
def lotm(x, z): return (O[0] + x * UX[0] + z * UZ[0], O[1] + x * UX[1] + z * UZ[1])
CC = lotm(26.5, 3.4)                                                                          # centro da planta do térreo
def S(p): return (p[0] - CC[0], -(p[1] - CC[1]))                                              # -> SVG (y para baixo)
pts = lambda P: ' '.join(f'{x:.1f},{y:.1f}' for x, y in P)
W = {'h:primary': 11, 'h:primary_link': 8, 'h:tertiary': 9, 'h:unclassified': 7, 'h:residential': 6, 'h:living_street': 5, 'h:service': 4, 'h:track': 3.5}
ways = D['ways']
coast = [w['p'] for w in ways if w['k'] == 'n:coastline']
coast.sort(key=lambda P: -max(p[0] for p in P))
chain = [S(p) for P in coast for p in (P if P[0][0] > P[-1][0] else P[::-1])]
sea = chain + [(chain[-1][0], -9000), (chain[0][0], -9000)]
s = ['<svg id="sitmap" viewBox="-1180 -500 2160 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">',
     '<defs><pattern id="hx" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(38)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="#b5542b" stroke-width=".35" opacity=".7"/></pattern>',
     '<pattern id="wv" width="56" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(-20)"><path d="M0 10 q14 -8 28 0 t28 0" fill="none" stroke="#1c1b18" stroke-width="1" opacity=".22"/></pattern></defs>',
     '<g id="sitrot">',
     f'<polyline points="{pts(chain)}" fill="none" stroke="#ece2c8" stroke-width="150" stroke-linejoin="round"/>',
     f'<polygon points="{pts(sea)}" fill="#cfe0dc"/><polygon points="{pts(sea)}" fill="url(#wv)"/>',
     f'<polyline points="{pts(chain)}" fill="none" stroke="#1c1b18" stroke-width="1.5" vector-effect="non-scaling-stroke"/>']
for w in ways:
    if w['k'] == 'n:water': s.append(f'<polygon points="{pts([S(p) for p in w["p"]])}" fill="#cfe0dc" stroke="#1c1b18" stroke-width=".7" vector-effect="non-scaling-stroke" opacity=".9"/>')
    if w['k'].startswith('w:'): s.append(f'<polyline points="{pts([S(p) for p in w["p"]])}" fill="none" stroke="#9dbdb7" stroke-width="3"/>')
roads = [w for w in ways if w['k'] in W]
s.append('<g fill="none" stroke="#1c1b18" stroke-linejoin="round" stroke-linecap="round" opacity=".8">' + ''.join(f'<polyline points="{pts([S(p) for p in w["p"]])}" stroke-width="{W[w["k"]] + 1.6}"/>' for w in roads) + '</g>')
s.append('<g fill="none" stroke="#fbf8ef" stroke-linejoin="round" stroke-linecap="round">' + ''.join(f'<polyline points="{pts([S(p) for p in w["p"]])}" stroke-width="{W[w["k"]]}"/>' for w in roads) + '</g>')
L = [S(lotm(*p)) for p in [(0, 0), (30, 0), (30, -16.2), (53.9, -16.2), (53.9, 24), (3.2, 24), (3.2, 16), (0, 16)]]
s.append(f'<g id="sitlot"><polygon points="{pts(L)}" fill="#f3efe4"/><polygon points="{pts(L)}" fill="#b5542b" opacity=".16"/><polygon points="{pts(L)}" fill="url(#hx)"/><polygon points="{pts(L)}" fill="none" stroke="#b5542b" stroke-width="2.6" vector-effect="non-scaling-stroke"/></g>')
# rótulos de rua: tamanho constante na tela, giram com o mapa ("al" = ao longo da rua). data-a/b = trecho do zoom em que aparecem
def along(name, frag, a, b, cls='st', idx=None, dy=4, near=None):
    # o trecho (com pelo menos 25 m) mais perto do terreno, para o nome aparecer também no zoom
    segs = [(S(w['p'][i]), S(w['p'][i + 1])) for w in roads if frag in w['n'] for i in range(len(w['p']) - 1)]
    segs = [g for g in segs if math.dist(*g) >= 25] or segs
    (xa, ya), (xb, yb) = min(segs, key=lambda g: math.hypot((g[0][0] + g[1][0]) / 2 - (S(near)[0] if near else 0), (g[0][1] + g[1][1]) / 2 - (S(near)[1] if near else 0))); ang = math.degrees(math.atan2(yb - ya, xb - xa))
    if ang > 60 or ang < -120: ang += 180
    return f'<g class="mk al" data-x="{(xa + xb) / 2:.1f}" data-y="{(ya + yb) / 2:.1f}" data-r="{ang:.1f}" data-a="{a}" data-b="{b}"><text class="{cls}" text-anchor="middle" y="{dy}">{name}</text></g>'
s += [along('Av. Antonieta Reis Veloso', 'Antonieta', .3, 2), along('R. Francisco Gomes', 'Francisco Gomes', .45, 2), along('R. Vicente Vaz', 'Rua Vicente Vaz', .55, 2),
      along('Travessa Vicente Vaz · sem saída', 'Travessa', .6, 2), along('R. Miguel de Paulo', 'Miguel de Paulo', .45, 2), along('R. José Galeno', 'Galeno', .3, .8), along('Av. Barramares', 'Barramares', -1, .7)]
def lab(x, y, r, cls, txt, a, b): return f'<g class="mk al" data-x="{x:.0f}" data-y="{y:.0f}" data-r="{r}" data-a="{a}" data-b="{b}"><text class="{cls}" text-anchor="middle">{txt}</text></g>'
s += [lab(*S((-760, 395)), 0, 'big', 'Praia do Coqueiro', -1, .4), lab(*S((-760, 455)), 0, 'sea', 'oceano Atlântico', -1, .35), along('PI-116', 'Avenida Piauí', -1, .5, near=(-1100, -190))]
# o caminho de quem chega de carro pelo oeste: PI-116 -> Balão do Coqueiro -> Av. Antonieta Reis Veloso -> R. Vicente Vaz -> travessa
def way(pred): return next(w['p'] for w in ways if pred(w))
pi = [p for p in way(lambda w: w['k'] == 'h:primary' and len(w['p']) > 50 and w['p'][-1][0] < 0) if p[0] > -1900]
BAL = (-459.5, -478.4)
arc = [(BAL[0] + 17 * math.cos(math.radians(a)), BAL[1] + 17 * math.sin(math.radians(a))) for a in range(160, 395, 15)]  # contorna o balão no sentido da mão
av = way(lambda w: 'Antonieta' in w['n'] and any(abs(p[0] + 65) < 2 and abs(p[1] + 146) < 2 for p in w['p']))
av = av if av[0][0] < av[-1][0] else av[::-1]
av = av[:next(i for i, p in enumerate(av) if abs(p[0] + 65) < 2 and abs(p[1] + 146) < 2) + 1]
route = [S(p) for p in pi + arc + av + [(-109, -54), E]]
s.append(f'<polyline id="sitroute" points="{pts(route)}" fill="none" stroke="#b5542b" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" stroke-dasharray="0 99999"/>')
s.append('<g id="sitcar"><rect x="-15" y="-8" width="30" height="16" rx="5" fill="#b5542b" stroke="#1c1b18" stroke-width="1.5"/><rect x="-6" y="-6" width="13" height="12" rx="2.5" fill="#1c1b18" opacity=".85"/><rect x="11" y="-6" width="3" height="4" rx="1" fill="#fff3d6"/><rect x="11" y="2" width="3" height="4" rx="1" fill="#fff3d6"/></g>')
s.append('</g>')   # fim do grupo que gira
# marcadores: sempre em pé ("up"), ponto + etiqueta
def pin(p, txt, sub, a, b, side=1, main=False):
    x, y = S(p); w = max(len(txt) * 7.4, len(sub) * 6.2) + 18; x0 = 14 if side > 0 else -14 - w
    c = 'pin main' if main else 'pin'
    return (f'<g class="mk up {c}" data-x="{x:.1f}" data-y="{y:.1f}" data-a="{a}" data-b="{b}"><circle r="{11 if main else 8}" class="halo"/><circle r="{5.5 if main else 4}" class="dot"/>'
            f'<rect x="{x0:.0f}" y="-17" width="{w:.0f}" height="{34 if sub else 22}" class="tag"/><text x="{x0 + 9:.0f}" y="-2" class="t1">{txt}</text>' + (f'<text x="{x0 + 9:.0f}" y="11" class="t2">{sub}</text>' if sub else '') + '</g>')
# Aimberê: terreno grande, marcador no meio entre a R. Francisco Gomes e a faixa de areia. Praça: coordenada do Google Maps passada pelo Leonardo (-2.906498, -41.574703)
s += [pin((-250, 62), 'Aimberê Eco Resort', 'HOTEL', -1, .62, -1), pin((206, 309), 'Alô Brasil', 'RESTAURANTE NA PRAIA', -1, .62, -1),
      pin((360.5, 292.5), 'Praça do Coqueiro', 'PEDRO JOSÉ RODRIGUES', -1, .62), pin((-459.5, -478.4), 'Balão do Coqueiro', 'ENTRADA PELA PI-116', -1, .62, -1),
      pin((-277.7, -314.4), 'Sorveteria Araújo', 'AV. ANTONIETA REIS VELOSO', -1, .62, -1), pin(CC, 'o terreno', 'EM L · 1.633 m²', -1, .8, 1, True)]
s.append('</svg>')
svg = '\n'.join(s)
html = open('index.html', encoding='utf8').read()
html, n = re.subn(r'<!--SIT-->.*?<!--/SIT-->', lambda m: '<!--SIT-->' + svg + '<!--/SIT-->', html, flags=re.S)
assert n == 1, 'marcadores <!--SIT--> não encontrados em index.html'
open('index.html', 'w', encoding='utf8').write(html)
d = min(math.dist(lotm(40, -16.2), (p[0] + CC[0], CC[1] - p[1])) for p in chain)
print('ok', len(svg), 'centro', [round(v, 1) for v in CC], 'costa mais próxima (vértice) ~', round(d), 'm')
