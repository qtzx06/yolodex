export default function VignetteOverlay({ className = '' }) {
  return <div className={`vignette-overlay ${className}`.trim()} aria-hidden="true" />
}
