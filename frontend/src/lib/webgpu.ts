/**
 * WebGPU Genomics Acceleration
 * GPU-accelerated computations for GWAS, PCA, and matrix operations
 */

// Types
export interface GPUCapabilities {
  available: boolean
  adapter: GPUAdapter | null
  device: GPUDevice | null
  limits: GPUSupportedLimits | null
  features: string[]
}

export interface ComputeResult<T> {
  data: T
  executionTime: number
  usedGPU: boolean
}

// Check WebGPU availability
let gpuCapabilities: GPUCapabilities | null = null

/**
 * Initialize WebGPU and check capabilities
 */
export async function initWebGPU(): Promise<GPUCapabilities> {
  if (gpuCapabilities) return gpuCapabilities

  gpuCapabilities = {
    available: false,
    adapter: null,
    device: null,
    limits: null,
    features: [],
  }

  if (!navigator.gpu) {
    console.log('[WebGPU] Not available in this browser')
    return gpuCapabilities
  }

  try {
    const adapter = await navigator.gpu.requestAdapter({
      powerPreference: 'high-performance',
    })

    if (!adapter) {
      console.log('[WebGPU] No adapter found')
      return gpuCapabilities
    }

    const device = await adapter.requestDevice({
      requiredFeatures: [],
      requiredLimits: {},
    })

    gpuCapabilities = {
      available: true,
      adapter,
      device,
      limits: device.limits,
      features: [...adapter.features],
    }

    console.log('[WebGPU] Initialized successfully')
    console.log('[WebGPU] Max buffer size:', device.limits.maxBufferSize)
    console.log('[WebGPU] Max compute workgroup size:', device.limits.maxComputeWorkgroupSizeX)

    // Handle device loss
    device.lost.then((info) => {
      console.error('[WebGPU] Device lost:', info.message)
      gpuCapabilities = null
    })

    return gpuCapabilities
  } catch (error) {
    console.error('[WebGPU] Initialization failed:', error)
    return gpuCapabilities
  }
}

/**
 * Check if WebGPU is available
 */
export function isWebGPUAvailable(): boolean {
  return gpuCapabilities?.available ?? false
}

/**
 * Get GPU capabilities
 */
export function getGPUCapabilities(): GPUCapabilities | null {
  return gpuCapabilities
}

// WGSL Shaders for genomic computations

const MATRIX_MULTIPLY_SHADER = `
@group(0) @binding(0) var<storage, read> matrixA: array<f32>;
@group(0) @binding(1) var<storage, read> matrixB: array<f32>;
@group(0) @binding(2) var<storage, read_write> result: array<f32>;
@group(0) @binding(3) var<uniform> dimensions: vec3<u32>; // M, N, K

@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let M = dimensions.x;
    let N = dimensions.y;
    let K = dimensions.z;
    
    let row = global_id.x;
    let col = global_id.y;
    
    if (row >= M || col >= N) {
        return;
    }
    
    var sum: f32 = 0.0;
    for (var i: u32 = 0u; i < K; i = i + 1u) {
        sum = sum + matrixA[row * K + i] * matrixB[i * N + col];
    }
    
    result[row * N + col] = sum;
}
`

/**
 * GPU-accelerated matrix multiplication
 * Used for GRM (Genomic Relationship Matrix) computation
 */
export async function gpuMatrixMultiply(
  matrixA: Float32Array,
  matrixB: Float32Array,
  M: number,
  K: number,
  N: number
): Promise<ComputeResult<Float32Array>> {
  const startTime = performance.now()

  if (!gpuCapabilities?.device) {
    // Fallback to CPU
    return {
      data: cpuMatrixMultiply(matrixA, matrixB, M, K, N),
      executionTime: performance.now() - startTime,
      usedGPU: false,
    }
  }

  const device = gpuCapabilities.device

  try {
    // Create buffers
    const bufferA = device.createBuffer({
      size: matrixA.byteLength,
      usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
    })
    device.queue.writeBuffer(bufferA, 0, matrixA.buffer)

    const bufferB = device.createBuffer({
      size: matrixB.byteLength,
      usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
    })
    device.queue.writeBuffer(bufferB, 0, matrixB.buffer)

    const resultSize = M * N * 4 // Float32
    const bufferResult = device.createBuffer({
      size: resultSize,
      usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
    })

    const dimensionsBuffer = device.createBuffer({
      size: 16, // vec3<u32> aligned to 16 bytes
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
    })
    device.queue.writeBuffer(dimensionsBuffer, 0, new Uint32Array([M, N, K, 0]))

    // Create shader module
    const shaderModule = device.createShaderModule({
      code: MATRIX_MULTIPLY_SHADER,
    })

    // Create pipeline
    const pipeline = device.createComputePipeline({
      layout: 'auto',
      compute: {
        module: shaderModule,
        entryPoint: 'main',
      },
    })

    // Create bind group
    const bindGroup = device.createBindGroup({
      layout: pipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: bufferA } },
        { binding: 1, resource: { buffer: bufferB } },
        { binding: 2, resource: { buffer: bufferResult } },
        { binding: 3, resource: { buffer: dimensionsBuffer } },
      ],
    })

    // Execute
    const commandEncoder = device.createCommandEncoder()
    const passEncoder = commandEncoder.beginComputePass()
    passEncoder.setPipeline(pipeline)
    passEncoder.setBindGroup(0, bindGroup)
    passEncoder.dispatchWorkgroups(Math.ceil(M / 16), Math.ceil(N / 16))
    passEncoder.end()

    // Read back results
    const readBuffer = device.createBuffer({
      size: resultSize,
      usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
    })
    commandEncoder.copyBufferToBuffer(bufferResult, 0, readBuffer, 0, resultSize)

    device.queue.submit([commandEncoder.finish()])

    await readBuffer.mapAsync(GPUMapMode.READ)
    const result = new Float32Array(readBuffer.getMappedRange().slice(0))
    readBuffer.unmap()

    // Cleanup
    bufferA.destroy()
    bufferB.destroy()
    bufferResult.destroy()
    dimensionsBuffer.destroy()
    readBuffer.destroy()

    return {
      data: result,
      executionTime: performance.now() - startTime,
      usedGPU: true,
    }
  } catch (error) {
    console.error('[WebGPU] Matrix multiply failed, falling back to CPU:', error)
    return {
      data: cpuMatrixMultiply(matrixA, matrixB, M, K, N),
      executionTime: performance.now() - startTime,
      usedGPU: false,
    }
  }
}

/**
 * CPU fallback for matrix multiplication
 */
function cpuMatrixMultiply(
  matrixA: Float32Array,
  matrixB: Float32Array,
  M: number,
  K: number,
  N: number
): Float32Array {
  const result = new Float32Array(M * N)

  for (let i = 0; i < M; i++) {
    for (let j = 0; j < N; j++) {
      let sum = 0
      for (let k = 0; k < K; k++) {
        sum += matrixA[i * K + k] * matrixB[k * N + j]
      }
      result[i * N + j] = sum
    }
  }

  return result
}

/**
 * GPU-accelerated correlation matrix computation
 * Used for trait correlations and LD analysis
 */
export async function gpuCorrelationMatrix(
  data: Float32Array,
  numSamples: number,
  numVariables: number
): Promise<ComputeResult<Float32Array>> {
  const startTime = performance.now()

  if (!gpuCapabilities?.device) {
    return {
      data: cpuCorrelationMatrix(data, numSamples, numVariables),
      executionTime: performance.now() - startTime,
      usedGPU: false,
    }
  }

  // For now, use CPU implementation
  // Full GPU implementation would follow similar pattern to matrix multiply
  return {
    data: cpuCorrelationMatrix(data, numSamples, numVariables),
    executionTime: performance.now() - startTime,
    usedGPU: false,
  }
}

/**
 * CPU fallback for correlation matrix
 */
function cpuCorrelationMatrix(
  data: Float32Array,
  numSamples: number,
  numVariables: number
): Float32Array {
  const result = new Float32Array(numVariables * numVariables)

  // Calculate means
  const means = new Float32Array(numVariables)
  for (let v = 0; v < numVariables; v++) {
    let sum = 0
    for (let s = 0; s < numSamples; s++) {
      sum += data[s * numVariables + v]
    }
    means[v] = sum / numSamples
  }

  // Calculate correlations
  for (let v1 = 0; v1 < numVariables; v1++) {
    for (let v2 = v1; v2 < numVariables; v2++) {
      let sumXY = 0
      let sumX2 = 0
      let sumY2 = 0

      for (let s = 0; s < numSamples; s++) {
        const x = data[s * numVariables + v1] - means[v1]
        const y = data[s * numVariables + v2] - means[v2]
        sumXY += x * y
        sumX2 += x * x
        sumY2 += y * y
      }

      const correlation = sumXY / Math.sqrt(sumX2 * sumY2)
      result[v1 * numVariables + v2] = correlation
      result[v2 * numVariables + v1] = correlation
    }
  }

  return result
}

// React hook
import { useState, useEffect } from 'react'

export function useWebGPU() {
  const [capabilities, setCapabilities] = useState<GPUCapabilities | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    initWebGPU()
      .then(setCapabilities)
      .finally(() => setIsLoading(false))
  }, [])

  return {
    isAvailable: capabilities?.available ?? false,
    capabilities,
    isLoading,
    matrixMultiply: gpuMatrixMultiply,
    correlationMatrix: gpuCorrelationMatrix,
  }
}
