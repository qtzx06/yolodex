import { useState, useRef } from 'react'
import './PipelineStage.css'

export default function PipelineStage({
  index,
  title,
  description,
  imageSrc,
  altText,
  isActive = false,
  delay = 0,
}) {
  const [isHovered, setIsHovered] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const cardRef = useRef(null)

  const handleMouseMove = (e) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    setMousePosition({ x, y })
  }

  const handleMouseEnter = () => setIsHovered(true)
  const handleMouseLeave = () => {
    setIsHovered(false)
    setMousePosition({ x: 50, y: 50 })
  }

  return (
    <article
      ref={cardRef}
      className={`pipeline-stage ${isActive ? 'is-active' : ''} ${isHovered ? 'is-hovered' : ''}`}
      style={{ '--delay': `${delay}ms` }}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div
        className="pipeline-stage-glow"
        style={{
          '--mouse-x': `${mousePosition.x}%`,
          '--mouse-y': `${mousePosition.y}%`,
        }}
      />

      <div className="pipeline-stage-number">
        <span>{String(index).padStart(2, '0')}</span>
        <div className="pipeline-stage-pulse" />
      </div>

      <div className="pipeline-stage-visual">
        <div className="pipeline-stage-image-wrapper">
          <img
            src={imageSrc}
            alt={altText}
            className="pipeline-stage-image"
          />
          <div className="pipeline-stage-scan-line" />
        </div>
        <div className="pipeline-stage-particles">
          <span />
          <span />
          <span />
        </div>
      </div>

      <div className="pipeline-stage-content">
        <h3 className="pipeline-stage-title">{title}</h3>
        <p className="pipeline-stage-description">{description}</p>
      </div>

      <div className="pipeline-stage-connector">
        <svg className="pipeline-connector-svg" viewBox="0 0 100 2">
          <line
            x1="0" y1="1" x2="100" y2="1"
            stroke="url(#pipeline-gradient)"
            strokeWidth="2"
            strokeDasharray="5 5"
            className="pipeline-connector-line"
          />
          <defs>
            <linearGradient id="pipeline-gradient">
              <stop offset="0%" stopColor="rgba(100, 140, 255, 0)" />
              <stop offset="50%" stopColor="rgba(120, 160, 255, 0.8)" />
              <stop offset="100%" stopColor="rgba(100, 140, 255, 0)" />
            </linearGradient>
          </defs>
        </svg>
        <div className="pipeline-flow-dot" />
      </div>
    </article>
  )
}
