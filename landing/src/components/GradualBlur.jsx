import { memo, useEffect, useMemo, useRef, useState } from 'react'
import './GradualBlur.css'

const DEFAULT_CONFIG = {
  position: 'bottom',
  strength: 2,
  height: '6rem',
  divCount: 5,
  exponential: false,
  zIndex: 1000,
  animated: false,
  duration: '0.3s',
  easing: 'ease-out',
  opacity: 1,
  curve: 'linear',
  responsive: false,
  target: 'parent',
  className: '',
  style: {},
}

const CURVE_FUNCTIONS = {
  linear: (p) => p,
  bezier: (p) => p * p * (3 - 2 * p),
  'ease-in': (p) => p * p,
  'ease-out': (p) => 1 - (1 - p) ** 2,
  'ease-in-out': (p) => (p < 0.5 ? 2 * p * p : 1 - ((-2 * p + 2) ** 2) / 2),
}

const getGradientDirection = (position) =>
  (
    {
      top: 'to top',
      bottom: 'to bottom',
      left: 'to left',
      right: 'to right',
    }[position] || 'to bottom'
  )

function debounce(fn, wait) {
  let timer
  return (...args) => {
    window.clearTimeout(timer)
    timer = window.setTimeout(() => fn(...args), wait)
  }
}

function useResponsiveDimension(responsive, config, key) {
  const [value, setValue] = useState(config[key])

  useEffect(() => {
    if (!responsive) return undefined
    const calc = () => {
      const w = window.innerWidth
      let next = config[key]
      const capKey = key[0].toUpperCase() + key.slice(1)

      if (w <= 480 && config[`mobile${capKey}`]) next = config[`mobile${capKey}`]
      else if (w <= 768 && config[`tablet${capKey}`]) next = config[`tablet${capKey}`]
      else if (w <= 1024 && config[`desktop${capKey}`]) next = config[`desktop${capKey}`]

      setValue(next)
    }

    const onResize = debounce(calc, 100)
    calc()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [config, key, responsive])

  return responsive ? value : config[key]
}

function useIntersectionObserver(ref, shouldObserve = false) {
  const [isVisible, setIsVisible] = useState(!shouldObserve)

  useEffect(() => {
    if (!shouldObserve || !ref.current) return undefined

    const observer = new IntersectionObserver(([entry]) => setIsVisible(entry.isIntersecting), { threshold: 0.1 })
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [ref, shouldObserve])

  return isVisible
}

function GradualBlur(props) {
  const containerRef = useRef(null)
  const [isHovered, setIsHovered] = useState(false)

  const config = useMemo(() => ({ ...DEFAULT_CONFIG, ...props }), [props])

  const responsiveHeight = useResponsiveDimension(config.responsive, config, 'height')
  const responsiveWidth = useResponsiveDimension(config.responsive, config, 'width')
  const isVisible = useIntersectionObserver(containerRef, config.animated === 'scroll')

  const blurDivs = useMemo(() => {
    const divs = []
    const increment = 100 / config.divCount
    const currentStrength = isHovered && config.hoverIntensity ? config.strength * config.hoverIntensity : config.strength
    const curveFunc = CURVE_FUNCTIONS[config.curve] || CURVE_FUNCTIONS.linear

    for (let i = 1; i <= config.divCount; i += 1) {
      let progress = i / config.divCount
      progress = curveFunc(progress)

      const blurValue = config.exponential
        ? 2 ** (progress * 4) * 0.0625 * currentStrength
        : 0.0625 * (progress * config.divCount + 1) * currentStrength

      const p1 = Math.round((increment * i - increment) * 10) / 10
      const p2 = Math.round(increment * i * 10) / 10
      const p3 = Math.round((increment * i + increment) * 10) / 10
      const p4 = Math.round((increment * i + increment * 2) * 10) / 10

      let gradient = `transparent ${p1}%, black ${p2}%`
      if (p3 <= 100) gradient += `, black ${p3}%`
      if (p4 <= 100) gradient += `, transparent ${p4}%`

      const direction = getGradientDirection(config.position)
      const divStyle = {
        position: 'absolute',
        inset: '0',
        maskImage: `linear-gradient(${direction}, ${gradient})`,
        WebkitMaskImage: `linear-gradient(${direction}, ${gradient})`,
        backdropFilter: `blur(${blurValue.toFixed(3)}rem)`,
        WebkitBackdropFilter: `blur(${blurValue.toFixed(3)}rem)`,
        opacity: config.opacity,
        transition:
          config.animated && config.animated !== 'scroll'
            ? `backdrop-filter ${config.duration} ${config.easing}`
            : undefined,
      }

      divs.push(<div key={i} style={divStyle} />)
    }

    return divs
  }, [config, isHovered])

  const containerStyle = useMemo(() => {
    const isVertical = ['top', 'bottom'].includes(config.position)
    const isPageTarget = config.target === 'page'
    const baseStyle = {
      position: isPageTarget ? 'fixed' : 'absolute',
      pointerEvents: config.hoverIntensity ? 'auto' : 'none',
      opacity: isVisible ? 1 : 0,
      transition: config.animated ? `opacity ${config.duration} ${config.easing}` : undefined,
      zIndex: isPageTarget ? config.zIndex + 100 : config.zIndex,
      ...config.style,
    }

    if (isVertical) {
      baseStyle.height = responsiveHeight
      baseStyle.width = responsiveWidth || '100%'
      baseStyle[config.position] = 0
      baseStyle.left = 0
      baseStyle.right = 0
    } else {
      baseStyle.width = responsiveWidth || responsiveHeight
      baseStyle.height = '100%'
      baseStyle[config.position] = 0
      baseStyle.top = 0
      baseStyle.bottom = 0
    }

    return baseStyle
  }, [config, isVisible, responsiveHeight, responsiveWidth])

  return (
    <div
      ref={containerRef}
      className={`gradual-blur ${config.target === 'page' ? 'gradual-blur-page' : 'gradual-blur-parent'} ${config.className}`}
      style={containerStyle}
      onMouseEnter={config.hoverIntensity ? () => setIsHovered(true) : undefined}
      onMouseLeave={config.hoverIntensity ? () => setIsHovered(false) : undefined}
    >
      <div className="gradual-blur-inner">{blurDivs}</div>
    </div>
  )
}

const GradualBlurMemo = memo(GradualBlur)
GradualBlurMemo.displayName = 'GradualBlur'
export default GradualBlurMemo
