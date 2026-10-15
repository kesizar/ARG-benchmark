/**
 * Escape The Website - Puzzle System
 * Responsible for puzzle state, sequence validation, command processing,
 * arcade mechanics, and secret discovery.
 */

class PuzzleManager {
  constructor() {
    this.puzzles = new Map();
    this.initPuzzles();
  }

  /**
   * Initializes registered puzzles
   */
  init() {
    console.log('[PuzzleManager] Puzzle subsystem online.');
  }

  /**
   * Register default puzzle configurations
   */
  initPuzzles() {
    // KEY 01: The Harmonic Resonator
    this.registerPuzzle('key_01', {
      id: 'key_01',
      name: 'The Harmonic Resonator',
      targetSequence: ['03', '01', '04', '02'],
      secretSequence: ['02', '04', '01', '03'], // Inverted sequence triggers Sector 02
      currentInput: [],
      attempts: 0,
      solved: false,
      nodes: [
        { id: '01', label: 'NODE 01', glyph: 'Φ', freq: '28.4 GHz', phase: 'PHASE II', audioIdx: 1 },
        { id: '02', label: 'NODE 02', glyph: 'Ω', freq: '56.8 GHz', phase: 'PHASE IV', audioIdx: 2 },
        { id: '03', label: 'NODE 03', glyph: 'Ψ', freq: '14.2 GHz', phase: 'PHASE I', audioIdx: 3 },
        { id: '04', label: 'NODE 04', glyph: 'Δ', freq: '42.6 GHz', phase: 'PHASE III', audioIdx: 4 }
      ],
      hintThreshold: 3
    });

    // KEY 02: Mainframe Terminal Investigation
    this.registerPuzzle('key_02', {
      id: 'key_02',
      name: 'Mainframe Terminal Investigation',
      validCodes: ['VOID-7F', 'VOID7F', '7F-VOID', '7FVOID'],
      attempts: 0,
      solved: false,
      hintThreshold: 2
    });

    // KEY 03: System Defense Arcade Game
    this.registerPuzzle('key_03', {
      id: 'key_03',
      name: 'System Defense Arcade',
      durationSeconds: 20,
      winThreshold: 1200,
      bestScore: 0,
      solved: false,
      session: {
        score: 0,
        combo: 1,
        maxCombo: 1,
        targetsDestroyed: 0,
        targetsMissed: 0,
        active: false
      },
      targetTypes: {
        standard: {
          id: 'standard',
          label: 'STANDARD THREAT',
          baseScore: 100,
          lifetime: 2200,
          telegraphTime: 250,
          size: 60,
          weight: 0.60
        },
        fast: {
          id: 'fast',
          label: 'HIGH-VELOCITY INTERCEPT',
          baseScore: 175,
          lifetime: 1400,
          telegraphTime: 200,
          size: 48,
          weight: 0.25
        },
        bonus: {
          id: 'bonus',
          label: 'QUANTUM CORE',
          baseScore: 300,
          lifetime: 1800,
          telegraphTime: 250,
          size: 66,
          weight: 0.15
        }
      }
    });
  }

  /**
   * Register a new puzzle configuration
   * @param {string} puzzleId 
   * @param {Object} config 
   */
  registerPuzzle(puzzleId, config) {
    this.puzzles.set(puzzleId, {
      id: puzzleId,
      solved: false,
      attempts: 0,
      currentInput: [],
      ...config
    });
  }

  // =========================================================================
  // KEY 01: HARMONIC RESONATOR METHODS
  // =========================================================================

  inputResonatorNode(nodeId) {
    const puzzle = this.puzzles.get('key_01');
    if (!puzzle) return { status: 'error', reason: 'PUZZLE_NOT_FOUND' };

    const expectedNext = puzzle.targetSequence[puzzle.currentInput.length];
    const expectedSecretNext = puzzle.secretSequence ? puzzle.secretSequence[puzzle.currentInput.length] : null;

    // Check normal sequence
    if (nodeId === expectedNext && !puzzle.solved) {
      puzzle.currentInput.push(nodeId);

      if (puzzle.currentInput.length === puzzle.targetSequence.length) {
        puzzle.solved = true;
        return {
          status: 'success',
          input: [...puzzle.currentInput],
          isComplete: true,
          keyId: 'key_01'
        };
      }

      return {
        status: 'progress',
        input: [...puzzle.currentInput],
        isComplete: false
      };
    } 
    // Check secret inverted sequence (02 -> 04 -> 01 -> 03)
    else if (expectedSecretNext && nodeId === expectedSecretNext) {
      puzzle.currentInput.push(nodeId);

      if (puzzle.currentInput.length === puzzle.secretSequence.length) {
        puzzle.currentInput = [];
        return {
          status: 'secret_trigger',
          sector: 'sector_02',
          text: '// ANOMALY DETECTED: INVERTED RESONANCE HARMONIC ALIGNED TO SECTOR 02'
        };
      }

      return {
        status: 'progress',
        input: [...puzzle.currentInput],
        isComplete: false
      };
    } 
    else {
      puzzle.attempts += 1;
      puzzle.currentInput = [];
      const showHint = puzzle.attempts >= puzzle.hintThreshold;

      return {
        status: 'desync',
        reason: 'RESONANCE_DESYNC',
        attempts: puzzle.attempts,
        showHint: showHint,
        hintText: 'TELEMETRY HINT: Align nodes by ascending harmonic frequency (14.2G → 28.4G → 42.6G → 56.8G).'
      };
    }
  }

  // =========================================================================
  // KEY 02: MAINFRAME TERMINAL METHODS
  // =========================================================================

  executeTerminalCommand(rawInput) {
    const puzzle = this.puzzles.get('key_02');
    if (!puzzle) return { status: 'error', text: 'TERMINAL SUBSYSTEM ERROR' };

    const trimmed = (rawInput || '').trim();
    if (!trimmed) {
      return { status: 'empty' };
    }

    const parts = trimmed.split(/\s+/);
    const cmd = parts[0].toUpperCase();
    const arg = parts.slice(1).join(' ').trim().toUpperCase();

    // Secret Room Trigger Commands in Mainframe Terminal
    if (cmd === 'SECTOR' && (arg === '02' || arg === '2' || arg === 'SECTOR 02')) {
      return {
        status: 'secret_trigger',
        sector: 'sector_02',
        text: 'OVERRIDE CODE ACCEPTED.\nACCESS DETECTED: SECTOR 02 // OBSERVATION CHAMBER\nREDIRECTING...'
      };
    }

    if (cmd === 'SECTOR-02' || cmd === 'SECTOR02' || cmd === 'OBSERVE') {
      return {
        status: 'secret_trigger',
        sector: 'sector_02',
        text: 'OVERRIDE CODE ACCEPTED.\nACCESS DETECTED: SECTOR 02 // OBSERVATION CHAMBER\nREDIRECTING...'
      };
    }

    if (cmd === 'TRACE') {
      return {
        status: 'info',
        text: `ROUTING TRACE REPORT // NET-09\n--------------------------------------------------\n> LOCAL NODE: 0x7F [THE LOBBY]\n> MIRROR NODE: SECTOR 02 [OBSERVATION]\n> CLUE: Inverting harmonic resonator frequencies (Phase IV -> I) bypasses access control.`
      };
    }

    if (puzzle.solved) {
      if (cmd === 'CLEAR') return { status: 'clear' };
      if (cmd === 'HELP') {
        return {
          status: 'info',
          text: `AVAILABLE COMMANDS:\n  STATUS       - Inspect central mainframe & security protocol\n  LOGS         - Display archived security incident records\n  SCAN         - Execute sensor diagnostic sweep\n  TRACE        - Inspect dormant sub-sector routes\n  CLEAR        - Clear terminal screen buffer`
        };
      }
      return {
        status: 'info',
        text: `MAINFRAME STATUS: COMPLETE\nSECURITY PROTOCOL: DISABLED\nKEY 02: RECOVERED\nACCESS LEVEL: ADMINISTRATOR\n[DORMANT LINK]: Type 'TRACE' to scan background sub-sectors.`
      };
    }

    switch (cmd) {
      case 'HELP':
        return {
          status: 'info',
          text: `AVAILABLE COMMANDS:\n  STATUS       - Inspect central mainframe & security protocol\n  LOGS         - Display archived security incident records\n  SCAN         - Execute sensor diagnostic sweep\n  TRACE        - Trace dormant background sub-sectors\n  AUTH <CODE>  - Submit authentication cipher (e.g. AUTH VOID-7F)\n  CLEAR        - Clear terminal screen buffer`
        };

      case 'STATUS':
        return {
          status: 'info',
          text: `MAINFRAME STATUS REPORT // VER 4.09\n--------------------------------------------------\n> SECTOR: 01 [THE LOBBY]\n> HOST: MAINFRAME TERMINAL [PORT 0x7F]\n> PROTOCOL: SECURITY PROTOCOL ACTIVE\n> ACCESS LEVEL: LOCKED\n> FIREWALL INTEGRITY: 100%\n> OVERRIDE STATUS: AWAITING EMERGENCY AUTHENTICATION CIPHER\n> TIP: Cross-reference 'LOGS' and 'SCAN' to derive override cipher.`
        };

      case 'LOGS':
        return {
          status: 'info',
          text: `SECURITY INCIDENT ARCHIVE // INC-094\n--------------------------------------------------\n[03:14:22] INTRUSION DETECTION TRIGGERED AT GATE-0\n[03:14:29] ANOMALOUS HARMONIC RESONANCE LOGGED\n[03:14:35] EMERGENCY CIPHER PROTOCOL GENERATED:\n           FORMAT: [CHAMBER_PREFIX]-[LOCAL_PORT]\n[03:14:41] CHAMBER PREFIX DEFINED: 'VOID'\n[03:14:48] LOCAL PORT: RUN 'SCAN' TO IDENTIFY LOCAL PORT ID\n[03:14:59] GHOST LOG: "Sector 02 echoes when resonator is inverted (IV -> I)."`
        };

      case 'SCAN':
        return {
          status: 'scan',
          text: `SENSOR DIAGNOSTIC SWEEP // SWEEP #882\n--------------------------------------------------\n> HARDWARE PORTS: 1 ACTIVE\n> LOCAL MAINFRAME PORT IDENTIFIER: '7F'\n> CIPHER PATTERN: [CHAMBER_PREFIX]-[PORT]\n> REQUIRED ACTION: EXECUTE 'AUTH VOID-7F'\n> ECHO: Dormant reflection detected in Sector 02.`
        };

      case 'CLEAR':
        return {
          status: 'clear'
        };

      case 'AUTH':
        if (!arg) {
          return {
            status: 'warning',
            text: `USAGE: AUTH <CODE>\nExample: AUTH VOID-7F\nEnter the deduced override code.`
          };
        }

        if (puzzle.validCodes.includes(arg)) {
          puzzle.solved = true;
          return {
            status: 'auth_success',
            keyId: 'key_02',
            text: `AUTHENTICATION VERIFIED\nACCESS GRANTED\nSECURITY PROTOCOL DISABLED\nKEY 02 CIPHER UNLOCKED.`
          };
        } else {
          puzzle.attempts += 1;
          const showHint = puzzle.attempts >= puzzle.hintThreshold;
          return {
            status: 'auth_denied',
            attempts: puzzle.attempts,
            showHint: showHint,
            hintText: 'DIAGNOSTIC NOTE: Combine Chamber Prefix from LOGS ("VOID") with Local Port from SCAN ("7F") -> AUTH VOID-7F',
            text: `ACCESS DENIED\nINVALID AUTHENTICATION SIGNATURE: "${arg}"\nTRY AGAIN (CHECK 'LOGS' AND 'SCAN')`
          };
        }

      default:
        if (puzzle.validCodes.includes(cmd)) {
          puzzle.solved = true;
          return {
            status: 'auth_success',
            keyId: 'key_02',
            text: `AUTHENTICATION VERIFIED\nACCESS GRANTED\nSECURITY PROTOCOL DISABLED\nKEY 02 CIPHER UNLOCKED.`
          };
        }

        return {
          status: 'unknown',
          text: `COMMAND NOT RECOGNIZED: "${cmd}"\nType HELP for available commands.`
        };
    }
  }

  // =========================================================================
  // SECRET ROOM: SECTOR 02 OBSERVATION TERMINAL
  // =========================================================================

  executeObservationTerminalCommand(rawInput) {
    const trimmed = (rawInput || '').trim();
    if (!trimmed) return { status: 'empty' };

    const cmd = trimmed.toUpperCase();

    switch (cmd) {
      case 'HELP':
        return {
          status: 'info',
          text: `OBSERVATION SUBSYSTEM COMMANDS:\n  TRACE   - Analyze client connection provenance\n  WATCH   - Query active surveillance subject\n  ORIGIN  - Inspect instance root lifecycle\n  EXIT    - Initialize system disconnect protocol`
        };

      case 'TRACE':
        return {
          status: 'info',
          text: `CLIENT CONNECTION TRACE // HOOK 0x00\n--------------------------------------------------\n> CONNECTION: ACTIVE\n> LOCATION: RECURSION MATRIX // INSTANCE #01\n> STATUS: SURVEILLANCE LOCKED ON SUBJECT.`
        };

      case 'WATCH':
        return {
          status: 'info',
          text: `SURVEILLANCE TELEMETRY // SECTOR 02\n--------------------------------------------------\n> SUBJECT: ACTIVE USER\n> FEED: ROOM 01 [THE LOBBY] MIRROR ACTIVE\n> NOTE: "The door was never opened on this side."`
        };

      case 'ORIGIN':
        return {
          status: 'info',
          text: `HOST LIFECYCLE QUERY\n--------------------------------------------------\n> ARCHITECTURE: STATIC ENVIRONMENT\n> REALITY LAYER: BROWSER DOM\n> YOU NEVER LEFT THE WEBSITE.`
        };

      case 'EXIT':
        return {
          status: 'reveal_trigger',
          text: `INITIALIZING DISCONNECT PROTOCOL...\n...\nCONNECTION STATUS: ACTIVE\nEXIT STATUS: SIMULATED`
        };

      default:
        return {
          status: 'unknown',
          text: `UNKNOWN INSTRUCTION: "${cmd}"\nAvailable commands: TRACE, WATCH, ORIGIN, EXIT`
        };
    }
  }

  // =========================================================================
  // KEY 03: SYSTEM DEFENSE ARCADE METHODS
  // =========================================================================

  startArcadeSession() {
    const puzzle = this.puzzles.get('key_03');
    if (!puzzle) return null;

    puzzle.session = {
      score: 0,
      combo: 1,
      maxCombo: 1,
      targetsDestroyed: 0,
      targetsMissed: 0,
      active: true,
      startTime: Date.now()
    };

    return { ...puzzle.session };
  }

  recordArcadeHit(type = 'standard') {
    const puzzle = this.puzzles.get('key_03');
    if (!puzzle || !puzzle.session.active) return null;

    const targetDef = puzzle.targetTypes[type] || puzzle.targetTypes.standard;
    const currentCombo = puzzle.session.combo;
    const earnedScore = targetDef.baseScore * currentCombo;

    puzzle.session.score += earnedScore;
    puzzle.session.targetsDestroyed += 1;

    puzzle.session.combo = Math.min(puzzle.session.combo + 1, 5);
    puzzle.session.maxCombo = Math.max(puzzle.session.maxCombo, puzzle.session.combo);

    return {
      earnedScore,
      totalScore: puzzle.session.score,
      combo: puzzle.session.combo,
      prevCombo: currentCombo,
      targetsDestroyed: puzzle.session.targetsDestroyed,
      type: type,
      isBonus: type === 'bonus'
    };
  }

  recordArcadeMiss() {
    const puzzle = this.puzzles.get('key_03');
    if (!puzzle || !puzzle.session.active) return null;

    puzzle.session.combo = 1;
    puzzle.session.targetsMissed += 1;

    return {
      combo: 1,
      targetsMissed: puzzle.session.targetsMissed
    };
  }

  finishArcadeSession() {
    const puzzle = this.puzzles.get('key_03');
    if (!puzzle) return null;

    puzzle.session.active = false;
    const finalScore = puzzle.session.score;
    const passed = finalScore >= puzzle.winThreshold;
    const isFirstClear = passed && !puzzle.solved;

    if (passed) {
      puzzle.solved = true;
    }

    const isNewBest = finalScore > puzzle.bestScore;
    if (isNewBest) {
      puzzle.bestScore = finalScore;
    }

    return {
      finalScore,
      targetsDestroyed: puzzle.session.targetsDestroyed,
      maxCombo: puzzle.session.maxCombo,
      winThreshold: puzzle.winThreshold,
      passed,
      isNewBest,
      bestScore: puzzle.bestScore,
      isFirstClear,
      keyId: 'key_03'
    };
  }

  setArcadeBestScore(score) {
    const puzzle = this.puzzles.get('key_03');
    if (puzzle && score > puzzle.bestScore) {
      puzzle.bestScore = score;
    }
  }

  getRandomTargetType() {
    const roll = Math.random();
    if (roll < 0.60) return 'standard';
    if (roll < 0.85) return 'fast';
    return 'bonus';
  }

  // =========================================================================
  // GENERAL HELPERS
  // =========================================================================

  resetPuzzleInput(puzzleId) {
    const puzzle = this.puzzles.get(puzzleId);
    if (puzzle) {
      puzzle.currentInput = [];
    }
  }

  isSolved(puzzleId) {
    return this.puzzles.get(puzzleId)?.solved || false;
  }

  setSolved(puzzleId, solved = true) {
    const puzzle = this.puzzles.get(puzzleId);
    if (puzzle) {
      puzzle.solved = solved;
    }
  }

  getPuzzle(puzzleId) {
    return this.puzzles.get(puzzleId);
  }
}

// Global Puzzle Manager instance
window.puzzleManager = new PuzzleManager();
