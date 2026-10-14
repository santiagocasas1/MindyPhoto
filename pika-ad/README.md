# PIKA K-Store: publicidad vertical (30 s)

Video publicitario para [PIKA 피카 K-Store](https://pikakstore.mitiendanube.com/) (Av. La Plata 169, Caballito), pensado para **Reels, Historias y feed de Instagram**.

- **Formato:** 1080×1920 (9:16), 30 fps, H.264 + AAC 320 kbps, 30 s.
- **Hecho con código:** [Remotion](https://www.remotion.dev/) (React + TypeScript). Cada frame se genera a partir del código, así que se puede re-exportar a cualquier resolución sin perder calidad.
- **Música original** compuesta por código (`audio/compose.py`): future-bass / K-pop a 120 BPM, sin copyright, masterizada a -14 LUFS (el nivel de Instagram).
- **Sincronía exacta:** `timeline.json` es la única fuente de verdad. El video y el audio leen los mismos cues, así que cada golpe, corte y "삑" del escáner cae en el frame exacto del beat (1 beat = 15 frames).

## Guion

| Tiempo | Compases | Escena |
|---|---|---|
| 0–2 s | 1 | Neón que titila y P·I·K·A golpeando una letra por beat |
| 2–4 s | 2 | **Drop**: logo completo con extrusión 3D, onda expansiva, "K · STORE · CABALLITO" |
| 4–8 s | 3–4 | "Tu K-store en Caballito" + carrusel 라면 / 음료 / 스낵 / 캔디 a tempo |
| 8–18 s | 5–9 | **Escáner de 편의점**: 10 productos reales, láser, "삑!" y ticket que se imprime |
| 18–20 s | 10 | Break: el ticket se revela completo (TOTAL: SEOUL MOOD ✓) y se arranca |
| 20–22 s | 11 | **Drop 2**: placa naranja "ARMÁ TU COMBO PIKA" |
| 22–26 s | 12–13 | Ramen + bebida + snack = Combo PIKA |
| 26–30 s | 14–15 | Cierre: retiro gratis, envíos, "Pedí online", @pika.kstore, WhatsApp |

Los textos importantes quedan dentro de la zona segura de Instagram (entre y=250 y y=1500), para que la interfaz de Reels/Historias no los tape.

## Comandos

```bash
npm install
npm run studio        # editor visual en el navegador
npm run render        # out/pika-ad-1080x1920.mp4
npm run render:4k     # out/pika-ad-2160x3840.mp4 (mismo video, escala x2)
npm run audio         # regenera la música (requiere python3 + numpy + scipy + ffmpeg)
```

## Estructura

```
timeline.json          BPM, escenas y cues de sonido/imagen compartidos
audio/compose.py       sintetizador + mezcla + mastering de la banda sonora
public/products/       fotos de productos de la tienda con fondo recortado (IA)
public/audio/          pika-soundtrack.wav
src/brand/logo.ts      logo PIKA vectorizado letra por letra (nítido en 4K)
src/scenes/            Hook, Tagline, Scanner, Combo, EndCard
src/components/        Logo, Receipt (ticket), Background (neón + grilla), fx (motion blur, aberración cromática, grano)
```

## Notas

- Los precios no aparecen a propósito: con la inflación, un precio en el video lo deja desactualizado en semanas.
- Para la versión 4K conviene conseguir fotos de producto en mayor resolución (algunas de la tienda miden ~300–600 px). Si no, se pueden reescalar con IA.
