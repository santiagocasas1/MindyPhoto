import {continueRender, delayRender} from 'remotion';
import '@fontsource/poppins/500.css';
import '@fontsource/poppins/600.css';
import '@fontsource/poppins/700.css';
import '@fontsource/poppins/800.css';
import '@fontsource/poppins/900.css';
import '@fontsource/noto-sans-kr/700.css';
import '@fontsource/noto-sans-kr/900.css';
import '@fontsource/space-mono/400.css';
import '@fontsource/space-mono/700.css';

// Todo el texto coreano del video, para precargar sólo los fragmentos de la fuente que se usan.
const KR = '피카라면음료스낵캔디떡볶이달콤소주과자젤리콤보감사합니다삑편의점';

const handle = delayRender('Cargando tipografías');
Promise.all([
  ...[500, 600, 700, 800, 900].map((w) => document.fonts.load(`${w} 100px Poppins`, 'AÁÉÍÓÚÑaáé0123456789·@')),
  ...[700, 900].map((w) => document.fonts.load(`${w} 100px "Noto Sans KR"`, KR)),
  ...[400, 700].map((w) => document.fonts.load(`${w} 100px "Space Mono"`, 'ABC0123456789·./')),
])
  .then(() => continueRender(handle))
  .catch((err) => {
    console.error(err);
    continueRender(handle);
  });
