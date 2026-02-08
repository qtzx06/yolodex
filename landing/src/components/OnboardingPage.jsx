import VolumetricBackground from './VolumetricBackground'
import VignetteOverlay from './VignetteOverlay'

export default function OnboardingPage() {
  return (
    <main className="app-shell onboarding-page">
      <VolumetricBackground />
      <section className="onboarding-section" id="onboarding">
        <a className="page-back-link glass" href="/">
          ← back to landing
        </a>
        <p className="section-kicker">onboarding</p>
        <h1 className="section-title">yolodex onboarding</h1>
        <div className="onboarding-flow">
          <article className="flow-step">
            <p className="flow-index">01</p>
            <div className="flow-body">
              <p className="step-label">clone + install (2 min)</p>
              <pre>{`git clone <repo-url> && cd yolodex
bash setup.sh`}</pre>
              <p>setup installs ffmpeg, yt-dlp, uv, and python deps. if something fails, it tells you what is missing.</p>
            </div>
          </article>

          <article className="flow-step">
            <p className="flow-index">02</p>
            <div className="flow-body">
              <p className="step-label">api keys (30 sec)</p>
              <pre>{`# .env
OPENAI_API_KEY=sk-...
# optional
GEMINI_API_KEY=...`}</pre>
              <p>never commit `.env` (already gitignored).</p>
            </div>
          </article>

          <article className="flow-step">
            <p className="flow-index">03</p>
            <div className="flow-body">
              <p className="step-label">pick video + classes (`config.json`)</p>
              <pre>{`{
  "project": "fortnite-clips",
  "video_url": "https://youtube.com/...",
  "classes": ["player", "weapon", "vehicle"],
  "label_mode": "gpt | gemini | cua+sam"
}`}</pre>
              <p>choose label mode by speed vs bbox quality.</p>
            </div>
          </article>

          <article className="flow-step" id="run-it">
            <p className="flow-index">04</p>
            <div className="flow-body">
              <p className="step-label">run it</p>
              <h3>option a — codex interactive</h3>
              <p>open codex in `yolodex/` and ask it to train from your url/classes/project.</p>
              <h3>option b — manual skills</h3>
              <pre>{`source .env
uv run .agents/skills/collect/scripts/run.py
uv run .agents/skills/label/scripts/run.py
uv run .agents/skills/augment/scripts/run.py
uv run .agents/skills/train/scripts/run.py
uv run .agents/skills/eval/scripts/run.py`}</pre>
              <h3>option c — autonomous loop</h3>
              <pre>{`source .env && bash yolodex.sh`}</pre>
            </div>
          </article>
        </div>

        <section className="advanced-options glass" aria-label="results and key things to know">
          <p className="advanced-options-title">results + key things to know</p>
          <p>
            `runs/&lt;project&gt;/eval_results.json` has mAP/precision/recall and class breakdown.
            `runs/&lt;project&gt;/weights/best.pt` is your trained model. output is isolated per project.
            gpt mode is easiest, gemini has native bbox, cua+sam is best quality but slower. for
            parallel labeling: `bash .agents/skills/label/scripts/dispatch.sh 8`.
          </p>
        </section>
      </section>

      <footer className="site-footer" id="credits">
        <p>built at openai codex hackathon</p>
        <p>stephen hung • joshua lin • ryan ni • philip chen</p>
      </footer>
      <VignetteOverlay />
    </main>
  )
}
