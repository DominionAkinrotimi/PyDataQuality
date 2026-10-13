/** The PyDataQuality mark. It is drawn on white, so give it a white surface to sit on. */
export function Mark({ size = 24, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="82 42 330 330" width={size} height={size} className={className} aria-hidden>
      <path d="M262 66a15 15 0 0 1 30 0V308L262 336Z" fill="#090a0f"/>
      <path d="M238 153L292 203L241 261L193 206Z" fill="#fff" stroke="#fff" strokeWidth="30" strokeLinejoin="round"/>
      <rect x="150" y="139" width="29" height="223" rx="14.5" fill="#090a0f"/>
      <path d="M238 153L292 203L241 261L193 206Z" fill="#090a0f" stroke="#090a0f" strokeWidth="13" strokeLinejoin="round"/>
      <path d="M211 209L229 225L263 190" fill="none" stroke="#2f9e4f" strokeWidth="15" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M320 299L343 296L345.5 299L288 361H256Z" fill="#2f9e4f" stroke="#2f9e4f" strokeWidth="3" strokeLinejoin="round"/>
    </svg>
  );
}
