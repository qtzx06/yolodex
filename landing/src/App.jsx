import { useEffect, useState } from 'react'
import VolumetricBackground from './components/VolumetricBackground'
import CodexOrb from './components/CodexOrb'
import VignetteOverlay from './components/VignetteOverlay'
import LoadingScreen from './components/LoadingScreen'
import GradualBlur from './components/GradualBlur'
import BentoSection from './components/BentoSection'
import WhyYolodex from './components/WhyYolodex'
import OnboardingSection from './components/OnboardingSection'
import Footer from './components/Footer'
import CVOverlay from './components/CVOverlay'
import pipelineIngest from './assets/pipeline-ingest.svg'
import pipelineAnnotate from './assets/pipeline-annotate.svg'
import pipelineTrain from './assets/pipeline-train.svg'
import './App.css'

const cvTargets = [
  {
    selector: '.codex-orb',
    label: 'codex_orb',
    roi: { x: 0.14, y: 0.1, w: 0.72, h: 0.78 },
    maxWidth: 2000,
    maxHeight: 2000,
  },
  { selector: '.hero-title', label: 'hero_title', tightText: true, maxWidth: 2000, maxHeight: 2000 },
  {
    selector: '.hero-header',
    label: 'hero_content',
    roi: { x: 0, y: 0.42, w: 1, h: 0.58 },
    padding: 6,
  },
]

function App() {
  const [loading, setLoading] = useState(true)
  const [renderScene, setRenderScene] = useState(false)
  const [typedTitle, setTypedTitle] = useState('')
  const [cloudOpacity, setCloudOpacity] = useState(1)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [showCVOverlay, setShowCVOverlay] = useState(false)

  useEffect(() => {
    let cancelled = false

    const warmScene = () => {
      if (!cancelled) setRenderScene(true)
    }

    let idleId = null
    if ('requestIdleCallback' in window) {
      idleId = window.requestIdleCallback(warmScene, { timeout: 1200 })
    } else {
      idleId = window.setTimeout(warmScene, 450)
    }

    const timer = window.setTimeout(() => {
      setLoading(false)
    }, 2200)

    return () => {
      cancelled = true
      if ('cancelIdleCallback' in window && typeof idleId === 'number') {
        window.cancelIdleCallback(idleId)
      } else if (typeof idleId === 'number') {
        window.clearTimeout(idleId)
      }
      window.clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    if (loading) return undefined

    const word = 'yolodex'
    let index = 0
    let timerId

    const tick = () => {
      setTypedTitle(word.slice(0, index))

      if (index < word.length) {
        index += 1
        timerId = window.setTimeout(tick, 120)
      }
    }

    tick()
    return () => window.clearTimeout(timerId)
  }, [loading])

  useEffect(() => {
    if (!renderScene) return undefined

    const revealTargets = document.querySelectorAll('.reveal')
    if (!revealTargets.length) return undefined

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        })
      },
      {
        threshold: 0.16,
        rootMargin: '0px 0px -8% 0px',
      },
    )

    revealTargets.forEach((target) => observer.observe(target))
    return () => observer.disconnect()
  }, [renderScene])

  useEffect(() => {
    if (loading) return undefined

    const timer = window.setTimeout(() => {
      setShowCVOverlay(true)
    }, 4000)

    return () => window.clearTimeout(timer)
  }, [loading])

  useEffect(() => {
    let rafId = 0

    const updateCloudOpacity = () => {
      const startFadePx = 80
      const fadeDistancePx = 850
      const minOpacity = 0.18
      const y = window.scrollY || document.documentElement.scrollTop || 0
      const progress = Math.min(Math.max((y - startFadePx) / fadeDistancePx, 0), 1)
      const nextOpacity = 1 - progress * (1 - minOpacity)
      setCloudOpacity(nextOpacity)
      setScrollProgress(Math.min(y / 1800, 1))
      rafId = 0
    }

    const onScroll = () => {
      if (rafId) return
      rafId = window.requestAnimationFrame(updateCloudOpacity)
    }

    updateCloudOpacity()
    window.addEventListener('scroll', onScroll, { passive: true })

    return () => {
      if (rafId) window.cancelAnimationFrame(rafId)
      window.removeEventListener('scroll', onScroll)
    }
  }, [])

  useEffect(() => {
    const canonicalHref = `${window.location.origin}${window.location.pathname}`

    let canonical = document.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.setAttribute('rel', 'canonical')
      document.head.appendChild(canonical)
    }
    canonical.setAttribute('href', canonicalHref)

    const setMeta = (attribute, key, value) => {
      let meta = document.querySelector(`meta[${attribute}="${key}"]`)
      if (!meta) {
        meta = document.createElement('meta')
        meta.setAttribute(attribute, key)
        document.head.appendChild(meta)
      }
      meta.setAttribute('content', value)
    }

    setMeta('property', 'og:url', canonicalHref)
    setMeta('name', 'twitter:url', canonicalHref)
  }, [])

  return (
    <>
      <main className="app-shell" style={{ '--scroll-progress': scrollProgress }}>
        {renderScene ? <VolumetricBackground style={{ opacity: cloudOpacity }} /> : null}
        <section className="hero-stage">
          <CodexOrb />
          <header className="hero-header">
            <p className="hero-eyebrow">autonomous yolo training data generation</p>
            <h1 className="hero-title" aria-label="yolodex" id="top">
              <span>{loading ? 'yolodex' : typedTitle || 'yolodex'}</span>
              <span className="typing-cursor" aria-hidden="true">
                |
              </span>
            </h1>
            <p className="hero-subtitle">
              turn gameplay footage into production-ready yolo datasets in minutes, not days of manual labeling.
            </p>
            <p className="hero-sub-kpi">engine-agnostic footage • yolo txt labels • train/eval loop built in</p>
            <div className="hero-actions">
              <a className="hero-btn hero-btn-primary" href="#onboarding">
                start onboarding
              </a>
              <a className="hero-btn hero-btn-secondary" href="#how">
                see live demo
              </a>
              <a
                className="hero-btn hero-btn-secondary"
                href="https://github.com/qtzx06/yolodex"
                target="_blank"
                rel="noreferrer"
              >
                github repo
              </a>
            </div>
          </header>
          <a className="scroll-cue" href="#how" aria-label="scroll to how it works">
            <span>scroll</span>
            <span className="scroll-cue-arrow" aria-hidden="true">
              ↓
            </span>
          </a>
        </section>
        <BentoSection
          pipelineIngest={pipelineIngest}
          pipelineAnnotate={pipelineAnnotate}
          pipelineTrain={pipelineTrain}
        />
        <WhyYolodex />
        <OnboardingSection />
        <GradualBlur
          target="page"
          position="bottom"
          height="8rem"
          strength={2.2}
          divCount={6}
          curve="bezier"
          exponential
          opacity={0.9}
          zIndex={2}
        />
        <Footer />
        <VignetteOverlay />
        <CVOverlay active={showCVOverlay} targets={cvTargets} />
      </main>
      <LoadingScreen visible={loading} />
    </>
  )
}

export default App
