import { useState } from 'react'
import './OnboardingSection.css'

export default function OnboardingSection() {
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [activeStep, setActiveStep] = useState(0)

  const handleCopy = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch {
      setCopiedIndex(null)
    }
  }

  const steps = [
    {
      number: '01',
      label: 'clone + install',
      time: '~2 min',
      code: `git clone https://github.com/qtzx06/yolodex.git
cd yolodex && bash setup.sh`,
      description: 'setup installs ffmpeg, yt-dlp, uv, and python deps',
    },
    {
      number: '02',
      label: 'set config.json',
      time: '~1 min',
      code: `{
  "project": "subway-surfers",
  "video_url": "https://www.youtube.com/watch?v=i0M4ARe9v0Y",
  "classes": ["player", "train", "coins", "powerup", "obstacle", "barrier"],
  "label_mode": "codex",
  "num_agents": 8,
  "target_accuracy": 0.75
}`,
      filename: 'config.json',
      description: 'codex mode is default and does not require api keys',
    },
    {
      number: '03',
      label: 'run autonomous loop',
      time: '1 min',
      code: `bash yolodex.sh`,
      description: 'runs collect -> label -> augment -> train -> eval automatically',
    },
    {
      number: '04',
      label: 'manual mode (optional)',
      time: '~2 min',
      code: `uv run .agents/skills/collect/scripts/run.py
bash .agents/skills/label/scripts/dispatch.sh 8
uv run .agents/skills/augment/scripts/run.py
uv run .agents/skills/train/scripts/run.py
uv run .agents/skills/eval/scripts/run.py`,
      description: 'use this when you want stage-by-stage control',
      highlight: true,
    },
  ]

  return (
    <section className="onboarding-section" id="onboarding">
      <div className="onboarding-container">
        <header className="onboarding-header">
          <p className="section-kicker">quick start</p>
          <h2 className="section-title">4 steps to production datasets</h2>
          <p className="section-description">
            from zero to trained model in under 10 minutes
          </p>
        </header>

        <div className="onboarding-content">
          {/* Step selector */}
          <div className="step-selector">
            {steps.map((step, i) => (
              <button
                type="button"
                key={i}
                className={`step-tab ${activeStep === i ? 'is-active' : ''}`}
                onClick={() => setActiveStep(i)}
              >
                <span className="step-tab-number">{step.number}</span>
                <span className="step-tab-label">{step.label}</span>
                <span className="step-tab-time">{step.time}</span>
              </button>
            ))}
          </div>

          {/* Active step display */}
          <div className="step-display">
            <div className="step-content">
              <div className="step-header">
                <div className="step-title">
                  <span className="step-number-large">{steps[activeStep].number}</span>
                  <div>
                    <h3>{steps[activeStep].label}</h3>
                    <p className="step-description">{steps[activeStep].description}</p>
                  </div>
                </div>
                <span className="step-time">{steps[activeStep].time}</span>
              </div>

              <div className="code-block">
                {steps[activeStep].filename && (
                  <div className="code-header">
                    <span className="code-filename">{steps[activeStep].filename}</span>
                  </div>
                )}
                <pre className="code-content">
                  <code>{steps[activeStep].code}</code>
                </pre>
                <button
                  type="button"
                  className="copy-button"
                  onClick={() => handleCopy(steps[activeStep].code, activeStep)}
                  aria-label="Copy code"
                >
                  {copiedIndex === activeStep ? (
                    <span className="copy-feedback">copied!</span>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M10 2H4C3.45 2 3 2.45 3 3v8h1V3h6V2zm2 2H7c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h5c.55 0 1-.45 1-1V5c0-.55-.45-1-1-1zm0 10H7V5h5v9z"/>
                    </svg>
                  )}
                </button>
              </div>

              {steps[activeStep].highlight && (
                <div className="step-highlight">
                  <span className="highlight-icon">→</span>
                  <span>outputs land in runs/&lt;project&gt;/ and team_exports/ for sharing</span>
                </div>
              )}
            </div>

            {/* Progress dots */}
            <div className="step-progress">
              {steps.map((_, i) => (
                <button
                  type="button"
                  key={i}
                  className={`progress-dot ${activeStep === i ? 'is-active' : ''}`}
                  onClick={() => setActiveStep(i)}
                  aria-label={`Go to step ${i + 1}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="onboarding-footer">
          <a href="https://github.com/qtzx06/yolodex" className="footer-link">
            <span className="link-icon">↗</span>
            view on github
          </a>
          <a href="https://github.com/qtzx06/yolodex/tree/main/docs" className="footer-link" target="_blank" rel="noreferrer">
            <span className="link-icon">docs</span>
            full documentation
          </a>
          <a href="https://github.com/qtzx06/yolodex/wiki" className="footer-link" target="_blank" rel="noreferrer">
            <span className="link-icon">howto</span>
            video tutorial
          </a>
        </div>
      </div>
    </section>
  )
}
