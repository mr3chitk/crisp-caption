import type { DotState } from '@/types';

const ICE = [{ urls: 'stun:stun.l.google.com:19302' }];

export interface CaptureCallbacks {
  onRtcState: (text: string, dot: DotState) => void;
  onAudioState: (text: string, dot: DotState) => void;
  onSessionLabel: (text: string) => void;
  onLog: (line: string) => void;
}

export class CaptureSession {
  private pc: RTCPeerConnection | null = null;
  private activeStream: MediaStream | null = null;

  constructor(private readonly callbacks: CaptureCallbacks) {}

  async startDisplay(): Promise<void> {
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
    await this.connectWithStream(stream, 'tab audio');
  }

  async startMicrophone(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    await this.connectWithStream(stream, 'microphone');
  }

  stop(): void {
    if (this.activeStream) {
      this.activeStream.getTracks().forEach((track) => track.stop());
      this.activeStream = null;
    }
    if (this.pc) {
      this.pc.close();
      this.pc = null;
    }
    this.callbacks.onSessionLabel('No active capture');
    this.callbacks.onRtcState('idle', '');
    this.callbacks.onAudioState('none', '');
  }

  private async connectWithStream(stream: MediaStream, label: string): Promise<void> {
    this.stop();
    const audioTracks = stream.getAudioTracks();
    if (!audioTracks.length) {
      stream.getTracks().forEach((track) => track.stop());
      throw new Error('No audio track was selected.');
    }

    this.activeStream = stream;
    this.callbacks.onAudioState(label, 'ok');
    this.callbacks.onRtcState('connecting', 'warn');
    this.callbacks.onSessionLabel(`Capturing ${label}`);

    const pc = new RTCPeerConnection({ iceServers: ICE });
    this.pc = pc;
    const channel = pc.createDataChannel('meta');
    channel.onopen = () => undefined;
    pc.onconnectionstatechange = () => {
      const state = this.pc ? this.pc.connectionState : 'closed';
      const dot =
        state === 'connected' ? 'ok' : state === 'failed' || state === 'closed' ? 'bad' : 'warn';
      this.callbacks.onRtcState(state, dot);
    };

    audioTracks.forEach((track) => pc.addTrack(track, stream));
    stream.getVideoTracks().forEach((track) => {
      track.enabled = false;
    });
    audioTracks[0].onended = () => {
      this.callbacks.onLog('Audio track ended');
      this.stop();
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    const response = await fetch('/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
    });
    if (!response.ok) {
      let detail = `POST /offer failed ${response.status}`;
      try {
        const err = (await response.json()) as { error?: string };
        if (err.error) detail += `: ${err.error}`;
      } catch {
        // Ignore non-JSON error bodies.
      }
      throw new Error(detail);
    }
    const answer = (await response.json()) as RTCSessionDescriptionInit;
    await pc.setRemoteDescription({ type: answer.type, sdp: answer.sdp });
    this.callbacks.onRtcState('connected', 'ok');
    this.callbacks.onLog(`Capture connected: ${label}`);
  }
}
