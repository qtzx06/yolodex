import './Footer.css'

export default function Footer() {
  return (
    <footer className="site-footer" id="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3 className="footer-title">yolodex</h3>
            <p className="footer-description">
              autonomous yolo training data generation.
              turn gameplay footage into production-ready
              datasets in minutes.
            </p>
            <div className="footer-badges">
              <span className="badge">v1.0.0</span>
              <span className="badge">mit license</span>
              <span className="badge">open source</span>
            </div>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">quick links</h4>
            <div className="footer-links">
              <a href="#how" className="footer-link">
                <span className="link-arrow">→</span>
                how it works
              </a>
              <a href="#trust" className="footer-link">
                <span className="link-arrow">→</span>
                why yolodex
              </a>
              <a href="#onboarding" className="footer-link">
                <span className="link-arrow">→</span>
                get started
              </a>
              <a href="https://github.com/qtzx06/yolodex/wiki" className="footer-link" target="_blank" rel="noreferrer">
                <span className="link-arrow">→</span>
                documentation
              </a>
            </div>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">resources</h4>
            <div className="footer-links">
              <a href="https://github.com/qtzx06" className="footer-link" target="_blank" rel="noreferrer">
                <span className="link-arrow">↗</span>
                qtzx06
              </a>
              <a href="https://github.com/philip-chen6" className="footer-link" target="_blank" rel="noreferrer">
                <span className="link-arrow">↗</span>
                philip-chen6
              </a>
              <a href="https://github.com/stephenhungg" className="footer-link" target="_blank" rel="noreferrer">
                <span className="link-arrow">↗</span>
                stephenhungg
              </a>
              <a href="https://github.com/ryunzz" className="footer-link" target="_blank" rel="noreferrer">
                <span className="link-arrow">↗</span>
                ryunzz
              </a>
            </div>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">team</h4>
            <div className="footer-team">
              <a href="https://github.com/stephenhungg" className="team-member" target="_blank" rel="noreferrer">
                stephen hung
              </a>
              <a href="https://github.com/qtzx06" className="team-member" target="_blank" rel="noreferrer">
                joshua lin
              </a>
              <a href="https://github.com/ryunzz" className="team-member" target="_blank" rel="noreferrer">
                ryan ni
              </a>
              <a href="https://github.com/philip-chen6" className="team-member" target="_blank" rel="noreferrer">
                philip chen
              </a>
            </div>
            <p className="footer-note">
              built at openai codex hackathon
            </p>
          </div>
        </div>

        <div className="footer-bottom">
          <p className="footer-copyright">
            © 2024 yolodex team. all rights reserved.
          </p>
          <a href="https://github.com/qtzx06/yolodex" className="footer-link" target="_blank" rel="noreferrer">
            <span className="link-arrow">↗</span>
            project repo
          </a>
        </div>
      </div>
    </footer>
  )
}
