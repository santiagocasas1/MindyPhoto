# AFM BRAND — Entregables

| Archivo | Qué es |
|---|---|
| `AFM_BRAND_Reels_1080p.mp4` | Comercial final de 30 s, vertical 9:16, 1080×1920, H.264 + AAC, para Instagram Reels y TikTok |
| `AFM_BRAND_QA.md` | Control de calidad técnico y visual: mediciones, verificaciones y limitaciones |
| `qa/` | Hojas de contacto (un cuadro cada 0,5 s), tiras de transiciones, primer y último cuadro, ffprobe en JSON |
| `audio/AFM_BRAND_music_stem.wav` | Stem de música original (48 kHz / 24 bit) |
| `audio/AFM_BRAND_sfx_stem.wav` | Stem de diseño sonoro (48 kHz / 24 bit) |
| `../AFM_BRAND_Project/` | Proyecto completo y reproducible: código, assets, audio y scripts de render ([README](../AFM_BRAND_Project/README.md)) |

La versión 4K (`AFM_BRAND_Cinematic_4K.mp4`, 2160×3840) **no se exportó todavía**, a pedido del cliente. Para generarla con un render real a 2160×3840 (no un reescalado), ejecutá `bash tools/render.sh 4k` desde `AFM_BRAND_Project/`.
