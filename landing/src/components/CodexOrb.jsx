import logo from '../assets/codex-orb-mask.svg'
import MetallicPaint from './MetallicPaint'

export default function CodexOrb() {
  return (
    <div className="codex-orb" aria-hidden="true">
      <div className="codex-orb-glow" />
      <div className="codex-orb-shell">
        <MetallicPaint
          imageSrc={logo}
          seed={42}
          scale={4}
          patternSharpness={1}
          noiseScale={0.5}
          speed={0.3}
          liquid={0.75}
          mouseAnimation={false}
          brightness={2}
          contrast={0.5}
          refraction={0.01}
          blur={0.015}
          chromaticSpread={2}
          fresnel={1}
          angle={0}
          waveAmplitude={1}
          distortion={1}
          contour={0.2}
          lightColor="#ffffff"
          darkColor="#000000"
          tintColor="#84a8ff"
        />
      </div>
    </div>
  )
}
