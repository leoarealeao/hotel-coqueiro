# Hotel Praia do Coqueiro — contexto do projeto

Estudo preliminar de um pequeno condomínio de apartamentos de temporada num terreno do Leonardo na Praia do Coqueiro, Luís Correia (PI), ~200 m do mar. Não é anúncio de venda: é para mostrar o que pode ser construído ali. Rodapé obrigatório em toda peça: "Estudo preliminar · imagens ilustrativas".

Leonardo responde em português, quer respostas curtas e objetivas, é visual, e quer conferir resultados por imagem/vídeo. Sempre revise visualmente (screenshot) o que gerar antes de entregar.

## Fonte da verdade da geometria
- `referencia/modelo/hotel.glb` — o modelo 3D completo (exportado do three.js, y para cima, metros). É ESTE modelo que deve ser usado. Não redesenhe nada do zero.
- `referencia/modelo/maquete_navegavel.html` — a maquete original em three.js r128 que gerou o GLB (código das funções `aptoA`, `aptoB`, `interiorApto`, `palm`, recepção etc.). Use para entender a lógica, não precisa reaproveitar o código.
- `referencia/modelo/cameras.json` — 12 câmeras aprovadas: `[nome, [posição x,y,z], [alvo x,y,z], fov_vertical]` em coordenadas do GLB.
- `referencia/modelo/materiais_do_glb.txt` — cada material do GLB, com a cor hex original, textura (Image_N) e um exemplo de objeto. Use a cor hex para reconhecer o material (ex.: `#f4f1ea` = reboco, `#8a6f4d` = tronco de coqueiro, Image_6 = palha do telhado, Image_0 = areia, Image_1 = gramado, Image_2 = cimento queimado da recepção, Image_3 = madeira escura, `#35c3c9` = água da piscina, alpha 0.22 = vidro).
- `referencia/plantas/` — planta numerada (térreo e superior) e plantas tipo mobiliadas.
- `referencia/tecnicas/flat-to-3d/` — sete técnicas de desenho que vira 3D com scroll (MIT, Samnang Aing). Pode reaproveitar mantendo o LICENSE.
- `referencia/blender/` — scripts que já geram uma versão realista no Blender (materiais procedurais, coqueiros com folíolos, franja de palha, grama em folhas, carros). Úteis como receita de formas e cores.

## Coordenadas (metros)
- x: frente (0, estacionamento/acesso) → fundo (53). z: lado do mar (0) → lado de terra (23). y para cima.
- Terreno ~53 × 23 m (~1.200 m²). Frente com "dente": muro em x=0 para z 0–15,6 e recuado para x=2 em z 15,6–23 (entrada de carro).

## Programa
- Estacionamento de areia compactada na frente (x 0–~16), 6 vagas.
- Bloco A (lado do mar, z 1,2–8,7): apartamentos de 2 quartos (~50 m²). Térreo 1–4, superior 8–11.
- Bloco B (lado de terra, z 17,3–21,8): apartamentos de 1 quarto (~35 m²). Térreo: recepção aberta, 5, 6, 7. Superior 12–15.
- Total: 15 apartamentos + recepção. Módulos em x = 21, 29,25, 36, 44,25 (largura 6,75 m), escadas entre módulos.
- Pátio central gramado (z 10,2–15,8) com piscina orgânica única (~15,5 × até 3 m), espreguiçadeiras no fundo, pufes redondos de palha e mesinhas na frente. Ducha no muro do fundo.
- Varandas de 1,5 m voltadas para a piscina, com redes de tecido cru. Térreo entra pela varanda; superior entra pelo patamar da escada.
- Recepção: térreo aberto sob o apto 12, pilares roliços de madeira com base de pedra, piso cimento queimado, tapete de palha, sofá de madeira com almofadas de linho, poltronas de rattan, mesa de centro redonda, balcão ripado, pendentes de palha, salinha de apoio.

## Materiais e estética (aprovados)
- Paredes brancas de reboco; telhados de palha de piaçava (beiral 1,0 m no pátio, 0,8 m nas pontas, 0,6 m no fundo); madeira escura em portas, janelas, pilares e estrutura.
- Guarda-corpos e divisórias de privacidade de VARAS ROLIÇAS de madeira na vertical (também nas pontas do bloco A).
- Coqueiros (6 no terreno) e, fora dos muros, um coqueiral contínuo com vegetação baixa de restinga — moldura que foi aprovada.
- Luz de fim de tarde, céu azul suave com poucas nuvens, sol baixo e quente. Arandelas de cerâmica, balizadores baixos no gramado, postes de madeira no estacionamento, tudo com luz quente.

## Já rejeitado pelo Leonardo (não repetir)
- Caminhos/lajotas de pedra por todo o pátio ("muito xiita") — chão é gramado.
- Pilares de concreto na recepção — são de madeira roliça.
- Vizinhança de casinhas soltas na areia; deserto; mata amazônica densa.
- IA generativa redesenhando a geometria. Aqui a geometria é sempre a do GLB.

## Pendências conhecidas do projeto (não resolver agora, só não piorar)
- Patamar da escada do bloco B estreito (1,5 m); pilares de madeira carregando apartamento; medidas estimadas (terreno levemente trapezoidal).
