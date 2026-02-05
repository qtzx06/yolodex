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
uniform vec4 iMouse;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;

out vec4 outColor;

#define NOISE_METHOD 2
#define LOOK 0
#define USE_LOD 1

mat3 setCamera( in vec3 ro, in vec3 ta, float cr )
{
  vec3 cw = normalize(ta-ro);
  vec3 cp = vec3(sin(cr), cos(cr),0.0);
  vec3 cu = normalize( cross(cw,cp) );
  vec3 cv = normalize( cross(cu,cw) );
  return mat3( cu, cv, cw );
}

float noise( in vec3 x )
{
  vec3 p = floor(x);
  vec3 f = fract(x);
  f = f*f*(3.0-2.0*f);

#if NOISE_METHOD==0
  x = p + f;
  return textureLod(iChannel2,(x+0.5)/32.0,0.0).x*2.0-1.0;
#endif
#if NOISE_METHOD==1
  vec2 uv = (p.xy+vec2(37.0,239.0)*p.z) + f.xy;
  vec2 rg = textureLod(iChannel0,(uv+0.5)/256.0,0.0).yx;
  return mix( rg.x, rg.y, f.z )*2.0-1.0;
#endif
#if NOISE_METHOD==2
  ivec3 q = ivec3(p);
  ivec2 uv = q.xy + ivec2(37,239)*q.z;
  vec2 rg = mix(mix(texelFetch(iChannel0,(uv           )&255,0),
            texelFetch(iChannel0,(uv+ivec2(1,0))&255,0),f.x),
          mix(texelFetch(iChannel0,(uv+ivec2(0,1))&255,0),
            texelFetch(iChannel0,(uv+ivec2(1,1))&255,0),f.x),f.y).yx;
  return mix( rg.x, rg.y, f.z )*2.0-1.0;
#endif
}

#if LOOK==0
float map( in vec3 p, int oct )
{
  vec3 q = p - vec3(0.0,0.1,1.0)*iTime;
  float g = 0.5+0.5*noise( q*0.3 );

  float f;
  f  = 0.50000*noise( q ); q = q*2.02;
  #if USE_LOD==1
  if( oct>=2 )
  #endif
  f += 0.25000*noise( q ); q = q*2.23;
  #if USE_LOD==1
  if( oct>=3 )
  #endif
  f += 0.12500*noise( q ); q = q*2.41;
  #if USE_LOD==1
  if( oct>=4 )
  #endif
  f += 0.06250*noise( q ); q = q*2.62;
  #if USE_LOD==1
  if( oct>=5 )
  #endif
  f += 0.03125*noise( q );

  f = mix( f*0.1-0.5, f, g*g );

  return 1.5*f - 0.5 - p.y;
}

const int kDiv = 1;
const vec3 sundir = normalize( vec3(1.0,0.0,-1.0) );

vec4 raymarch( in vec3 ro, in vec3 rd, in vec3 bgcol, in ivec2 px )
{
  const float yb = -3.0;
  const float yt =  0.6;
  float tb = (yb-ro.y)/rd.y;
  float tt = (yt-ro.y)/rd.y;

  float tmin, tmax;
  if( ro.y>yt )
  {
    if( tt<0.0 ) return vec4(0.0);
    tmin = tt;
    tmax = tb;
  }
  else
  {
    tmin = 0.0;
    tmax = 60.0;
    if( tt>0.0 ) tmax = min( tmax, tt );
    if( tb>0.0 ) tmax = min( tmax, tb );
  }

  float t = tmin + 0.1*texelFetch( iChannel1, px&1023, 0 ).x;

  vec4 sum = vec4(0.0);
  for( int i=0; i<190*kDiv; i++ )
  {
    float dt = max(0.05,0.02*t/float(kDiv));

    #if USE_LOD==0
    const int oct = 5;
    #else
    int oct = 5 - int( log2(1.0+t*0.5) );
    #endif

    vec3 pos = ro + t*rd;
    float den = map( pos,oct );
    if( den>0.01 )
    {
      float dif = clamp((den - map(pos+0.3*sundir,oct))/0.25, 0.0, 1.0 );
      vec3  lin = vec3(0.65,0.65,0.75)*1.1 + 0.8*vec3(1.0,0.6,0.3)*dif;
      vec4  col = vec4( mix( vec3(1.0,0.93,0.84), vec3(0.25,0.3,0.4), den ), den );
      col.xyz *= lin;
      col.xyz = mix(col.xyz,bgcol, 1.0-exp2(-0.1*t));
      col.w = min(col.w*8.0*dt,1.0);
      col.rgb *= col.w;
      sum += col*(1.0-sum.a);
    }
    t += dt;
    if( t>tmax || sum.a>0.99 ) break;
  }

  return clamp( sum, 0.0, 1.0 );
}

vec4 render( in vec3 ro, in vec3 rd, in ivec2 px )
{
  float sun = clamp( dot(sundir,rd), 0.0, 1.0 );

  vec3 col = vec3(0.76,0.75,0.95);
  col -= 0.6*vec3(0.90,0.75,0.95)*rd.y;
  col += 0.2*vec3(1.00,0.60,0.10)*pow( sun, 8.0 );

  vec4 res = raymarch( ro, rd, col, px );
  col = col*(1.0-res.w) + res.xyz;

  col += 0.2*vec3(1.0,0.4,0.2)*pow( sun, 3.0 );

  col = smoothstep(0.15,1.1,col);

  return vec4( col, 1.0 );
}

#else

float map5( in vec3 p )
{
  vec3 q = p - vec3(0.0,0.1,1.0)*iTime;
  float f;
  f  = 0.50000*noise( q ); q = q*2.02;
  f += 0.25000*noise( q ); q = q*2.03;
  f += 0.12500*noise( q ); q = q*2.01;
  f += 0.06250*noise( q ); q = q*2.02;
  f += 0.03125*noise( q );
  return clamp( 1.5 - p.y - 2.0 + 1.75*f, 0.0, 1.0 );
}
float map4( in vec3 p )
{
  vec3 q = p - vec3(0.0,0.1,1.0)*iTime;
  float f;
  f  = 0.50000*noise( q ); q = q*2.02;
  f += 0.25000*noise( q ); q = q*2.03;
  f += 0.12500*noise( q ); q = q*2.01;
  f += 0.06250*noise( q );
  return clamp( 1.5 - p.y - 2.0 + 1.75*f, 0.0, 1.0 );
}
float map3( in vec3 p )
{
  vec3 q = p - vec3(0.0,0.1,1.0)*iTime;
  float f;
  f  = 0.50000*noise( q ); q = q*2.02;
  f += 0.25000*noise( q ); q = q*2.03;
  f += 0.12500*noise( q );
  return clamp( 1.5 - p.y - 2.0 + 1.75*f, 0.0, 1.0 );
}
float map2( in vec3 p )
{
  vec3 q = p - vec3(0.0,0.1,1.0)*iTime;
  float f;
  f  = 0.50000*noise( q );
  q = q*2.02;
  f += 0.25000*noise( q );
  return clamp( 1.5 - p.y - 2.0 + 1.75*f, 0.0, 1.0 );
}

const vec3 sundir = vec3(-0.7071,0.0,-0.7071);

#define MARCH(STEPS,MAPLOD) for(int i=0; i<STEPS; i++) { vec3 pos = ro + t*rd; if( pos.y<-3.0 || pos.y>2.0 || sum.a>0.99 ) break; float den = MAPLOD( pos ); if( den>0.01 ) { float dif = clamp((den - MAPLOD(pos+0.3*sundir))/0.6, 0.0, 1.0 ); vec3  lin = vec3(1.0,0.6,0.3)*dif+vec3(0.91,0.98,1.05); vec4  col = vec4( mix( vec3(1.0,0.95,0.8), vec3(0.25,0.3,0.35), den ), den ); col.xyz *= lin; col.xyz = mix( col.xyz, bgcol, 1.0-exp(-0.003*t*t) ); col.w *= 0.4; col.rgb *= col.a; sum += col*(1.0-sum.a); } t += max(0.06,0.05*t); }

vec4 raymarch( in vec3 ro, in vec3 rd, in vec3 bgcol, in ivec2 px )
{
  vec4 sum = vec4(0.0);
  float t = 0.05*texelFetch( iChannel1, px&255, 0 ).x;
  MARCH(40,map5);
  MARCH(40,map4);
  MARCH(30,map3);
  MARCH(30,map2);
  return clamp( sum, 0.0, 1.0 );
}

vec4 render( in vec3 ro, in vec3 rd, in ivec2 px )
{
  float sun = clamp( dot(sundir,rd), 0.0, 1.0 );
  vec3 col = vec3(0.6,0.71,0.75) - rd.y*0.2*vec3(1.0,0.5,1.0) + 0.15*0.5;
  col += 0.2*vec3(1.0,.6,0.1)*pow( sun, 8.0 );
  vec4 res = raymarch( ro, rd, col, px );
  col = col*(1.0-res.w) + res.xyz;
  col += vec3(0.2,0.08,0.04)*pow( sun, 3.0 );
  return vec4( col, 1.0 );
}

#endif

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
  vec2 p = (2.0*fragCoord-iResolution.xy)/iResolution.y;
  float camYaw = 3.5208;
  float camPitch = 0.34;
  float camDist = 4.0;
  vec3 ro = camDist * normalize(vec3(sin(camYaw), camPitch, cos(camYaw))) - vec3(0.0,1.4,0.0);
  vec3 ta = vec3(0.0, -1.2, 0.8);
  mat3 ca = setCamera( ro, ta, 0.07*cos(0.25*iTime) );
  vec3 rd = ca * normalize( vec3(p.xy,1.5));

  fragColor = render( ro, rd, ivec2(fragCoord-0.5) );
}

void main() {
  mainImage(outColor, gl_FragCoord.xy);
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

function createRandomTexture(gl, width, height) {
  const data = new Uint8Array(width * height * 4)
  for (let i = 0; i < data.length; i++) {
    data[i] = Math.floor(Math.random() * 256)
  }

  const tex = gl.createTexture()
  gl.bindTexture(gl.TEXTURE_2D, tex)
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, data)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT)
  return tex
}

export default function VolumetricBackground({ className = 'volumetric-bg', style }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false })
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
    const mouseLoc = gl.getUniformLocation(program, 'iMouse')

    const channel0 = createRandomTexture(gl, 256, 256)
    const channel1 = createRandomTexture(gl, 1024, 1024)
    const channel2 = createRandomTexture(gl, 32, 32)

    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, channel0)
    gl.uniform1i(gl.getUniformLocation(program, 'iChannel0'), 0)

    gl.activeTexture(gl.TEXTURE1)
    gl.bindTexture(gl.TEXTURE_2D, channel1)
    gl.uniform1i(gl.getUniformLocation(program, 'iChannel1'), 1)

    gl.activeTexture(gl.TEXTURE2)
    gl.bindTexture(gl.TEXTURE_2D, channel2)
    gl.uniform1i(gl.getUniformLocation(program, 'iChannel2'), 2)

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
      if (!isVisible) {
        rafId = window.requestAnimationFrame(frame)
        return
      }
      if (now - lastFrameTime < targetFrameMs) {
        rafId = window.requestAnimationFrame(frame)
        return
      }
      lastFrameTime = now

      gl.uniform1f(timeLoc, now * 0.001)
      gl.uniform2f(resLoc, canvas.width, canvas.height)
      gl.uniform4f(mouseLoc, 0, 0, 0, 0)
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

      gl.deleteTexture(channel0)
      gl.deleteTexture(channel1)
      gl.deleteTexture(channel2)
      gl.deleteBuffer(buffer)
      gl.deleteVertexArray(vao)
      gl.deleteProgram(program)
      gl.deleteShader(vertexShader)
      gl.deleteShader(fragmentShader)
    }
  }, [])

  return <canvas ref={canvasRef} className={className} style={style} aria-hidden="true" />
}
