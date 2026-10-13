import { useMemo } from "react";
import { layoutCells } from "@/lib/sheet";

/**
 * The still picture of the hero scene, drawn with plain elements and CSS 3D so it is there on the
 * first paint. It shows the settled state: flagged cells lifted, the rest passed. It stays in place
 * of the 3D scene on low-power devices and when the visitor prefers reduced motion.
 */
export function HeroPoster() {
  const cells = useMemo(layoutCells, []);
  return (
    <div className="absolute inset-0 grid place-items-center [perspective:1500px]">
      <div
        className="relative aspect-[6.6/5] w-[74%] [transform-style:preserve-3d]"
        style={{ transform: "translateY(-4%) rotateX(49deg) rotateZ(-24deg)" }}
      >
        {cells.map((cell) => {
          const header = cell.row === 0;
          const tone = header ? "header" : cell.flag ?? "ok";
          const lift = tone === "problem" ? 34 : tone === "warning" ? 20 : 0;
          const background = { header: "#2b3140", ok: "#12231c", problem: "#ef4444", warning: "#f59e0b" }[tone];
          const bar = { header: "#c3cad8", ok: "#3fbf74", problem: "#ffffff", warning: "#ffffff" }[tone];
          const glow = tone === "problem" ? "0 0 26px 4px rgba(255,59,59,0.5)" : tone === "warning" ? "0 0 22px 3px rgba(255,171,31,0.42)" : undefined;
          return (
            <span
              key={`${cell.row}-${cell.col}`}
              className="absolute block rounded-[1px]"
              style={{
                left: `${cell.x * 100}%`,
                top: `${cell.y * 100}%`,
                width: `calc(${cell.w * 100}% - 3px)`,
                height: `calc(${cell.h * 100}% - 3px)`,
                background,
                boxShadow: glow,
                transform: lift ? `translateZ(${lift}px)` : undefined,
              }}
            >
              <span className="absolute left-[13%] top-[40%] block h-[20%]" style={{ width: `${cell.fill * 74}%`, background: bar }} />
            </span>
          );
        })}
      </div>
    </div>
  );
}
