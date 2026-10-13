import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { PerformanceMonitor } from "@react-three/drei/core/PerformanceMonitor";
import * as THREE from "three";
import { layoutCells, type Cell } from "@/lib/sheet";

/**
 * The hero scene: a sheet of cells lying in space. A plane of light sweeps down it. Cells with
 * something wrong lift out and glow red (problem) or amber (warning); the rest tick over to green.
 * Everything is three instanced meshes and two planes, so it costs five draw calls.
 */

export type ScenePhase = "checking" | "verdict";

interface SceneProps {
  /** Rendering stops while this is false (the hero is off screen or the tab is hidden). */
  active: boolean;
  onReady: () => void;
  onPhase: (phase: ScenePhase) => void;
  /** Called instead of onReady when the browser would draw the scene without a graphics chip. */
  onUnsupported: () => void;
}

const SHEET_W = 6.6;
const SHEET_H = 5.0;
const GAP = 0.07;
const DEPTH = 0.09;
const FOV = 34;

// One loop, in seconds. It starts in the settled state so it matches the poster it replaces.
const HOLD_END = 3.6;
const RESET_END = 4.6;
const SCAN_END = 7.8;
const LOOP = 8.6;

const C = {
  tile: new THREE.Color("#171b26"),
  header: new THREE.Color("#2b3140"),
  tileOk: new THREE.Color("#12231c"),
  tileProblem: new THREE.Color("#ef4444"),
  tileWarning: new THREE.Color("#f59e0b"),
  bar: new THREE.Color("#4c5466"),
  barHeader: new THREE.Color("#c3cad8"),
  barOk: new THREE.Color("#3fbf74"),
  barFlag: new THREE.Color("#ffffff"),
  glowProblem: new THREE.Color("#ff3b3b"),
  glowWarning: new THREE.Color("#ffab1f"),
};

const smooth = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};

/** A box whose front face is full brightness and whose sides are darker, so lifted cells read as solid without lights. */
function shadedBox(): THREE.BoxGeometry {
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const colors: number[] = [];
  for (let face = 0; face < 6; face++) {
    const shade = face === 4 ? 1 : face === 2 ? 0.7 : 0.42;
    for (let v = 0; v < 4; v++) colors.push(shade, shade, shade);
  }
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  return geometry;
}

function glowTexture(): THREE.Texture {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, "rgba(255,255,255,0.9)");
  gradient.addColorStop(0.35, "rgba(255,255,255,0.28)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

const BEAM_VERTEX = /* glsl */ `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
`;
// uv.y = 0 is the leading edge of the sweep; the light trails off behind it.
const BEAM_FRAGMENT = /* glsl */ `
  varying vec2 vUv;
  uniform float uStrength;
  uniform float uLine;
  void main() {
    float edge = smoothstep(0.0, 0.12, vUv.x) * smoothstep(1.0, 0.88, vUv.x);
    float line = uLine * smoothstep(0.045, 0.0, vUv.y);
    float trail = pow(1.0 - vUv.y, 3.0) * 0.22;
    gl_FragColor = vec4(vec3(0.86, 0.92, 1.0), (line + trail) * edge * uStrength);
  }
`;

function Sheet({ onPhase }: { onPhase: (phase: ScenePhase) => void }) {
  const cells = useMemo<Cell[]>(layoutCells, []);
  const group = useRef<THREE.Group>(null);
  const tiles = useRef<THREE.InstancedMesh>(null);
  const bars = useRef<THREE.InstancedMesh>(null);
  const glows = useRef<THREE.InstancedMesh>(null);
  const beam = useRef<THREE.Mesh>(null);
  const curtain = useRef<THREE.Mesh>(null);

  const box = useMemo(shadedBox, []);
  const plane = useMemo(() => new THREE.PlaneGeometry(1, 1), []);
  const glowMap = useMemo(glowTexture, []);
  const beamMaterial = useMemo(
    () => new THREE.ShaderMaterial({
      vertexShader: BEAM_VERTEX, fragmentShader: BEAM_FRAGMENT, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uStrength: { value: 0 }, uLine: { value: 1 } },
    }),
    [],
  );
  const curtainMaterial = useMemo(() => {
    const material = beamMaterial.clone();
    material.uniforms.uLine.value = 0.5;
    return material;
  }, [beamMaterial]);

  useEffect(() => () => {
    box.dispose(); plane.dispose(); glowMap.dispose(); beamMaterial.dispose(); curtainMaterial.dispose();
  }, [box, plane, glowMap, beamMaterial, curtainMaterial]);

  const pointer = useRef({ x: 0, y: 0 });
  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      pointer.current.x = (event.clientX / window.innerWidth) * 2 - 1;
      pointer.current.y = (event.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  const scratch = useMemo(() => ({ matrix: new THREE.Object3D(), color: new THREE.Color() }), []);
  const clock = useRef(0);
  const phase = useRef<ScenePhase>("verdict");

  useFrame((state, delta) => {
    if (!tiles.current || !bars.current || !glows.current || !group.current || !beam.current || !curtain.current) return;
    // Clamp the step so the loop does not jump after the tab or the hero has been away.
    clock.current = (clock.current + Math.min(delta, 0.05)) % LOOP;
    const t = clock.current;

    const scanning = t > RESET_END && t < SCAN_END;
    const scan = scanning ? (t - RESET_END) / (SCAN_END - RESET_END) : 0;
    // The sweep runs from just above the sheet to just below it.
    const scanY = SHEET_H / 2 + 0.4 - scan * (SHEET_H + 0.8);
    const fadeOut = t > HOLD_END && t <= RESET_END ? 1 - smooth((t - HOLD_END) / (RESET_END - HOLD_END)) : 1;

    const next: ScenePhase = t > HOLD_END && t < SCAN_END - 0.25 ? "checking" : "verdict";
    if (next !== phase.current) { phase.current = next; onPhase(next); }

    const { matrix, color } = scratch;
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      const w = cell.w * SHEET_W - GAP;
      const h = cell.h * SHEET_H - GAP;
      const x = (cell.x + cell.w / 2 - 0.5) * SHEET_W;
      const y = (0.5 - cell.y - cell.h / 2) * SHEET_H;

      // 0 = untouched, 1 = judged. Judged cells stay that way until the loop fades them back.
      let k: number;
      if (t <= HOLD_END) k = 1;
      else if (t <= RESET_END) k = fadeOut;
      else if (scanning) k = smooth((y - scanY) / 0.55);
      else k = 1;

      const isHeader = cell.row === 0;
      const lift = isHeader ? 0 : cell.flag === "problem" ? 0.62 * k : cell.flag === "warning" ? 0.36 * k : 0;
      const z = lift;

      matrix.position.set(x, y, z);
      matrix.scale.set(w, h, DEPTH);
      matrix.updateMatrix();
      tiles.current.setMatrixAt(i, matrix.matrix);
      color.copy(isHeader ? C.header : C.tile);
      if (!isHeader) color.lerp(cell.flag === "problem" ? C.tileProblem : cell.flag === "warning" ? C.tileWarning : C.tileOk, k);
      tiles.current.setColorAt(i, color);

      const barW = w * 0.74 * cell.fill;
      matrix.position.set(x - w / 2 + w * 0.13 + barW / 2, y, z + DEPTH / 2 + 0.004);
      matrix.scale.set(barW, h * 0.2, 1);
      matrix.updateMatrix();
      bars.current.setMatrixAt(i, matrix.matrix);
      color.copy(isHeader ? C.barHeader : C.bar);
      if (!isHeader) color.lerp(cell.flag ? C.barFlag : C.barOk, k);
      bars.current.setColorAt(i, color);

      const glow = cell.flag ? k : 0;
      matrix.position.set(x, y, z - DEPTH);
      matrix.scale.set((w + 0.9) * glow, (h + 0.9) * glow, 1);
      matrix.updateMatrix();
      glows.current.setMatrixAt(i, matrix.matrix);
      glows.current.setColorAt(i, cell.flag === "warning" ? C.glowWarning : C.glowProblem);
    }
    for (const mesh of [tiles.current, bars.current, glows.current]) {
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    }

    const strength = scanning ? smooth(scan / 0.08) * smooth((1 - scan) / 0.08) : 0;
    beamMaterial.uniforms.uStrength.value = strength;
    curtainMaterial.uniforms.uStrength.value = strength * 0.8;
    beam.current.position.y = scanY + 0.7;
    curtain.current.position.y = scanY;

    // Keep the whole sheet in view whatever shape the canvas is: back off on a narrow one.
    const fit = 2 * Math.tan(THREE.MathUtils.degToRad(FOV / 2));
    state.camera.position.z = Math.max(8.7 / (fit * (state.size.width / state.size.height)), 10.5);

    // Pointer and scroll: the sheet leans a little toward the pointer and lies back as the page scrolls.
    const scroll = Math.min(1, window.scrollY / Math.max(1, window.innerHeight));
    const targetX = -0.86 - scroll * 0.32 + pointer.current.y * 0.07;
    const targetY = pointer.current.x * 0.1;
    const ease = 1 - Math.pow(0.001, delta);
    group.current.rotation.x += (targetX - group.current.rotation.x) * ease;
    group.current.rotation.y += (targetY - group.current.rotation.y) * ease;
    group.current.position.y = 0.15 + Math.sin(t * ((Math.PI * 2) / LOOP)) * 0.06 + scroll * 0.9;
    group.current.position.z = -scroll * 1.6;
  });

  return (
    <group ref={group} rotation={[-0.86, 0, 0.42]}>
      <instancedMesh ref={glows} args={[plane, undefined, cells.length]} frustumCulled={false}>
        <meshBasicMaterial map={glowMap} transparent depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} opacity={0.7} />
      </instancedMesh>
      <instancedMesh ref={tiles} args={[box, undefined, cells.length]} frustumCulled={false}>
        <meshBasicMaterial vertexColors toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={bars} args={[plane, undefined, cells.length]} frustumCulled={false}>
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <mesh ref={beam} geometry={plane} material={beamMaterial} scale={[SHEET_W + 1.2, 1.4, 1]} position={[0, 0, DEPTH / 2 + 0.012]} />
      <mesh ref={curtain} geometry={plane} material={curtainMaterial} scale={[SHEET_W + 1.2, 1.5, 1]} position={[0, 0, 0.75]} rotation={[Math.PI / 2, 0, 0]} />
    </group>
  );
}

export default function HeroScene({ active, onReady, onPhase, onUnsupported }: SceneProps) {
  const [dpr, setDpr] = useState(() => Math.min(window.devicePixelRatio || 1, 1.5));
  return (
    <Canvas
      flat
      dpr={dpr}
      frameloop={active ? "always" : "never"}
      camera={{ position: [0, 0, 14.2], fov: FOV }}
      gl={{ antialias: true, alpha: true }}
      onCreated={({ gl }) => {
        const context = gl.getContext();
        const info = context.getExtension("WEBGL_debug_renderer_info");
        const renderer = info ? String(context.getParameter(info.UNMASKED_RENDERER_WEBGL)) : "";
        if (/swiftshader|llvmpipe|software|basic render/i.test(renderer)) onUnsupported();
        else onReady();
      }}
      style={{ pointerEvents: "none" }}
      aria-hidden
      tabIndex={-1}
    >
      {/* If the frame rate drops, render fewer pixels instead of dropping frames. */}
      <PerformanceMonitor onDecline={() => setDpr(1)} />
      <Sheet onPhase={onPhase} />
    </Canvas>
  );
}
