#
# Translated from Blane3: AudioCaptureManager.ts
# Original: ../candy_mountain/blane3/lib/audio/AudioCaptureManager.ts
# Translation date: 2025-11-11
# Manual adaptation required for full Nevil integration
#
"""
AudioCaptureManager - Translated from Blane3
Handles microphone input for Realtime API (24kHz PCM16)
"""

import pyaudio
import numpy as np
import base64
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

/**
 * Microphone capture manager for Blane 3.0
 * Handles audio input, real-time processing, and PCM encoding
 */

import { AudioProcessor } from './AudioProcessor';

export interface AudioCaptureConfig {
  sampleRate?: int | float;
  channelCount?: int | float;
  echoCancellation?: bool;
  noiseSuppression?: bool;
  autoGainControl?: bool;
}

export interface AudioCaptureCallbacks {
  onAudioData?: (base64Audio: str, volumeLevel: int | float) => void;
  onVolumeChange?: (volumeLevel: int | float) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: 'inactive' | 'recording' | 'paused') => void;
}

class AudioCaptureManager {
  audioContext: pyaudio.PyAudio | null = null;
  mediaStream: MediaStream | null = null;
  sourceNode: MediaStreamAudioSourceNode | null = null;
  processorNode: ScriptProcessorNode | null = null;
  analyserNode: AnalyserNode | null = null;

  isRecording = false;
  isPaused = false;
  callbacks: AudioCaptureCallbacks = {};
  flushAudioBuffer: (() => void) | null = null;

  readonly config: Required<AudioCaptureConfig>;
  readonly BUFFER_SIZE = 4096;
  readonly CHUNK_SIZE = 4800; // 200ms at 24kHz

  def __init__(self, config: AudioCaptureConfig = {}, callbacks: AudioCaptureCallbacks = {}) {
    this.config = {
      sampleRate: config.sampleRate ?? 24000,
      channelCount: config.channelCount ?? 1,
      echoCancellation: config.echoCancellation ?? true,
      noiseSuppression: config.noiseSuppression ?? true,
      autoGainControl: config.autoGainControl ?? true
    };

    this.callbacks = callbacks;
  }

  /**
   * Request microphone permission and initialize audio context
   */
  async def initialize(self):
    
    try {
      // Request microphone permission
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: this.config.channelCount,
          echoCancellation: this.config.echoCancellation,
          noiseSuppression: this.config.noiseSuppression,
          autoGainControl: this.config.autoGainControl
        }
      });

      // Create audio context
      this.audioContext = new pyaudio.PyAudio({
        sampleRate: this.config.sampleRate
      });

      // Create source node from media stream
      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create analyser for volume calculation
      this.analyserNode = this.audioContext.createAnalyser();
      this.analyserNode.fftSize = 2048;
      this.analyserNode.smoothingTimeConstant = 0.8;

      // Create script processor for audio data
      this.processorNode = this.audioContext.createScriptProcessor(
        this.BUFFER_SIZE,
        this.config.channelCount,
        this.config.channelCount
      );

      // Connect nodes
      this.sourceNode.connect(this.analyserNode);
      this.analyserNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

      // Set up audio processing
      this.setupAudioProcessing();

      this.callbacks.onStateChange?.('inactive');
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to initialize audio capture');
      this.callbacks.onError?.(err);
      throw err;
    }
  }

  /**
   * Set up audio processing callback
   */
  def setupAudioProcessing(self):
    
    if (!this.processorNode || !this.analyserNode) return;

    let audioBuffer: Float32Array[] = [];
    let bufferLength = 0;

    // Store references for flush method
    const getAudioBuffer = () => ({ audioBuffer, bufferLength });
    const resetAudioBuffer = () => {
      audioBuffer = [];
      bufferLength = 0;
    };

    // Store flush function for external access
    this.flushAudioBuffer = () => {
      const { audioBuffer: currentBuffer, bufferLength: currentLength } = getAudioBuffer();
      
      if (currentLength === 0) {
        console.log('📭 [AudioCaptureManager] No audio to flush (buffer empty)');
        return;
      }

      console.log(`🚿 [AudioCaptureManager] Flushing ${currentLength} samples (${(currentLength / this.config.sampleRate * 1000).toFixed(1)}ms)`);

      try {
        // Concatenate buffered audio
        const concatenated = new Float32Array(currentLength);
        let offset = 0;

        for (const chunk of currentBuffer) {
          concatenated.set(chunk, offset);
          offset += chunk.length;
        }

        // Convert to PCM16 and encode
        const pcm16 = AudioProcessor.float32ToPCM16(concatenated);
        const base64Audio = AudioProcessor.encodeBase64(pcm16);

        // Calculate volume for the flushed data
        const volumeLevel = AudioProcessor.calculateVolume(concatenated);

        // Send to callback
        this.callbacks.onAudioData?.(base64Audio, volumeLevel);
        console.log(`✅ [AudioCaptureManager] Flushed audio sent to callback`);

        // Reset buffer
        resetAudioBuffer();
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Audio flush error');
        this.callbacks.onError?.(err);
        console.error('❌ [AudioCaptureManager] Flush error:', err);
      }
    };

    this.processorNode.onaudioprocess = (event) => {
      if (!this.isRecording || this.isPaused) return;

      try {
        // Get input audio data
        const inputData = event.inputBuffer.getChannelData(0);

        // Calculate volume level
        const volumeLevel = AudioProcessor.calculateVolume(inputData);
        this.callbacks.onVolumeChange?.(volumeLevel);

        // Buffer audio data
        audioBuffer.push(new Float32Array(inputData));
        bufferLength += inputData.length;

        // When we have enough data (200ms chunk), process it
        if (bufferLength >= this.CHUNK_SIZE) {
          // Concatenate buffered audio
          const concatenated = new Float32Array(bufferLength);
          let offset = 0;

          for (const chunk of audioBuffer) {
            concatenated.set(chunk, offset);
            offset += chunk.length;
          }

          // Convert to PCM16 and encode
          const pcm16 = AudioProcessor.float32ToPCM16(concatenated);
          const base64Audio = AudioProcessor.encodeBase64(pcm16);

          // Send to callback
          this.callbacks.onAudioData?.(base64Audio, volumeLevel);

          // Reset buffer
          resetAudioBuffer();
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Audio processing error');
        this.callbacks.onError?.(err);
      }
    };
  }

  /**
   * Start recording audio
   */
  async def startRecording(self):
    
    if (!this.audioContext || !this.mediaStream) {
      throw new Error('Audio capture not initialized. Call initialize() first.');
    }

    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    this.isRecording = true;
    this.isPaused = false;
    this.callbacks.onStateChange?.('recording');
  }

  /**
   * Pause recording
   */
  def pause(self):
    
    if (!this.isRecording) return;

    this.isPaused = true;
    this.callbacks.onStateChange?.('paused');
  }

  /**
   * Resume recording
   */
  def resume(self):
    
    if (!this.isRecording || !this.isPaused) return;

    this.isPaused = false;
    this.callbacks.onStateChange?.('recording');
  }

  /**
   * Flush any remaining buffered audio before stopping/committing
   */
  def flush(self):
    
    console.log('🚿 [AudioCaptureManager] flush() called');
    if (this.flushAudioBuffer) {
      this.flushAudioBuffer();
    } else {
      console.warn('⚠️ [AudioCaptureManager] Cannot flush - audio processing not initialized');
    }
  }

  /**
   * Stop recording audio
   */
  def stopRecording(self):
    
    console.log('🛑 [AudioCaptureManager] stopRecording() called');
    
    // Flush any remaining buffered audio before stopping
    this.flush();
    
    this.isRecording = false;
    this.isPaused = false;
    this.callbacks.onStateChange?.('inactive');
  }

  /**
   * Get current volume level (0-100)
   */
  getCurrentVolume(): int | float {
    if (!this.analyserNode) return 0;

    const dataArray = new Float32Array(this.analyserNode.fftSize);
    this.analyserNode.getFloatTimeDomainData(dataArray);

    return AudioProcessor.calculateVolume(dataArray);
  }

  /**
   * Get current state
   */
  getState(): 'inactive' | 'recording' | 'paused' {
    if (!this.isRecording) return 'inactive';
    if (this.isPaused) return 'paused';
    return 'recording';
  }

  /**
   * Get frequency data for visualization
   */
  def getFrequencyData(self):
    
    if (!this.analyserNode) return new Uint8Array(128);

    const frequencyData = new Uint8Array(this.analyserNode.frequencyBinCount);
    this.analyserNode.getByteFrequencyData(frequencyData);

    return frequencyData;
  }

  /**
   * Update callbacks
   */
  def setCallbacks(self):
    
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Clean up resources
   */
  def dispose(self):
    
    this.stopRecording();

    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode.onaudioprocess = null;
      this.processorNode = null;
    }

    if (this.analyserNode) {
      this.analyserNode.disconnect();
      this.analyserNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}
