/**
 * Escape The Website - Game Engine & Room Transition Architecture
 * Manages active game session, persistent state, inventory, time tracking, 
 * arcade scores, secret discovery, and room lifecycles.
 */

const STORAGE_KEY = 'escape_the_website_save_v1';

class GameManager {
  constructor() {
    this.initialState = {
      keysCollected: [],
      score: 0,
      arcadeBestScore: 0,
      secretDiscovered: false,
      currentRoom: 'lobby',
      unlockedRooms: ['lobby'],
      gameStarted: false,
      gameCompleted: false,
      gameStartTime: null,
      completionTime: null,
      finalTime: null,
      timestamp: null
    };

    // Working state
    this.state = { ...this.initialState };
    this.listeners = new Set();

    // Declarative Room Definitions
    this.rooms = {
      lobby: {
        id: 'lobby',
        number: 'ROOM 01',
        name: 'THE LOBBY',
        subtitle: 'Sub-Level Mainframe Terminal',
        description: 'An abandoned digital chamber humming with dormant power conduits. Multiple access ports lie dormant.',
        locked: false,
        ambientColor: '#00f0ff'
      },
      sector02: {
        id: 'sector02',
        number: 'ROOM 02',
        name: 'THE OBSERVATION CHAMBER',
        subtitle: 'Sector 02 Surveillance Overlook',
        description: 'A cold, abandoned surveillance overlook staring through one-way glass back into the Lobby.',
        locked: false,
        ambientColor: '#a855f7'
      }
    };
  }

  /**
   * Initializes the game state, loads from storage, or creates initial state
   */
  init() {
    const hasSave = this.loadState();
    if (!hasSave) {
      this.state = { ...this.initialState };
    }

    // Sync puzzle states from loaded keys
    if (window.puzzleManager) {
      if (this.state.keysCollected.includes('key_01')) {
        window.puzzleManager.setSolved('key_01', true);
      }
      if (this.state.keysCollected.includes('key_02')) {
        window.puzzleManager.setSolved('key_02', true);
      }
      if (this.state.keysCollected.includes('key_03')) {
        window.puzzleManager.setSolved('key_03', true);
      }
      if (this.state.arcadeBestScore) {
        window.puzzleManager.setArcadeBestScore(this.state.arcadeBestScore);
      }
    }

    return this.state;
  }

  /**
   * Register a state change listener
   * @param {Function} callback 
   */
  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify subscribers of state mutations
   * @param {string} eventType 
   * @param {any} payload 
   */
  notify(eventType, payload) {
    this.listeners.forEach(callback => {
      try {
        callback(eventType, payload, this.getState());
      } catch (e) {
        console.error('[GameManager] Error in listener callback:', e);
      }
    });
  }

  /**
   * Start or resume game session
   */
  startGame() {
    this.state.gameStarted = true;
    if (!this.state.gameStartTime) {
      this.state.gameStartTime = Date.now();
    }
    if (!this.state.timestamp) {
      this.state.timestamp = Date.now();
    }
    this.saveState();
    this.notify('GAME_STARTED', this.state);
  }

  /**
   * Complete game session on final escape
   */
  completeGame() {
    if (!this.state.gameCompleted) {
      this.state.gameCompleted = true;
      this.state.completionTime = Date.now();

      const start = this.state.gameStartTime || (this.state.completionTime - 120000);
      this.state.finalTime = this.formatElapsedTime(start, this.state.completionTime);

      this.saveState();
      this.notify('GAME_COMPLETED', this.state);
    }
    return this.state;
  }

  /**
   * Mark secret room as discovered (persists across resets)
   */
  discoverSecret() {
    this.state.secretDiscovered = true;
    if (!this.state.unlockedRooms.includes('sector02')) {
      this.state.unlockedRooms.push('sector02');
    }
    this.saveState();
    this.notify('SECRET_DISCOVERED', { secretDiscovered: true });
  }

  /**
   * Format milliseconds into MM:SS or HH:MM:SS
   */
  formatElapsedTime(startTime, endTime) {
    const elapsedMs = Math.max(0, endTime - startTime);
    const totalSeconds = Math.floor(elapsedMs / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const pad = (n) => n.toString().padStart(2, '0');

    if (hours > 0) {
      return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${pad(minutes)}:${pad(seconds)}`;
  }

  /**
   * Get formatted current run duration
   */
  getCurrentRunTime() {
    if (this.state.finalTime) return this.state.finalTime;
    if (!this.state.gameStartTime) return '00:00';
    return this.formatElapsedTime(this.state.gameStartTime, Date.now());
  }

  /**
   * Room Transition Engine
   * @param {string} roomId 
   * @returns {boolean}
   */
  enterRoom(roomId) {
    if (!this.rooms[roomId]) return false;

    const previousRoom = this.state.currentRoom;
    this.state.currentRoom = roomId;
    this.saveState();

    this.notify('ROOM_CHANGED', {
      from: previousRoom,
      to: roomId,
      roomData: this.rooms[roomId]
    });
    return true;
  }

  /**
   * Unlock a newly discovered room
   * @param {string} roomId 
   */
  unlockRoom(roomId) {
    if (!this.rooms[roomId]) return false;

    if (!this.state.unlockedRooms.includes(roomId)) {
      this.state.unlockedRooms.push(roomId);
      this.saveState();
      this.notify('ROOM_UNLOCKED', { roomId });
      return true;
    }
    return false;
  }

  /**
   * Award a collected key (guards against duplicate points)
   * @param {string} keyId 
   */
  collectKey(keyId) {
    if (!this.state.keysCollected.includes(keyId)) {
      this.state.keysCollected.push(keyId);
      this.addScore(300);
      
      if (window.puzzleManager) {
        window.puzzleManager.setSolved(keyId, true);
      }

      this.saveState();
      this.notify('KEY_COLLECTED', { keyId, count: this.state.keysCollected.length });

      // Check if all 3 keys are collected
      if (this.state.keysCollected.length === 3) {
        this.notify('ALL_KEYS_COLLECTED', this.state);
      }

      return true;
    }
    return false;
  }

  /**
   * Update arcade high score
   * @param {number} score 
   */
  recordArcadeBestScore(score) {
    if (score > (this.state.arcadeBestScore || 0)) {
      this.state.arcadeBestScore = score;
      this.saveState();
      this.notify('ARCADE_BEST_UPDATED', { bestScore: score });
      return true;
    }
    return false;
  }

  /**
   * Add score points
   * @param {number} points 
   */
  addScore(points) {
    this.state.score += points;
    this.saveState();
    this.notify('SCORE_UPDATED', { score: this.state.score });
  }

  /**
   * Save game state to localStorage
   */
  saveState() {
    try {
      if (typeof localStorage === 'undefined') return false;
      const serialized = JSON.stringify(this.state);
      localStorage.setItem(STORAGE_KEY, serialized);
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Load game state from localStorage
   */
  loadState() {
    try {
      if (typeof localStorage === 'undefined') return false;
      const data = localStorage.getItem(STORAGE_KEY);
      if (data) {
        const parsed = JSON.parse(data);
        this.state = {
          ...this.initialState,
          ...parsed,
          keysCollected: Array.isArray(parsed.keysCollected) ? [...parsed.keysCollected] : [],
          unlockedRooms: Array.isArray(parsed.unlockedRooms) ? [...parsed.unlockedRooms] : ['lobby']
        };
        return true;
      }
    } catch (e) {
      this.state = { ...this.initialState };
    }
    return false;
  }

  /**
   * Reset game state and clear localStorage while preserving meta-progression
   */
  resetState() {
    try {
      const best = this.state.arcadeBestScore || 0;
      const secret = Boolean(this.state.secretDiscovered);

      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }

      this.state = {
        ...this.initialState,
        keysCollected: [],
        score: 0,
        unlockedRooms: secret ? ['lobby', 'sector02'] : ['lobby'],
        arcadeBestScore: best,
        secretDiscovered: secret,
        currentRoom: 'lobby',
        gameStarted: false,
        gameCompleted: false,
        gameStartTime: null,
        completionTime: null,
        finalTime: null,
        timestamp: null
      };

      if (window.puzzleManager) {
        window.puzzleManager.initPuzzles();
      }

      this.saveState();
      this.notify('STATE_RESET', this.state);
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Get active state clone
   */
  getState() {
    return { 
      ...this.state, 
      keysCollected: [...this.state.keysCollected], 
      unlockedRooms: [...this.state.unlockedRooms] 
    };
  }

  /**
   * Check if all 3 keys are recovered
   */
  hasAllKeys() {
    return this.state.keysCollected.length >= 3;
  }

  /**
   * Get current room information
   */
  getCurrentRoomInfo() {
    return this.rooms[this.state.currentRoom] || this.rooms.lobby;
  }
}

// Global Game Manager instance
window.gameManager = new GameManager();
