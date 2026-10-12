# AFM BRAND — Control de calidad

**Archivo verificado:** `output/AFM_BRAND_Reels_1080p.mp4`, codificado el 12/10/2026.
**Herramientas:** FFprobe/FFmpeg 7, scripts propios (`AFM_BRAND_Project/tools/qa.sh`, `tools/frame_diff.py`) y revisión visual cuadro por cuadro.

## 1. Especificaciones técnicas (medidas con ffprobe)

| Parámetro | Pedido | Medido | Estado |
|---|---|---|---|
| Duración | 30 s | **30,000 s** (video y audio) | ✅ |
| Resolución y aspecto | 1080×1920, 9:16 | **1080×1920** (render real, sin reescalar) | ✅ |
| Cuadros | 30 fps constantes | **30/1**, `r_frame_rate = avg_frame_rate`, **900 cuadros** | ✅ |
| Códec de video | H.264 compatible con móviles | **H.264 High @ L4.2**, yuv420p, GOP de 2 s | ✅ |
| Color | SDR Rec.709 | Primarios, transferencia y matriz **bt709**, rango **tv** (conversión RGB→YUV con matriz BT.709 explícita) | ✅ |
| Bitrate | Adecuado para redes | **16,3 Mbps** totales (video 15,97 + audio 0,32), 2 pasadas | ✅ |
| Audio | AAC estéreo 48 kHz | **AAC-LC, 48 000 Hz, 2 canales**, 322 kbps | ✅ |
| Contenedor | MP4 | MP4 con `+faststart` (reproducción inmediata en web), 61,1 MB | ✅ |

El JSON completo de ffprobe está en `qa/AFM_BRAND_Reels_1080p_ffprobe.json`.

## 2. Audio

| Verificación | Resultado |
|---|---|
| Loudness integrado (EBU R128) | **−14,1 LUFS** (el estándar de normalización de Reels y TikTok) |
| True peak | **−1,1 dBTP**. El máster WAV tiene **0 muestras recortadas** |
| Silencios inesperados (< −50 dB durante más de 0,3 s) | **Ninguno** |
| Sincronía de audio y video | Correlación cruzada entre el audio del MP4 y el WAV fuente: **0 muestras de desfase** |
| Impactos frente a sus cues | Arranque del golpe: logo −30 ms (adelantado un cuadro a propósito), drop 0 ms, cierre +5 ms. Todos dentro de **±1 cuadro** |
| Arco dinámico (RMS por segundo) | Intro −22 dB → construcción −18 → **impacto del logo −11,9** → groove −14 → chat −15,9 (batería atenuada) → **impacto final −11,7** → cola −18. Sin cortes abruptos: fade de 10 ms al inicio y cola natural con fade de 350 ms al final |

## 3. Imagen

| Verificación | Resultado |
|---|---|
| Cuadros negros (`blackdetect`, pix_th 0,10) | **Ninguno**. El cuadro 0 ya muestra el trazo rojo y el celular iluminado |
| Congelamientos involuntarios (`freezedetect`) | **Ninguno** |
| Saltos de animación | Se midió la diferencia entre cada par de cuadros consecutivos sobre los PNG originales. Todos los picos coinciden con momentos guionados (giros de cámara en cada beat, swipes, entrada en la pantalla, impacto del logo) y son rampas de varios cuadros con aceleración y frenado. **No hay picos aislados de un solo cuadro** |
| Cierre estable | Entre 28,4 y 30,0 s, el cambio máximo entre cuadros es **0,000**: totalmente quieto. El grano se agrega en el encode, así que la verificación se hizo sobre los cuadros fuente |
| Revisión visual | Hoja de contacto con un cuadro cada 0,5 s (`qa/…_contact_0.5s.png`), 10 tiras de transiciones de 6 cuadros cada una (`qa/…_transition_*.png`), primer y último cuadro, y más de 150 cuadros sueltos revisados durante el desarrollo |

### Fidelidad del logo

- **Archivo:** se usa el **PNG original** publicado en afmbrand.com.ar (2000×2000), recortado solo en su margen transparente.
- **Separación en capas:** para animarlo se separó en dos capas complementarias (cúpula roja y letras negras). Recombinadas, dan **píxeles idénticos** al original, y `prepare_assets.py` lo verifica con un `assert`.
- **Proporciones y color:** se escala siempre de forma uniforme (relación 1831:1086) y nunca se recolorea, deforma ni redibuja. Aparece siempre sobre **blanco** (splash del celular y placa final) porque sus letras son negras.
- **Cierre:** el logo ocupa 760 px de ancho, con aire a su alrededor.

### Texto y ortografía

- **Marcas**, tal como se escriben: OKF, Milkis, Pepero, HTB, Soonhari, Saero.
- **Copy:** "¿Antojo de Corea?", "Explorá", "Armá tu pedido", "Hablá con un asesor" y el chat. Todo en español rioplatense, revisado.
- **Textos tomados del sitio:**
  - "BIENVENIDO A AFM BRAND"
  - "¡Tu puente directo a lo mejor de Corea y el Mundo!" (con la mayúscula en "Mundo", como en el sitio)
  - "Carrito de compras", "Compra protegida", las categorías
  - Web, WhatsApp (+54 9 11 4066 8682) e Instagram (@afmbrand.arg), tal como figuran en afmbrand.com.ar el 12/10/2026
- **Ningún texto cortado** en los cuadros revisados.
- **Sin** precios, descuentos, certificaciones, cifras ni la mención "distribuidor oficial".
- **Leyenda de alcohol:** mientras Soonhari y Saero están en pantalla (14,85–18,05 s) se muestra "BEBER CON MODERACIÓN. PROHIBIDA SU VENTA A MENORES DE 18 AÑOS." sobre una banda oscura legible.

### Zonas seguras de Reels y TikTok

- Titulares entre y = 210 y 560 px.
- Placa final entre y = 486 y 1400 px.
- Leyenda legal en y ≈ 1418–1500 px.
- No hay información esencial en los 380 px inferiores ni pegada a los bordes laterales.

## 4. Problemas encontrados y corregidos

| # | Problema | Solución |
|---|---|---|
| 1 | Los recortes automáticos de las latas transparentes de OKF y de la caja de Pepero Choco Cookie tenían agujeros: se perdía texto del envase ("F PERO") | Máscara por filas para el PET transparente, relleno de huecos y envolvente convexa para latas. Pepero Choco Cookie se usa solo como foto original dentro de la interfaz |
| 2 | El titular del gancho se superponía con el celular | Se reencuadró la cámara del gancho |
| 3 | "BIENVENIDO…" chocaba con "ALL FOOD MARKET" del logo | Se ajustaron el layout y el timing del splash |
| 4 | Los productos protagonistas salían cortados por el borde, y los de marcas anteriores tapaban los títulos | El celular se corre hacia el lado opuesto en cada beat y los productos salen del cuadro al cambiar de marca |
| 5 | La caja de Pepero se cortaba en el borde derecho | Se redujeron su tamaño y su desplazamiento |
| 6 | La leyenda de alcohol se leía mal sobre la interfaz | Se le agregó una banda oscura con borde sutil |
| 7 | El texto del chat se veía chico en un teléfono | Acercamiento de cámara y burbujas a 17,5 pt |
| 8 | Los datos de contacto del cierre eran chicos y de bajo contraste | Se pasaron a 35 px en gris oscuro |
| 9 | El vuelo de los productos al carrito arrancaba durante el beat de Saero y se veía amontonado | Se retrasó 0,15 s; se rehízo el audio y se volvieron a renderizar los cuadros 525–605 |
| 10 | Los impactos graves se percibían unos 50 ms tarde por su ataque lento | Se adelantaron un cuadro |
| 11 | El render tardaba 3,7 s por cuadro en CPU | Fondo en un único canvas, sin modos de fusión del compositor, materiales PBR estándar, grano en el encode y dos procesos de navegador en paralelo: **~1 s por cuadro**, sin cambio visual |

## 5. Limitaciones y notas

- **4K no exportado.** A pedido del cliente se entregó solo la versión 1080p revisada. Si se necesita, `bash tools/render.sh 4k` hace un render real a 2160×3840 (factor de escala 2, no un reescalado). En esta máquina sin GPU se estima entre 60 y 90 minutos.
- **El audio se validó por medición, no escuchando:** loudness, picos, espectrograma, silencios y sincronía. Antes de publicar conviene escucharlo en el parlante de un teléfono.
- **Rendering 3D por software (SwiftShader):** el celular es PBR en tiempo real con reflejos de entorno (PMREM), no ray tracing.
- **No hay personas reales ni filmación:** el punto de vista en primera persona se transmite con los toques en pantalla. El chat con el asesor es una dramatización, con contenido basado en la página "¿Querés ser mayorista?" del sitio.
- **Fotos de producto:** son las imágenes del catálogo publicado por AFM BRAND. Los derechos de los envases y marcas pertenecen a sus titulares. Se excluyeron las cajas de Pepero con imágenes de artistas.
- **Grano de película:** se agrega con el filtro `noise` de FFmpeg para evitar el banding. Por eso `freezedetect` no puede detectar el cierre quieto, y esa verificación se hizo sobre los cuadros fuente.
- **Anticipación del trazo:** durante unos 0,1 s antes de que se dibuje el logo (a los 4,0 y 26,1 s) se ve una mínima pincelada roja en el pie izquierdo de la cúpula. Es el inicio del trazo y se dejó como anticipación.
