# AFM BRAND — Comercial POV "Tu puente directo" (30 s · 9:16)

Comercial vertical de 30 segundos para Instagram Reels y TikTok. Muestra, en primera persona, a alguien que explora la tienda de AFM BRAND en un celular 3D, arma un pedido y habla con un asesor. Termina con el logo original de la marca.

Todo es **código reproducible**:

- **Imagen:** Remotion (React) + Three.js. Celular 3D real, con iluminación de estudio y reflejos PBR.
- **Interfaz de la tienda:** HTML real, proyectado sobre la pantalla 3D con una homografía.
- **Audio:** sintetizado en Python (numpy y scipy), sin samples ni música de terceros.
- **Encode:** FFmpeg.

> Cada ventana de una escena y cada impacto se definen en **un solo archivo**: `config/timeline.json`. El video y el audio leen los mismos tiempos, así que no pueden desincronizarse.

---

## Estructura narrativa

| Tiempo | Escena | Qué pasa | Sonido |
|---|---|---|---|
| 0:00–0:04 | **Gancho** | Oscuridad. Un trazo de luz roja dibuja la cúpula del logo alrededor de un celular de titanio. El celular gira, se enciende la pantalla y llega una notificación de AFM BRAND. Titular: *"¿Antojo de Corea?"* | Atmósfera, barrido de luz, *chime* de notificación, riser |
| 0:04–0:08 | **Revelación** | La notificación se abre a pantalla completa. El **logo original** aparece con máscaras (primero la cúpula roja, después las letras) y un brillo lo recorre. Se lee *"BIENVENIDO A AFM BRAND"* y el eslogan real del sitio. | **Impacto** grave a los 4,0 s, pad abierto |
| 0:08–0:18 | **Explorar** | Scroll por la home de la tienda y swipe entre fichas. En cada beat, el producto **sale de la pantalla** en 3D: OKF → Milkis → Pepero → HTB → Soonhari → Saero. Se agrega cada uno al carrito. | *Drop* a los 8,0 s, groove a 120 BPM, *whip* y *pop* por marca, notas ascendentes en cada agregado |
| 0:18–0:22 | **Pedido** | Los seis productos vuelven volando y caen en el carrito. Se toca *"Hablar con un asesor"*. | *Pops* afinados, *whoosh* |
| 0:22–0:26 | **Asesor** | Chat con el *Asesor de ventas* de AFM BRAND: pedido y consulta mayorista. | Batería atenuada, sonidos de mensajes |
| 0:26–0:30 | **Cierre** | La cámara entra en la pantalla y todo pasa a blanco. El logo original se dibuja con luz. Debajo, el eslogan y los contactos reales: web, WhatsApp e Instagram. Desde los 28,4 s el cuadro queda **estable**. | Resolución en re mayor, impacto final, cola natural |

## Dirección de arte

- **Logo:** se usa el PNG original de afmbrand.com.ar (`public/assets/brand/afm_logo_original.png`), sin alterarlo.
  - Para animarlo se separó en dos capas complementarias: la cúpula roja y las letras negras. Al recombinarlas, el resultado es **idéntico byte a byte** al original (`tools/prepare_assets.py` lo verifica con un `assert`).
  - Como el texto es negro, el logo aparece **siempre sobre blanco**: en la pantalla del celular y en la placa final. Nunca se recolorea.
- **Paleta:**
  - Rojo AFM `#EC090A` (del logo) y rojo de la tienda `#D62210` (botones del sitio).
  - Grafito `#0B0B0E`, carbón `#17171C`, titanio `#3B3B41` y blanco porcelana `#F6F4F0`.
  - Cada marca tiñe la luz de fondo con el color de su envase.
- **Tipografía:**
  - **Jost** para titulares y placa final: geométrica, de la misma familia visual que la tipografía tipo Futura del logo.
  - **Inter** para la interfaz.
  - Ambas tienen licencia OFL y se instalan desde npm (`@fontsource`).
- **Estética:**
  - Estudio oscuro con haces de luz volumétrica y polvo en suspensión.
  - Profundidad de campo en las variantes de sabor.
  - Reflejos del entorno que se deslizan sobre el titanio.
  - Grano fino para evitar el *banding*.

## Autenticidad

- **Fotos de producto:** son las **fotos de catálogo de afmbrand.com.ar**. Las URL de origen de cada SKU están en `config/products.json`.
  - Solo se recortaron, con rembg y limpieza de máscara.
  - Las cajas de Pepero con caras de artistas (Stray Kids) se dejaron afuera por derechos de imagen.
- **Textos:**
  - El eslogan, *"BIENVENIDO A AFM BRAND"*, *"Compra protegida"*, *"Carrito de compras"*, las categorías y los datos de contacto salen del sitio.
  - El copy narrativo (*"¿Antojo de Corea?"*, *"Explorá"*, *"Armá tu pedido"*, *"Hablá con un asesor"*) es una llamada a la acción, no una afirmación comercial.
- **Lo que no se muestra:** no aparecen precios, descuentos, certificaciones ni cifras.
- **Bebidas alcohólicas:** Soonhari y Saero son soju. Mientras están en pantalla se muestra la leyenda *"BEBER CON MODERACIÓN. PROHIBIDA SU VENTA A MENORES DE 18 AÑOS."* (Ley 24.788).

## Estructura del proyecto

```
AFM_BRAND_Project/
├── config/
│   ├── timeline.json        # guion: escenas, cues, copy, marcas, paleta (fuente única)
│   └── products.json        # SKUs usados + URL de origen en afmbrand.com.ar
├── src/
│   ├── Commercial.tsx       # composición: capas en orden de profundidad
│   ├── lib/anim.ts          # easings, keyframes, ruido, PRNG determinístico
│   ├── lib/choreo.ts        # cámara y pose del celular (mm reales), proyección, homografía
│   ├── lib/data.ts          # acceso a assets y timeline
│   ├── three/PhoneCanvas.tsx# celular 3D (Three.js): titanio, vidrio, cámaras, estudio PMREM
│   ├── ui/PhoneUI.tsx       # tienda AFM en la pantalla: bloqueo, splash, home, ficha, carrito, chat
│   └── layers/              # World (fondo, productos 3D, polvo) · Overlay (titulares, arco, placa, acabado)
├── audio/compose.py         # banda sonora + diseño sonoro sintetizados (48 kHz / 24 bit)
├── public/assets/           # logo (original y capas), recortes de producto, fotos de la tienda
├── public/audio/soundtrack.wav
└── tools/
    ├── prepare_assets.py    # descarga logo y fotos del sitio y los recorta
    ├── render.sh            # render de frames + encode final (1080 o 4k)
    ├── qa.sh / frame_diff.py# verificación técnica y visual del MP4 y de los frames
    ├── bench.mjs            # medición de tiempo por cuadro
    └── stills.mjs           # render rápido de cuadros sueltos para revisión
```

## Cómo volver a renderizar

Requisitos: Node 18 o superior, Python 3.10 o superior, FFmpeg con libx264 y Chromium o Chrome headless.

```bash
cd AFM_BRAND_Project
npm install

# (opcional) regenerar assets desde afmbrand.com.ar
pip install "rembg[cpu]" pillow numpy scipy
python3 tools/prepare_assets.py

# (opcional) regenerar la banda sonora
pip install numpy scipy soundfile pyloudnorm
python3 audio/compose.py

# vista previa interactiva
npx remotion studio src/index.ts

# render final 1080x1920 -> ../output/AFM_BRAND_Reels_1080p.mp4
AFM_BROWSER=/ruta/a/chrome-headless-shell bash tools/render.sh 1080

# render real 2160x3840 (deviceScaleFactor 2, no es un reescalado) -> ../output/AFM_BRAND_Cinematic_4K.mp4
AFM_BROWSER=/ruta/a/chrome-headless-shell bash tools/render.sh 4k
```

`AFM_BROWSER` es opcional: sin esa variable, Remotion descarga su propio Chrome headless. `AFM_CONCURRENCY` define cuántos cuadros se renderizan en paralelo (por defecto, 2). `AFM_ENCODE_ONLY=1` vuelve a codificar los cuadros existentes sin renderizar.

**Rendimiento (máquina sin GPU, 4 núcleos):** el WebGL corre por software (SwiftShader). Un único proceso de navegador comparte un solo proceso gráfico, así que conviene dividir el render en dos procesos con rangos distintos. Con eso se llega a ~1 s por cuadro:

```bash
npx remotion render src/index.ts AFMCommercial out/frames_1080 --sequence --image-format=png --frames=0-449   --concurrency=1 --gl=swangle &
npx remotion render src/index.ts AFMCommercial out/frames_1080 --sequence --image-format=png --frames=450-899 --concurrency=1 --gl=swangle
AFM_ENCODE_ONLY=1 bash tools/render.sh 1080
```

Control de calidad: `bash tools/qa.sh ../output/AFM_BRAND_Reels_1080p.mp4` y `python3 tools/frame_diff.py out/frames_1080`. Para revisar cuadros sueltos: `node tools/stills.mjs out/stills 0 120 300`.

### Especificación de exportación

| | 1080p (Reels/TikTok) | 4K (máster) |
|---|---|---|
| Resolución | 1080×1920 | 2160×3840 |
| Video | H.264 High @ L4.2, yuv420p, 2 pasadas, 16 Mbps (máx. 22) | H.264 High @ L5.1, 2 pasadas, 45 Mbps (máx. 60) |
| Color | SDR Rec.709 (matriz, primarios y transferencia BT.709, rango limitado) | igual |
| Cuadros | 30 fps constantes, GOP de 2 s | igual |
| Audio | AAC-LC 320 kbps, 48 kHz, estéreo, −14 LUFS, true peak ≤ −1 dBTP | igual |
| Contenedor | MP4 con `+faststart` | igual |

## Zonas seguras

- Los titulares viven entre y = 210 y 560 px.
- La placa final ocupa y = 486 a 1400 px, en la columna central.
- La leyenda de alcohol está en y ≈ 1418–1500 px.
- Ningún elemento esencial cae en los 380 px inferiores ni en los bordes laterales, que son las zonas que tapan los botones y los textos de Reels y TikTok.
