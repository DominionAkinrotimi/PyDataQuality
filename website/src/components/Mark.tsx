/**
 * The PyDataQuality logo. It takes the text colour, so it is ink on a light page and white on a
 * dark one. `ground` is the colour behind it, used for the tick and the gap around the tile.
 */
export function Mark({ size = 24, ground = "#ffffff", className }: { size?: number; ground?: string; className?: string }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} className={className} aria-hidden>
      <path d="M58 16a10 10 0 0 1 20 0V72L58 90Z" fill="currentColor"/>
      <path d="M46 31L69 52L48 75L25 54Z" fill={ground} stroke={ground} strokeWidth="17" strokeLinejoin="round"/>
      <rect x="12" y="30" width="20" height="62" rx="10" fill="currentColor"/>
      <path d="M46 31L69 52L48 75L25 54Z" fill="currentColor" stroke="currentColor" strokeWidth="8" strokeLinejoin="round"/>
      <path d="M36 53L44.5 61L58 45" fill="none" stroke={ground} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M85 72L96 70.5L74 93H57Z" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
    </svg>
  );
}
