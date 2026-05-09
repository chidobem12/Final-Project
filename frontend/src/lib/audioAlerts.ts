class AegisAudioSystem {
  private ctx: AudioContext | null = null;

  private getCtx(): AudioContext {
    if (!this.ctx) {
      this.ctx = new AudioContext();
    }
    return this.ctx;
  }

  playAlert(severity: 'CRITICAL' | 'HIGH' | 'MEDIUM') {
    const ctx = this.getCtx();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    const configs = {
      CRITICAL: { freq: 880, duration: 0.3, pulses: 3, volume: 0.4 },
      HIGH: { freq: 660, duration: 0.2, pulses: 2, volume: 0.25 },
      MEDIUM: { freq: 440, duration: 0.1, pulses: 1, volume: 0.15 },
    };

    const { freq, duration, pulses, volume } = configs[severity];

    oscillator.frequency.setValueAtTime(freq, ctx.currentTime);
    oscillator.type = 'sine';

    for (let i = 0; i < pulses; i += 1) {
      const start = ctx.currentTime + i * (duration + 0.05);
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(volume, start + 0.01);
      gain.gain.linearRampToValueAtTime(0, start + duration);
    }

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + pulses * (duration + 0.05) + 0.1);
  }

  playConnectionRestored() {
    const ctx = this.getCtx();
    [440, 660].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = freq;
      osc.type = 'sine';
      const start = ctx.currentTime + i * 0.15;
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(0.2, start + 0.05);
      gain.gain.linearRampToValueAtTime(0, start + 0.2);
      osc.start(start);
      osc.stop(start + 0.25);
    });
  }
}

export const audioSystem = new AegisAudioSystem();
