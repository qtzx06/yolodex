import * as THREE from 'three'
import { useEffect, useRef, useState } from 'react'

const noiseShader = `
vec3 mod289(vec3 x) {
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 mod289(vec4 x) {
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 permute(vec4 x) {
  return mod289(((x*34.0)+10.0)*x);
}

vec4 taylorInvSqrt(vec4 r) {
  return 1.79284291400159 - 0.85373472095314 * r;
}

float snoise(vec3 v) {
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
              i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 105.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
`

function createDotTexture(sizePx = 32) {
  const sizeHalf = sizePx * 0.5
  const canvas = document.createElement('canvas')
  canvas.width = sizePx
  canvas.height = sizePx
  const ctx = canvas.getContext('2d')
  if (!ctx) return new THREE.CanvasTexture(canvas)

  const gradient = ctx.createRadialGradient(sizeHalf, sizeHalf, 0, sizeHalf, sizeHalf, sizeHalf)
  gradient.addColorStop(0, '#d8e8ff')
  gradient.addColorStop(0.45, '#7aa2ff')
  gradient.addColorStop(1, '#2946d9')

  const circle = new Path2D()
  circle.arc(sizeHalf, sizeHalf, sizeHalf, 0, 2 * Math.PI)
  ctx.fillStyle = gradient
  ctx.fill(circle)

  return new THREE.CanvasTexture(canvas)
}

function setupNoiseShader(material, { radius, particleSizeMin, particleSizeMax }) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.time = { value: 0 }
    shader.uniforms.radius = { value: radius }
    shader.uniforms.particleSizeMin = { value: particleSizeMin }
    shader.uniforms.particleSizeMax = { value: particleSizeMax }

    shader.vertexShader = `
uniform float particleSizeMax;
uniform float particleSizeMin;
uniform float radius;
uniform float time;
${noiseShader}
${shader.vertexShader}
    `

    shader.vertexShader = shader.vertexShader.replace(
      '#include <begin_vertex>',
      `
vec3 p = position;
float n = snoise(vec3(p.x*.6 + time*0.2, p.y*0.4 + time*0.3, p.z*.2 + time*0.2));
p += n * 0.4;
float l = radius / length(p);
p *= l;
float s = mix(particleSizeMin, particleSizeMax, n);
vec3 transformed = vec3(p.x, p.y, p.z);
      `,
    )

    shader.vertexShader = shader.vertexShader.replace('gl_PointSize = size;', 'gl_PointSize = s;')
    material.userData.shader = shader
  }
}

export default function NoiseOrb({ size = 280 }) {
  const mountRef = useRef(null)
  const [dimensions, setDimensions] = useState({ width: `${size}px`, height: `${size}px` })

  useEffect(() => {
    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth < 640 ? '200px' : `${size}px`,
        height: window.innerWidth < 640 ? '200px' : `${size}px`,
      })
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [size])

  useEffect(() => {
    const container = mountRef.current
    if (!container) return undefined

    container.innerHTML = ''

    const isMobile = window.innerWidth < 640
    const radius = isMobile ? 0.5 : 0.65
    const detail = 26
    const particleSizeMin = 0.01
    const particleSizeMax = 0.08

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      75,
      (container.clientWidth || 1) / (container.clientHeight || 1),
      0.1,
      1000,
    )
    camera.position.z = 2

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.setClearColor(0x000000, 0)
    renderer.domElement.style.opacity = '0'
    renderer.domElement.style.transform = 'scale(0.96)'
    renderer.domElement.style.transition =
      'opacity 900ms cubic-bezier(0.2, 0.8, 0.2, 1), transform 900ms cubic-bezier(0.2, 0.8, 0.2, 1)'
    renderer.domElement.style.willChange = 'opacity, transform'
    container.appendChild(renderer.domElement)

    const geometry = new THREE.IcosahedronGeometry(1, detail)
    const material = new THREE.PointsMaterial({
      map: createDotTexture(),
      blending: THREE.NormalBlending,
      color: 0xffffff,
      opacity: 0.86,
      transparent: true,
      depthTest: false,
    })
    setupNoiseShader(material, { radius, particleSizeMin, particleSizeMax })
    const mesh = new THREE.Points(geometry, material)
    scene.add(mesh)

    const handleResize = () => {
      const width = container.clientWidth
      const height = container.clientHeight
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }

    let animationFrameId = 0
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)
      const time = performance.now() * 0.001
      mesh.rotation.set(0, time * 0.2, 0)
      if (material.userData?.shader?.uniforms?.time) {
        material.userData.shader.uniforms.time.value = time
      }
      renderer.render(scene, camera)
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    animate()
    requestAnimationFrame(() => {
      renderer.domElement.style.opacity = '1'
      renderer.domElement.style.transform = 'scale(1)'
    })

    return () => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(animationFrameId)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      material.map?.dispose?.()
      geometry.dispose()
      material.dispose()
      renderer.dispose()
    }
  }, [size])

  return (
    <div
      ref={mountRef}
      style={{
        width: dimensions.width,
        height: dimensions.height,
      }}
    />
  )
}
