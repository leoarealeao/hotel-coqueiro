# Prompt para colar no Claude Code (primeira mensagem)

Copie tudo abaixo da linha e cole na sessão nova.
Quer a outra abertura (planta que vira prédio, estilo Casa Serra)? Troque a linha "TÉCNICA BASE" por: `TÉCNICA BASE: planta baixa que ganha volume (estilo Casa Serra)`.

---

Leia o CLAUDE.md e a pasta `referencia/` antes de qualquer coisa. Em `referencia/tecnicas/flat-to-3d/` estão sete técnicas prontas de "desenho plano que vira 3D com o scroll", com código sob licença MIT (pode reaproveitar, mantendo o aviso de licença).

TÉCNICA BASE: 04-build-time-lapse (o terreno vazio e o empreendimento subindo, etapa por etapa, até a inauguração), terminando com uma caminhada pelo hotel pronto.

Quero uma landing page guiada por scroll para o nosso hotel. NÃO pare para me pedir opções: tome as decisões você mesmo, construa uma primeira versão completa e só me mostre no final. Eu itero depois.

A história:
- Abre numa prancha de arquitetura em nanquim sobre papel: as etapas da obra do NOSSO hotel (terreno vazio, fundações, estrutura, paredes, telhados de palha, paisagismo e piscina), com carimbo "Praia do Coqueiro · Luís Correia, PI".
- Os desenhos são o próprio modelo `referencia/modelo/hotel.glb` visto por lente muito longa. Ao rolar, mergulha na primeira prancha e o terreno real aparece; o scroll vira o calendário e o hotel sobe ao redor da câmera.
- No fim da obra, luz de fim de tarde e caminhada na altura dos olhos: estacionamento → recepção → pátio e piscina → sobe a escada → varanda do apto 10 → sala → quarto, terminando numa vista aérea do pátio. Use `referencia/modelo/cameras.json` como pontos de passagem.
- Textos curtos ao longo do percurso: "Praia do Coqueiro · 200 m do mar", "15 apartamentos + recepção", "1 e 2 quartos · varandas para a piscina". Rodapé fixo: "Estudo preliminar · imagens ilustrativas". Tudo em português.

Técnico:
- three.js de CDN com versão fixa, HTML/CSS/JS simples, sem build. `index.html` na raiz (vai para o GitHub Pages). GSAP/Lenis só se ajudarem.
- A geometria é a do GLB: não redesenhe o hotel. Para a obra, agrupe as peças do GLB por etapa (pela altura e pelo material, ver `materiais_do_glb.txt`).
- Materiais por cor hex do GLB: reboco e madeira com as texturas de `assets/textures/` (CC0); palha, areia, grama e água procedurais. Coqueiros mais realistas (folhas com folíolos, como em `referencia/blender/`). Coqueiral de fundo fora dos muros.
- Página leve (alvo < 15 MB). Bom no computador, aceitável no celular.

Processo:
1. Construa tudo de uma vez.
2. Antes de me entregar, abra num navegador headless, tire screenshots em 8 pontos do scroll e corrija o que estiver quebrado, preto, fora de lugar ou feio. Repita até ficar apresentável.
3. Grave um vídeo de ~20 s do percurso completo (1920×1080) em `entrega/percurso.mp4`.
4. Commit e push na branch principal.
5. Me mande: o vídeo, uma prancha com os 8 screenshots e uma lista curta de cada trecho com nota de 0 a 10 e o que você melhoraria primeiro.
