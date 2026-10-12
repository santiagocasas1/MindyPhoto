// Camera + phone choreography. Units: millimetres (the phone is real-size),
// angles in degrees. Everything is a pure function of time t (seconds).
import * as THREE from "three";
import T from "../../config/timeline.json";
import { ease, track, noise1, prog, mix } from "./anim";

export const PHONE = {
  w: 71.5, h: 147, r: 10.6, t: 7.9,
  // display area (inside a thin black border) — the store UI is mapped here
  dw: 67.9, dh: 143.4, dr: 8.9,
};
export const W = T.width, H = T.height;
const B = T.cues.brandBeats;
const d2r = THREE.MathUtils.degToRad;

// ---------- camera tracks ----------
// Explore: camera alternates sides on every brand beat (whip on the beat).
const exploreYaw: [number, number, any][] = [];
const exploreTx: [number, number, any][] = [];
B.forEach((b, i) => {
  const side = T.brands[i].side;
  exploreYaw.push([b - 0.22, i === 0 ? -6 : -T.brands[i - 1].side * 12, ease.linear]);
  exploreYaw.push([b + 0.28, -side * 12, ease.snap]);
  exploreTx.push([b - 0.22, i === 0 ? 0 : T.brands[i - 1].side * 24, ease.linear]);
  exploreTx.push([b + 0.28, side * 24, ease.snap]);
});
const camTx = track([[0, 0], [8.8, 0], ...exploreTx, [17.8, -24, ease.linear], [18.25, 0, ease.snap]]);

const camYaw = track([
  [0, -34], [2.5, -12, ease.inOutSoft], [4.0, 0, ease.in],
  [5.9, 0], [7.55, 21, ease.inOut], [8.0, 8, ease.snap], [8.78, -6, ease.inOutSoft],
  ...exploreYaw,
  [17.8, 12, ease.linear], [18.25, 0, ease.snap], [21.6, 7, ease.inOutSoft],
  [22.0, -12, ease.snap], [25.5, -4, ease.inOutSoft], [26.05, 0, ease.in],
]);
const camPitch = track([
  [0, 12], [2.5, 5, ease.inOutSoft], [4.0, 0, ease.in],
  [5.9, 0], [7.55, 7, ease.inOut], [8.0, 6, ease.snap],
  [17.8, 6], [18.25, 10, ease.snap], [21.6, 8],
  [22.0, 4, ease.snap], [25.5, 3, ease.inOutSoft], [26.05, 0, ease.in],
]);
const camDist = track([
  [0, 470], [2.5, 422, ease.inOutSoft], [3.05, 415], [4.0, 322, ease.in],
  [5.9, 309, ease.linear], [7.55, 495, ease.inOut], [8.0, 545, ease.snap],
  [9.0, 525, ease.inOutSoft], [12.0, 510, ease.inOutSoft], [15.0, 530, ease.inOutSoft], [17.8, 520, ease.inOutSoft],
  [18.25, 505, ease.snap], [21.6, 480, ease.inOutSoft],
  [22.0, 470, ease.snap], [22.9, 462, ease.linear], [23.8, 352, ease.inOutSoft], [25.5, 334, ease.inOutSoft], [26.05, 58, ease.in],
]);
const camTy = track([
  [0, 46], [2.5, 38, ease.inOutSoft], [3.05, 36], [4.0, 0, ease.in], [5.9, 0], [7.55, 18, ease.inOut], [8.0, 30, ease.snap],
  [17.8, 30], [18.25, 26, ease.snap], [21.6, 26],
  [22.0, 22, ease.snap], [22.9, 22], [23.8, 16, ease.inOutSoft], [25.5, 14], [26.05, 0, ease.in],
]);
const camRoll = track([
  [0, -6], [2.5, -2, ease.inOutSoft], [4.0, 0, ease.in], [21.9, 0], [22.0, -2.2, ease.snap], [25.5, -1.2], [26.05, 0, ease.in],
]);

// ---------- phone tracks ----------
const exploreRy: [number, number, any][] = [];
B.forEach((b, i) => {
  exploreRy.push([b - 0.2, i === 0 ? 0 : -T.brands[i - 1].side * 6, ease.linear]);
  exploreRy.push([b + 0.3, -T.brands[i].side * 6, ease.snap]);
});
const phoneRy = track([
  [0, 152], [0.3, 148, ease.linear], [2.4, 8, ease.out], [4.0, 0, ease.in],
  [5.9, 0], [7.55, -20, ease.inOut], [8.0, -6, ease.snap],
  [8.6, 0, ease.inOutSoft], ...exploreRy, [17.8, 6], [18.25, 0, ease.snap], [21.6, -4], [22.0, 6, ease.snap], [25.5, 3], [26.05, 0, ease.in],
]);
const phoneRx = track([[0, -16], [2.4, -3, ease.out], [4.0, 0, ease.in], [7.55, -4], [8.0, -2, ease.snap], [17.8, -2], [18.25, -6, ease.snap], [21.6, -5], [22.0, -2, ease.snap], [26.05, 0, ease.in]]);
const phoneRz = track([[0, 9], [2.4, -2, ease.out], [4.0, 0, ease.in], [7.55, 2], [8.0, 0, ease.snap], [17.8, 0], [21.6, 0], [22.0, 1.5, ease.snap], [26.05, 0, ease.in]]);

export type Rig = {
  t: number;
  camera: THREE.PerspectiveCamera;
  phone: THREE.Matrix4;
  /** how much the display faces the camera (1 = straight on, <0 = away) */
  facing: number;
  yaw: number;
};

const _cam = new THREE.PerspectiveCamera(28, W / H, 5, 6000);
const _m = new THREE.Matrix4();
const _q = new THREE.Quaternion();

/** Float amount: idle drift, killed during the dive so the hand-off is exact. */
const floatAmt = (t: number) => 1 - prog(t, 25.45, 25.9);

export function rigAt(t: number): Rig {
  const yaw = camYaw(t), pitch = camPitch(t), dist = camDist(t);
  const target = new THREE.Vector3(camTx(t), camTy(t), 0);
  const cp = Math.cos(d2r(pitch));
  _cam.position.set(
    target.x + dist * cp * Math.sin(d2r(yaw)),
    target.y + dist * Math.sin(d2r(pitch)),
    target.z + dist * cp * Math.cos(d2r(yaw)),
  );
  _cam.up.set(0, 1, 0);
  _cam.lookAt(target);
  _cam.rotateZ(d2r(camRoll(t)));
  _cam.near = Math.max(2, dist - 300);
  _cam.far = dist + 3000;
  _cam.updateProjectionMatrix();
  _cam.updateMatrixWorld(true);

  const f = floatAmt(t);
  const fy = 1.6 * noise1(t * 0.45, 3) * f;
  const frx = 1.1 * noise1(t * 0.37, 7) * f;
  const fry = 1.4 * noise1(t * 0.31, 11) * f;
  _q.setFromEuler(new THREE.Euler(d2r(phoneRx(t) + frx), d2r(phoneRy(t) + fry), d2r(phoneRz(t)), "YXZ"));
  _m.compose(new THREE.Vector3(0, fy, 0), _q, new THREE.Vector3(1, 1, 1));

  const normal = new THREE.Vector3(0, 0, 1).applyQuaternion(_q);
  const toCam = _cam.position.clone().sub(new THREE.Vector3(0, fy, 0)).normalize();
  return { t, camera: _cam.clone(), phone: _m.clone(), facing: normal.dot(toCam), yaw };
}

/** Project a world-space point to composition pixels. Returns depth (camera-space distance) too. */
export function project(rig: Rig, p: THREE.Vector3) {
  const v = p.clone().project(rig.camera);
  const camSpace = p.clone().applyMatrix4(rig.camera.matrixWorldInverse);
  return { x: (v.x * 0.5 + 0.5) * W, y: (-v.y * 0.5 + 0.5) * H, depth: -camSpace.z };
}

/** Phone-local point (mm) to composition pixels. */
export function projectLocal(rig: Rig, x: number, y: number, z: number) {
  return project(rig, new THREE.Vector3(x, y, z).applyMatrix4(rig.phone));
}

/** Pixel size of a world-space length at a given camera depth. */
export function pxPerMm(rig: Rig, depth: number) {
  const visH = 2 * depth * Math.tan(d2r(rig.camera.fov / 2));
  return H / visH;
}

/** Homography that maps a w×h element onto 4 projected corners (TL, TR, BR, BL). */
export function homography(w: number, h: number, q: { x: number; y: number }[]) {
  const src = [[0, 0], [w, 0], [w, h], [0, h]];
  const A: number[][] = [];
  const bb: number[] = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = src[i];
    const { x: X, y: Y } = q[i];
    A.push([x, y, 1, 0, 0, 0, -x * X, -y * X]); bb.push(X);
    A.push([0, 0, 0, x, y, 1, -x * Y, -y * Y]); bb.push(Y);
  }
  // Gaussian elimination
  const n = 8;
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]]; [bb[c], bb[p]] = [bb[p], bb[c]];
    for (let r = c + 1; r < n; r++) {
      const k = A[r][c] / A[c][c];
      for (let k2 = c; k2 < n; k2++) A[r][k2] -= k * A[c][k2];
      bb[r] -= k * bb[c];
    }
  }
  const s = new Array(n).fill(0);
  for (let r = n - 1; r >= 0; r--) {
    let acc = bb[r];
    for (let k = r + 1; k < n; k++) acc -= A[r][k] * s[k];
    s[r] = acc / A[r][r];
  }
  const [a, b, c, d, e, f, g, hh] = s;
  return `matrix3d(${a},${d},0,${g},${b},${e},0,${hh},0,0,1,0,${c},${f},0,1)`;
}

/** Corners of the display (TL, TR, BR, BL) in composition pixels. */
export function displayQuad(rig: Rig) {
  const x = PHONE.dw / 2, y = PHONE.dh / 2, z = PHONE.t / 2 + 0.06;
  return [
    projectLocal(rig, -x, y, z), projectLocal(rig, x, y, z),
    projectLocal(rig, x, -y, z), projectLocal(rig, -x, -y, z),
  ];
}

export { mix };
