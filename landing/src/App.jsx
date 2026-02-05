import { useEffect, useState } from 'react'
import VolumetricBackground from './components/VolumetricBackground'
import CodexOrb from './components/CodexOrb'
import VignetteOverlay from './components/VignetteOverlay'
import LoadingScreen from './components/LoadingScreen'
import GradualBlur from './components/GradualBlur'
import BentoSection from './components/BentoSection'
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

  return (
    <>
      {renderScene ? (
        <main className="app-shell" style={{ '--scroll-progress': scrollProgress }}>
          <VolumetricBackground style={{ opacity: cloudOpacity }} />
          <nav className="top-nav">
            <a href="#how">see it in action</a>
            <a href="#trust">why yolodex</a>
            <a href="#onboarding">get started</a>
            <a href="#footer">github</a>
          </nav>
          <section className="hero-stage">
            <CodexOrb />
            <header className="hero-header">
              <p className="hero-eyebrow">autonomous yolo training data generation</p>
              <h1 className="hero-title" aria-label="yolodex" id="top">
                <span>{typedTitle || ' '}</span>
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
          <section className="section-wrap reveal" id="trust">
            <p className="section-kicker">why yolodex</p>
            <h2 className="section-title">faster than manual labeling, built for iteration</h2>
            <div className="trust-grid">
              <article className="trust-item glass reveal">
                <h3>time savings</h3>
                <p>automates collect → label → augment → train → eval with one loop command.</p>
              </article>
              <article className="trust-item glass reveal">
                <h3>supported inputs</h3>
                <p>works with gameplay footage regardless of engine (unity, unreal, custom) since input is video.</p>
              </article>
              <article className="trust-item glass reveal">
                <h3>model stack</h3>
                <p>default training on yolov8n with configurable modes and dataset controls in `config.json`.</p>
              </article>
              <article className="trust-item glass reveal">
                <h3>open workflow</h3>
                <p>skill-based architecture, project-isolated runs, and codex-native automation via `AGENTS.md`.</p>
              </article>
            </div>
          </section>
          <section className="onboarding-section reveal" id="onboarding">
            <p className="section-kicker">onboarding</p>
            <h2 className="section-title">streamlined teammate setup</h2>
            <div className="onboarding-flow">
              <article className="flow-step reveal">
                <p className="flow-index">01</p>
                <div className="flow-body">
                  <p className="step-label">clone + install (2 min)</p>
                  <pre>{`git clone <repo-url> && cd yolodex
bash setup.sh`}</pre>
                </div>
              </article>
              <article className="flow-step reveal">
                <p className="flow-index">02</p>
                <div className="flow-body">
                  <p className="step-label">create .env</p>
                  <pre>{`OPENAI_API_KEY=sk-...
GEMINI_API_KEY=... # optional`}</pre>
                </div>
              </article>
              <article className="flow-step reveal">
                <p className="flow-index">03</p>
                <div className="flow-body">
                  <p className="step-label">configure project/classes</p>
                  <pre>{`{
  "project": "fortnite-clips",
  "video_url": "https://youtube.com/...",
  "classes": ["player", "weapon"],
  "label_mode": "gpt | gemini | cua+sam"
}`}</pre>
                </div>
              </article>
              <article className="flow-step reveal" id="run-it">
                <p className="flow-index">04</p>
                <div className="flow-body">
                  <p className="step-label">run</p>
                  <pre>{`source .env && bash yolodex.sh`}</pre>
                </div>
              </article>
            </div>
          </section>
          <footer className="site-footer reveal" id="footer">
            <p>built at openai codex hackathon</p>
            <p>stephen hung • joshua lin • ryan ni • philip chen</p>
            <p>
              <a href="https://github.com/" target="_blank" rel="noreferrer">
                github
              </a>{' '}
              •{' '}
              <a href="#onboarding">docs</a> •{' '}
              <a href="mailto:partnercomms@openai.com">contact</a>
            </p>
          </footer>
          <GradualBlur
            target="page"
            position="bottom"
            height="8rem"
            strength={2.2}
            divCount={6}
            curve="bezier"
            exponential
            opacity={0.9}
            zIndex={-94}
          />
          <VignetteOverlay />
          <CVOverlay active={showCVOverlay} targets={cvTargets} />
        </main>
      ) : null}
      <LoadingScreen visible={loading} />
    </>
  )
}

export default App
