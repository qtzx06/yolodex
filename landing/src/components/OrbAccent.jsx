export default function OrbAccent() {
  return (
    <div className="orb-scene" aria-hidden="true">
      <div className="orb-glow" />
      <div className="orb-shell">
        <div className="orb-caustic orb-caustic-a" />
        <div className="orb-caustic orb-caustic-b" />
        <div className="orb-sheen" />
      </div>
      <div className="orb-ring" />
    </div>
  )
}
