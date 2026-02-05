import NoiseOrb from './NoiseOrb'

export default function LoadingScreen({ visible }) {
  return (
    <div className={`loading-screen ${visible ? 'is-visible' : 'is-hidden'}`} aria-hidden={!visible}>
      <div className="loading-content">
        <div className="loading-orb-wrap">
          <NoiseOrb size={300} />
        </div>
        <p className="loading-text">initializing yolodex</p>
      </div>
    </div>
  )
}
