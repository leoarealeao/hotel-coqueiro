# Planta de situação (prancha A-00): mapa de localização desenhado, esquemático, a partir da imagem aérea anotada
# pelo Leonardo. Gera o SVG e o injeta em index.html entre os marcadores <!--SIT--> ... <!--/SIT-->.
# Coordenadas em pixels da imagem aérea original (norte para cima, ~0,337 m por pixel).
import math, re, sys
M = 53 / 157.0                       # metros por pixel
O = (318, 236); UX = (0.968, -0.248); UZ = (0.248, 0.968)   # canto frente/mar do lote; eixos frente->fundo e mar->terra
def lot(x, z): return (O[0] + (x * UX[0] + z * UZ[0]) / M, O[1] + (x * UX[1] + z * UZ[1]) / M)
X0, Y0, X1, Y1 = -600, -300, 1060, 392   # proporção ~2,4:1, a da moldura da prancha
pts = lambda P: ' '.join(f'{x:.1f},{y:.1f}' for x, y in P)
C = lot(27, 10); D = (-0.64, -0.77); Pp = (0.77, -0.64)       # direção do mar e direção da costa
def coast(off):
    out = []
    for i in range(-22, 26):
        t = i * 70; w = 14 * math.sin(i * 0.9) + 9 * math.sin(i * 0.37 + 1)
        out.append((C[0] + D[0] * (200 / M + off + w) + Pp[0] * t, C[1] + D[1] * (200 / M + off + w) + Pp[1] * t))
    return out
water, sand = coast(0), coast(-125)
sea = water + [(water[-1][0], Y0 - 900), (X0 - 900, Y0 - 900), (X0 - 900, water[0][1])]
beach = water + sand[::-1]
streets = [  # (nome, largura px, pontos, posição do rótulo 0..1)
    ('Av. Antonieta Reis Veloso', 30, [(300, 660), (430, 520), (560, 400), (700, 250), (940, 10), (1150, -200)], 0.6),
    ('R. Vicente Vaz', 20, [(140, 168), (175, 250), (235, 340), (300, 500), (350, 640)], 0.2),
    ('R. Francisco Gomes', 20, [(-420, 520), (-120, 330), (60, 215), (140, 165), (250, 95), (470, -50), (700, -210)], 0.72),
]
trav = [(226, 347), lot(1.5, 20.5)]
L = [lot(*p) for p in [(0, 0), (30, 0), (30, -16.2), (53.9, -16.2), (53.9, 24), (3.2, 24), (3.2, 16), (0, 16)]]
def label(name, P, t, dy=-16, cls='st'):
    n = len(P) - 1; i = min(n - 1, int(t * n)); (xa, ya), (xb, yb) = P[i], P[i + 1]; f = t * n - i
    x, y = xa + (xb - xa) * f, ya + (yb - ya) * f; a = math.degrees(math.atan2(yb - ya, xb - xa))
    if a > 90 or a < -90: a += 180
    return f'<text class="{cls}" transform="translate({x:.0f},{y:.0f}) rotate({a:.1f})" y="{dy}" text-anchor="middle">{name}</text>'
s = [f'<svg id="sitmap" viewBox="{X0} {Y0} {X1 - X0} {Y1 - Y0}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">',
     '<defs><pattern id="hx" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(38)"><line x1="0" y1="0" x2="0" y2="7" stroke="#1c1b18" stroke-width=".8" opacity=".5"/></pattern>',
     '<pattern id="wv" width="46" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(-40)"><path d="M0 8 q11.5 -7 23 0 t23 0" fill="none" stroke="#1c1b18" stroke-width=".7" opacity=".28"/></pattern>',
     '<pattern id="dt" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="3" r=".7" fill="#1c1b18" opacity=".3"/><circle cx="6.5" cy="7" r=".6" fill="#1c1b18" opacity=".22"/></pattern></defs>',
     f'<polygon points="{pts(sea)}" fill="#cfe0dc"/><polygon points="{pts(sea)}" fill="url(#wv)"/>',
     f'<polygon points="{pts(beach)}" fill="#ece2c8"/><polygon points="{pts(beach)}" fill="url(#dt)"/>',
     f'<polyline points="{pts(water)}" fill="none" stroke="#1c1b18" stroke-width="1.6"/>',
     f'<polyline points="{pts(sand)}" fill="none" stroke="#1c1b18" stroke-width=".8" stroke-dasharray="5 5" opacity=".6"/>']
for name, w, P, t in streets:
    s.append(f'<polyline points="{pts(P)}" fill="none" stroke="#1c1b18" stroke-width="{w + 2.4}" stroke-linejoin="round"/><polyline points="{pts(P)}" fill="none" stroke="#fbf8ef" stroke-width="{w}" stroke-linejoin="round"/>')
s.append(f'<polyline points="{pts(trav)}" fill="none" stroke="#1c1b18" stroke-width="15.4"/><polyline points="{pts(trav)}" fill="none" stroke="#fbf8ef" stroke-width="13"/>')
for name, w, P, t in streets: s.append(label(name, P, t, 4))
s += [f'<polygon points="{pts(L)}" fill="#b5542b" opacity=".2"/><polygon points="{pts(L)}" fill="url(#hx)"/><polygon points="{pts(L)}" fill="none" stroke="#b5542b" stroke-width="3.2" stroke-linejoin="miter"/>']
cx, cy = lot(27, 9)
s.append(f'<g transform="translate({cx:.0f},{cy:.0f}) rotate(-14.4)"><text class="lt" text-anchor="middle" y="-2">o terreno</text><text class="mono" style="font-size:10px" text-anchor="middle" y="15">EM L · 1.633 m²</text></g>')
# distância ao mar
a = lot(30, -16.2); b = (a[0] + D[0] * (200 / M - 62), a[1] + D[1] * (200 / M - 62))
s.append(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="#b5542b" stroke-width="1.6" stroke-dasharray="7 5"/><circle cx="{b[0]:.0f}" cy="{b[1]:.0f}" r="4" fill="#b5542b"/>')
mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
s.append(f'<g transform="translate({mx + 14:.0f},{my:.0f}) rotate(50.3)"><text class="mono acc" text-anchor="middle">~200 m ATÉ O MAR</text></g>')
bx, by = C[0] + D[0] * (200 / M - 62), C[1] + D[1] * (200 / M - 62)
s.append(f'<g transform="translate({bx - 215:.0f},{by + 200:.0f}) rotate(-39.7)"><text class="big" text-anchor="middle">Praia do Coqueiro</text></g>')
s.append(f'<g transform="translate({bx - 420:.0f},{by + 90:.0f}) rotate(-39.7)"><text class="sea" text-anchor="middle">oceano Atlântico</text></g>')
# notas
tx, ty = trav[0]
s.append(f'<text class="mono" x="{tx - 40:.0f}" y="{ty + 2:.0f}" text-anchor="end">TRAVESSA VICENTE VAZ</text><text class="mono" x="{tx - 40:.0f}" y="{ty + 17:.0f}" text-anchor="end">SEM SAÍDA · ENTRADA DO TERRENO</text><line x1="{tx - 34:.0f}" y1="{ty + 2:.0f}" x2="{tx + 26:.0f}" y2="{ty - 10:.0f}" stroke="#1c1b18" stroke-width="1"/>')
qx, qy = lot(18, -34)
s.append(f'<g transform="translate({qx:.0f},{qy:.0f}) rotate(-14.4)"><text class="mono dim" text-anchor="middle">QUARTEIRÃO DE CASAS</text><text class="mono dim" text-anchor="middle" y="13">~6 m MAIS ALTO</text></g>')
# norte e escala
s.append(f'<g transform="translate({X1 - 80},{Y1 - 70})"><circle r="30" fill="#f3efe4" stroke="#1c1b18" stroke-width="1.2"/><path d="M0 -24 L8 14 L0 7 L-8 14 Z" fill="#1c1b18"/><text class="mono" text-anchor="middle" y="-36">N</text></g>')
w100 = 100 / M
s.append(f'<g transform="translate({X0 + 50},{Y1 - 45})"><rect x="-14" y="-26" width="{w100 + 28:.0f}" height="46" fill="#f3efe4" opacity=".9"/><line x1="0" y1="0" x2="{w100:.0f}" y2="0" stroke="#1c1b18" stroke-width="2"/>' +
         ''.join(f'<line x1="{i * w100 / 4:.0f}" y1="-6" x2="{i * w100 / 4:.0f}" y2="0" stroke="#1c1b18" stroke-width="1.4"/>' for i in range(5)) +
         f'<text class="mono" x="0" y="-11">0</text><text class="mono" x="{w100 / 2:.0f}" y="-11" text-anchor="middle">50</text><text class="mono" x="{w100:.0f}" y="-11" text-anchor="end">100 m</text><text class="mono dim" x="0" y="14">ESCALA APROXIMADA</text></g>')
s.append('</svg>')
svg = '\n'.join(s)
html = open('index.html', encoding='utf8').read()
html, n = re.subn(r'<!--SIT-->.*?<!--/SIT-->', lambda m: '<!--SIT-->' + svg + '<!--/SIT-->', html, flags=re.S)
assert n == 1, 'marcadores <!--SIT--> não encontrados em index.html'
open('index.html', 'w', encoding='utf8').write(html)
print('ok', len(svg))
