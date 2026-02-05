import { useEffect, useRef } from 'react'

const vert = `#version 300 es
in vec2 a_position;
void main() {
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`

const frag = `#version 300 es
precision highp float;

uniform vec2 iResolution;
uniform float iTime;

out vec4 outColor;

void mainImage( out vec4 O, vec2 I )
{
  float i = 0.0;
  float d = 0.0;
  float s = 0.0;
  float sd = 0.0;
  float n = 0.0;
  float t = iTime;
  float m = 1.0;
  float l = 0.0;

  vec3 p = vec3(0.0);
  vec3 k = vec3(0.0);
  vec3 r = vec3(iResolution, 1.0);

  mat2 R = mat2(cos(sin(t/2.0)*.785 + vec4(0.0,33.0,11.0,0.0)));

  O = vec4(0.0);
  for(; i++ < 100.0; ){
    p = vec3(((I+I-r.xy)/r.y)*1.12 + vec2(0.78, 0.0), d-10.0);
    l = length(p.xy-vec2(-0.95+sin(t)/4.0,.28+sin(t+t)/6.0));
    float orb = max(l * 3.0, 0.001);

    p.xy *= d;
    if(abs(p.x)>6.0) break;

    p.xz *= R;

    k = p;
    p *= .5;
    for(n = .01; n < 1.0; n += n){
      p.y += .9+abs(dot(sin(p.x + 2.0*t+p/n), .2+p-p )) * n;
    }

    sd = mix(
      sin(length(ceil(k*8.0).x+k)),
      mix(sin(length(p)-.2),l,.3-l),
      smoothstep(5.5, 6.0, p.y)
    );

    d += s = .012+.08*abs(max(sd,length(k)-5.0)-i/150.0);
    O += max(sin(vec4(1.0,2.0,3.0,1.0)+i*.5)*1.5/s+vec4(1.0,2.0,3.0,1.0)*.04/orb,-length(k*k));
  }

  O = tanh(O*O/8e5)*m;
}

void main() {
  vec4 c;
  mainImage(c, gl_FragCoord.xy);
  float a = smoothstep(0.08, 0.45, max(max(c.r, c.g), c.b));
  outColor = vec4(c.rgb * a, a);
}
`

function compileShader(gl, type, source) {
  const shader = gl.createShader(type)
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || 'shader compile failed'
    gl.deleteShader(shader)
    throw new Error(message)
  }
  return shader
}

export default function GemmariumHero({ children, className = '' }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl2', { antialias: false, alpha: true, premultipliedAlpha: true })
    if (!gl) {
      console.error('webgl2 not supported')
      return
    }

    const program = gl.createProgram()
    const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vert)
    const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, frag)

    gl.attachShader(program, vertexShader)
    gl.attachShader(program, fragmentShader)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      const message = gl.getProgramInfoLog(program) || 'program link failed'
      throw new Error(message)
    }
    gl.useProgram(program)

    const vertices = new Float32Array([
      -1, -1, 1, -1, -1, 1,
      -1, 1, 1, -1, 1, 1,
    ])

    const vao = gl.createVertexArray()
    gl.bindVertexArray(vao)

    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW)

    const posLoc = gl.getAttribLocation(program, 'a_position')
    gl.enableVertexAttribArray(posLoc)
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0)

    const timeLoc = gl.getUniformLocation(program, 'iTime')
    const resLoc = gl.getUniformLocation(program, 'iResolution')

    let rafId = 0
    let lastFrameTime = 0
    let isVisible = document.visibilityState === 'visible'
    const targetFrameMs = 1000 / 30

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.25)
      const width = Math.max(320, Math.floor(window.innerWidth * dpr))
      const height = Math.max(180, Math.floor(window.innerHeight * dpr))
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width
        canvas.height = height
        gl.viewport(0, 0, width, height)
      }
    }

    const onVisibilityChange = () => {
      isVisible = document.visibilityState === 'visible'
    }

    const frame = (now) => {
      if (!isVisible || now - lastFrameTime < targetFrameMs) {
        rafId = window.requestAnimationFrame(frame)
        return
      }
      lastFrameTime = now
      gl.clearColor(0, 0, 0, 0)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.uniform1f(timeLoc, now * 0.001)
      gl.uniform2f(resLoc, canvas.width, canvas.height)
      gl.drawArrays(gl.TRIANGLES, 0, 6)
      rafId = window.requestAnimationFrame(frame)
    }

    resize()
    window.addEventListener('resize', resize, { passive: true })
    document.addEventListener('visibilitychange', onVisibilityChange)
    rafId = window.requestAnimationFrame(frame)

    return () => {
      window.cancelAnimationFrame(rafId)
      window.removeEventListener('resize', resize)
      document.removeEventListener('visibilitychange', onVisibilityChange)
      gl.deleteBuffer(buffer)
      gl.deleteVertexArray(vao)
      gl.deleteProgram(program)
      gl.deleteShader(vertexShader)
      gl.deleteShader(fragmentShader)
    }
  }, [])

  return (
    <section className={`gemmarium-hero ${className}`.trim()}>
      <canvas ref={canvasRef} className="gemmarium-canvas" aria-hidden="true" />
      {children ? <div className="gemmarium-content">{children}</div> : null}
    </section>
  )
}
