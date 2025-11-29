/**
 * WebSocket Voice Client Service
 * Handles real-time bidirectional voice communication with backend
 */

export interface VoiceMessage {
  type: 'session_initialized' | 'transcription' | 'processing' | 'agent_speaking' | 
        'agent_finished' | 'interrupted' | 'error' | 'timeout' | 'heartbeat' | 
        'pong' | 'session_complete' | 'stopped';
  session_id?: string;
  status?: string;
  text?: string;
  is_final?: boolean;
  message?: string;
  spoken_text?: string;
  has_pending_work?: boolean;
  session_complete?: boolean;
}

export interface VoiceClientConfig {
  onSessionInitialized?: (sessionId: string) => void;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onProcessing?: (message: string) => void;
  onAgentSpeaking?: (text: string) => void;
  onAgentFinished?: (sessionComplete: boolean) => void;
  onAudioReceived?: (audioData: ArrayBuffer) => void;
  onInterrupted?: (spokenText: string, hasPendingWork: boolean) => void;
  onError?: (error: string) => void;
  onDisconnected?: () => void;
  onTimeout?: () => void;
}

export class VoiceWebSocketClient {
  private ws: WebSocket | null = null;
  private config: VoiceClientConfig;
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private audioQueue: ArrayBuffer[] = [];
  private isPlaying: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 3;
  private reconnectDelay: number = 2000;
  private sessionId: string | null = null;
  private isConnected: boolean = false;
  private turnEndTimer: NodeJS.Timeout | null = null;
  private silenceDuration: number = 2000; // 2 seconds of silence

  constructor(config: VoiceClientConfig) {
    this.config = config;
  }

  /**
   * Connect to WebSocket voice endpoint
   */
  async connect(businessId: number = 2, userId: number = 1): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Determine WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        
        // In development, connect directly to backend (Vite proxy doesn't support WebSocket upgrades properly)
        // In production, use the same host as the frontend
        const wsUrl = import.meta.env.DEV 
          ? 'ws://127.0.0.1:8000/voice/ws/voice'
          : `${protocol}//${window.location.host}/voice/ws/voice`;

        this.ws = new WebSocket(wsUrl);
        this.ws.binaryType = 'arraybuffer';

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          
          // Send initial connection message
          this.send({
            business_id: businessId,
            user_id: userId
          });
          
          this.isConnected = true;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = async (event) => {
          if (event.data instanceof ArrayBuffer) {
            // Audio data from TTS
            this.audioQueue.push(event.data);
            await this.playAudioQueue();
            
            if (this.config.onAudioReceived) {
              this.config.onAudioReceived(event.data);
            }
          } else {
            // JSON message
            try {
              const message: VoiceMessage = JSON.parse(event.data);
              this.handleMessage(message);
            } catch (error) {
              console.error('Error parsing message:', error);
            }
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (this.config.onError) {
            this.config.onError('Connection error occurred');
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          
          if (this.config.onDisconnected) {
            this.config.onDisconnected();
          }
          
          // Attempt reconnection
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            
            setTimeout(() => {
              this.connect(businessId, userId).catch(console.error);
            }, this.reconnectDelay);
          }
        };

      } catch (error) {
        console.error('Connection error:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: VoiceMessage): void {
    console.log('Received message:', message.type, message);

    switch (message.type) {
      case 'session_initialized':
        this.sessionId = message.session_id || null;
        if (this.config.onSessionInitialized && this.sessionId) {
          this.config.onSessionInitialized(this.sessionId);
        }
        break;

      case 'transcription':
        if (this.config.onTranscription && message.text) {
          this.config.onTranscription(message.text, message.is_final || false);
        }
        break;

      case 'processing':
        if (this.config.onProcessing && message.message) {
          this.config.onProcessing(message.message);
        }
        break;

      case 'agent_speaking':
        if (this.config.onAgentSpeaking && message.text) {
          this.config.onAgentSpeaking(message.text);
        }
        break;

      case 'agent_finished':
        if (this.config.onAgentFinished) {
          this.config.onAgentFinished(message.session_complete || false);
        }
        break;

      case 'interrupted':
        if (this.config.onInterrupted) {
          this.config.onInterrupted(
            message.spoken_text || '',
            message.has_pending_work || false
          );
        }
        break;

      case 'error':
        if (this.config.onError && message.message) {
          this.config.onError(message.message);
        }
        break;

      case 'timeout':
        if (this.config.onTimeout) {
          this.config.onTimeout();
        }
        break;

      case 'heartbeat':
        // Respond to heartbeat
        this.send({ command: 'ping' });
        break;

      case 'session_complete':
        console.log('Session completed');
        break;
    }
  }

  /**
   * Start capturing and streaming microphone audio
   */
  async startRecording(): Promise<void> {
    try {
      // Check if mediaDevices is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          'Microphone access not available. Please access the app via localhost or HTTPS.'
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Create MediaRecorder with appropriate codec
      const mimeType = 'audio/webm;codecs=opus';
      
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        throw new Error('Required audio format not supported');
      }

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 16000
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.isConnected) {
          // Convert to ArrayBuffer and send
          event.data.arrayBuffer().then(buffer => {
            this.sendAudio(buffer);
            
            // Reset turn end timer on new audio
            this.resetTurnEndTimer();
          });
        }
      };

      // Capture audio in 100ms chunks
      this.mediaRecorder.start(100);
      console.log('Recording started');

    } catch (error) {
      console.error('Error starting recording:', error);
      if (this.config.onError) {
        this.config.onError('Failed to access microphone');
      }
      throw error;
    }
  }

  /**
   * Reset turn end timer (called when new audio is captured)
   */
  private resetTurnEndTimer(): void {
    if (this.turnEndTimer) {
      clearTimeout(this.turnEndTimer);
    }
    
    // Start new timer - if no audio for silenceDuration, signal turn end
    this.turnEndTimer = setTimeout(() => {
      if (this.isConnected) {
        console.log('Silence detected - ending turn');
        this.send({ command: 'turn_end' });
      }
    }, this.silenceDuration);
  }

  /**
   * Stop recording
   */
  stopRecording(): void {
    if (this.turnEndTimer) {
      clearTimeout(this.turnEndTimer);
      this.turnEndTimer = null;
    }
    
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
      
      // Stop all tracks
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
      
      this.mediaRecorder = null;
      console.log('Recording stopped');
    }
  }

  /**
   * Send audio data to server
   */
  private sendAudio(audioData: ArrayBuffer): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
    }
  }

  /**
   * Send JSON message to server
   */
  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Play audio queue with Web Audio API
   */
  private async playAudioQueue(): Promise<void> {
    if (this.isPlaying || this.audioQueue.length === 0) {
      return;
    }

    this.isPlaying = true;

    try {
      if (!this.audioContext) {
        this.audioContext = new AudioContext({ sampleRate: 24000 });
      }

      while (this.audioQueue.length > 0) {
        const audioData = this.audioQueue.shift();
        if (!audioData) continue;

        try {
          // Decode and play audio
          const audioBuffer = await this.audioContext.decodeAudioData(audioData);
          const source = this.audioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(this.audioContext.destination);
          
          // Wait for audio to finish playing
          await new Promise<void>((resolve) => {
            source.onended = () => resolve();
            source.start();
          });
          
        } catch (error) {
          console.error('Error playing audio chunk:', error);
        }
      }
    } finally {
      this.isPlaying = false;
    }
  }

  /**
   * Clear audio queue (for interruption)
   */
  clearAudioQueue(): void {
    this.audioQueue = [];
    this.isPlaying = false;
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.stopRecording();
    this.clearAudioQueue();
    
    if (this.turnEndTimer) {
      clearTimeout(this.turnEndTimer);
      this.turnEndTimer = null;
    }
    
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    if (this.ws) {
      this.send({ command: 'stop' });
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
    this.sessionId = null;
  }

  /**
   * Check if connected
   */
  isSocketConnected(): boolean {
    return this.isConnected && this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }
}
