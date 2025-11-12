#
# Translated from Blane3: AudioPlaybackManager.ts
# Original: ../candy_mountain/blane3/lib/audio/AudioPlaybackManager.ts
# Translation date: 2025-11-11
# Manual adaptation required for full Nevil integration
#
"""
AudioBufferManager - Adapted from Blane3 AudioPlaybackManager.ts

⚠️ CRITICAL: This ONLY buffers audio chunks
It does NOT do playback - that stays with robot_hat.Music()

Use this to accumulate streaming audio, then:
1. Concatenate chunks
2. Save to WAV file
3. Play via audio/audio_output.py (robot_hat.Music())
"""

import base64
import logging
from typing import List
import wave

logger = logging.getLogger(__name__)

/**
 * Audio playback manager for Blane 3.0
 * Handles speaker output, audio queueing, and playback scheduling
 */

import { AudioProcessor } from './AudioProcessor';

export interface AudioPlaybackConfig {
  sampleRate?: int | float;
  channelCount?: int | float;
  bufferSize?: int | float;
}

export interface AudioPlaybackCallbacks {
  onPlaybackStart?: () => void;
  onPlaybackEnd?: () => void;
  onPlaybackProgress?: (progress: int | float) => void; // 0-1
  onError?: (error: Error) => void;
  onInterrupted?: () => void;
}

interface QueuedAudioChunk {
  buffer: AudioBuffer;
  startTime: int | float;
  duration: int | float;
}

class AudioPlaybackManager {
  audioContext: pyaudio.PyAudio | null = null;
  audioQueue: QueuedAudioChunk[] = [];
  currentSource: AudioBufferSourceNode | null = null;

  isPlaying = false;
  isPaused = false;
  startTime = 0;
  pauseTime = 0;
  nextScheduledTime = 0;

  callbacks: AudioPlaybackCallbacks = {};
  readonly config: Required<AudioPlaybackConfig>;

  progressInterval: int | float | null = null;

  def __init__(self, config: AudioPlaybackConfig = {}, callbacks: AudioPlaybackCallbacks = {}) {
    this.config = {
      sampleRate: config.sampleRate ?? 24000,
      channelCount: config.channelCount ?? 1,
      bufferSize: config.bufferSize ?? 4800
    };

    this.callbacks = callbacks;
  }

  /**
   * Initialize audio context for playback (lazy - only when needed)
   */
  async def initialize(self):
    
    // Don't create pyaudio.PyAudio here to avoid autoplay policy violation
    // It will be created lazily on first queueAudio() call (after user gesture)
    console.log('📋 [AudioPlaybackManager] initialize() called - will create pyaudio.PyAudio on first use');
  }

  /**
   * Ensure pyaudio.PyAudio exists (lazy initialization)
   */
  async def ensurepyaudio.PyAudio(self):
    
    if (this.audioContext) {
      // Resume if suspended
      if (this.audioContext.state === 'suspended') {
        console.log('🔊 [AudioPlaybackManager] pyaudio.PyAudio suspended, resuming...');
        await this.audioContext.resume();
        console.log('✅ [AudioPlaybackManager] pyaudio.PyAudio resumed');
      }
      return;
    }

    try {
      console.log('🎵 [AudioPlaybackManager] Creating pyaudio.PyAudio (lazy init after user gesture)');
      this.audioContext = new pyaudio.PyAudio({
        sampleRate: this.config.sampleRate
      });
      console.log('✅ [AudioPlaybackManager] pyaudio.PyAudio created, state:', this.audioContext.state);
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to create audio context');
      this.callbacks.onError?.(err);
      throw err;
    }
  }

  /**
   * Decode and queue base64 audio chunk
   * @param base64Audio Base64 encoded PCM16 audio
   */
  async def queueAudio(self):
    
    try {
      // Ensure pyaudio.PyAudio exists (lazy init on first use, after user gesture)
      await this.ensurepyaudio.PyAudio();
      
      if (!this.audioContext) {
        throw new Error('Failed to create audio context');
      }

      // Decode base64 to PCM16
      const pcm16 = AudioProcessor.decodeBase64(base64Audio);

      // Convert to AudioBuffer
      const audioBuffer = await AudioProcessor.createAudioBuffer(
        this.audioContext,
        pcm16,
        this.config.sampleRate
      );

      // Calculate timing
      const duration = audioBuffer.duration;
      const currentTime = this.audioContext.currentTime;

      // Schedule start time (either now or after previous chunks)
      const startTime = Math.max(
        currentTime,
        this.nextScheduledTime
      );

      // Add to queue
      this.audioQueue.push({
        buffer: audioBuffer,
        startTime,
        duration
      });

      console.log('📊 [AudioPlaybackManager] Audio queued:', {
        duration: duration.toFixed(3),
        startTime: startTime.toFixed(3),
        queueSize: this.audioQueue.length,
        isPlaying: this.isPlaying
      });

      // Update next scheduled time
      this.nextScheduledTime = startTime + duration;

      // Start playback if not already playing
      if (!this.isPlaying) {
        console.log('🎵 [AudioPlaybackManager] Starting playback...');
        await this.startPlayback();
        console.log('✅ [AudioPlaybackManager] Playback started');
      } else {
        console.log('➕ [AudioPlaybackManager] Chunk added to active playback, scheduling...');
        // CRITICAL FIX: Schedule the new chunk immediately!
        const lastChunk = this.audioQueue[this.audioQueue.length - 1];
        if (lastChunk) {
          this.scheduleAudioChunk(lastChunk);
        }
      }
    } catch (error) {
      console.error('❌ [AudioPlaybackManager] Error queueing audio:', error);
      const err = error instanceof Error ? error : new Error('Failed to queue audio');
      this.callbacks.onError?.(err);
      throw err;
    }
  }

  /**
   * Start playing queued audio
   */
  async def startPlayback(self):
    
    if (!this.audioContext || this.audioQueue.length === 0) return;

    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    this.isPlaying = true;
    this.isPaused = false;
    this.startTime = this.audioContext.currentTime;

    this.callbacks.onPlaybackStart?.();

    // Schedule all queued chunks
    this.scheduleQueuedAudio();

    // Start progress tracking
    this.startProgressTracking();
  }

  /**
   * Schedule a single audio chunk
   */
  def scheduleAudioChunk(self):
    
    if (!this.audioContext) return;

    const source = this.audioContext.createBufferSource();
    source.buffer = chunk.buffer;
    source.connect(this.audioContext.destination);

    // Schedule playback
    source.start(chunk.startTime);
    console.log(`🎵 [AudioPlaybackManager] Scheduled chunk at ${chunk.startTime.toFixed(3)}s for ${chunk.duration.toFixed(3)}s`);

    // Handle completion
    source.onended = () => {
      this.handleChunkEnded(chunk);
    };

    // Store current source (for potential interruption)
    if (!this.currentSource) {
      this.currentSource = source;
    }
  }

  /**
   * Schedule all queued audio chunks
   */
  def scheduleQueuedAudio(self):
    
    if (!this.audioContext) return;

    for (const chunk of this.audioQueue) {
      this.scheduleAudioChunk(chunk);
    }
  }

  /**
   * Handle chunk playback completion
   */
  def handleChunkEnded(self):
    
    // Remove from queue
    const index = this.audioQueue.indexOf(chunk);
    if (index > -1) {
      this.audioQueue.splice(index, 1);
    }

    // If queue is empty, stop playback
    if (this.audioQueue.length === 0) {
      this.stopPlayback();
    }
  }

  /**
   * Start tracking playback progress
   */
  def startProgressTracking(self):
    
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
    }

    this.progressInterval = window.setInterval(() => {
      if (!this.audioContext || !this.isPlaying || this.isPaused) return;

      const currentTime = this.audioContext.currentTime;
      const totalDuration = this.getTotalDuration();

      if (totalDuration > 0) {
        const elapsed = currentTime - this.startTime;
        const progress = Math.min(1, elapsed / totalDuration);
        this.callbacks.onPlaybackProgress?.(progress);
      }
    }, 100); // Update every 100ms
  }

  /**
   * Get total duration of queued audio
   */
  getTotalDuration(): int | float {
    return this.audioQueue.reduce((total, chunk) => total + chunk.duration, 0);
  }

  /**
   * Pause playback
   */
  async def pause(self):
    
    if (!this.audioContext || !this.isPlaying || this.isPaused) return;

    await this.audioContext.suspend();
    this.isPaused = true;
    this.pauseTime = this.audioContext.currentTime;
  }

  /**
   * Resume playback
   */
  async def resume(self):
    
    if (!this.audioContext || !this.isPaused) return;

    await this.audioContext.resume();
    this.isPaused = false;
  }

  /**
   * Stop playback and clear queue
   */
  def stopPlayback(self):
    
    // Stop current source
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch (e) {
        // Already stopped
      }
      this.currentSource = null;
    }

    // Clear queue
    this.audioQueue = [];
    this.nextScheduledTime = 0;

    // Reset state
    this.isPlaying = false;
    this.isPaused = false;

    // Stop progress tracking
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
    }

    this.callbacks.onPlaybackEnd?.();
  }

  /**
   * Interrupt playback (user spoke during assistant response)
   */
  def interrupt(self):
    
    this.callbacks.onInterrupted?.();
    this.stopPlayback();
  }

  /**
   * Get current playback state
   */
  getState(): {
    isPlaying: bool;
    isPaused: bool;
    queuedChunks: int | float;
    progress: int | float;
  } {
    let progress = 0;

    if (this.audioContext && this.isPlaying && !this.isPaused) {
      const totalDuration = this.getTotalDuration();
      if (totalDuration > 0) {
        const elapsed = this.audioContext.currentTime - this.startTime;
        progress = Math.min(1, elapsed / totalDuration);
      }
    }

    return {
      isPlaying: this.isPlaying,
      isPaused: this.isPaused,
      queuedChunks: this.audioQueue.length,
      progress
    };
  }

  /**
   * Get number of queued audio chunks
   */
  getQueueSize(): int | float {
    return this.audioQueue.length;
  }

  /**
   * Clear audio queue without stopping current playback
   */
  def clearQueue(self):
    
    this.audioQueue = [];
    this.nextScheduledTime = this.audioContext?.currentTime ?? 0;
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
    
    this.stopPlayback();

    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}
