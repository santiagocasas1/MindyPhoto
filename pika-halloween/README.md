# PIKA Halloween — "Dulce o Piku" (versión 2)

| Archivo | Qué es |
|---|---|
| `pika_halloween_15s.mp4` | Reel publicitario: 15 s, 1080×1920 vertical, 30 fps, H.264 + AAC 48 kHz, -14 LUFS. |
| `pika_ganador.mp4` | Clip de 7,5 s para mandarle por DM a cada ganador: Piku atrapa la caja de Pepero y aparece "¡GANASTE!". |
| `portada_reel.jpg` | Portada sugerida para el Reel (1080×1920). |

## Guion del Reel (128 BPM, cada escena dura 2 compases)

1. **0–3,75 s**: Piku entra de un salto con un silbato de dibujo animado y baila al ritmo (saluda con el brazo, se balancea, le flamea la capa y parpadea). El logo cae rebotando, "DULCE O PIKU" cae letra por letra con un golpe orquestal y aparece "SÁBADO 31/10". Hay rayos de luz, murciélagos y un fantasmita.
2. **Transición**: pasa una bandada de murciélagos.
3. **3,75–7,5 s**: "¿Encontrás las 3 cajas de Pepero?". La foto de la tienda está "viva": tiene movimiento 3D por profundidad y las calabazas titilan. Una lupa de vidrio la recorre sin pasar por donde están las cajas. Aparece "Pausá y buscalas 👀".
4. **Transición**: una capa violeta barre la pantalla.
5. **7,5–11,25 s**: "¿CÓMO PARTICIPAR?". Los 3 pasos entran con brillo y Piku saluda desde abajo.
6. **Transición**: estallido de luz.
7. **11,25–15 s**: "¡GANÁ UNA GOLOSINA!", lluvia de caramelos con profundidad de campo, "Sábado 31/10 · Retirá tu premio en Pika", las condiciones y @pika.kstore. El final llega con un acorde de órgano y una explosión de caramelos.

## Herramientas usadas

- **Superresolución con IA**: Real-ESRGAN x4 (`RealESRGAN_x4plus`, `x4plus_anime_6B`, `realesr-general-x4v3`) con PyTorch + spandrel. Las capturas de 1220 px quedaron nítidas a 4×, y se les devolvió la textura de peluche de Piku.
- **Recorte**: rembg (IS-Net) y un filtro guiado sobre la imagen 4× para lograr bordes limpios, sin halo naranja del fondo. El título se separó letra por letra con una transformada de distancia.
- **Profundidad con IA**: Depth Anything V2 Small (Apache-2.0) para el paralaje 3D de la foto de la tienda.
- **Animación de Piku**: rig 2D propio con skinning de pesos suaves (balanceo, brazo, bolso), ondas en la capa y parpadeo.
- **Gráficos**: texto cinético letra por letra, luces aditivas, transiciones temáticas, motion blur por submuestreo temporal, golpes de cámara, viñeta y corrección de color. El render se hace en paralelo con varios núcleos.
- **Música**: composición propia renderizada con FluidSynth y el banco de sonidos FluidR3 GM (licencia MIT). Usa xilofón, cuerdas en pizzicato, tuba, fagot, celesta, glockenspiel, timbales, golpe orquestal, órgano, silbato y batería. Tiene reverb por convolución, compresión y está en -14 LUFS (BS.1770) con limitador a -1 dBFS.

## Cómo regenerar

Hace falta `python3` con `pillow`, `numpy`, `scipy`, `opencv-python-headless`, `mido` y `pyloudnorm`. También `ffmpeg`, `fluidsynth` y el soundfont `fluid-soundfont-gm` (en Ubuntu: `apt install fluidsynth fluid-soundfont-gm`).

```bash
cd fuente/src
python3 music2.py ../work/music2_main.wav --kind main
python3 music2.py ../work/music2_winner.wav --kind winner
python3 render2.py main   ../../pika_halloween_15s.mp4 ../work/music2_main.wav
python3 render2.py winner ../../pika_ganador.mp4       ../work/music2_winner.wav
# cuadros sueltos para revisar, sin renderizar todo
python3 render2.py main --stills 1.0,5.0,12.0 ../work/stills
```

Los textos, los tiempos y las posiciones están en `render2.py`. La música está en `music2.py`, el rig de Piku en `rig.py` y la foto viva en `livephoto.py`.

Los recursos ya procesados están en `fuente/work/` (sprites en alta resolución, letras del título y mapa de profundidad). Los scripts de preprocesado que los generaron también están incluidos: `fix_badge.py`, `cutouts.py`, `sr.py`, `cutouts_hr.py` y `split_title.py`. Para correrlos de nuevo hacen falta las capturas originales, `rembg`, `torch`, `spandrel`, `transformers` y los pesos de los modelos.

La versión 1 (`render_main.py`, `render_winner.py`, `music.py`) queda como referencia. `music.py` también aporta los whooshes sintetizados que usa la versión 2.

La tipografía es Fredoka (licencia SIL OFL, en `fuente/fonts/`).
