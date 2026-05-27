import type { VideoRealtimeFrame } from '../transport/transport-client';

export const FRAME_WIDTH = 1280;
export const FRAME_HEIGHT = 720;

export interface UvRegion {
  offsetU: number;
  offsetV: number;
  scaleU: number;
  scaleV: number;
}

export const FULL_UV_REGION: UvRegion = {
  offsetU: 0,
  offsetV: 0,
  scaleU: 1,
  scaleV: 1,
};

const FRAGMENT_SHADER = `
precision mediump float;
varying vec2 vUv;
uniform sampler2D uFrame;

void main() {
  gl_FragColor = texture2D(uFrame, vUv);
}
`;

const VERTEX_SHADER = `
attribute vec2 aPosition;
attribute vec2 aUv;
uniform vec2 uUvOffset;
uniform vec2 uUvScale;
varying vec2 vUv;

void main() {
  vUv = aUv * uUvScale + uUvOffset;
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;

export class WebGlRealtimeRenderer {
  private canvas: HTMLCanvasElement;
  private gl: WebGL2RenderingContext;
  private positionBuffer: WebGLBuffer;
  private program: WebGLProgram;
  private region: UvRegion;
  private texture: WebGLTexture;
  private textureHeight = 0;
  private textureWidth = 0;
  private uvBuffer: WebGLBuffer;
  private uvOffsetLocation: null | WebGLUniformLocation = null;
  private uvScaleLocation: null | WebGLUniformLocation = null;

  constructor(canvas: HTMLCanvasElement, region: UvRegion = FULL_UV_REGION) {
    const gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      preserveDrawingBuffer: false,
      stencil: false,
    });
    if (!gl) {
      throw new Error('当前浏览器不支持 WebGL2');
    }
    this.canvas = canvas;
    this.canvas.width = FRAME_WIDTH;
    this.canvas.height = FRAME_HEIGHT;
    this.gl = gl;
    this.region = region;
    this.program = createProgram(gl);
    this.positionBuffer = createBuffer(gl, new Float32Array([
      -1, -1,
      1, -1,
      -1, 1,
      -1, 1,
      1, -1,
      1, 1,
    ]));
    this.uvBuffer = createBuffer(gl, new Float32Array([
      0, 1,
      1, 1,
      0, 0,
      0, 0,
      1, 1,
      1, 0,
    ]));
    const texture = gl.createTexture();
    if (!texture) {
      throw new Error('无法创建 WebGL2 纹理');
    }
    this.texture = texture;
    gl.useProgram(this.program);
    gl.uniform1i(gl.getUniformLocation(this.program, 'uFrame'), 0);
    this.uvOffsetLocation = gl.getUniformLocation(this.program, 'uUvOffset');
    this.uvScaleLocation = gl.getUniformLocation(this.program, 'uUvScale');
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.clearColor(0, 0, 0, 1);
  }

  dispose() {
    this.gl.deleteBuffer(this.positionBuffer);
    this.gl.deleteBuffer(this.uvBuffer);
    this.gl.deleteTexture(this.texture);
    this.gl.deleteProgram(this.program);
  }

  // 调用者负责 frame.close()，这里不干预 VideoFrame 的生命周期。
  renderVideo(frame: VideoRealtimeFrame) {
    const width = frame.frame.displayWidth || FRAME_WIDTH;
    const height = frame.frame.displayHeight || FRAME_HEIGHT;
    this.ensureTexture(width, height);
    this.gl.bindTexture(this.gl.TEXTURE_2D, this.texture);
    this.gl.pixelStorei(this.gl.UNPACK_ALIGNMENT, 1);
    this.gl.texSubImage2D(
      this.gl.TEXTURE_2D,
      0,
      0,
      0,
      this.gl.RGB,
      this.gl.UNSIGNED_BYTE,
      frame.frame,
    );
    this.draw();
  }

  setRegion(region: UvRegion) {
    this.region = region;
  }

  private draw() {
    const positionLocation = this.gl.getAttribLocation(this.program, 'aPosition');
    const uvLocation = this.gl.getAttribLocation(this.program, 'aUv');
    this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    this.gl.clear(this.gl.COLOR_BUFFER_BIT);
    this.gl.useProgram(this.program);
    if (this.uvOffsetLocation) {
      this.gl.uniform2f(this.uvOffsetLocation, this.region.offsetU, this.region.offsetV);
    }
    if (this.uvScaleLocation) {
      this.gl.uniform2f(this.uvScaleLocation, this.region.scaleU, this.region.scaleV);
    }
    this.gl.activeTexture(this.gl.TEXTURE0);
    this.gl.bindTexture(this.gl.TEXTURE_2D, this.texture);
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.positionBuffer);
    this.gl.enableVertexAttribArray(positionLocation);
    this.gl.vertexAttribPointer(positionLocation, 2, this.gl.FLOAT, false, 0, 0);
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.uvBuffer);
    this.gl.enableVertexAttribArray(uvLocation);
    this.gl.vertexAttribPointer(uvLocation, 2, this.gl.FLOAT, false, 0, 0);
    this.gl.drawArrays(this.gl.TRIANGLES, 0, 6);
  }

  private ensureTexture(width: number, height: number) {
    if (this.textureWidth === width && this.textureHeight === height) {
      return;
    }
    this.textureWidth = width;
    this.textureHeight = height;
    this.gl.bindTexture(this.gl.TEXTURE_2D, this.texture);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
    this.gl.texImage2D(
      this.gl.TEXTURE_2D,
      0,
      this.gl.RGBA,
      width,
      height,
      0,
      this.gl.RGBA,
      this.gl.UNSIGNED_BYTE,
      null,
    );
  }
}

function compileShader(gl: WebGL2RenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) {
    throw new Error('无法创建 WebGL2 Shader');
  }
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || 'WebGL2 Shader 编译失败';
    gl.deleteShader(shader);
    throw new Error(message);
  }
  return shader;
}

function createBuffer(gl: WebGL2RenderingContext, data: Float32Array) {
  const buffer = gl.createBuffer();
  if (!buffer) {
    throw new Error('无法创建 WebGL2 Buffer');
  }
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
  return buffer;
}

function createProgram(gl: WebGL2RenderingContext) {
  const vertexShader = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
  const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
  const program = gl.createProgram();
  if (!program) {
    throw new Error('无法创建 WebGL2 Program');
  }
  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);
  gl.deleteShader(vertexShader);
  gl.deleteShader(fragmentShader);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const message = gl.getProgramInfoLog(program) || 'WebGL2 Program 链接失败';
    gl.deleteProgram(program);
    throw new Error(message);
  }
  return program;
}
