/**
 * Escape The Website - Audio Subsystem
 * Web Audio API synthesizer with persistent audio preference, 
 * clean node lifecycle, and non-clipping gain mixing.
 */

const AUDIO_STORAGE_KEY = 'escape_the_website_audio_v1';

class AudioManager {
  constructor() {
    this.soundEnabled = true;
    this.musicEnabled = true;
    this.audioContext = null;
    this.masterGain = null;
    this.ambienceGain = null;
    this.sfxGain = null;
    this.ambienceOscillators = [];
    this.isInitialized = false;

    this.loadAudioPreference();
  }

  /**
   * Load persisted user audio preference
   */
  loadAudioPreference() {
    try {
      if (typeof localStorage !== 'undefined') {
        const saved = localStorage.getItem(AUDIO_STORAGE_KEY);
        if (saved) {
          const pref = JSON.parse(saved);
          if (typeof pref.sound === 'boolean') this.soundEnabled = pref.sound;
          if (typeof pref.music === 'boolean') this.musicEnabled = pref.music;
        }
      }
    } catch (e) {
      this.soundEnabled = true;
      this.musicEnabled = true;
    }
  }

  /**
   * Save audio preference to localStorage
   */
  saveAudioPreference() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(AUDIO_STORAGE_KEY, JSON.stringify({
          sound: this.soundEnabled,
          music: this.musicEnabled
        }));
      }
    } catch (e) {}
  }

  /**
   * Initializes audio context on first user gesture
   */
  init() {
    if (this.isInitialized && this.audioContext) {
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume().catch(() => {});
      }
      return;
    }

    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioContext = new AudioContextClass();

        // Master Gain (tamed to avoid clipping)
        this.masterGain = this.audioContext.createGain();
        this.masterGain.gain.setValueAtTime(0.75, this.audioContext.currentTime);

        // SFX Gain
        this.sfxGain = this.audioContext.createGain();
        this.sfxGain.gain.setValueAtTime(this.soundEnabled ? 0.85 : 0, this.audioContext.currentTime);
        this.sfxGain.connect(this.masterGain);

        // Ambience Gain
        this.ambienceGain = this.audioContext.createGain();
        this.ambienceGain.gain.setValueAtTime(this.musicEnabled ? 0.3 : 0, this.audioContext.currentTime);
        this.ambienceGain.connect(this.masterGain);

        this.masterGain.connect(this.audioContext.destination);
        this.isInitialized = true;
      }
    } catch (e) {
      console.warn('[AudioManager] Web Audio API initialization deferred or unsupported.');
    }
  }

  /**
   * Toggle global audio on/off
   */
  toggleGlobalAudio() {
    const newState = !this.soundEnabled;
    this.soundEnabled = newState;
    this.musicEnabled = newState;

    if (this.audioContext) {
      const now = this.audioContext.currentTime;
      if (this.sfxGain) {
        this.sfxGain.gain.setTargetAtTime(this.soundEnabled ? 0.85 : 0, now, 0.05);
      }
      if (this.ambienceGain) {
        this.ambienceGain.gain.setTargetAtTime(this.musicEnabled ? 0.3 : 0, now, 0.08);
      }
    }

    if (!this.musicEnabled) {
      this.stopAmbientDrone();
    } else {
      this.startAmbientDrone();
    }

    this.saveAudioPreference();
    return this.soundEnabled;
  }

  /**
   * Toggle sound FX
   */
  toggleSound() {
    this.soundEnabled = !this.soundEnabled;
    if (this.sfxGain && this.audioContext) {
      this.sfxGain.gain.setTargetAtTime(this.soundEnabled ? 0.85 : 0, this.audioContext.currentTime, 0.05);
    }
    this.saveAudioPreference();
    return this.soundEnabled;
  }

  /**
   * Toggle music/ambience
   */
  toggleMusic() {
    this.musicEnabled = !this.musicEnabled;
    if (this.ambienceGain && this.audioContext) {
      this.ambienceGain.gain.setTargetAtTime(this.musicEnabled ? 0.3 : 0, this.audioContext.currentTime, 0.1);
    }
    if (!this.musicEnabled) {
      this.stopAmbientDrone();
    } else {
      this.startAmbientDrone();
    }
    this.saveAudioPreference();
    return this.musicEnabled;
  }

  /**
   * Synthesize atmospheric click / enter transition sound
   */
  playEnterSound() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;

      // Deep Sub Bass Impact
      const subOsc = this.audioContext.createOscillator();
      const subGain = this.audioContext.createGain();
      subOsc.type = 'sine';
      subOsc.frequency.setValueAtTime(140, now);
      subOsc.frequency.exponentialRampToValueAtTime(32, now + 1.2);

      subGain.gain.setValueAtTime(0.65, now);
      subGain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);

      subOsc.connect(subGain);
      subGain.connect(this.sfxGain);
      subOsc.start(now);
      subOsc.stop(now + 1.3);

      // Cyber Warp / Resonant Shimmer
      const warpOsc = this.audioContext.createOscillator();
      const warpGain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(400, now);
      filter.frequency.exponentialRampToValueAtTime(2000, now + 0.6);
      filter.frequency.exponentialRampToValueAtTime(200, now + 1.4);
      filter.Q.setValueAtTime(4, now);

      warpOsc.type = 'sawtooth';
      warpOsc.frequency.setValueAtTime(110, now);
      warpOsc.frequency.exponentialRampToValueAtTime(440, now + 0.5);
      warpOsc.frequency.exponentialRampToValueAtTime(55, now + 1.4);

      warpGain.gain.setValueAtTime(0.01, now);
      warpGain.gain.linearRampToValueAtTime(0.25, now + 0.2);
      warpGain.gain.exponentialRampToValueAtTime(0.001, now + 1.4);

      warpOsc.connect(filter);
      filter.connect(warpGain);
      warpGain.connect(this.sfxGain);
      warpOsc.start(now);
      warpOsc.stop(now + 1.5);

      setTimeout(() => {
        this.startAmbientDrone();
      }, 700);
    } catch (e) {}
  }

  /**
   * Hover tick sound
   */
  playHoverSound() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(900, now);
      osc.frequency.exponentialRampToValueAtTime(1300, now + 0.025);

      gain.gain.setValueAtTime(0.03, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.025);

      osc.connect(gain);
      gain.connect(this.sfxGain);
      osc.start(now);
      osc.stop(now + 0.03);
    } catch (e) {}
  }

  /**
   * Modal Open sound
   */
  playModalOpen() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.16);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(1100, now);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.1, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.24);
    } catch (e) {}
  }

  /**
   * Modal Close sound
   */
  playModalClose() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(500, now);
      osc.frequency.exponentialRampToValueAtTime(180, now + 0.1);

      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.13);
    } catch (e) {}
  }

  /**
   * Terminal Cyber Prompt / Beep sound
   */
  playTerminalBeep() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(1100, now);
      osc.frequency.setValueAtTime(1600, now + 0.04);

      gain.gain.setValueAtTime(0.035, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.1);
    } catch (e) {}
  }

  /**
   * Terminal Keystroke click
   */
  playTerminalKeystroke() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(1350 + Math.random() * 150, now);

      gain.gain.setValueAtTime(0.018, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.02);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.025);
    } catch (e) {}
  }

  /**
   * Terminal Command Execution Chirp
   */
  playTerminalCommandExec() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(550, now);
      osc.frequency.exponentialRampToValueAtTime(1100, now + 0.05);

      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.08);
    } catch (e) {}
  }

  /**
   * Terminal Diagnostic Radar Sweep
   */
  playTerminalScan() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(750, now + 0.22);
      osc.frequency.exponentialRampToValueAtTime(250, now + 0.45);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(550, now);
      filter.Q.setValueAtTime(4, now);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.07, now + 0.08);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.52);
    } catch (e) {}
  }

  /**
   * Locked / Access Denied low buzzer
   */
  playLockedSound() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(80, now);
      osc.frequency.setValueAtTime(70, now + 0.09);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.27);
    } catch (e) {}
  }

  /**
   * Resonance Node Harmonic Tone
   */
  playResonanceNodeTone(nodeIndex) {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    const pitches = {
      1: 440.00,
      2: 554.37,
      3: 659.25,
      4: 880.00
    };

    const freq = pitches[nodeIndex] || 440;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, now);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(freq * 1.4, now);
      filter.Q.setValueAtTime(3, now);

      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.15, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.4);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.42);
    } catch (e) {}
  }

  /**
   * Resonance Desync / Failed Sequence Buzz
   */
  playResonanceDesync() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(130, now);
      osc.frequency.exponentialRampToValueAtTime(65, now + 0.22);

      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.3);
    } catch (e) {}
  }

  /**
   * Resonance Calibration Complete / Sequence Success Chord
   */
  playResonanceSuccess() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const chord = [440, 554.37, 659.25, 880, 1108.73];

      chord.forEach((freq, i) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        const filter = this.audioContext.createBiquadFilter();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + (i * 0.07));

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(2400, now);

        gain.gain.setValueAtTime(0, now + (i * 0.07));
        gain.gain.linearRampToValueAtTime(0.1, now + (i * 0.07) + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.sfxGain);

        osc.start(now + (i * 0.07));
        osc.stop(now + 1.5);
      });
    } catch (e) {}
  }

  /**
   * Radiant Key Extraction Chime
   */
  playKeyExtractChime() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const arpeggio = [880, 1108.73, 1318.51, 1760, 2217.46];

      arpeggio.forEach((freq, idx) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);

        gain.gain.setValueAtTime(0, now + idx * 0.08);
        gain.gain.linearRampToValueAtTime(0.09, now + idx * 0.08 + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.6 + idx * 0.05);

        osc.connect(gain);
        gain.connect(this.sfxGain);

        osc.start(now + idx * 0.08);
        osc.stop(now + 1.7);
      });
    } catch (e) {}
  }

  // =========================================================================
  // ARCADE SYSTEM DEFENSE SOUNDS
  // =========================================================================

  playArcadeCountdown(num) {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      const freq = num === 1 ? 840 : 420;
      osc.type = 'square';
      osc.frequency.setValueAtTime(freq, now);

      gain.gain.setValueAtTime(0.07, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.11);
    } catch (e) {}
  }

  playArcadeStart() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.22);

      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.32);
    } catch (e) {}
  }

  playTargetTelegraph() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(950, now);
      osc.frequency.exponentialRampToValueAtTime(1500, now + 0.04);

      gain.gain.setValueAtTime(0.02, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.055);
    } catch (e) {}
  }

  playTargetHit(type = 'standard', combo = 1) {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      const baseFreq = type === 'bonus' ? 880 : type === 'fast' ? 680 : 480;
      const pitchMultiplier = 1 + (Math.min(combo, 5) - 1) * 0.1;

      osc.type = type === 'bonus' ? 'triangle' : 'sawtooth';
      osc.frequency.setValueAtTime(baseFreq * pitchMultiplier, now);
      osc.frequency.exponentialRampToValueAtTime(90, now + 0.14);

      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.16);
    } catch (e) {}
  }

  playBonusTargetHit() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      [1100, 1500, 1900].forEach((freq, idx) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.035);

        gain.gain.setValueAtTime(0.07, now + idx * 0.035);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25 + idx * 0.035);

        osc.connect(gain);
        gain.connect(this.sfxGain);

        osc.start(now + idx * 0.035);
        osc.stop(now + 0.28 + idx * 0.035);
      });
    } catch (e) {}
  }

  playTargetMiss() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(260, now);
      osc.frequency.exponentialRampToValueAtTime(90, now + 0.08);

      gain.gain.setValueAtTime(0.025, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.1);
    } catch (e) {}
  }

  playTimerWarning() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(700, now);

      gain.gain.setValueAtTime(0.035, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.06);
    } catch (e) {}
  }

  playArcadeVictory() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const fan = [523.25, 659.25, 783.99, 1046.50, 1318.51];

      fan.forEach((freq, idx) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.07);

        gain.gain.setValueAtTime(0, now + idx * 0.07);
        gain.gain.linearRampToValueAtTime(0.1, now + idx * 0.07 + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4 + idx * 0.04);

        osc.connect(gain);
        gain.connect(this.sfxGain);

        osc.start(now + idx * 0.07);
        osc.stop(now + 1.5 + idx * 0.04);
      });
    } catch (e) {}
  }

  playDoorUnlockResonance() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;

      // Deep Sub Rumble
      const sub = this.audioContext.createOscillator();
      const subGain = this.audioContext.createGain();
      sub.type = 'sawtooth';
      sub.frequency.setValueAtTime(55, now);
      sub.frequency.exponentialRampToValueAtTime(24, now + 1.8);

      subGain.gain.setValueAtTime(0.16, now);
      subGain.gain.exponentialRampToValueAtTime(0.001, now + 1.8);

      sub.connect(subGain);
      subGain.connect(this.sfxGain);
      sub.start(now);
      sub.stop(now + 1.9);

      // Metallic Hydraulic Release
      const metallic = this.audioContext.createOscillator();
      const filter = this.audioContext.createBiquadFilter();
      const mGain = this.audioContext.createGain();

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1100, now);
      filter.frequency.linearRampToValueAtTime(280, now + 1.4);
      filter.Q.setValueAtTime(5, now);

      metallic.type = 'sawtooth';
      metallic.frequency.setValueAtTime(200, now);

      mGain.gain.setValueAtTime(0.1, now);
      mGain.gain.exponentialRampToValueAtTime(0.001, now + 1.6);

      metallic.connect(filter);
      filter.connect(mGain);
      mGain.connect(this.sfxGain);
      metallic.start(now);
      metallic.stop(now + 1.7);
    } catch (e) {}
  }

  // =========================================================================
  // FINAL ESCAPE SEQUENCE SOUNDS
  // =========================================================================

  playEscapeInit() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(45, now);
      osc.frequency.linearRampToValueAtTime(70, now + 1.8);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.2, now + 0.9);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 2.2);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 2.3);
    } catch (e) {}
  }

  playLockRelease(lockNum = 1) {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;

      const snap = this.audioContext.createOscillator();
      const snapGain = this.audioContext.createGain();
      const baseFreq = 160 + lockNum * 70;

      snap.type = 'triangle';
      snap.frequency.setValueAtTime(baseFreq, now);
      snap.frequency.exponentialRampToValueAtTime(36, now + 0.35);

      snapGain.gain.setValueAtTime(0.18, now);
      snapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

      snap.connect(snapGain);
      snapGain.connect(this.sfxGain);
      snap.start(now);
      snap.stop(now + 0.42);

      const echo = this.audioContext.createOscillator();
      const echoGain = this.audioContext.createGain();
      echo.type = 'sine';
      echo.frequency.setValueAtTime(baseFreq * 2, now);

      echoGain.gain.setValueAtTime(0.06, now);
      echoGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.8);

      echo.connect(echoGain);
      echoGain.connect(this.sfxGain);
      echo.start(now);
      echo.stop(now + 0.85);
    } catch (e) {}
  }

  playDoorPowerUp() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(50, now);
      osc.frequency.exponentialRampToValueAtTime(300, now + 1.6);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(380, now);
      filter.frequency.exponentialRampToValueAtTime(2200, now + 1.6);

      gain.gain.setValueAtTime(0.02, now);
      gain.gain.linearRampToValueAtTime(0.22, now + 1.0);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 2.0);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 2.1);
    } catch (e) {}
  }

  playDoorSlideOpen() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;

      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(75, now);
      osc.frequency.linearRampToValueAtTime(40, now + 2.2);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(280, now);
      filter.frequency.linearRampToValueAtTime(140, now + 2.2);
      filter.Q.setValueAtTime(3, now);

      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 2.5);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 2.6);
    } catch (e) {}
  }

  playEscapeFinalChord() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const freqs = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50];

      freqs.forEach((freq, idx) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        const filter = this.audioContext.createBiquadFilter();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.1);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(2800, now);

        gain.gain.setValueAtTime(0, now + idx * 0.1);
        gain.gain.linearRampToValueAtTime(0.08, now + idx * 0.1 + 0.06);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 3.5 + idx * 0.08);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.sfxGain);

        osc.start(now + idx * 0.1);
        osc.stop(now + 3.7 + idx * 0.08);
      });
    } catch (e) {}
  }

  // =========================================================================
  // SECRET ROOM: SECTOR 02 AUDIO
  // =========================================================================

  playSectorAnomaly() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.linearRampToValueAtTime(100, now + 0.5);
      osc.frequency.linearRampToValueAtTime(400, now + 1.1);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(750, now);
      filter.Q.setValueAtTime(6, now);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.14, now + 0.18);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.3);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 1.4);
    } catch (e) {}
  }

  playObservationRoomAmbience() {
    this.init();
    if (!this.musicEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      const filter = this.audioContext.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(46, now);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(110, now);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.12, now + 1.2);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.ambienceGain);

      osc.start(now);
    } catch (e) {}
  }

  playMonitorGlitch() {
    this.init();
    if (!this.soundEnabled || !this.audioContext) return;

    try {
      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(1600 + Math.random() * 400, now);
      osc.frequency.setValueAtTime(300, now + 0.035);

      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

      osc.connect(gain);
      gain.connect(this.sfxGain);

      osc.start(now);
      osc.stop(now + 0.11);
    } catch (e) {}
  }

  /**
   * Start dark ambient drone
   */
  startAmbientDrone() {
    if (!this.musicEnabled || !this.audioContext || this.ambienceOscillators.length > 0) return;

    try {
      const now = this.audioContext.currentTime;
      const freqs = [55, 110, 164.81];
      
      freqs.forEach((freq, i) => {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        const filter = this.audioContext.createBiquadFilter();

        osc.type = i === 0 ? 'sine' : 'triangle';
        osc.frequency.setValueAtTime(freq, now);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(300 + (i * 80), now);

        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.05 / (i + 1), now + 2.5);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.ambienceGain);

        osc.start(now);
        this.ambienceOscillators.push({ osc, gain });
      });
    } catch (e) {}
  }

  /**
   * Stop ambient drone
   */
  stopAmbientDrone() {
    if (!this.audioContext) return;
    const now = this.audioContext.currentTime;
    this.ambienceOscillators.forEach(({ osc, gain }) => {
      try {
        gain.gain.linearRampToValueAtTime(0.0001, now + 0.3);
        osc.stop(now + 0.35);
      } catch (e) {}
    });
    this.ambienceOscillators = [];
  }
}

// Global Audio Manager instance
window.audioManager = new AudioManager();
