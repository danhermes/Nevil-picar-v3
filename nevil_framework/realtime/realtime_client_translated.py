#
# Translated from Blane3: RealtimeClient.ts
# Original: ../candy_mountain/blane3/lib/realtime/RealtimeClient.ts
# Translation date: 2025-11-11
# Manual adaptation required for full Nevil integration
#
"""
RealtimeConnectionManager - Translated from Blane3 RealtimeClient.ts
Production-tested WebSocket client for OpenAI Realtime API
"""

import asyncio
import websockets
import json
import base64
import logging
from typing import Dict, Callable, Any, Optional
from threading import Thread, Lock

logger = logging.getLogger(__name__)

/**
 * WebSocket client for OpenAI Realtime API
 * Handles connection lifecycle, authentication, and message routing
 */

import { RealtimeEventHandler } from './RealtimeEventHandlers';
import { ConnectionState } from './RealtimeTypes';  // Import enum as value, not type
import type {
  ConnectionConfig,
  ConnectionMetrics,
  RealtimeClientOptions,
  ClientMessage,
  ServerEvent,
  SessionConfig,
  EventHandlers,
  ReconnectOptions
} from './RealtimeTypes';

const DEFAULT_REALTIME_URL = 'wss://api.openai.com/v1/realtime';
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 5;
const DEFAULT_RECONNECT_BASE_DELAY = 1000; // 1 second
const DEFAULT_CONNECTION_TIMEOUT = 30000; // 30 seconds

/**
 * WebSocket client for OpenAI Realtime API with automatic reconnection
 */
class RealtimeClient {
  ws: WebSocket | null = null;
  config: Required<ConnectionConfig>;
  state: ConnectionState = ConnectionState.DISCONNECTED;
  eventHandler: RealtimeEventHandler;
  sessionConfig?: SessionConfig;
  debug: bool;

  // Connection management
  reconnectAttempts = 0;
  reconnectTimer?: NodeJS.Timeout;
  connectionTimer?: NodeJS.Timeout;
  connectionStartTime?: Date;

  // Metrics
  metrics: ConnectionMetrics = {
    connectionAttempts: 0,
    reconnectAttempts: 0,
    totalUptime: 0,
    messagesSent: 0,
    messagesReceived: 0
  };

  // Message queue for offline messages
  messageQueue: ClientMessage[] = [];
  maxQueueSize = 100;

  def __init__(self, options: RealtimeClientOptions = {}) {
    // Initialize configuration
    this.config = {
      apiKey: options.apiKey,
      ephemeralToken: options.ephemeralToken,
      url: options.url || DEFAULT_REALTIME_URL,
      maxReconnectAttempts: options.maxReconnectAttempts || DEFAULT_MAX_RECONNECT_ATTEMPTS,
      reconnectBaseDelay: options.reconnectBaseDelay || DEFAULT_RECONNECT_BASE_DELAY,
      connectionTimeout: options.connectionTimeout || DEFAULT_CONNECTION_TIMEOUT
    };

    this.sessionConfig = options.sessionConfig;
    this.debug = options.debug || false;

    // Initialize event handler
    this.eventHandler = new RealtimeEventHandler(options.handlers || {}, this.debug);

    // Forward internal events
    this.setupEventForwarding();
  }

  // ============================================================================
  // Connection Management
  // ============================================================================

  /**
   * Connect to OpenAI Realtime API
   */
  async def connect(self):
    
    console.log('🔵 [RealtimeClient] connect() called, current state:', this.state);

    if (this.state === ConnectionState.CONNECTED || this.state === ConnectionState.CONNECTING) {
      this.log('Already connected or connecting');
      console.log('🟡 [RealtimeClient] Skipping - already connected or connecting');
      return;
    }

    this.setState(ConnectionState.CONNECTING);
    this.metrics.connectionAttempts++;
    this.connectionStartTime = new Date();

    try {
      // Validate authentication
      this.validateAuth();
      console.log('✅ [RealtimeClient] Authentication validated');

      // Build WebSocket URL with authentication
      const url = this.buildConnectionUrl();
      console.log('🔗 [RealtimeClient] WebSocket URL:', url);

      // Create WebSocket connection (browser native WebSocket)
      // For ephemeral tokens, pass token via Sec-WebSocket-Protocol header
      if (this.config.ephemeralToken) {
        console.log('🔑 [RealtimeClient] Creating WebSocket with ephemeral token');
        console.log('🔑 [RealtimeClient] Token (first 20 chars):', this.config.ephemeralToken.substring(0, 20));

        this.ws = await websockets.connect(url, [
          'realtime',
          `openai-insecure-api-key.${this.config.ephemeralToken}`,
          'openai-beta.realtime-v1'
        ]);

        console.log('🌐 [RealtimeClient] WebSocket created, readyState:', this.ws.readyState);
        console.log('🌐 [RealtimeClient] readyState meanings: 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED');
      } else {
        console.log('🔓 [RealtimeClient] Creating WebSocket without token (API key mode)');
        this.ws = await websockets.connect(url);
        console.log('🌐 [RealtimeClient] WebSocket created, readyState:', this.ws.readyState);
      }

      // Setup connection timeout
      this.setupConnectionTimeout();
      console.log('⏰ [RealtimeClient] Connection timeout setup complete');

      // Setup WebSocket event handlers
      this.setupWebSocketHandlers();
      console.log('🎯 [RealtimeClient] WebSocket handlers setup complete');

      // Log WebSocket object details
      console.log('📊 [RealtimeClient] WebSocket details:', {
        url: this.ws.url,
        protocol: this.ws.protocol,
        readyState: this.ws.readyState,
        bufferedAmount: this.ws.bufferedAmount
      });

    } catch (error) {
      console.error('❌ [RealtimeClient] Error in connect():', error);
      this.handleConnectionError(error);
    }

    console.log('🏁 [RealtimeClient] connect() method completed');
  }

  /**
   * Disconnect from server
   */
  def disconnect(self):
    
    this.log(`Disconnecting: ${reason}`);

    // Clear reconnection timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    // Clear connection timeout
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer);
      this.connectionTimer = undefined;
    }

    // Close WebSocket
    if (this.ws) {
      await self.ws.close(1000, reason);
      this.ws = null;
    }

    // Update metrics
    this.updateUptime();

    // Update state
    this.setState(ConnectionState.DISCONNECTED);

    // Emit disconnect event
    this.eventHandler.emit('disconnect', reason);
  }

  /**
   * Reconnect with exponential backoff
   */
  async def reconnect(self):
    
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log(`Max reconnection attempts (${this.config.maxReconnectAttempts}) reached`);
      this.setState(ConnectionState.FAILED);
      this.eventHandler.emit('error', new Error('Max reconnection attempts reached'));
      return;
    }

    this.reconnectAttempts++;
    this.metrics.reconnectAttempts++;
    this.setState(ConnectionState.RECONNECTING);

    // Calculate exponential backoff delay: 1s, 2s, 4s, 8s, 16s
    const delay = Math.min(
      this.config.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts - 1),
      16000
    );

    const options: ReconnectOptions = {
      attempt: this.reconnectAttempts,
      maxAttempts: this.config.maxReconnectAttempts,
      delay,
      reason
    };

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);
    this.eventHandler.emit('reconnecting', options);

    // Schedule reconnection
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        this.log(`Reconnection failed: ${error.message}`);
        this.reconnect(error.message);
      });
    }, delay);
  }

  // ============================================================================
  // WebSocket Event Handlers
  // ============================================================================

  def setupWebSocketHandlers(self):
    
    if (!this.ws) {
      console.error('❌ [RealtimeClient] setupWebSocketHandlers called but this.ws is null!');
      return;
    }

    console.log('🎯 [RealtimeClient] Setting up WebSocket handlers...');

    // Browser WebSocket uses addEventListener or direct assignment
    this.ws.onopen = () => {
      console.log('🎉 [RealtimeClient] WebSocket onopen fired!');
      this.handleOpen();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      console.log('📨 [RealtimeClient] WebSocket onmessage fired');
      this.handleMessage(event.data);
    };

    this.ws.onerror = (event: Event) => {
      console.error('❌ [RealtimeClient] WebSocket onerror fired:', event);
      this.handleError(new Error('WebSocket error'));
    };

    this.ws.onclose = (event: CloseEvent) => {
      console.log('🔴 [RealtimeClient] WebSocket onclose fired, code:', event.code, 'reason:', event.reason);
      this.handleClose(event.code, event.reason);
    };

    console.log('✅ [RealtimeClient] All WebSocket handlers attached');
  }

  def handleOpen(self):
    
    console.log('🎊 [RealtimeClient] handleOpen() called');
    this.log('WebSocket connection opened');

    // Clear connection timeout
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer);
      this.connectionTimer = undefined;
    }

    // Reset reconnection attempts
    this.reconnectAttempts = 0;

    // Update state
    console.log('📊 [RealtimeClient] Setting state to CONNECTED');
    this.setState(ConnectionState.CONNECTED);

    // Update metrics
    this.metrics.lastConnectedAt = new Date();

    // Send session configuration if provided
    if (this.sessionConfig) {
      this.updateSession(this.sessionConfig);
    }

    // Process queued messages
    this.processMessageQueue();

    // Emit connect event
    console.log('📡 [RealtimeClient] About to emit "connect" event');
    this.eventHandler.emit('connect');
    console.log('✅ [RealtimeClient] "connect" event emitted');
  }

  async def handleMessage(self):
    
    try {
      // Handle both string and Blob data from browser WebSocket
      const message = typeof data === 'string' ? data : await data.text();
      this.metrics.messagesReceived++;

      // Parse server event
      const event: ServerEvent = JSON.parse(message);

      if (this.debug) {
        this.log(`Received event: ${event.type}`, event);
      }

      // Process event through handler
      await this.eventHandler.handleEvent(event);

    } catch (error) {
      this.log(`Error processing message: ${error}`);
      this.eventHandler.emit('error', error instanceof Error ? error : new Error(String(error)));
    }
  }

  def handleError(self):
    
    this.log(`WebSocket error: ${error.message}`);
    this.eventHandler.emit('error', error);
  }

  def handleClose(self):
    
    this.log(`WebSocket closed: ${code} - ${reason}`);

    // Update metrics
    this.updateUptime();

    // Update state
    const wasConnected = this.state === ConnectionState.CONNECTED;
    this.setState(ConnectionState.DISCONNECTED);

    // Emit disconnect event
    this.eventHandler.emit('disconnect', reason || `Connection closed with code ${code}`);

    // Attempt reconnection if it was an unexpected disconnect
    if (wasConnected && code !== 1000) {
      this.reconnect(`Connection closed unexpectedly: ${code}`);
    }
  }

  // ============================================================================
  // Message Sending
  // ============================================================================

  /**
   * Send message to server
   */
  def send(self):
    
    if (this.state !== ConnectionState.CONNECTED) {
      this.log(`Not connected, queueing message: ${message.type}`);
      this.queueMessage(message);
      return;
    }

    try {
      const json = JSON.stringify(message);
      this.ws?.send(json);
      this.metrics.messagesSent++;

      if (this.debug) {
        this.log(`Sent message: ${message.type}`, message);
      }
    } catch (error) {
      this.log(`Error sending message: ${error}`);
      this.eventHandler.emit('error', error instanceof Error ? error : new Error(String(error)));
      this.queueMessage(message);
    }
  }

  /**
   * Update session configuration
   */
  def updateSession(self):
    
    this.sessionConfig = config;
    this.send({
      type: 'session.update',
      session: config
    });
  }

  /**
   * Append audio to input buffer
   */
  def appendInputAudio(self):
    
    this.send({
      type: 'input_audio_buffer.append',
      audio: audioBase64
    });
  }

  /**
   * Commit audio buffer
   */
  def commitInputAudio(self):
    
    this.send({
      type: 'input_audio_buffer.commit'
    });
  }

  /**
   * Clear audio buffer
   */
  def clearInputAudio(self):
    
    this.send({
      type: 'input_audio_buffer.clear'
    });
  }

  /**
   * Create response
   */
  def createResponse(self):
    
    this.send({
      type: 'response.create',
      response: config
    });
  }

  /**
   * Cancel response
   */
  def cancelResponse(self):
    
    this.send({
      type: 'response.cancel'
    });
  }

  // ============================================================================
  // State Management
  // ============================================================================

  def setState(self):
    
    const oldState = this.state;
    this.state = newState;

    if (oldState !== newState) {
      this.log(`State changed: ${oldState} -> ${newState}`);
      this.eventHandler.emit('stateChange', { from: oldState, to: newState });
    }
  }

  def getState(self):
    
    return this.state;
  }

  def isConnected(self):
    
    return this.state === ConnectionState.CONNECTED;
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  def validateAuth(self):
    
    if (!this.config.apiKey && !this.config.ephemeralToken) {
      throw new Error('Either apiKey or ephemeralToken must be provided');
    }
  }

  def buildConnectionUrl(self):
    
    const baseUrl = this.config.url || DEFAULT_REALTIME_URL;

    // Browser WebSocket doesn't support custom headers
    // For ephemeral tokens, OpenAI expects the URL format: wss://api.openai.com/v1/realtime?model=MODEL
    // Then the token is passed via the Authorization header in the initial HTTP upgrade request
    // Since we can't set headers in browser WebSocket, we need a different approach

    if (this.config.ephemeralToken) {
      // The token will be validated via the initial handshake
      // We'll construct a URL that uses the ephemeral token approach
      return `${baseUrl}?model=gpt-4o-realtime-preview-2024-12-17`;
    } else if (this.config.apiKey) {
      // For API keys, this won't work in browser - ephemeral tokens should be used
      console.warn('Direct API key usage not supported in browser. Use ephemeral tokens.');
      return `${baseUrl}?model=gpt-4o-realtime-preview-2024-12-17`;
    }

    return baseUrl;
  }

  def setupConnectionTimeout(self):
    
    this.connectionTimer = setTimeout(() => {
      if (this.state === ConnectionState.CONNECTING) {
        this.log('Connection timeout');
        this.disconnect('Connection timeout');
        this.reconnect('Connection timeout');
      }
    }, this.config.connectionTimeout);
  }

  def queueMessage(self):
    
    if (this.messageQueue.length >= this.maxQueueSize) {
      this.log('Message queue full, dropping oldest message');
      this.messageQueue.shift();
    }
    this.messageQueue.push(message);
  }

  def processMessageQueue(self):
    
    if (this.messageQueue.length === 0) return;

    this.log(`Processing ${this.messageQueue.length} queued messages`);

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  def updateUptime(self):
    
    if (this.connectionStartTime) {
      const uptime = Date.now() - this.connectionStartTime.getTime();
      this.metrics.totalUptime += uptime;
      this.metrics.lastDisconnectedAt = new Date();
      this.connectionStartTime = undefined;
    }
  }

  def handleConnectionError(self):
    
    const err = error instanceof Error ? error : new Error(String(error));
    this.log(`Connection error: ${err.message}`);
    this.setState(ConnectionState.FAILED);
    this.eventHandler.emit('error', err);
    this.reconnect(err.message);
  }

  def setupEventForwarding(self):
    
    // Event forwarding not needed - events are already accessible through eventHandler
    // The eventHandler is used directly by external consumers via on/off/once methods
    // Removed infinite loop: listening to event and re-emitting same event
  }

  def log(self):
    
    if (this.debug) {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] [RealtimeClient] ${message}`, data || '');
    }
  }

  // ============================================================================
  // Public API
  // ============================================================================

  /**
   * Get connection metrics
   */
  def getMetrics(self):
    
    return { ...this.metrics };
  }

  /**
   * Get event statistics
   */
  getEventStats(): Record<string, number> {
    return this.eventHandler.getEventStats();
  }

  /**
   * Update event handlers at runtime
   */
  def updateHandlers(self):
    
    this.eventHandler.updateHandlers(handlers);
  }

  /**
   * Subscribe to events using object pattern
   */
  on(event: str, listener: (...args: any[]) => void): this {
    this.eventHandler.on(event, listener);
    return this;
  }

  /**
   * Unsubscribe from events
   */
  off(event: str, listener: (...args: any[]) => void): this {
    this.eventHandler.off(event, listener);
    return this;
  }

  /**
   * Subscribe to event once
   */
  once(event: str, listener: (...args: any[]) => void): this {
    this.eventHandler.once(event, listener);
    return this;
  }

  /**
   * Clean up resources
   */
  def destroy(self):
    
    this.disconnect('Client destroyed');
    this.eventHandler.removeAllListeners();
  }
}
