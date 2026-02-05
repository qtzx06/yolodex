import { useEffect, useState } from 'react'

function confidenceFromTarget(target, index) {
  let hash = 17 + index * 31
  const seed = `${target.selector}:${target.label}`

  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 33 + seed.charCodeAt(i)) % 1000003
  }

  return 0.84 + (hash % 15) / 100
}

function hashSeed(value) {
  let hash = 23
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 37 + value.charCodeAt(i)) % 1000003
  }
  return hash
}

function animatedConfidence(base, seedValue, frame) {
  const hash = hashSeed(seedValue)
  const phase = (hash % 360) * (Math.PI / 180)
  const speed = 0.12 + (hash % 5) * 0.02
  const wave = Math.sin(frame * speed + phase)
  const drift = ((hash % 9) - 4) * 0.0007
  const raw = base + wave * 0.018 + drift
  const clamped = Math.max(0.6, Math.min(0.999, raw))
  return clamped.toFixed(2)
}

function isRectVisible(rect) {
  if (rect.width < 10 || rect.height < 10) return false
  if (rect.bottom < 0 || rect.top > window.innerHeight) return false
  if (rect.right < 0 || rect.left > window.innerWidth) return false
  return true
}

function getTextRects(element) {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT)
  const result = []
  let node = walker.nextNode()

  while (node) {
    if (node.textContent && node.textContent.trim()) {
      const range = document.createRange()
      range.selectNodeContents(node)
      const lineRects = Array.from(range.getClientRects())
      lineRects.forEach((lineRect) => {
        const rect = {
          left: lineRect.left,
          top: lineRect.top,
          right: lineRect.right,
          bottom: lineRect.bottom,
          width: lineRect.width,
          height: lineRect.height,
        }
        if (isRectVisible(rect)) result.push(rect)
      })
      range.detach()
    }
    node = walker.nextNode()
  }

  return result
}

function rectWithRoi(rect, target) {
  if (!target.roi) return rect

  const roi = target.roi ?? { x: 0, y: 0, w: 1, h: 1 }
  const x = Math.min(Math.max(roi.x ?? 0, 0), 1)
  const y = Math.min(Math.max(roi.y ?? 0, 0), 1)
  const w = Math.min(Math.max(roi.w ?? 1, 0.05), 1 - x)
  const h = Math.min(Math.max(roi.h ?? 1, 0.05), 1 - y)

  return {
    left: rect.left + rect.width * x,
    top: rect.top + rect.height * y,
    right: rect.left + rect.width * x + rect.width * w,
    bottom: rect.top + rect.height * y + rect.height * h,
    width: rect.width * w,
    height: rect.height * h,
  }
}

function toBox(rect, target, key, index) {
  const padding = target.padding ?? 0
  const left = Math.max(4, rect.left - padding)
  const top = Math.max(4, rect.top - padding)
  const right = Math.min(window.innerWidth - 4, rect.right + padding)
  const bottom = Math.min(window.innerHeight - 4, rect.bottom + padding)

  const width = Math.max(10, right - left)
  const height = Math.max(10, bottom - top)
  if (width < 10 || height < 10) return null

  return {
    id: `${key}-${index}`,
    label: target.label,
    confidenceBase: confidenceFromTarget(target, index),
    left,
    top,
    width,
    height,
  }
}

function getElementBoxes(target, targetIndex) {
  const elements = target.multiple
    ? Array.from(document.querySelectorAll(target.selector))
    : [document.querySelector(target.selector)].filter(Boolean)

  if (!elements.length) return []

  const boxes = []
  elements.forEach((element, elementIndex) => {
    const elementRect = element.getBoundingClientRect()
    if (!isRectVisible(elementRect)) return

    const key = `${target.selector}-${targetIndex}-${elementIndex}`
    if (target.tightText) {
      const textRects = getTextRects(element)
      if (textRects.length) {
        textRects.forEach((textRect, textIndex) => {
          const box = toBox(textRect, target, key, textIndex)
          if (box) boxes.push(box)
        })
        return
      }
    }

    const roiRect = rectWithRoi(elementRect, target)
    const box = toBox(roiRect, target, key, 0)
    if (box) boxes.push(box)
  })

  return boxes
}

function clampBoxToViewport(box) {
  const left = Math.max(4, Math.min(window.innerWidth - 14, box.left))
  const top = Math.max(4, Math.min(window.innerHeight - 14, box.top))
  const width = Math.max(10, Math.min(box.width, window.innerWidth - left - 4))
  const height = Math.max(10, Math.min(box.height, window.innerHeight - top - 4))
  return {
    ...box,
    left,
    top,
    width,
    height,
  }
}

export default function CVOverlay({ active, targets }) {
  const [boxes, setBoxes] = useState([])
  const [frame, setFrame] = useState(0)

  useEffect(() => {
    if (!active) return undefined

    let rafId = 0
    let intervalId = 0

    const updateBoxes = () => {
      const anchors = targets.flatMap((target, index) => getElementBoxes(target, index))
      const nextBoxes = anchors.map(clampBoxToViewport)
      setBoxes(nextBoxes)
      rafId = 0
    }

    const scheduleUpdate = () => {
      if (rafId) return
      rafId = window.requestAnimationFrame(updateBoxes)
    }

    scheduleUpdate()
    window.addEventListener('scroll', scheduleUpdate, { passive: true })
    window.addEventListener('resize', scheduleUpdate, { passive: true })
    intervalId = window.setInterval(scheduleUpdate, 900)

    return () => {
      if (rafId) window.cancelAnimationFrame(rafId)
      if (intervalId) window.clearInterval(intervalId)
      window.removeEventListener('scroll', scheduleUpdate)
      window.removeEventListener('resize', scheduleUpdate)
    }
  }, [active, targets])

  useEffect(() => {
    if (!active) return undefined

    const timer = window.setInterval(() => {
      setFrame((value) => value + 1)
    }, 170)

    return () => window.clearInterval(timer)
  }, [active])

  if (!active) return null

  return (
    <div className="cv-overlay" aria-hidden="true">
      {boxes.map((box) => {
        const confidence = animatedConfidence(box.confidenceBase, box.id, frame)
        return (
          <div
            className="cv-box"
            key={box.id}
            data-label={box.label}
            style={{
              left: `${box.left}px`,
              top: `${box.top}px`,
              width: `${box.width}px`,
              height: `${box.height}px`,
              animationDelay: `${(box.left + box.top) % 160}ms`,
            }}
          >
            <span className="cv-label">
              <span className="cv-label-name">{box.label}</span>
              <span className="cv-label-score">{confidence}</span>
            </span>
          </div>
        )
      })}
    </div>
  )
}
