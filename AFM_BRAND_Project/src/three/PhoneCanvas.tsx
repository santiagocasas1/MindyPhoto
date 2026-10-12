import React, { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { PHONE, Rig, W, H } from "../lib/choreo";
import { prog, ease, mix, track } from "../lib/anim";
import T from "../../config/timeline.json";

const roundedRect = (w: number, h: number, r: number) => {
  const s = new THREE.Shape();
  const x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h);
  s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r);
  s.quadraticCurveTo(x, y, x + r, y);
  return s;
};

/** Studio used only for reflections: dark room, one big softbox, a red and a white strip. */
function buildEnvironment(renderer: THREE.WebGLRenderer) {
  const env = new THREE.Scene();
  const room = new THREE.Mesh(
    new THREE.BoxGeometry(60, 40, 60),
    new THREE.MeshBasicMaterial({ color: 0x0c0c0f, side: THREE.BackSide }),
  );
  env.add(room);
  const panel = (w: number, h: number, color: number, intensity: number, pos: [number, number, number], look: [number, number, number]) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide }));
    m.position.set(...pos);
    m.lookAt(...look);
    env.add(m);
  };
  panel(30, 12, 0xffffff, 9.0, [0, 18, 4], [0, 0, 0]); // overhead softbox
  panel(4, 34, 0xff1d12, 16.0, [-26, 2, 4], [0, 0, 0]); // AFM red strip, camera left
  panel(3.5, 34, 0xfff1e2, 12.0, [26, 0, 0], [0, 0, 0]); // warm white strip, camera right
  panel(40, 3, 0xffffff, 3.0, [0, -12, 26], [0, 0, 0]); // low front kicker
  panel(50, 30, 0x8a8f99, 0.5, [0, 4, 29], [0, 0, 0]); // dim wall behind camera -> glass sheen
  panel(6, 30, 0xffffff, 6.0, [-12, 4, -28], [0, 0, 0]); // back rim source
  const pmrem = new THREE.PMREMGenerator(renderer);
  const tex = pmrem.fromScene(env, 0.035).texture;
  pmrem.dispose();
  return tex;
}

function buildPhone() {
  const g = new THREE.Group();
  const { w, h, r, t } = PHONE;
  const bev = 1.7;
  const body = new THREE.ExtrudeGeometry(roundedRect(w - 2 * bev, h - 2 * bev, r - bev), {
    depth: t - 2 * bev, bevelEnabled: true, bevelThickness: bev, bevelSize: bev, bevelSegments: 10, curveSegments: 64,
  });
  body.translate(0, 0, -(t - 2 * bev) / 2);
  const frame = new THREE.MeshStandardMaterial({ color: 0x55555c, metalness: 1, roughness: 0.27, envMapIntensity: 1.55 });
  const back = new THREE.MeshStandardMaterial({ color: 0x1a1a1f, metalness: 0.35, roughness: 0.34, envMapIntensity: 1.0 });
  g.add(new THREE.Mesh(body, [back, frame]));

  // front cover glass (the display UI is composited on top of it)
  const glass = new THREE.Mesh(
    new THREE.ShapeGeometry(roundedRect(w - 1.1, h - 1.1, r - 0.55), 64),
    new THREE.MeshStandardMaterial({ color: 0x020203, metalness: 0.6, roughness: 0.06, envMapIntensity: 0.9 }),
  );
  glass.position.z = t / 2 + 0.02;
  g.add(glass);

  // camera plateau + three lenses (back, top-left as seen from behind)
  const plateau = new THREE.Mesh(
    new THREE.ExtrudeGeometry(roundedRect(31, 31, 7.5), { depth: 0.6, bevelEnabled: true, bevelThickness: 0.5, bevelSize: 0.5, bevelSegments: 4, curveSegments: 32 }),
    new THREE.MeshStandardMaterial({ color: 0x232328, metalness: 0.5, roughness: 0.16, envMapIntensity: 1.1 }),
  );
  plateau.rotation.y = Math.PI;
  plateau.position.set(w / 2 - 19.5, h / 2 - 19.5, -t / 2 - 0.1);
  g.add(plateau);
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x6c6c74, metalness: 1, roughness: 0.22, envMapIntensity: 1.6 });
  const lensMat = new THREE.MeshStandardMaterial({ color: 0x050508, metalness: 0.7, roughness: 0.03, envMapIntensity: 1.4 });
  const lensPos: [number, number][] = [[-7.3, 7.3], [-7.3, -7.3], [7.0, 0]];
  for (const [lx, ly] of lensPos) {
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(6.0, 6.2, 1.8, 48), ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.set(plateau.position.x - lx, plateau.position.y + ly, -t / 2 - 1.9);
    g.add(ring);
    const lens = new THREE.Mesh(new THREE.CylinderGeometry(4.6, 4.6, 0.6, 48), lensMat);
    lens.rotation.x = Math.PI / 2;
    lens.position.set(ring.position.x, ring.position.y, -t / 2 - 2.6);
    g.add(lens);
  }
  const flash = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 0.4, 32), new THREE.MeshStandardMaterial({ color: 0xd8d2c4, roughness: 0.3, metalness: 0 }));
  flash.rotation.x = Math.PI / 2;
  flash.position.set(plateau.position.x - 7.0, plateau.position.y + 9.4, -t / 2 - 1.3);
  g.add(flash);

  // side buttons
  const btn = (x: number, y: number, len: number) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(1.2, len, 3.2), frame);
    m.position.set(x, y, 0);
    g.add(m);
  };
  btn(-w / 2 - 0.35, 38, 7);
  btn(-w / 2 - 0.35, 24, 12);
  btn(-w / 2 - 0.35, 9, 12);
  btn(w / 2 + 0.35, 20, 18);
  return g;
}

// Reflections glide across the titanium while the camera moves.
const envSpin = track([[0, -1.1], [2.6, 0.15, ease.out], [4.0, 0.0], [6.0, -0.15], [8.0, 0.35], [18, -0.35], [22, 0.25], [26, 0]]);

export const PhoneCanvas: React.FC<{ rig: Rig }> = ({ rig }) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  const ctx = useRef<{ renderer: THREE.WebGLRenderer; scene: THREE.Scene; phone: THREE.Group; red: THREE.PointLight; key: THREE.DirectionalLight } | null>(null);

  const init = () => {
    if (ctx.current || !canvas.current) return;
    const renderer = new THREE.WebGLRenderer({ canvas: canvas.current, antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(W, H, false);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor(0x000000, 0);
    const scene = new THREE.Scene();
    scene.environment = buildEnvironment(renderer);
    const phone = buildPhone();
    phone.matrixAutoUpdate = false;
    scene.add(phone);
    scene.add(new THREE.AmbientLight(0xffffff, 0.12));
    const key = new THREE.DirectionalLight(0xfff1e6, 2.2);
    key.position.set(-300, 500, 400);
    scene.add(key);
    const rimL = new THREE.DirectionalLight(0xff3b2b, 3.0);
    rimL.position.set(-500, 120, -300);
    scene.add(rimL);
    const rimR = new THREE.DirectionalLight(0xdfe6ff, 2.4);
    rimR.position.set(500, 260, -260);
    scene.add(rimR);
    const red = new THREE.PointLight(0xff2010, 0, 900, 1.6);
    scene.add(red);
    ctx.current = { renderer, scene, phone, red, key };
  };

  useLayoutEffect(() => {
    init();
    const c = ctx.current!;
    const t = rig.t;
    c.phone.matrix.copy(rig.phone);
    c.phone.matrixWorldNeedsUpdate = true;
    (c.scene as any).environmentRotation = new THREE.Euler(0, envSpin(t), 0);
    // Hook: a red light travels the same dome arc that draws on screen.
    const [a0, a1] = T.cues.arcSweep;
    const p = prog(t, a0, a1 + 0.5, ease.inOutSoft);
    const ang = mix(Math.PI * 0.95, Math.PI * 0.05, p);
    c.red.position.set(Math.cos(ang) * 160, 40 + Math.sin(ang) * 120, 120);
    c.red.intensity = 9000 * Math.sin(Math.PI * Math.min(1, p * 1.05));
    c.red.visible = t < 2.2; // only lit during the hook: one light fewer in the shader afterwards
    c.renderer.render(c.scene, rig.camera);
  });

  return <canvas ref={canvas} width={W} height={H} style={{ position: "absolute", inset: 0, width: W, height: H }} />;
};
