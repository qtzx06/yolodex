import { useState } from 'react'
import './BentoSection.css'

export default function BentoSection({
  pipelineIngest,
  pipelineAnnotate,
  pipelineTrain
}) {
  const [activeStage, setActiveStage] = useState(2)

  const stages = [
    {
      index: 1,
      title: "ingest footage",
      description: "youtube urls or local mp4 files",
      icon: pipelineIngest,
      output: "raw frames extracted"
    },
    {
      index: 2,
      title: "auto annotate",
      description: "parallel labeling with ai models",
      icon: pipelineAnnotate,
      output: "bbox annotations generated"
    },
    {
      index: 3,
      title: "export + train",
      description: "yolo format with eval metrics",
      icon: pipelineTrain,
      output: "model weights + metrics"
    }
  ]

  return (
    <section className="bento-section" id="how">
      <div className="bento-header">
        <p className="section-kicker">see it in action</p>
        <h2 className="section-title">from gameplay footage to trained yolo model</h2>
      </div>

      <div className="bento-grid">
        {/* Main preview panel */}
        <div className="bento-preview">
          <div className="preview-header">
            <span className="preview-label">live output preview</span>
            <span className="preview-stage">stage {activeStage}: {stages[activeStage - 1].title}</span>
          </div>

          <div className="preview-frame">
            <div className="preview-image">
              {/* Simulated game footage with annotations */}
              <div className="bbox bbox-player">
                <span className="bbox-label">player</span>
                <span className="bbox-conf">0.94</span>
              </div>
              <div className="bbox bbox-weapon">
                <span className="bbox-label">weapon</span>
                <span className="bbox-conf">0.87</span>
              </div>
              <div className="bbox bbox-vehicle">
                <span className="bbox-label">vehicle</span>
                <span className="bbox-conf">0.91</span>
              </div>

              {/* Stage-specific overlays */}
              {activeStage === 1 && (
                <div className="stage-overlay stage-ingest">
                  <div className="scan-effect" />
                  <span className="overlay-text">extracting frames...</span>
                </div>
              )}
              {activeStage === 2 && (
                <div className="stage-overlay stage-annotate">
                  <div className="detection-grid" />
                </div>
              )}
              {activeStage === 3 && (
                <div className="stage-overlay stage-train">
                  <div className="metrics-overlay">
                    <div className="metric">mAP: 0.89</div>
                    <div className="metric">precision: 0.92</div>
                    <div className="metric">recall: 0.86</div>
                  </div>
                </div>
              )}
            </div>

            <div className="preview-footer">
              <code className="output-format">
                {activeStage === 1 && "frames/001.jpg, frames/002.jpg, ..."}
                {activeStage === 2 && "0 0.415 0.234 0.128 0.195  # class x y w h"}
                {activeStage === 3 && "runs/train/weights/best.pt"}
              </code>
            </div>
          </div>
        </div>

        {/* Pipeline steps */}
        <div className="bento-pipeline">
          {stages.map((stage) => (
            <button
              key={stage.index}
              className={`bento-stage ${activeStage === stage.index ? 'is-active' : ''}`}
              onClick={() => setActiveStage(stage.index)}
              onMouseEnter={() => setActiveStage(stage.index)}
            >
              <div className="stage-number">{String(stage.index).padStart(2, '0')}</div>

              <div className="stage-content">
                <div className="stage-icon">
                  <img src={stage.icon} alt={stage.title} />
                </div>

                <div className="stage-info">
                  <h3 className="stage-title">{stage.title}</h3>
                  <p className="stage-description">{stage.description}</p>
                  <span className="stage-output">→ {stage.output}</span>
                </div>
              </div>

              {stage.index < 3 && (
                <div className="stage-connector">
                  <svg viewBox="0 0 100 2" className="connector-line">
                    <line x1="0" y1="1" x2="100" y2="1"
                      stroke="url(#flow-gradient)"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                      className={activeStage >= stage.index ? 'is-flowing' : ''}
                    />
                    <defs>
                      <linearGradient id="flow-gradient">
                        <stop offset="0%" stopColor="rgba(100, 140, 255, 0.2)" />
                        <stop offset="50%" stopColor="rgba(120, 160, 255, 0.8)" />
                        <stop offset="100%" stopColor="rgba(100, 140, 255, 0.2)" />
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Stats panel */}
        <div className="bento-stats">
          <h3 className="stats-title">typical results</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">5min</span>
              <span className="stat-label">footage → dataset</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">10k+</span>
              <span className="stat-label">auto labels/hour</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">0.9+</span>
              <span className="stat-label">typical mAP</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">100%</span>
              <span className="stat-label">automated</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}