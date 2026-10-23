# PIKA Halloween — "Dulce o Piku"

| Archivo | Qué es |
|---|---|
| `pika_halloween_15s.mp4` | Reel publicitario: 15 s, 1080×1920 vertical, 30 fps, H.264 + AAC, con música propia libre de derechos (-14 LUFS). |
| `pika_ganador.mp4` | Clip de 7,5 s para mandarle por DM a cada ganador: Piku atrapa la caja de Pepero y aparece "¡GANASTE!". |
| `portada_reel.jpg` | Portada sugerida para el Reel (1080×1920). |

## Guion del Reel (128 BPM, cada escena dura 2 compases)

1. **0–3,75 s** — Piku entra saltando y baila al ritmo. Logo PIKA HALLOWEEN, título "DULCE O PIKU", "SÁBADO 31/10", murciélagos y un fantasmita.
2. **3,75–7,5 s** — "¿Encontrás las 3 cajas de Pepero?": la foto de la tienda entera, con una lupa que la recorre sin pasar por donde están las cajas, y el botón "Pausá y buscalas 👀".
3. **7,5–11,25 s** — "¿CÓMO PARTICIPAR?": los 3 pasos aparecen uno por uno, en el tiempo de la música.
4. **11,25–15 s** — "¡GANÁ UNA GOLOSINA!", lluvia de caramelos, "Sábado 31/10 · Retirá tu premio en Pika", las condiciones y @pika.kstore.

## Cómo regenerar (para hacer cambios)

Hace falta `python3` con `pillow`, `numpy` y `scipy`, además de `ffmpeg`.

```bash
cd fuente/src
# música (y el clip del ganador) normalizada a -14 LUFS
python3 music.py ../work/music_raw.wav && ./norm.sh ../work/music_raw.wav ../work/music_main.wav
python3 music.py ../work/music_w_raw.wav --sfx winner --seconds 7.5 && ./norm.sh ../work/music_w_raw.wav ../work/music_winner.wav
# videos
python3 render_main.py ../../pika_halloween_15s.mp4 ../work/music_main.wav
python3 render_winner.py ../../pika_ganador.mp4 ../work/music_winner.wav
# cuadros sueltos para revisar, sin renderizar todo
python3 render_main.py --stills 1.0,5.0,12.0 ../work/stills
```

Los textos, los tiempos y las posiciones están en `render_main.py` y `render_winner.py`. La música está en `music.py`.

`fix_badge.py` y `cutouts.py` son el preprocesado que ya está hecho: sacan el contador "2/3" de Instagram de las capturas y recortan a Piku, el logo, el título, el murciélago y la caja de Pepero (con `rembg`). Sus resultados ya están en `fuente/work/`. La tipografía es Fredoka (licencia SIL OFL, en `fuente/fonts/`).
