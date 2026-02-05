import { useRef } from 'react'
import './TiltedCard.css'

export default function TiltedCard({
  imageSrc,
  altText = 'tilted card image',
  captionText = '',
  containerHeight = '220px',
  containerWidth = '100%',
  imageHeight = '220px',
  imageWidth = '100%',
  scaleOnHover = 1.05,
  rotateAmplitude = 12,
  showTooltip = true,
  overlayContent = null,
  displayOverlayContent = false,
}) {
  const ref = useRef(null)
  const innerRef = useRef(null)
  const tooltipRef = useRef(null)
  const rafRef = useRef(0)

  const setTransform = (rotateX, rotateY, scale) => {
    if (!innerRef.current) return
    innerRef.current.style.setProperty('--tilt-rotate-x', `${rotateX}deg`)
    innerRef.current.style.setProperty('--tilt-rotate-y', `${rotateY}deg`)
    innerRef.current.style.setProperty('--tilt-scale', `${scale}`)
  }

  const handleMouseMove = (event) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const offsetX = event.clientX - rect.left - rect.width / 2
    const offsetY = event.clientY - rect.top - rect.height / 2

    const rotationX = (offsetY / (rect.height / 2)) * -rotateAmplitude
    const rotationY = (offsetX / (rect.width / 2)) * rotateAmplitude

    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(() => {
      setTransform(rotationX, rotationY, scaleOnHover)
      if (tooltipRef.current && showTooltip) {
        tooltipRef.current.style.left = `${event.clientX - rect.left}px`
        tooltipRef.current.style.top = `${event.clientY - rect.top}px`
        tooltipRef.current.style.opacity = '1'
      }
    })
  }

  const handleMouseLeave = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    setTransform(0, 0, 1)
    if (tooltipRef.current) tooltipRef.current.style.opacity = '0'
  }

  return (
    <figure
      ref={ref}
      className="tilted-card-figure"
      style={{ height: containerHeight, width: containerWidth }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        ref={innerRef}
        className="tilted-card-inner"
        style={{
          width: imageWidth,
          height: imageHeight,
        }}
      >
        <img src={imageSrc} alt={altText} className="tilted-card-img" />

        {displayOverlayContent && overlayContent ? <div className="tilted-card-overlay">{overlayContent}</div> : null}
      </div>

      {showTooltip ? (
        <figcaption
          ref={tooltipRef}
          className="tilted-card-caption"
        >
          {captionText}
        </figcaption>
      ) : null}
    </figure>
  )
}
