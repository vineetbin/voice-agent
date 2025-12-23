/**
 * Hook for managing Retell web calls via the Web SDK.
 * 
 * This enables browser-based calling for non-USA testing.
 * Uses WebRTC to establish real-time voice communication.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { RetellWebClient } from 'retell-client-js-sdk';

export type WebCallStatus = 'idle' | 'connecting' | 'connected' | 'ended' | 'error';

export interface WebCallState {
  status: WebCallStatus;
  error: string | null;
  isMuted: boolean;
}

export interface UseRetellWebCallReturn {
  state: WebCallState;
  startCall: (accessToken: string) => Promise<void>;
  endCall: () => void;
  toggleMute: () => void;
}

/**
 * Hook for managing Retell web calls
 * 
 * @example
 * ```tsx
 * const { state, startCall, endCall, toggleMute } = useRetellWebCall();
 * 
 * // Start a call with access token from backend
 * await startCall(response.access_token);
 * 
 * // End the call
 * endCall();
 * ```
 */
export function useRetellWebCall(): UseRetellWebCallReturn {
  const [state, setState] = useState<WebCallState>({
    status: 'idle',
    error: null,
    isMuted: false,
  });
  
  const clientRef = useRef<RetellWebClient | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (clientRef.current) {
        clientRef.current.stopCall();
        clientRef.current = null;
      }
    };
  }, []);

  const startCall = useCallback(async (accessToken: string) => {
    if (!accessToken) {
      setState((prev) => ({ ...prev, status: 'error', error: 'No access token provided' }));
      return;
    }

    try {
      setState((prev) => ({ ...prev, status: 'connecting', error: null }));

      // Create new client instance
      const client = new RetellWebClient();
      clientRef.current = client;

      // Set up event handlers
      client.on('call_started', () => {
        console.log('Retell call started');
        setState((prev) => ({ ...prev, status: 'connected' }));
      });

      client.on('call_ended', () => {
        console.log('Retell call ended');
        setState((prev) => ({ ...prev, status: 'ended' }));
        clientRef.current = null;
      });

      client.on('error', (error: Error) => {
        console.error('Retell call error:', error);
        setState((prev) => ({ 
          ...prev, 
          status: 'error', 
          error: error.message || 'Call error occurred' 
        }));
        clientRef.current = null;
      });

      // Start the call
      await client.startCall({
        accessToken,
        sampleRate: 24000,
        captureDeviceId: 'default',
        playbackDeviceId: 'default',
      });

    } catch (error) {
      console.error('Failed to start Retell call:', error);
      setState((prev) => ({ 
        ...prev, 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Failed to start call' 
      }));
      clientRef.current = null;
    }
  }, []);

  const endCall = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.stopCall();
      clientRef.current = null;
    }
    setState((prev) => ({ ...prev, status: 'ended' }));
  }, []);

  const toggleMute = useCallback(() => {
    if (clientRef.current) {
      const newMutedState = !state.isMuted;
      if (newMutedState) {
        clientRef.current.mute();
      } else {
        clientRef.current.unmute();
      }
      setState((prev) => ({ ...prev, isMuted: newMutedState }));
    }
  }, [state.isMuted]);

  return {
    state,
    startCall,
    endCall,
    toggleMute,
  };
}

