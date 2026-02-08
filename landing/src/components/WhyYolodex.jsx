import { useState, useRef, useEffect } from 'react'
import { useOutsideClick } from '../hooks/use-outside-click'
import pipelineIngest from '../assets/pipeline-ingest.svg'
import pipelineAnnotate from '../assets/pipeline-annotate.svg'
import pipelineTrain from '../assets/pipeline-train.svg'
import turnaroundTrainingImage from '../assets/turnaround-training.png'
import mapScoreImage from '../assets/map-score.png'
import fullyAutomatedImage from '../assets/fully-automated.png'
import engineAgnosticImage from '../assets/engine-agnostic.png'
import hackableDesignImage from '../assets/hackable-design.png'
import './WhyYolodex.css'

export default function WhyYolodex() {
  const [active, setActive] = useState(null)
  const ref = useRef(null)
  const carouselRef = useRef(null)

  // Scroll to middle card on mount
  useEffect(() => {
    if (carouselRef.current) {
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        const container = carouselRef.current
        const cards = container.querySelectorAll('.carousel-card')
        if (cards.length >= 3) {
          const middleCard = cards[2] // 3rd card (flexibility) is the middle
          const containerWidth = container.offsetWidth
          const cardLeft = middleCard.offsetLeft
          const cardWidth = middleCard.offsetWidth
          const scrollPosition = cardLeft - (containerWidth / 2) + (cardWidth / 2)

          // Set scroll position immediately (no animation on initial load)
          container.scrollLeft = scrollPosition
        }
      }, 100)
    }
  }, [])

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === 'Escape') {
        setActive(null)
      }
    }

    if (active) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'auto'
    }

    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = 'auto'
    }
  }, [active])

  useOutsideClick(ref, () => setActive(null))

  const cards = [
    {
      id: 1,
      category: "speed",
      title: "5-minute turnaround",
      description: "from raw footage to production-ready yolo dataset",
      content: (
        <div className="card-content">
          <div className="content-section">
            <h3>lightning fast pipeline</h3>
            <p>
              our parallel processing architecture handles footage ingestion, frame extraction,
              and auto-labeling simultaneously. what used to take days of manual work now
              happens in minutes.
            </p>
          </div>
          <div className="content-stats">
            <div className="stat">
              <span className="stat-number">10k+</span>
              <span className="stat-label">labels per hour</span>
            </div>
            <div className="stat">
              <span className="stat-number">95%</span>
              <span className="stat-label">time saved</span>
            </div>
            <div className="stat">
              <span className="stat-number">∞</span>
              <span className="stat-label">scale potential</span>
            </div>
          </div>
          <div className="content-visual">
            <div className="speed-bars">
              <div className="bar bar-manual">manual: 8 hours</div>
              <div className="bar bar-yolodex">yolodex: 5 min</div>
            </div>
          </div>
        </div>
      ),
      gradient: 'linear-gradient(135deg, #21406a 0%, #2a80bb 100%)',
      media: turnaroundTrainingImage,
    },
    {
      id: 2,
      category: "accuracy",
      title: "0.9+ mAP scores",
      description: "ai-powered labeling with built-in quality checks",
      content: (
        <div className="card-content">
          <div className="content-section">
            <h3>intelligent annotation</h3>
            <p>
              multiple ai models (gpt-4v, gemini, claude) work in parallel to ensure
              high-quality bounding boxes. automatic validation catches and fixes
              edge cases that humans might miss.
            </p>
          </div>
          <div className="content-metrics">
            <div className="metric-row">
              <span className="metric-label">precision</span>
              <div className="metric-bar">
                <div className="metric-fill" style={{ width: '92%' }}>0.92</div>
              </div>
            </div>
            <div className="metric-row">
              <span className="metric-label">recall</span>
              <div className="metric-bar">
                <div className="metric-fill" style={{ width: '86%' }}>0.86</div>
              </div>
            </div>
            <div className="metric-row">
              <span className="metric-label">f1 score</span>
              <div className="metric-bar">
                <div className="metric-fill" style={{ width: '89%' }}>0.89</div>
              </div>
            </div>
          </div>
          <div className="content-section">
            <p className="content-note">
              automatic bad frame detection and re-labeling ensures consistent quality
              across your entire dataset.
            </p>
          </div>
        </div>
      ),
      gradient: 'linear-gradient(135deg, #3a1f3f 0%, #b33f58 100%)',
      media: mapScoreImage,
    },
    {
      id: 3,
      category: "flexibility",
      title: "engine agnostic",
      description: "works with any game engine or video source",
      content: (
        <div className="card-content">
          <div className="content-section">
            <h3>universal compatibility</h3>
            <p>
              doesn't matter if your footage comes from unity, unreal, godot, or
              even screen recordings. if it's a video, we can process it.
            </p>
          </div>
          <div className="content-grid">
            <div className="grid-item">
              <span className="grid-icon">u</span>
              <span className="grid-label">unity</span>
            </div>
            <div className="grid-item">
              <span className="grid-icon">ue</span>
              <span className="grid-label">unreal</span>
            </div>
            <div className="grid-item">
              <span className="grid-icon">g</span>
              <span className="grid-label">godot</span>
            </div>
            <div className="grid-item">
              <span className="grid-icon">obs</span>
              <span className="grid-label">obs</span>
            </div>
            <div className="grid-item">
              <span className="grid-icon">yt</span>
              <span className="grid-label">youtube</span>
            </div>
            <div className="grid-item">
              <span className="grid-icon">mp4</span>
              <span className="grid-label">mp4/avi</span>
            </div>
          </div>
          <div className="content-section">
            <p className="content-note">
              supports youtube urls, local files, and streaming inputs.
              handles any resolution from 480p to 4k.
            </p>
          </div>
        </div>
      ),
      gradient: 'linear-gradient(135deg, #5a2a2a 0%, #c57a33 100%)',
      media: engineAgnosticImage,
    },
    {
      id: 4,
      category: "automation",
      title: "fully automated",
      description: "one command from footage to trained model",
      content: (
        <div className="card-content">
          <div className="content-section">
            <h3>end-to-end pipeline</h3>
            <p>
              just run <code>bash yolodex.sh</code> and walk away. handles everything
              from video download to model training and evaluation.
            </p>
          </div>
          <div className="content-flow">
            <div className="flow-step">
              <span className="step-num">1</span>
              <span className="step-text">ingest footage</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">
              <span className="step-num">2</span>
              <span className="step-text">extract frames</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">
              <span className="step-num">3</span>
              <span className="step-text">auto label</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">
              <span className="step-num">4</span>
              <span className="step-text">augment data</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">
              <span className="step-num">5</span>
              <span className="step-text">train model</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">
              <span className="step-num">6</span>
              <span className="step-text">eval metrics</span>
            </div>
          </div>
          <div className="content-section">
            <p className="content-note">
              includes automatic data augmentation, train/val split, and comprehensive
              evaluation reports with confusion matrices.
            </p>
          </div>
        </div>
      ),
      gradient: 'linear-gradient(135deg, #1d4258 0%, #3d8f9d 100%)',
      media: fullyAutomatedImage,
    },
    {
      id: 5,
      category: "open source",
      title: "hackable by design",
      description: "skill-based architecture for easy customization",
      content: (
        <div className="card-content">
          <div className="content-section">
            <h3>modular skills system</h3>
            <p>
              built on codex's skill architecture. swap labeling models, add custom
              augmentations, or integrate your own validation logic with simple
              markdown files.
            </p>
          </div>
          <div className="content-code">
            <pre>{`# skills/custom_label.md
---
model: gemini-1.5-pro
confidence_threshold: 0.85
---

detect gameplay elements with
focus on: {{ classes }}
output: yolo format`}</pre>
          </div>
          <div className="content-features">
            <div className="feature">
              <span className="feature-check">✓</span>
              <span>drop-in model swapping</span>
            </div>
            <div className="feature">
              <span className="feature-check">✓</span>
              <span>custom class definitions</span>
            </div>
            <div className="feature">
              <span className="feature-check">✓</span>
              <span>extensible validation hooks</span>
            </div>
            <div className="feature">
              <span className="feature-check">✓</span>
              <span>project-isolated runs</span>
            </div>
          </div>
        </div>
      ),
      gradient: 'linear-gradient(135deg, #4b3522 0%, #c0865f 100%)',
      media: hackableDesignImage,
    },
  ]

  return (
    <section className="why-yolodex" id="trust">
      <div className="why-header">
        <p className="section-kicker">why yolodex</p>
        <h2 className="section-title">built for speed, accuracy, and scale</h2>
      </div>

      <div className="cards-carousel" ref={carouselRef}>
        <div className="carousel-track">
          {cards.map((card) => (
            <button
              type="button"
              key={card.id}
              className={`carousel-card ${active?.id === card.id ? 'is-active' : ''}`}
              onClick={() => setActive(card)}
              style={{ '--card-gradient': card.gradient }}
            >
              <div className="card-header">
                <span className="card-category">{card.category}</span>
                <h3 className="card-title">{card.title}</h3>
                <p className="card-description">{card.description}</p>
              </div>
              <div className="card-preview">
                <img className="card-media" src={card.media} alt={`${card.title} feature preview`} />
              </div>
            </button>
          ))}
        </div>
      </div>

      {active && (
        <div className="modal-overlay">
          <div className="modal-backdrop" />
          <div className="modal-container">
            <div
              ref={ref}
              className="modal-content"
              style={{ '--card-gradient': active.gradient }}
            >
              <button
                type="button"
                className="modal-close"
                onClick={() => setActive(null)}
                aria-label="Close modal"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>

              <div className="modal-header">
                <span className="modal-category">{active.category}</span>
                <h2 className="modal-title">{active.title}</h2>
                <p className="modal-description">{active.description}</p>
              </div>

              <div className="modal-body">
                <div className="modal-media-wrap">
                  <img className="modal-media" src={active.media} alt={`${active.title} feature preview`} />
                </div>
                {active.content}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
