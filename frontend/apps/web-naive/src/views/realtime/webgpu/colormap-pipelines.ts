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

const SHADER = `
struct Region {
  offset: vec2<f32>,
  scale: vec2<f32>,
};

struct VertexOutput {
  @builtin(position) position: vec4<f32>,
  @location(0) uv: vec2<f32>,
};

@group(0) @binding(0) var frameTexture: texture_external;
@group(0) @binding(1) var frameSampler: sampler;
@group(0) @binding(2) var<uniform> region: Region;

@vertex
fn vertexMain(@builtin(vertex_index) index: u32) -> VertexOutput {
  var positions = array<vec2<f32>, 6>(
    vec2<f32>(-1.0, -1.0),
    vec2<f32>(1.0, -1.0),
    vec2<f32>(-1.0, 1.0),
    vec2<f32>(-1.0, 1.0),
    vec2<f32>(1.0, -1.0),
    vec2<f32>(1.0, 1.0),
  );
  var uvs = array<vec2<f32>, 6>(
    vec2<f32>(0.0, 1.0),
    vec2<f32>(1.0, 1.0),
    vec2<f32>(0.0, 0.0),
    vec2<f32>(0.0, 0.0),
    vec2<f32>(1.0, 1.0),
    vec2<f32>(1.0, 0.0),
  );
  var output: VertexOutput;
  output.position = vec4<f32>(positions[index], 0.0, 1.0);
  output.uv = uvs[index] * region.scale + region.offset;
  return output;
}

@fragment
fn fragmentMain(input: VertexOutput) -> @location(0) vec4<f32> {
  return textureSampleBaseClampToEdge(frameTexture, frameSampler, input.uv);
}
`;

const GPU_BUFFER_USAGE_COPY_DST = 8;
const GPU_BUFFER_USAGE_UNIFORM = 64;
const GPU_SHADER_STAGE_VERTEX = 1;
const GPU_SHADER_STAGE_FRAGMENT = 2;

interface WebGpuCanvasContext {
  configure(configuration: GPUCanvasConfiguration): void;
  getCurrentTexture(): GPUTexture;
}

export class WebGpuRealtimeRenderer {
  private bindGroupLayout!: GPUBindGroupLayout;
  private canvas: HTMLCanvasElement;
  private context!: WebGpuCanvasContext;
  private device!: GPUDevice;
  private format!: GPUTextureFormat;
  private pipeline!: GPURenderPipeline;
  private region: UvRegion;
  private regionBuffer!: GPUBuffer;
  private sampler!: GPUSampler;

  private constructor(canvas: HTMLCanvasElement, region: UvRegion) {
    this.canvas = canvas;
    this.canvas.width = FRAME_WIDTH;
    this.canvas.height = FRAME_HEIGHT;
    this.region = region;
  }

  static async create(canvas: HTMLCanvasElement, region: UvRegion = FULL_UV_REGION) {
    const renderer = new WebGpuRealtimeRenderer(canvas, region);
    await renderer.init();
    return renderer;
  }

  dispose() {
    this.regionBuffer?.destroy();
    this.device?.destroy();
  }

  renderVideo(frame: VideoRealtimeFrame) {
    this.writeRegion();
    const frameTexture = this.device.importExternalTexture({ source: frame.frame });
    const bindGroup = this.device.createBindGroup({
      entries: [
        { binding: 0, resource: frameTexture },
        { binding: 1, resource: this.sampler },
        { binding: 2, resource: { buffer: this.regionBuffer } },
      ],
      layout: this.bindGroupLayout,
    });
    const encoder = this.device.createCommandEncoder();
    const pass = encoder.beginRenderPass({
      colorAttachments: [
        {
          clearValue: { a: 1, b: 0, g: 0, r: 0 },
          loadOp: 'clear',
          storeOp: 'store',
          view: this.context.getCurrentTexture().createView(),
        },
      ],
    });
    pass.setPipeline(this.pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.draw(6);
    pass.end();
    this.device.queue.submit([encoder.finish()]);
  }

  setRegion(region: UvRegion) {
    this.region = region;
  }

  private async init() {
    if (!navigator.gpu) {
      throw new Error('当前浏览器不支持 WebGPU，或页面不是 HTTPS/Secure Context');
    }
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) {
      throw new Error('无法获取 WebGPU Adapter');
    }
    this.device = await adapter.requestDevice();
    const context = this.canvas.getContext('webgpu') as null | WebGpuCanvasContext;
    if (!context) {
      throw new Error('无法创建 WebGPU CanvasContext');
    }
    this.context = context;
    this.format = navigator.gpu.getPreferredCanvasFormat();
    this.context.configure({
      alphaMode: 'opaque',
      device: this.device,
      format: this.format,
    });
    this.sampler = this.device.createSampler({
      magFilter: 'linear',
      minFilter: 'linear',
    });
    this.regionBuffer = this.device.createBuffer({
      size: 16,
      usage: GPU_BUFFER_USAGE_COPY_DST | GPU_BUFFER_USAGE_UNIFORM,
    });
    this.bindGroupLayout = this.device.createBindGroupLayout({
      entries: [
        { binding: 0, externalTexture: {}, visibility: GPU_SHADER_STAGE_FRAGMENT },
        { binding: 1, sampler: {}, visibility: GPU_SHADER_STAGE_FRAGMENT },
        { binding: 2, buffer: { type: 'uniform' }, visibility: GPU_SHADER_STAGE_VERTEX },
      ],
    });
    const pipelineLayout = this.device.createPipelineLayout({
      bindGroupLayouts: [this.bindGroupLayout],
    });
    const shaderModule = this.device.createShaderModule({ code: SHADER });
    this.pipeline = this.device.createRenderPipeline({
      fragment: {
        entryPoint: 'fragmentMain',
        module: shaderModule,
        targets: [{ format: this.format }],
      },
      layout: pipelineLayout,
      primitive: { topology: 'triangle-list' },
      vertex: {
        entryPoint: 'vertexMain',
        module: shaderModule,
      },
    });
    this.writeRegion();
  }

  private writeRegion() {
    this.device.queue.writeBuffer(
      this.regionBuffer,
      0,
      new Float32Array([
        this.region.offsetU,
        this.region.offsetV,
        this.region.scaleU,
        this.region.scaleV,
      ]),
    );
  }
}
