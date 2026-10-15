/**
 * Escape The Website - Main Game Controller & Orchestrator
 * High-performance, memory-safe controller handling the full gameplay loop,
 * interactive puzzles, arcade reaction game, multi-phase final escape,
 * hidden Sector 02 Observation Chamber, 1080x1350 canvas share card generator,
 * and failure-proof Google Analytics 4 event tracking.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Subsystems
  const gameState = window.gameManager ? window.gameManager.init() : null;
  if (window.puzzleManager) window.puzzleManager.init();

  // 2. DOM Elements Cache
  const dom = {
    introScreen: document.getElementById('intro-screen'),
    introEyebrow: document.getElementById('intro-eyebrow'),
    introTitle: document.getElementById('intro-title'),
    introSubtitle: document.getElementById('intro-subtitle'),
    introCta: document.getElementById('intro-cta'),
    btnEnter: document.getElementById('btn-enter'),
    gameWorld: document.getElementById('game-world'),
    canvas: document.getElementById('ambient-canvas'),
    cursorDot: document.getElementById('cursor-dot'),
    cursorRing: document.getElementById('cursor-ring'),
    // HUD
    mainGameHud: document.getElementById('main-game-hud'),
    hudRoomBadge: document.getElementById('hud-room-badge'),
    hudRoomName: document.getElementById('hud-room-name'),
    hudKeysCounter: document.getElementById('hud-keys-counter'),
    hudAllKeysBanner: document.getElementById('hud-all-keys-banner'),
    keySlots: [
      document.getElementById('key-slot-1'),
      document.getElementById('key-slot-2'),
      document.getElementById('key-slot-3')
    ],
    btnToggleAudio: document.getElementById('btn-toggle-audio'),
    audioStatusLabel: document.getElementById('audio-status-label'),
    // Parallax Layers & Stages
    layerBg: document.getElementById('layer-bg'),
    layerMg: document.getElementById('layer-mg'),
    stageLobby: document.getElementById('stage-lobby'),
    lobbyGrid: document.getElementById('lobby-grid'),
    stageSector02: document.getElementById('stage-sector02'),
    btnLeaveSector02: document.getElementById('btn-leave-sector02'),
    // Interactive Nodes in Lobby
    nodeDoor: document.getElementById('node-door'),
    doorNodeTitle: document.getElementById('door-node-title'),
    doorStatusIndicator: document.getElementById('door-status-indicator'),
    doorPortalVisual: document.getElementById('door-portal-visual'),
    doorFrameOuter: document.getElementById('door-frame-outer'),
    doorPanelLeft: document.getElementById('door-panel-left'),
    doorPanelRight: document.getElementById('door-panel-right'),
    doorRadiantAperture: document.getElementById('door-radiant-aperture'),
    doorLockRing: document.getElementById('door-lock-ring'),
    doorLockCore: document.getElementById('door-lock-core'),
    doorLockIcon: document.getElementById('door-lock-icon'),
    doorAccessLabel: document.getElementById('door-access-label'),
    doorAccessSub: document.getElementById('door-access-sub'),
    lockClamp1: document.getElementById('lock-clamp-1'),
    lockClamp2: document.getElementById('lock-clamp-2'),
    lockClamp3: document.getElementById('lock-clamp-3'),
    // Nodes 2, 3, 4
    nodeTerminal: document.getElementById('node-terminal'),
    terminalObjIndicator: document.getElementById('terminal-obj-indicator'),
    terminalPreviewStatus: document.getElementById('terminal-preview-status'),
    nodeStrangeObject: document.getElementById('node-strange-object'),
    resonatorObjIndicator: document.getElementById('resonator-obj-indicator'),
    resonatorObjHint: document.getElementById('resonator-obj-hint'),
    nodeArcade: document.getElementById('node-arcade'),
    arcadeObjIndicator: document.getElementById('arcade-obj-indicator'),
    arcadePreviewMarquee: document.getElementById('arcade-preview-marquee'),
    arcadePreviewFrame: document.getElementById('arcade-preview-frame'),
    arcadePreviewTag: document.getElementById('arcade-preview-tag'),
    arcadePreviewIcon: document.getElementById('arcade-preview-icon'),
    // Sector 02 Components
    obsWindowCard: document.getElementById('obs-window-card'),
    obsMonitorCard: document.getElementById('obs-monitor-card'),
    obsTerminalCard: document.getElementById('obs-terminal-card'),
    obsTerminalStream: document.getElementById('obs-terminal-stream'),
    obsInput: document.getElementById('obs-input'),
    obsChips: document.querySelectorAll('.obs-chip'),
    obsRevealStage: document.getElementById('obs-reveal-stage'),
    revealLine1: document.getElementById('reveal-line-1'),
    revealLine2: document.getElementById('reveal-line-2'),
    revealLine3: document.getElementById('reveal-line-3'),
    revealMainTitle: document.getElementById('reveal-main-title'),
    revealSubQuote: document.getElementById('reveal-sub-quote'),
    btnRevealReturnLobby: document.getElementById('btn-reveal-return-lobby'),
    btnRevealPlayAgain: document.getElementById('btn-reveal-play-again'),
    // Key 01 Resonator Modal
    resonatorModal: document.getElementById('resonator-modal'),
    resonatorCard: document.getElementById('resonator-card'),
    resStatusBadge: document.getElementById('res-status-badge'),
    btnResClose: document.getElementById('btn-res-close'),
    resClueText: document.getElementById('res-clue-text'),
    resStreamDisplay: document.getElementById('res-stream-display'),
    resHintBox: document.getElementById('res-hint-box'),
    resNodesGrid: document.getElementById('res-nodes-grid'),
    resNodeCards: document.querySelectorAll('.resonance-node-card'),
    keyExtractStage: document.getElementById('key-extract-stage'),
    btnClaimKey: document.getElementById('btn-claim-key'),
    // Key 02 Terminal Modal
    terminalModal: document.getElementById('terminal-modal'),
    terminalCard: document.getElementById('terminal-card'),
    termLedIndicator: document.getElementById('term-led-indicator'),
    btnTermClose: document.getElementById('btn-term-close'),
    termOutputStream: document.getElementById('term-output-stream'),
    termInput: document.getElementById('term-input'),
    btnTermSend: document.getElementById('btn-term-send'),
    termChips: document.querySelectorAll('.term-chip'),
    termKeyExtractStage: document.getElementById('term-key-extract-stage'),
    btnClaimKey2: document.getElementById('btn-claim-key-2'),
    // Key 03 Arcade Modal
    arcadeModal: document.getElementById('arcade-modal'),
    arcadeCard: document.getElementById('arcade-card'),
    arcadeBestBadge: document.getElementById('arcade-best-badge'),
    btnArcadeClose: document.getElementById('btn-arcade-close'),
    arcadeScoreVal: document.getElementById('arcade-score-val'),
    arcadeTimeVal: document.getElementById('arcade-time-val'),
    arcadeComboVal: document.getElementById('arcade-combo-val'),
    arcadeTargetsVal: document.getElementById('arcade-targets-val'),
    arcadePlayfield: document.getElementById('arcade-playfield'),
    arcadeCountdownOverlay: document.getElementById('arcade-countdown-overlay'),
    countdownNum: document.getElementById('countdown-num'),
    countdownSub: document.getElementById('countdown-sub'),
    arcadeSummaryStage: document.getElementById('arcade-summary-stage'),
    summaryStatusTitle: document.getElementById('summary-status-title'),
    summaryStatusSub: document.getElementById('summary-status-sub'),
    summaryFinalScore: document.getElementById('summary-final-score'),
    summaryTargetsDestroyed: document.getElementById('summary-targets-destroyed'),
    summaryMaxCombo: document.getElementById('summary-max-combo'),
    summaryBestScore: document.getElementById('summary-best-score'),
    btnClaimKey3: document.getElementById('btn-claim-key-3'),
    btnArcadeRetry: document.getElementById('btn-arcade-retry'),
    // Escape Sequence Banner & Transition
    escapeSequenceBanner: document.getElementById('escape-sequence-banner'),
    escapeBannerEyebrow: document.getElementById('escape-banner-eyebrow'),
    escapeBannerTitle: document.getElementById('escape-banner-title'),
    escapeWhiteWash: document.getElementById('escape-white-wash'),
    // Final Escape Results Screen
    escapeResultScreen: document.getElementById('escape-result-screen'),
    statTime: document.getElementById('stat-time'),
    statScore: document.getElementById('stat-score'),
    statKeys: document.getElementById('stat-keys'),
    statArcade: document.getElementById('stat-arcade'),
    btnPlayAgain: document.getElementById('btn-play-again'),
    btnShareScore: document.getElementById('btn-share-score'),
    btnExploreSecret: document.getElementById('btn-explore-secret'),
    escapeToast: document.getElementById('escape-toast'),
    // Standard Inspection Modal
    modalOverlay: document.getElementById('modal-overlay'),
    modalCard: document.getElementById('modal-card'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-content-body'),
    modalDiagLog: document.getElementById('modal-diag-log'),
    btnModalClose: document.getElementById('btn-modal-close'),
    btnModalAction: document.getElementById('btn-modal-action')
  };

  let isTransitioning = false;
  let isModalOpen = false;
  let isResonatorOpen = false;
  let isTerminalOpen = false;
  let isArcadeOpen = false;
  let isNodeProcessing = false;
  let isEscapeSequenceActive = false;
  let inSector02 = false;
  let toastTimer = null;
  let isSharing = false;

  // Terminal Command History
  const cmdHistory = [];
  let historyIndex = -1;

  // Arcade Session Engine
  let arcadeTimerInterval = null;
  let arcadeSpawnerTimeout = null;
  const activeTargets = new Set();
  let arcadeTimeRemaining = 20;
  let arcadeIsPlaying = false;

  // 3. Initialize Audio Label State
  if (window.audioManager && dom.audioStatusLabel) {
    dom.audioStatusLabel.textContent = window.audioManager.soundEnabled ? 'ON' : 'OFF';
  }

  // 4. Initialize Ambient Canvas, Custom Cursor & Parallax
  initAmbientCanvas(dom.canvas);
  initCustomCursor(dom.cursorDot, dom.cursorRing);
  initParallaxEngine(dom.layerBg, dom.layerMg);

  // 5. Save State Check: Completed game vs in-progress vs fresh
  if (gameState && gameState.gameCompleted) {
    if (dom.introScreen) dom.introScreen.style.display = 'none';
    showEscapeResultScreen(false);
  } else if (gameState && gameState.gameStarted) {
    if (dom.introScreen) dom.introScreen.style.display = 'none';
    if (dom.gameWorld) {
      dom.gameWorld.classList.add('active');
      dom.gameWorld.setAttribute('aria-hidden', 'false');
      dom.gameWorld.style.opacity = '1';
    }
    updateHUD();
    updateLobbyVisuals();
  } else {
    playCinematicIntro();
  }

  // 6. Subscribe to Game Engine State Updates & GA4 Event Tracking
  if (window.gameManager) {
    window.gameManager.subscribe((event, data, state) => {
      updateHUD();
      updateLobbyVisuals();

      // Dispatch GA4 events safely
      if (window.trackEvent) {
        if (event === 'KEY_COLLECTED') {
          if (data.keyId === 'key_01') {
            window.trackEvent('key_01_collected');
          } else if (data.keyId === 'key_02') {
            window.trackEvent('key_02_collected');
          } else if (data.keyId === 'key_03') {
            window.trackEvent('key_03_collected');
          }
        } else if (event === 'GAME_COMPLETED') {
          const startTime = data.gameStartTime || Date.now();
          const endTime = data.completionTime || Date.now();
          const timeSec = Math.max(0, Math.floor((endTime - startTime) / 1000));

          window.trackEvent('game_completed', {
            time_seconds: timeSec,
            score: data.score || 0,
            arcade_best_score: data.arcadeBestScore || 0,
            keys_collected: (data.keysCollected || []).length
          });
        } else if (event === 'SECRET_DISCOVERED') {
          window.trackEvent('secret_discovered');
        } else if (event === 'STATE_RESET') {
          if (window.analyticsManager) {
            window.analyticsManager.resetRunEvents();
          }
        }
      }
    });
  }

  // 7. Setup Interaction Event Listeners
  setupEventListeners();

  /**
   * GSAP Cinematic Intro Sequence
   */
  function playCinematicIntro() {
    if (typeof gsap === 'undefined') {
      if (dom.introEyebrow) dom.introEyebrow.style.opacity = '1';
      if (dom.introTitle) dom.introTitle.style.opacity = '1';
      if (dom.introSubtitle) dom.introSubtitle.style.opacity = '1';
      if (dom.introCta) dom.introCta.style.opacity = '1';
      return;
    }

    gsap.set([dom.introEyebrow, dom.introTitle, dom.introSubtitle, dom.introCta], {
      opacity: 0,
      y: 18
    });
    gsap.set(dom.introScreen, { opacity: 1, scale: 1, display: 'flex' });
    gsap.set(dom.gameWorld, { opacity: 0 });

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.to(dom.introEyebrow, {
      opacity: 1,
      y: 0,
      duration: 1.0,
      delay: 0.2
    })
    .to(dom.introTitle, {
      opacity: 1,
      y: 0,
      duration: 1.4,
      ease: 'power4.out'
    }, '-=0.4')
    .to(dom.introSubtitle, {
      opacity: 1,
      y: 0,
      duration: 1.2,
      ease: 'power2.out'
    }, '-=0.7')
    .to(dom.introCta, {
      opacity: 1,
      y: 0,
      duration: 1.0,
      ease: 'back.out(1.3)'
    }, '-=0.4');
  }

  /**
   * Transition into the Game World (Fires GA4 game_start)
   */
  function transitionToGameWorld() {
    if (isTransitioning) return;
    isTransitioning = true;

    // Fire GA4 game_start event once per gameplay run
    if (window.analyticsManager) {
      window.analyticsManager.trackUniqueEvent('run_game_start', 'game_start');
    } else if (window.trackEvent) {
      window.trackEvent('game_start');
    }

    if (window.audioManager) {
      window.audioManager.playEnterSound();
    }

    if (window.gameManager) {
      window.gameManager.startGame();
      updateHUD();
      updateLobbyVisuals();
    }

    if (typeof gsap !== 'undefined') {
      const tl = gsap.timeline({
        onComplete: () => {
          dom.introScreen.style.display = 'none';
          dom.gameWorld.classList.add('active');
          dom.gameWorld.setAttribute('aria-hidden', 'false');
          isTransitioning = false;
        }
      });

      tl.to(dom.introTitle, {
        scale: 1.12,
        opacity: 0,
        filter: 'blur(8px)',
        duration: 0.8,
        ease: 'power3.in'
      }, 0)
      .to(dom.introSubtitle, {
        opacity: 0,
        y: -12,
        duration: 0.5
      }, 0.1)
      .to(dom.introCta, {
        scale: 0.92,
        opacity: 0,
        duration: 0.4
      }, 0.1)
      .to(dom.introScreen, {
        opacity: 0,
        duration: 0.9,
        ease: 'power2.inOut'
      }, 0.25)
      .to(dom.gameWorld, {
        opacity: 1,
        duration: 1.0,
        ease: 'power2.out'
      }, 0.5);
    } else {
      dom.introScreen.style.display = 'none';
      dom.gameWorld.classList.add('active');
      dom.gameWorld.style.opacity = '1';
      isTransitioning = false;
    }
  }

  /**
   * Update HUD indicators
   */
  function updateHUD() {
    if (!window.gameManager) return;
    const state = window.gameManager.getState();
    const roomInfo = inSector02 ? window.gameManager.rooms.sector02 : window.gameManager.getCurrentRoomInfo();

    if (dom.hudRoomBadge) dom.hudRoomBadge.textContent = roomInfo.number;
    if (dom.hudRoomName) dom.hudRoomName.textContent = roomInfo.name;
    if (dom.hudKeysCounter) dom.hudKeysCounter.textContent = `${state.keysCollected.length} / 3`;

    if (dom.keySlots) {
      dom.keySlots.forEach((slot, index) => {
        if (slot) {
          if (index < state.keysCollected.length) {
            slot.classList.add('collected');
          } else {
            slot.classList.remove('collected');
          }
        }
      });
    }

    if (dom.hudAllKeysBanner) {
      if (state.keysCollected.length === 3 && !inSector02) {
        dom.hudAllKeysBanner.classList.remove('d-none');
      } else {
        dom.hudAllKeysBanner.classList.add('d-none');
      }
    }
  }

  /**
   * Update Lobby elements based on puzzle completion
   */
  function updateLobbyVisuals() {
    if (!window.gameManager) return;
    const state = window.gameManager.getState();
    const key1Found = state.keysCollected.includes('key_01');
    const key2Found = state.keysCollected.includes('key_02');
    const key3Found = state.keysCollected.includes('key_03');
    const allKeysFound = state.keysCollected.length >= 3;

    // Resonator (Key 01)
    if (dom.nodeStrangeObject) {
      if (key1Found) {
        dom.nodeStrangeObject.classList.add('solved');
        if (dom.resonatorObjIndicator) dom.resonatorObjIndicator.className = 'node-status-indicator emerald';
        if (dom.resonatorObjHint) {
          dom.resonatorObjHint.textContent = '// RESONANCE CALIBRATED';
          dom.resonatorObjHint.style.color = 'var(--accent-emerald)';
        }
      } else {
        dom.nodeStrangeObject.classList.remove('solved');
        if (dom.resonatorObjIndicator) dom.resonatorObjIndicator.className = 'node-status-indicator amber';
        if (dom.resonatorObjHint) {
          dom.resonatorObjHint.textContent = '// DORMANT FLUX DETECTED';
          dom.resonatorObjHint.style.color = 'var(--text-muted)';
        }
      }
    }

    // Terminal (Key 02)
    if (dom.nodeTerminal) {
      if (key2Found) {
        dom.nodeTerminal.classList.add('solved');
        if (dom.terminalObjIndicator) dom.terminalObjIndicator.className = 'node-status-indicator emerald';
        if (dom.terminalPreviewStatus) {
          dom.terminalPreviewStatus.textContent = '> [✓] PROTOCOL DEACTIVATED';
          dom.terminalPreviewStatus.className = 'terminal-code-line text-success';
        }
      } else {
        dom.nodeTerminal.classList.remove('solved');
        if (dom.terminalObjIndicator) dom.terminalObjIndicator.className = 'node-status-indicator active';
        if (dom.terminalPreviewStatus) {
          dom.terminalPreviewStatus.textContent = '> [!] ACCESS RESTRICTED';
          dom.terminalPreviewStatus.className = 'terminal-code-line text-warning';
        }
      }
    }

    // Arcade (Key 03)
    if (dom.nodeArcade) {
      if (key3Found) {
        dom.nodeArcade.classList.add('solved');
        if (dom.arcadeObjIndicator) dom.arcadeObjIndicator.className = 'node-status-indicator emerald';
        if (dom.arcadePreviewTag) {
          dom.arcadePreviewTag.textContent = 'STATUS: DEFEATED';
          dom.arcadePreviewTag.className = 'arcade-status-tag text-success';
        }
      } else {
        dom.nodeArcade.classList.remove('solved');
        if (dom.arcadeObjIndicator) dom.arcadeObjIndicator.className = 'node-status-indicator amber';
        if (dom.arcadePreviewTag) {
          dom.arcadePreviewTag.textContent = 'STATUS: READY';
          dom.arcadePreviewTag.className = 'arcade-status-tag';
        }
      }
    }

    // Central Blast Door Reaction when all 3 keys are collected
    if (dom.nodeDoor) {
      if (allKeysFound) {
        dom.nodeDoor.classList.add('door-ready');
        if (dom.doorNodeTitle) dom.doorNodeTitle.textContent = 'SECURITY BARRIER // READY';
        if (dom.doorStatusIndicator) dom.doorStatusIndicator.className = 'node-status-indicator emerald';
        if (dom.doorAccessLabel) {
          dom.doorAccessLabel.textContent = 'OVERRIDE ACCESS: READY';
          dom.doorAccessLabel.style.color = 'var(--accent-emerald)';
        }
        if (dom.doorAccessSub) {
          dom.doorAccessSub.textContent = '// ALL 3 CIPHER KEYS ACCEPTED';
          dom.doorAccessSub.style.color = 'var(--accent-cyan)';
        }
        if (dom.doorLockIcon) {
          dom.doorLockIcon.textContent = '🔓';
        }
      } else {
        dom.nodeDoor.classList.remove('door-ready');
        if (dom.doorNodeTitle) dom.doorNodeTitle.textContent = 'SECURITY BARRIER';
        if (dom.doorStatusIndicator) dom.doorStatusIndicator.className = 'node-status-indicator red';
        if (dom.doorAccessLabel) {
          dom.doorAccessLabel.textContent = 'ACCESS LEVEL: UNKNOWN';
          dom.doorAccessLabel.style.color = 'var(--text-secondary)';
        }
        if (dom.doorAccessSub) {
          dom.doorAccessSub.textContent = '// SEALED BY PROTOCOL';
          dom.doorAccessSub.style.color = 'var(--accent-red)';
        }
        if (dom.doorLockIcon) {
          dom.doorLockIcon.textContent = '✕';
        }
      }
    }
  }

  // =========================================================================
  // SECRET ROOM: SECTOR 02 (THE OBSERVATION CHAMBER)
  // =========================================================================

  function enterSector02() {
    inSector02 = true;

    if (isTerminalOpen) closeTerminalModal();
    if (isResonatorOpen) closeResonatorModal();
    if (isArcadeOpen) closeArcadeModal();
    if (isModalOpen) closeModal();

    if (dom.escapeResultScreen) {
      dom.escapeResultScreen.classList.remove('active');
      dom.escapeResultScreen.setAttribute('aria-hidden', 'true');
    }

    if (dom.gameWorld) {
      dom.gameWorld.style.display = 'flex';
      dom.gameWorld.classList.add('active');
      dom.gameWorld.style.opacity = '1';
    }

    if (window.audioManager) {
      window.audioManager.playSectorAnomaly();
      window.audioManager.playObservationRoomAmbience();
    }

    // GSAP Transition into Sector 02
    if (typeof gsap !== 'undefined') {
      gsap.to(dom.stageLobby, {
        opacity: 0,
        scale: 0.96,
        duration: 0.5,
        ease: 'power2.in',
        onComplete: () => {
          dom.stageLobby.style.display = 'none';
          dom.stageSector02.style.display = 'flex';
          dom.stageSector02.classList.add('active');
          dom.stageSector02.setAttribute('aria-hidden', 'false');

          gsap.fromTo(dom.stageSector02,
            { opacity: 0, scale: 1.03 },
            { opacity: 1, scale: 1, duration: 0.7, ease: 'power2.out' }
          );
        }
      });
    } else {
      dom.stageLobby.style.display = 'none';
      dom.stageSector02.style.display = 'flex';
      dom.stageSector02.classList.add('active');
      dom.stageSector02.style.opacity = '1';
    }

    updateHUD();
    showToast('// SECTOR 02 DETECTED • OBSERVATION CHAMBER ONLINE');
  }

  function leaveSector02() {
    inSector02 = false;

    if (window.audioManager) {
      window.audioManager.playModalClose();
      window.audioManager.startAmbientDrone();
    }

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.stageSector02, {
        opacity: 0,
        scale: 0.96,
        duration: 0.4,
        ease: 'power2.in',
        onComplete: () => {
          dom.stageSector02.style.display = 'none';
          dom.stageSector02.classList.remove('active');
          dom.stageSector02.setAttribute('aria-hidden', 'true');
          
          dom.stageLobby.style.display = 'flex';
          gsap.fromTo(dom.stageLobby,
            { opacity: 0, scale: 1.02 },
            { opacity: 1, scale: 1, duration: 0.5, ease: 'power2.out' }
          );
        }
      });
    } else {
      dom.stageSector02.style.display = 'none';
      dom.stageSector02.classList.remove('active');
      dom.stageLobby.style.display = 'flex';
      dom.stageLobby.style.opacity = '1';
    }

    updateHUD();
    updateLobbyVisuals();
  }

  function handleObservationTerminalCommand(cmdText) {
    const input = cmdText !== undefined ? cmdText : (dom.obsInput?.value || '');
    if (!input.trim() || !window.puzzleManager) return;

    if (dom.obsInput) dom.obsInput.value = '';

    if (window.audioManager) {
      window.audioManager.playTerminalCommandExec();
    }

    const log = document.createElement('div');
    log.className = 'text-light fw-bold';
    log.textContent = `> ${input}`;
    dom.obsTerminalStream.appendChild(log);

    const res = window.puzzleManager.executeObservationTerminalCommand(input);

    if (res.status === 'reveal_trigger') {
      const resp = document.createElement('div');
      resp.className = 'text-warning';
      resp.textContent = res.text;
      dom.obsTerminalStream.appendChild(resp);
      dom.obsTerminalStream.scrollTop = dom.obsTerminalStream.scrollHeight;

      setTimeout(() => {
        triggerSecretReveal();
      }, 1000);
    } else {
      const resp = document.createElement('div');
      resp.className = 'text-info';
      resp.textContent = res.text;
      dom.obsTerminalStream.appendChild(resp);
      dom.obsTerminalStream.scrollTop = dom.obsTerminalStream.scrollHeight;
    }
  }

  function triggerSecretReveal() {
    if (window.gameManager) {
      window.gameManager.discoverSecret();
    }

    if (window.audioManager) {
      window.audioManager.playSectorAnomaly();
    }

    dom.obsRevealStage.classList.add('active');
    dom.obsRevealStage.setAttribute('aria-hidden', 'false');

    gsap.set([dom.revealLine1, dom.revealLine2, dom.revealLine3, dom.revealMainTitle, dom.revealSubQuote], {
      opacity: 0,
      y: 12
    });

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.to(dom.obsRevealStage, { opacity: 1, duration: 0.5 })
      .to(dom.revealLine1, { opacity: 1, y: 0, duration: 0.7 }, '+=0.2')
      .to(dom.revealLine2, { opacity: 1, y: 0, duration: 0.7 }, '+=0.4')
      .to(dom.revealLine3, { opacity: 1, y: 0, duration: 0.5 }, '+=0.3')
      .to(dom.revealMainTitle, {
        opacity: 1,
        y: 0,
        duration: 1.2,
        ease: 'back.out(1.2)'
      }, '+=0.5')
      .to(dom.revealSubQuote, { opacity: 1, y: 0, duration: 1.0 }, '+=0.3');
  }

  // =========================================================================
  // FINAL ESCAPE SEQUENCE ORCHESTRATION
  // =========================================================================

  function triggerFinalEscapeSequence() {
    if (isEscapeSequenceActive) return;
    isEscapeSequenceActive = true;

    // 1. Disable all other interactive nodes
    [dom.nodeTerminal, dom.nodeStrangeObject, dom.nodeArcade, dom.nodeDoor].forEach(el => {
      if (el) el.style.pointerEvents = 'none';
    });

    if (window.audioManager) {
      window.audioManager.playEscapeInit();
    }

    const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });

    // PHASE 1 — Recognition & Sequence Banner
    dom.escapeSequenceBanner.style.display = 'flex';
    tl.fromTo(dom.escapeSequenceBanner,
      { opacity: 0, y: -20 },
      { opacity: 1, y: 0, duration: 0.7 }
    )
    .to(dom.escapeBannerTitle, {
      textContent: 'ESCAPE PROTOCOL INITIALIZING...',
      duration: 1.0,
      delay: 0.6
    })

    // PHASE 2 — Ambient Power Shutdown
    .to([dom.layerBg, dom.terminalPreviewStatus, dom.arcadePreviewFrame, dom.mainGameHud], {
      opacity: 0.2,
      duration: 1.2,
      ease: 'power1.inOut'
    }, '-=0.4')

    // PHASE 3 — Sequential Lock Releases (Locks 1, 2, 3)
    .call(() => {
      if (dom.lockClamp1) dom.lockClamp1.classList.add('released');
      if (dom.escapeBannerTitle) dom.escapeBannerTitle.textContent = 'LOCK 01 // RELEASED';
      if (window.audioManager) window.audioManager.playLockRelease(1);
    })
    .to(dom.doorLockRing, { rotate: 60, scale: 1.05, duration: 0.4 }, '+=0.2')

    .call(() => {
      if (dom.lockClamp2) dom.lockClamp2.classList.add('released');
      if (dom.escapeBannerTitle) dom.escapeBannerTitle.textContent = 'LOCK 02 // RELEASED';
      if (window.audioManager) window.audioManager.playLockRelease(2);
    }, null, '+=0.6')
    .to(dom.doorLockRing, { rotate: 140, scale: 1.1, duration: 0.4 })

    .call(() => {
      if (dom.lockClamp3) dom.lockClamp3.classList.add('released');
      if (dom.escapeBannerTitle) dom.escapeBannerTitle.textContent = 'LOCK 03 // RELEASED';
      if (window.audioManager) window.audioManager.playLockRelease(3);
    }, null, '+=0.6')
    .to(dom.doorLockRing, { rotate: 240, scale: 1.2, duration: 0.5 })

    // PHASE 4 — Door Power-Up & Energy Conduits Surge
    .call(() => {
      if (dom.escapeBannerTitle) dom.escapeBannerTitle.textContent = 'SECURITY BARRIER // OVERRIDE ACCEPTED';
      if (dom.doorAccessLabel) dom.doorAccessLabel.textContent = 'OVERRIDE: ACCEPTED';
      if (dom.doorAccessSub) dom.doorAccessSub.textContent = '// DISENGAGING HYDRAULICS';
      if (window.audioManager) window.audioManager.playDoorPowerUp();
    }, null, '+=0.5')
    .to(dom.doorFrameOuter, {
      boxShadow: '0 0 60px rgba(0, 255, 136, 0.8), inset 0 0 40px rgba(0, 240, 255, 0.6)',
      borderColor: '#00ff88',
      duration: 1.0
    })
    .to(dom.nodeDoor, {
      x: () => (Math.random() - 0.5) * 5,
      y: () => (Math.random() - 0.5) * 3,
      repeat: 6,
      yoyo: true,
      duration: 0.08,
      ease: 'none'
    }, '-=0.7')
    .set(dom.nodeDoor, { x: 0, y: 0 })

    // PHASE 5 — Door Opening (Panels Retract Horizontally)
    .call(() => {
      if (dom.doorRadiantAperture) dom.doorRadiantAperture.style.opacity = '1';
      if (dom.doorLockRing) dom.doorLockRing.style.opacity = '0';
      if (window.audioManager) window.audioManager.playDoorSlideOpen();
    }, null, '+=0.3')
    .to(dom.doorPanelLeft, { x: '-105%', duration: 2.0, ease: 'power3.inOut' })
    .to(dom.doorPanelRight, { x: '105%', duration: 2.0, ease: 'power3.inOut' }, '<')
    .to(dom.escapeSequenceBanner, { opacity: 0, duration: 0.7 }, '<')

    // PHASE 6 — Silence
    .call(() => {
      if (window.audioManager) window.audioManager.stopAmbientDrone();
    }, null, '+=0.2')

    // PHASE 7 — Escape Camera Push & White Wash
    .call(() => {
      if (dom.stageLobby && dom.doorFrameOuter) {
        const stageRect = dom.stageLobby.getBoundingClientRect();
        const doorRect = dom.doorFrameOuter.getBoundingClientRect();
        const originX = ((doorRect.left + doorRect.width / 2 - stageRect.left) / stageRect.width) * 100;
        const originY = ((doorRect.top + doorRect.height / 2 - stageRect.top) / stageRect.height) * 100;
        gsap.set(dom.stageLobby, {
          transformOrigin: `${originX.toFixed(2)}% ${originY.toFixed(2)}%`
        });
      }
    })
    .to(dom.stageLobby, {
      scale: 5.0,
      opacity: 0.1,
      duration: 2.4,
      ease: 'power3.in',
      delay: 0.4
    })
    .to(dom.escapeWhiteWash, {
      opacity: 1,
      duration: 1.1,
      ease: 'power2.in'
    }, '-=1.0')
    .call(() => {
      showEscapeResultScreen(true);
    });
  }

  function showEscapeResultScreen(playFinalChord = true) {
    if (!window.gameManager) return;
    const finalState = window.gameManager.completeGame();

    if (dom.gameWorld) dom.gameWorld.style.display = 'none';
    if (dom.escapeSequenceBanner) dom.escapeSequenceBanner.style.display = 'none';

    // Populate Results safely
    if (dom.statTime) {
      dom.statTime.textContent = finalState.finalTime || window.gameManager.getCurrentRunTime() || '02:30';
    }
    if (dom.statScore) {
      dom.statScore.textContent = typeof finalState.score === 'number' ? finalState.score : 900;
    }
    if (dom.statKeys) {
      const keysCount = Array.isArray(finalState.keysCollected) ? finalState.keysCollected.length : 3;
      dom.statKeys.textContent = `${keysCount} / 3`;
    }
    if (dom.statArcade) {
      dom.statArcade.textContent = typeof finalState.arcadeBestScore === 'number' ? finalState.arcadeBestScore : 0;
    }

    // Adapt Secret Button state on result screen
    if (dom.btnExploreSecret) {
      if (finalState.secretDiscovered) {
        dom.btnExploreSecret.textContent = 'SECTOR 02 // REVISIT';
        dom.btnExploreSecret.style.borderColor = 'var(--accent-violet)';
        dom.btnExploreSecret.style.color = 'var(--accent-violet)';
        dom.btnExploreSecret.title = 'Re-enter Observation Chamber';
      } else {
        dom.btnExploreSecret.textContent = 'EXPLORE SECRET';
        dom.btnExploreSecret.style.borderColor = 'var(--border-glass)';
        dom.btnExploreSecret.style.color = 'var(--text-primary)';
        dom.btnExploreSecret.title = 'Investigate hidden Sector';
      }
    }

    dom.escapeResultScreen.classList.add('active');
    dom.escapeResultScreen.setAttribute('aria-hidden', 'false');

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.escapeWhiteWash, { opacity: 0, duration: 1.2, ease: 'power2.out' });
      gsap.fromTo(dom.escapeResultScreen,
        { opacity: 0, scale: 0.96 },
        { opacity: 1, scale: 1, duration: 1.0, ease: 'power3.out' }
      );
    } else {
      dom.escapeWhiteWash.style.opacity = '0';
      dom.escapeResultScreen.style.opacity = '1';
    }

    if (playFinalChord && window.audioManager) {
      window.audioManager.playEscapeFinalChord();
    }
  }

  function handlePlayAgain() {
    isEscapeSequenceActive = false;
    inSector02 = false;

    if (window.gameManager) {
      window.gameManager.resetState();
    }

    // Reset Door DOM state
    if (dom.doorPanelLeft) dom.doorPanelLeft.style.transform = 'none';
    if (dom.doorPanelRight) dom.doorPanelRight.style.transform = 'none';
    if (dom.doorRadiantAperture) dom.doorRadiantAperture.style.opacity = '0';
    if (dom.doorLockRing) {
      dom.doorLockRing.style.opacity = '1';
      dom.doorLockRing.style.transform = 'none';
    }
    if (dom.lockClamp1) dom.lockClamp1.classList.remove('released');
    if (dom.lockClamp2) dom.lockClamp2.classList.remove('released');
    if (dom.lockClamp3) dom.lockClamp3.classList.remove('released');

    // Reset Interactive Nodes Pointer Events
    [dom.nodeTerminal, dom.nodeStrangeObject, dom.nodeArcade, dom.nodeDoor].forEach(el => {
      if (el) el.style.pointerEvents = 'auto';
    });

    // Reset Stage Lobby Scale / Opacity
    if (dom.stageLobby) {
      dom.stageLobby.style.display = 'flex';
      dom.stageLobby.style.transform = 'none';
      dom.stageLobby.style.opacity = '1';
    }
    if (dom.stageSector02) {
      dom.stageSector02.style.display = 'none';
      dom.stageSector02.classList.remove('active');
    }
    if (dom.obsRevealStage) {
      dom.obsRevealStage.classList.remove('active');
      dom.obsRevealStage.style.opacity = '0';
    }
    if (dom.layerBg) dom.layerBg.style.opacity = '1';
    if (dom.mainGameHud) dom.mainGameHud.style.opacity = '1';

    // Hide result screen, show intro
    dom.escapeResultScreen.classList.remove('active');
    dom.escapeResultScreen.setAttribute('aria-hidden', 'true');
    dom.escapeResultScreen.style.opacity = '0';

    if (dom.gameWorld) {
      dom.gameWorld.classList.remove('active');
      dom.gameWorld.setAttribute('aria-hidden', 'true');
      dom.gameWorld.style.display = 'flex';
      dom.gameWorld.style.opacity = '0';
    }

    playCinematicIntro();
  }

  // =========================================================================
  // PREMIUM 1080x1350 SHARE CARD CANVAS GENERATOR & NATIVE SHARE
  // =========================================================================

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
  }

  async function renderShareCardCanvas(state, time, score, keys, arcade) {
    const width = 1080;
    const height = 1350;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    // 1. Deep Space Dark Gradient Background
    const bgGrad = ctx.createRadialGradient(width / 2, height / 2, 80, width / 2, height / 2, width * 0.75);
    bgGrad.addColorStop(0, '#0a1630');
    bgGrad.addColorStop(0.5, '#050c1c');
    bgGrad.addColorStop(1, '#020408');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // 2. Atmospheric Perspective Grid
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.07)';
    ctx.lineWidth = 1;
    for (let x = 60; x < width; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 60; y < height; y += 60) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    ctx.restore();

    // 3. Scanline Texture Overlay
    ctx.save();
    ctx.fillStyle = 'rgba(0, 0, 0, 0.18)';
    for (let y = 0; y < height; y += 6) {
      ctx.fillRect(0, y, width, 3);
    }
    ctx.restore();

    // 4. Subtle Outer Border & Futuristic Corner Accents
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.35)';
    ctx.lineWidth = 2;
    ctx.strokeRect(40, 40, width - 80, height - 80);

    // Corner Brackets
    const bracketSize = 35;
    ctx.strokeStyle = state.secretDiscovered ? '#a855f7' : '#00f0ff';
    ctx.lineWidth = 4;

    // Top-Left
    ctx.beginPath();
    ctx.moveTo(40, 40 + bracketSize);
    ctx.lineTo(40, 40);
    ctx.lineTo(40 + bracketSize, 40);
    ctx.stroke();

    // Top-Right
    ctx.beginPath();
    ctx.moveTo(width - 40 - bracketSize, 40);
    ctx.lineTo(width - 40, 40);
    ctx.lineTo(width - 40, 40 + bracketSize);
    ctx.stroke();

    // Bottom-Left
    ctx.beginPath();
    ctx.moveTo(40, height - 40 - bracketSize);
    ctx.lineTo(40, height - 40);
    ctx.lineTo(40 + bracketSize, height - 40);
    ctx.stroke();

    // Bottom-Right
    ctx.beginPath();
    ctx.moveTo(width - 40 - bracketSize, height - 40);
    ctx.lineTo(width - 40, height - 40);
    ctx.lineTo(width - 40, height - 40 - bracketSize);
    ctx.stroke();
    ctx.restore();

    // 5. Header Branding
    ctx.save();
    ctx.textAlign = 'center';

    // Eyebrow
    ctx.font = '600 22px "JetBrains Mono", monospace';
    ctx.fillStyle = state.secretDiscovered ? '#a855f7' : '#00f0ff';
    ctx.letterSpacing = '6px';
    ctx.fillText('MISSION DEBRIEF // PROTOCOL 0x7F', width / 2, 130);

    // Main Game Title
    ctx.font = '900 58px "Orbitron", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0, 240, 255, 0.4)';
    ctx.shadowBlur = 20;
    ctx.fillText('ESCAPE THE WEBSITE', width / 2, 205);
    ctx.shadowBlur = 0;

    // Divider Line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(140, 250);
    ctx.lineTo(width - 140, 250);
    ctx.stroke();

    // 6. Central Victory Banner
    ctx.font = '900 50px "Orbitron", sans-serif';
    ctx.fillStyle = '#00ff88';
    ctx.shadowColor = 'rgba(0, 255, 136, 0.6)';
    ctx.shadowBlur = 25;
    ctx.fillText('YOU ESCAPED.', width / 2, 340);
    ctx.shadowBlur = 0;

    // Sub Status
    ctx.font = '500 22px "JetBrains Mono", monospace';
    ctx.fillStyle = state.secretDiscovered ? '#c084fc' : '#94a3b8';
    const subStatusText = state.secretDiscovered 
      ? '// ANOMALY DETECTED • SECTOR 02 DISCOVERED'
      : '// SECURITY BARRIER OVERRIDDEN • ACCESS RESTORED';
    ctx.fillText(subStatusText, width / 2, 390);

    ctx.restore();

    // Helper to draw rounded cards
    function drawStatCard(x, y, w, h, label, val, valColor) {
      ctx.save();
      ctx.fillStyle = 'rgba(8, 16, 32, 0.88)';
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
      ctx.lineWidth = 1.5;

      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, 14);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(x, y, w, h);
        ctx.strokeRect(x, y, w, h);
      }

      // Card Header / Label
      ctx.font = '600 20px "JetBrains Mono", monospace';
      ctx.fillStyle = '#94a3b8';
      ctx.textAlign = 'center';
      ctx.fillText(label, x + w / 2, y + 48);

      // Card Value
      ctx.font = '900 46px "Orbitron", sans-serif';
      ctx.fillStyle = valColor;
      ctx.shadowColor = valColor;
      ctx.shadowBlur = 12;
      ctx.fillText(val, x + w / 2, y + 115);
      ctx.restore();
    }

    // 7. 4 Statistics Cards
    const cardW = 410;
    const cardH = 175;
    const startX1 = 110;
    const startX2 = width - 110 - cardW;
    const row1Y = 460;
    const row2Y = 675;

    drawStatCard(startX1, row1Y, cardW, cardH, 'ESCAPE TIME', time, '#00f0ff');
    drawStatCard(startX2, row1Y, cardW, cardH, 'TOTAL SCORE', `${score} PTS`, '#00ff88');
    drawStatCard(startX1, row2Y, cardW, cardH, 'CIPHER KEYS', `◆ ◆ ◆  ${keys}`, '#00ff88');
    drawStatCard(startX2, row2Y, cardW, cardH, 'ARCADE BEST', `${arcade} PTS`, '#ffb800');

    // 8. Sector 02 Secret Banner (if unlocked) or Standard Encryption Stamp
    ctx.save();
    const bannerY = 900;
    const bannerW = width - 220;
    const bannerH = 160;
    const bannerX = 110;

    ctx.fillStyle = state.secretDiscovered ? 'rgba(30, 15, 55, 0.75)' : 'rgba(6, 14, 28, 0.75)';
    ctx.strokeStyle = state.secretDiscovered ? 'rgba(168, 85, 247, 0.5)' : 'rgba(0, 240, 255, 0.2)';
    ctx.lineWidth = 1.5;

    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(bannerX, bannerY, bannerW, bannerH, 12);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillRect(bannerX, bannerY, bannerW, bannerH);
      ctx.strokeRect(bannerX, bannerY, bannerW, bannerH);
    }

    ctx.textAlign = 'center';
    if (state.secretDiscovered) {
      ctx.font = '800 24px "Orbitron", sans-serif';
      ctx.fillStyle = '#a855f7';
      ctx.shadowColor = 'rgba(168, 85, 247, 0.6)';
      ctx.shadowBlur = 15;
      ctx.fillText('SECRET ROOM // SECTOR 02 OVERLOOK DISCOVERED', width / 2, bannerY + 60);
      ctx.shadowBlur = 0;

      ctx.font = '400 20px "JetBrains Mono", monospace';
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText('"The website does not let you leave. It builds another room."', width / 2, bannerY + 105);
    } else {
      ctx.font = '700 22px "Orbitron", sans-serif';
      ctx.fillStyle = '#00f0ff';
      ctx.fillText('SECURITY OVERRIDE COMPLETE // ALL 3 SECTORS SOLVED', width / 2, bannerY + 60);

      ctx.font = '400 20px "JetBrains Mono", monospace';
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('Master cipher validated • Clearance Level: ADMINISTRATOR', width / 2, bannerY + 105);
    }
    ctx.restore();

    // 9. Footer Watermark & Branding
    ctx.save();
    ctx.font = '500 20px "JetBrains Mono", monospace';
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'left';
    ctx.fillText('ESCAPE THE WEBSITE // TERMINAL 0x7F', 110, height - 90);

    ctx.textAlign = 'right';
    ctx.fillStyle = state.secretDiscovered ? '#a855f7' : '#00f0ff';
    ctx.fillText('AUTHENTICATED ACHIEVEMENT', width - 110, height - 90);
    ctx.restore();

    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error('Canvas blob generation failed'));
        }
      }, 'image/png');
    });
  }

  async function handleShareScore() {
    if (isSharing || !window.gameManager) return;
    isSharing = true;

    // Track GA4 share_clicked event
    if (window.trackEvent) {
      window.trackEvent('share_clicked');
    }

    const originalText = dom.btnShareScore ? dom.btnShareScore.textContent : 'SHARE MY SCORE';
    if (dom.btnShareScore) {
      dom.btnShareScore.textContent = 'GENERATING RESULT...';
      dom.btnShareScore.disabled = true;
      dom.btnShareScore.setAttribute('aria-busy', 'true');
    }

    try {
      const state = window.gameManager.getState();
      const time = state.finalTime || window.gameManager.getCurrentRunTime() || '02:30';
      const score = typeof state.score === 'number' ? state.score : 900;
      const arcade = typeof state.arcadeBestScore === 'number' ? state.arcadeBestScore : 0;
      const keys = `${Array.isArray(state.keysCollected) ? state.keysCollected.length : 3} / 3`;

      // Wait for fonts to be ready
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }

      const imageBlob = await renderShareCardCanvas(state, time, score, keys, arcade);
      const fileName = `escape-the-website-result.png`;
      const gameUrl = 'https://muhammedrinshad210.github.io/escape-the-website/';
      const keysCount = Array.isArray(state.keysCollected) ? state.keysCollected.length : 3;
      const shareTitle = 'ESCAPE THE WEBSITE';
      const shareText = `I escaped ESCAPE THE WEBSITE.\n\nTIME: ${time}\nSCORE: ${score}\nKEYS: ${keysCount}/3\n\nCan you escape too?\n${gameUrl}`;

      // 1. Native Web Share with File Support
      if (navigator.share && navigator.canShare && navigator.canShare({ files: [imageFile] })) {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          files: [imageFile]
        });
        if (window.trackEvent) {
          window.trackEvent('share_completed', { share_method: 'native_file' });
        }
        showToast('// RESULT SHARED');
      } else if (navigator.share && navigator.canShare && navigator.canShare({ title: shareTitle, text: shareText })) {
        // 2. Web share text fallback + auto-download image
        downloadBlob(imageBlob, fileName);
        await navigator.share({
          title: shareTitle,
          text: shareText
        });
        if (window.trackEvent) {
          window.trackEvent('share_completed', { share_method: 'native_text' });
        }
        showToast('// RESULT IMAGE DOWNLOADED');
      } else {
        // 3. Desktop / Unsupported browser fallback: Download PNG & Copy Text
        downloadBlob(imageBlob, fileName);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(shareText);
          showToast('// RESULT IMAGE SAVED • TEXT COPIED');
        } else {
          showToast('// RESULT IMAGE READY');
        }
        if (window.trackEvent) {
          window.trackEvent('share_completed', { share_method: 'download' });
        }
      }
    } catch (err) {
      if (err && err.name !== 'AbortError') {
        showToast('// RESULT IMAGE READY');
      }
    } finally {
      isSharing = false;
      if (dom.btnShareScore) {
        dom.btnShareScore.textContent = originalText;
        dom.btnShareScore.disabled = false;
        dom.btnShareScore.removeAttribute('aria-busy');
      }
    }
  }

  function showToast(msg) {
    if (!dom.escapeToast) return;
    const safeText = typeof msg === 'string' && msg.trim() ? msg : '// ACCESS RESTRICTED • SECTOR 02 LOCKED';
    dom.escapeToast.textContent = safeText;
    dom.escapeToast.classList.add('active');

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      dom.escapeToast.classList.remove('active');
    }, 2500);
  }

  // =========================================================================
  // KEY 03: ARCADE SYSTEM DEFENSE REACTION GAME
  // =========================================================================

  function openArcadeModal() {
    if (!dom.arcadeModal || !dom.arcadeCard || isEscapeSequenceActive || inSector02) return;
    isArcadeOpen = true;

    stopArcadeGame();
    clearArcadePlayfield();

    const state = window.gameManager?.getState();
    const bestScore = state?.arcadeBestScore || 0;
    if (dom.arcadeBestBadge) dom.arcadeBestBadge.textContent = `BEST: ${bestScore}`;

    if (dom.arcadeScoreVal) dom.arcadeScoreVal.textContent = '0000';
    if (dom.arcadeTimeVal) {
      dom.arcadeTimeVal.textContent = '20s';
      dom.arcadeTimeVal.className = 'arcade-stat-val';
    }
    if (dom.arcadeComboVal) dom.arcadeComboVal.textContent = 'x1';
    if (dom.arcadeTargetsVal) dom.arcadeTargetsVal.textContent = '0';

    dom.arcadeSummaryStage.classList.remove('active');
    dom.arcadeSummaryStage.style.opacity = '0';

    if (window.audioManager) {
      window.audioManager.playModalOpen();
    }

    dom.arcadeModal.classList.add('active');
    dom.arcadeModal.setAttribute('aria-hidden', 'false');

    if (typeof gsap !== 'undefined') {
      gsap.fromTo(dom.arcadeModal, { opacity: 0 }, { opacity: 1, duration: 0.25 });
      gsap.fromTo(dom.arcadeCard, 
        { opacity: 0, scale: 0.94, y: 15 }, 
        { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'power3.out' }
      );
    } else {
      dom.arcadeModal.style.opacity = '1';
    }

    startArcadeCountdown();
  }

  function closeArcadeModal() {
    if (!dom.arcadeModal || !isArcadeOpen) return;
    isArcadeOpen = false;

    stopArcadeGame();
    clearArcadePlayfield();

    if (window.audioManager) {
      window.audioManager.playModalClose();
    }

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.arcadeCard, {
        opacity: 0,
        scale: 0.94,
        y: 10,
        duration: 0.2,
        ease: 'power2.in'
      });
      gsap.to(dom.arcadeModal, {
        opacity: 0,
        duration: 0.25,
        onComplete: () => {
          dom.arcadeModal.classList.remove('active');
          dom.arcadeModal.setAttribute('aria-hidden', 'true');
        }
      });
    } else {
      dom.arcadeModal.classList.remove('active');
      dom.arcadeModal.setAttribute('aria-hidden', 'true');
    }
  }

  function startArcadeCountdown() {
    if (!dom.arcadeCountdownOverlay) return;

    dom.arcadeCountdownOverlay.style.display = 'flex';
    dom.arcadeCountdownOverlay.style.opacity = '1';

    let count = 3;
    dom.countdownNum.textContent = count;
    dom.countdownSub.textContent = 'CALIBRATING TARGETING GRID...';

    if (window.audioManager) {
      window.audioManager.playArcadeCountdown(count);
    }

    const countInterval = setInterval(() => {
      count--;
      if (count > 0) {
        dom.countdownNum.textContent = count;
        if (window.audioManager) window.audioManager.playArcadeCountdown(count);
      } else if (count === 0) {
        dom.countdownNum.textContent = 'SYSTEM ACTIVE';
        dom.countdownSub.textContent = 'ENGAGE TARGETS IMMEDIATELY!';
        if (window.audioManager) window.audioManager.playArcadeStart();
      } else {
        clearInterval(countInterval);
        if (typeof gsap !== 'undefined') {
          gsap.to(dom.arcadeCountdownOverlay, {
            opacity: 0,
            duration: 0.25,
            onComplete: () => {
              dom.arcadeCountdownOverlay.style.display = 'none';
              startArcadeGame();
            }
          });
        } else {
          dom.arcadeCountdownOverlay.style.display = 'none';
          startArcadeGame();
        }
      }
    }, 800);
  }

  function startArcadeGame() {
    if (!window.puzzleManager) return;
    arcadeIsPlaying = true;
    arcadeTimeRemaining = 20;

    window.puzzleManager.startArcadeSession();

    const startTime = performance.now();
    const durationMs = 20000;

    if (arcadeTimerInterval) clearInterval(arcadeTimerInterval);
    arcadeTimerInterval = setInterval(() => {
      const elapsed = performance.now() - startTime;
      const remainingMs = Math.max(0, durationMs - elapsed);
      arcadeTimeRemaining = Math.ceil(remainingMs / 1000);

      if (dom.arcadeTimeVal) {
        dom.arcadeTimeVal.textContent = `${arcadeTimeRemaining}s`;

        if (arcadeTimeRemaining <= 3) {
          dom.arcadeTimeVal.className = 'arcade-stat-val urgent';
          if (window.audioManager) window.audioManager.playTimerWarning();
        } else if (arcadeTimeRemaining <= 10) {
          dom.arcadeTimeVal.className = 'arcade-stat-val amber';
        }
      }

      if (remainingMs <= 0) {
        endArcadeGame();
      }
    }, 250);

    scheduleNextSpawn();
  }

  function scheduleNextSpawn() {
    if (!arcadeIsPlaying) return;

    if (activeTargets.size < 4) {
      spawnTarget();
    }

    const delay = Math.random() * 380 + 520;
    arcadeSpawnerTimeout = setTimeout(scheduleNextSpawn, delay);
  }

  function spawnTarget() {
    if (!dom.arcadePlayfield || !arcadeIsPlaying || !window.puzzleManager) return;

    const playfieldRect = dom.arcadePlayfield.getBoundingClientRect();
    const width = playfieldRect.width || 700;
    const height = playfieldRect.height || 420;

    const type = window.puzzleManager.getRandomTargetType();
    const targetDef = window.puzzleManager.getPuzzle('key_03')?.targetTypes[type];
    const size = targetDef?.size || 55;

    const margin = size + 20;
    const posX = Math.random() * (width - margin * 2) + margin;
    const posY = Math.random() * (height - margin * 2) + margin;

    const targetEl = document.createElement('div');
    targetEl.className = `arcade-target ${type} telegraphing`;
    targetEl.style.left = `${posX}px`;
    targetEl.style.top = `${posY}px`;
    targetEl.dataset.type = type;
    targetEl.setAttribute('role', 'button');
    targetEl.setAttribute('aria-label', `Target ${type}`);

    targetEl.innerHTML = `
      <div class="target-reticle-ring"></div>
      <div class="target-core-dot"></div>
    `;

    dom.arcadePlayfield.appendChild(targetEl);
    activeTargets.add(targetEl);

    if (window.audioManager) {
      window.audioManager.playTargetTelegraph();
    }

    setTimeout(() => {
      if (!targetEl.parentNode || !arcadeIsPlaying) return;
      targetEl.classList.remove('telegraphing');

      targetEl.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        e.stopPropagation();
        handleTargetHit(targetEl, posX, posY);
      });
    }, targetDef.telegraphTime || 250);

    const expireTimer = setTimeout(() => {
      if (!activeTargets.has(targetEl)) return;
      handleTargetMiss(targetEl);
    }, targetDef.lifetime || 2000);

    targetEl._expireTimer = expireTimer;
  }

  function handleTargetHit(targetEl, posX, posY) {
    if (!activeTargets.has(targetEl) || targetEl.dataset.hit === 'true') return;
    targetEl.dataset.hit = 'true';
    clearTimeout(targetEl._expireTimer);
    activeTargets.delete(targetEl);

    const type = targetEl.dataset.type || 'standard';
    const hitData = window.puzzleManager.recordArcadeHit(type);
    if (!hitData) return;

    if (window.audioManager) {
      if (hitData.isBonus) {
        window.audioManager.playBonusTargetHit();
      } else {
        window.audioManager.playTargetHit(type, hitData.combo);
      }
    }

    if (dom.arcadeScoreVal) dom.arcadeScoreVal.textContent = hitData.totalScore.toString().padStart(4, '0');
    if (dom.arcadeComboVal) dom.arcadeComboVal.textContent = `x${hitData.combo}`;
    if (dom.arcadeTargetsVal) dom.arcadeTargetsVal.textContent = hitData.targetsDestroyed;

    showScoreFloatTag(posX, posY, `+${hitData.earnedScore}${hitData.combo > 1 ? ` (x${hitData.combo})` : ''}`, hitData.isBonus);

    if (typeof gsap !== 'undefined') {
      gsap.to(targetEl, {
        scale: 1.35,
        opacity: 0,
        duration: 0.16,
        onComplete: () => {
          if (targetEl.parentNode) targetEl.parentNode.removeChild(targetEl);
        }
      });
    } else {
      if (targetEl.parentNode) targetEl.parentNode.removeChild(targetEl);
    }
  }

  function handleTargetMiss(targetEl) {
    activeTargets.delete(targetEl);
    clearTimeout(targetEl._expireTimer);

    if (window.puzzleManager) {
      window.puzzleManager.recordArcadeMiss();
    }

    if (window.audioManager) {
      window.audioManager.playTargetMiss();
    }

    if (dom.arcadeComboVal) dom.arcadeComboVal.textContent = 'x1';

    if (typeof gsap !== 'undefined') {
      gsap.to(targetEl, {
        opacity: 0,
        scale: 0.5,
        duration: 0.18,
        onComplete: () => {
          if (targetEl.parentNode) targetEl.parentNode.removeChild(targetEl);
        }
      });
    } else {
      if (targetEl.parentNode) targetEl.parentNode.removeChild(targetEl);
    }
  }

  function showScoreFloatTag(x, y, text, isBonus) {
    if (!dom.arcadePlayfield) return;
    const tag = document.createElement('div');
    tag.className = `score-float-tag ${isBonus ? 'bonus' : ''}`;
    tag.textContent = text;
    tag.style.left = `${x}px`;
    tag.style.top = `${y}px`;

    dom.arcadePlayfield.appendChild(tag);

    if (typeof gsap !== 'undefined') {
      gsap.fromTo(tag, 
        { opacity: 1, y: 0, scale: 0.8 }, 
        { opacity: 0, y: -30, scale: 1.1, duration: 0.6, ease: 'power2.out', onComplete: () => {
          if (tag.parentNode) tag.parentNode.removeChild(tag);
        }}
      );
    } else {
      setTimeout(() => {
        if (tag.parentNode) tag.parentNode.removeChild(tag);
      }, 500);
    }
  }

  function stopArcadeGame() {
    arcadeIsPlaying = false;
    if (arcadeTimerInterval) clearInterval(arcadeTimerInterval);
    if (arcadeSpawnerTimeout) clearTimeout(arcadeSpawnerTimeout);
    arcadeTimerInterval = null;
    arcadeSpawnerTimeout = null;
  }

  function clearArcadePlayfield() {
    activeTargets.forEach(targetEl => {
      clearTimeout(targetEl._expireTimer);
      if (targetEl.parentNode) targetEl.parentNode.removeChild(targetEl);
    });
    activeTargets.clear();
  }

  function endArcadeGame() {
    stopArcadeGame();
    clearArcadePlayfield();

    if (!window.puzzleManager) return;
    const result = window.puzzleManager.finishArcadeSession();

    if (window.gameManager && result.finalScore > 0) {
      window.gameManager.recordArcadeBestScore(result.finalScore);
    }

    if (dom.summaryFinalScore) dom.summaryFinalScore.textContent = result.finalScore;
    if (dom.summaryTargetsDestroyed) dom.summaryTargetsDestroyed.textContent = result.targetsDestroyed;
    if (dom.summaryMaxCombo) dom.summaryMaxCombo.textContent = `x${result.maxCombo}`;
    if (dom.summaryBestScore) dom.summaryBestScore.textContent = result.bestScore;
    if (dom.arcadeBestBadge) dom.arcadeBestBadge.textContent = `BEST: ${result.bestScore}`;

    const alreadySolved = window.gameManager?.getState().keysCollected.includes('key_03');

    if (result.passed) {
      if (window.audioManager) {
        window.audioManager.playArcadeVictory();
      }
      dom.summaryStatusTitle.textContent = 'SYSTEM DEFENSE DEFEATED';
      dom.summaryStatusTitle.className = 'h4 fw-bold text-success mb-2 font-monospace';
      dom.summaryStatusSub.textContent = 'Simulation passed (Score >= 1200). Defense protocol permanently deactivated.';

      if (!alreadySolved) {
        dom.btnClaimKey3.classList.remove('d-none');
      } else {
        dom.btnClaimKey3.classList.add('d-none');
      }
    } else {
      if (window.audioManager) {
        window.audioManager.playLockedSound();
      }
      dom.summaryStatusTitle.textContent = 'INSUFFICIENT SCORE';
      dom.summaryStatusTitle.className = 'h4 fw-bold text-warning mb-2 font-monospace';
      dom.summaryStatusSub.textContent = `Score was below target threshold (1200 pts required). Retry to claim Key 03.`;
      dom.btnClaimKey3.classList.add('d-none');
    }

    dom.arcadeSummaryStage.classList.add('active');
    if (typeof gsap !== 'undefined') {
      gsap.fromTo(dom.arcadeSummaryStage, { opacity: 0 }, { opacity: 1, duration: 0.3 });
    } else {
      dom.arcadeSummaryStage.style.opacity = '1';
    }
  }

  function handleClaimKey3() {
    if (!window.gameManager) return;
    window.gameManager.collectKey('key_03');

    if (window.audioManager) {
      window.audioManager.playDoorUnlockResonance();
    }

    closeArcadeModal();
    updateHUD();
    updateLobbyVisuals();
  }

  // =========================================================================
  // KEY 02: MAINFRAME TERMINAL LOGIC
  // =========================================================================

  function openTerminalModal() {
    if (!dom.terminalModal || !dom.terminalCard || isEscapeSequenceActive || inSector02) return;
    isTerminalOpen = true;

    const isSolved = window.puzzleManager ? window.puzzleManager.isSolved('key_02') : false;

    dom.termKeyExtractStage.classList.remove('active');
    dom.termKeyExtractStage.style.opacity = '0';

    if (isSolved) {
      dom.termLedIndicator.className = 'term-led-indicator online';
      dom.termOutputStream.innerHTML = `
<div class="terminal-entry-log success-msg">MAINFRAME TERMINAL // 0x7F</div>
<div class="terminal-entry-log system-msg">--------------------------------------------------</div>
<div class="terminal-entry-log success-msg">&gt; SECURITY PROTOCOL: DISABLED</div>
<div class="terminal-entry-log success-msg">&gt; AUTHENTICATION: VERIFIED</div>
<div class="terminal-entry-log success-msg">&gt; KEY 02: RECOVERED [CIPHER STORED IN HUD]</div>
<div class="terminal-entry-log system-msg">&gt; ARCHIVE STATUS: COMPLETE</div>
<div class="terminal-entry-log system-msg">&gt; SYSTEM ACCESS LEVEL: ADMINISTRATOR</div>
<div class="terminal-entry-log text-info">&gt; Type <span class="text-warning fw-bold">TRACE</span> to scan dormant sub-sectors.</div>
<div class="terminal-entry-log system-msg">--------------------------------------------------</div>
`;
    } else {
      dom.termLedIndicator.className = 'term-led-indicator';
      dom.termOutputStream.innerHTML = `
<div class="terminal-entry-log error-msg">SYSTEM // SECURITY PROTOCOL ACTIVE</div>
<div class="terminal-entry-log error-msg">ACCESS: LOCKED &bull; AUTHENTICATION REQUIRED</div>
<div class="terminal-entry-log system-msg">--------------------------------------------------</div>
<div class="terminal-entry-log">&gt; SYSTEM READY</div>
<div class="terminal-entry-log">&gt; AUTHENTICATION CHANNEL OPEN</div>
<div class="terminal-entry-log text-info">&gt; Type <span class="text-warning fw-bold">HELP</span> to view diagnostic commands.</div>
`;
    }

    if (window.audioManager) {
      window.audioManager.playTerminalBeep();
      window.audioManager.playModalOpen();
    }

    dom.terminalModal.classList.add('active');
    dom.terminalModal.setAttribute('aria-hidden', 'false');

    if (typeof gsap !== 'undefined') {
      gsap.fromTo(dom.terminalModal, { opacity: 0 }, { opacity: 1, duration: 0.25 });
      gsap.fromTo(dom.terminalCard, 
        { opacity: 0, scale: 0.94, y: 15 }, 
        { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'power3.out' }
      );
    } else {
      dom.terminalModal.style.opacity = '1';
    }

    setTimeout(() => {
      if (dom.termInput) dom.termInput.focus();
    }, 120);
  }

  function closeTerminalModal() {
    if (!dom.terminalModal || !isTerminalOpen) return;
    isTerminalOpen = false;

    if (window.audioManager) {
      window.audioManager.playModalClose();
    }

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.terminalCard, {
        opacity: 0,
        scale: 0.94,
        y: 10,
        duration: 0.2,
        ease: 'power2.in'
      });
      gsap.to(dom.terminalModal, {
        opacity: 0,
        duration: 0.25,
        onComplete: () => {
          dom.terminalModal.classList.remove('active');
          dom.terminalModal.setAttribute('aria-hidden', 'true');
        }
      });
    } else {
      dom.terminalModal.classList.remove('active');
      dom.terminalModal.setAttribute('aria-hidden', 'true');
    }
  }

  function handleTerminalSubmit(commandText) {
    if (!window.puzzleManager) return;
    const inputStr = commandText !== undefined ? commandText : (dom.termInput?.value || '');
    if (!inputStr.trim()) return;

    cmdHistory.push(inputStr);
    historyIndex = cmdHistory.length;

    const userLog = document.createElement('div');
    userLog.className = 'terminal-entry-log user-cmd';
    userLog.textContent = `0x7F:> ${inputStr}`;
    dom.termOutputStream.appendChild(userLog);

    if (dom.termInput) dom.termInput.value = '';

    if (window.audioManager) {
      window.audioManager.playTerminalCommandExec();
    }

    const res = window.puzzleManager.executeTerminalCommand(inputStr);

    if (res.status === 'clear') {
      dom.termOutputStream.innerHTML = '';
      return;
    }

    if (res.status === 'secret_trigger') {
      const sysLog = document.createElement('div');
      sysLog.className = 'terminal-entry-log success-msg';
      sysLog.textContent = res.text || '';
      dom.termOutputStream.appendChild(sysLog);
      dom.termOutputStream.scrollTop = dom.termOutputStream.scrollHeight;

      setTimeout(() => {
        closeTerminalModal();
        enterSector02();
      }, 900);
      return;
    }

    if (res.status === 'scan' && window.audioManager) {
      window.audioManager.playTerminalScan();
    }

    const sysLog = document.createElement('div');
    sysLog.className = `terminal-entry-log ${
      res.status === 'auth_success' ? 'success-msg' :
      res.status === 'auth_denied' ? 'error-msg' :
      res.status === 'warning' ? 'hint-msg' : 'system-msg'
    }`;
    sysLog.textContent = res.text || '';
    dom.termOutputStream.appendChild(sysLog);

    if (res.showHint && res.hintText) {
      const hintLog = document.createElement('div');
      hintLog.className = 'terminal-entry-log hint-msg';
      hintLog.textContent = res.hintText;
      dom.termOutputStream.appendChild(hintLog);
    }

    dom.termOutputStream.scrollTop = dom.termOutputStream.scrollHeight;

    if (res.status === 'auth_success') {
      dom.termLedIndicator.className = 'term-led-indicator online';

      if (window.audioManager) {
        window.audioManager.playResonanceSuccess();
      }

      setTimeout(() => {
        if (window.audioManager) {
          window.audioManager.playKeyExtractChime();
        }
        dom.termKeyExtractStage.classList.add('active');

        if (typeof gsap !== 'undefined') {
          gsap.fromTo(dom.termKeyExtractStage,
            { opacity: 0, scale: 0.9 },
            { opacity: 1, scale: 1, duration: 0.55, ease: 'back.out(1.2)' }
          );
        } else {
          dom.termKeyExtractStage.style.opacity = '1';
        }
      }, 600);
    } else if (res.status === 'auth_denied') {
      if (window.audioManager) {
        window.audioManager.playLockedSound();
      }
      if (typeof gsap !== 'undefined') {
        gsap.fromTo(dom.terminalCard, 
          { x: -4 }, 
          { x: 4, duration: 0.08, repeat: 3, yoyo: true, ease: 'none', onComplete: () => { gsap.set(dom.terminalCard, { x: 0 }); } }
        );
      }
    }
  }

  function handleClaimKey2() {
    if (!window.gameManager) return;
    window.gameManager.collectKey('key_02');

    closeTerminalModal();
    updateHUD();
    updateLobbyVisuals();
  }

  // =========================================================================
  // KEY 01: HARMONIC RESONATOR LOGIC
  // =========================================================================

  function openResonatorModal() {
    if (!dom.resonatorModal || !dom.resonatorCard || isEscapeSequenceActive || inSector02) return;
    isResonatorOpen = true;

    const isSolved = window.puzzleManager ? window.puzzleManager.isSolved('key_01') : false;

    dom.resNodeCards.forEach(card => card.classList.remove('active-step', 'desync-flash'));
    dom.keyExtractStage.classList.remove('active');
    dom.keyExtractStage.style.opacity = '0';

    if (isSolved) {
      dom.resStatusBadge.textContent = 'STATUS: STABLE // COMPLETE';
      dom.resStatusBadge.classList.add('stable');
      dom.resClueText.innerHTML = '<span class="text-success fw-bold">RESONANCE STABLE.</span> Master Cipher Key 01 has been recovered.';
      dom.resStreamDisplay.innerHTML = '<span class="text-success">ARCHIVE STATUS: CALIBRATED (03 &rarr; 01 &rarr; 04 &rarr; 02)</span>';
      if (dom.resHintBox) dom.resHintBox.classList.add('d-none');
    } else {
      dom.resStatusBadge.textContent = 'STATUS: UNCALIBRATED';
      dom.resStatusBadge.classList.remove('stable');
      dom.resClueText.innerHTML = 'Telemetry signature: Harmonize nodes in order of <span class="text-info fw-bold">ascending harmonic frequency</span> (Phase I &rarr; IV).';
      dom.resStreamDisplay.textContent = 'WAITING FOR SEQUENCE...';
      
      const puzzle = window.puzzleManager?.getPuzzle('key_01');
      if (puzzle && puzzle.attempts >= puzzle.hintThreshold && dom.resHintBox) {
        dom.resHintBox.textContent = 'TELEMETRY HINT: Align nodes by ascending harmonic frequency (14.2G → 28.4G → 42.6G → 56.8G).';
        dom.resHintBox.classList.remove('d-none');
      } else if (dom.resHintBox) {
        dom.resHintBox.classList.add('d-none');
      }
    }

    if (window.audioManager) {
      window.audioManager.playModalOpen();
    }

    dom.resonatorModal.classList.add('active');
    dom.resonatorModal.setAttribute('aria-hidden', 'false');

    if (typeof gsap !== 'undefined') {
      gsap.fromTo(dom.resonatorModal, { opacity: 0 }, { opacity: 1, duration: 0.25 });
      gsap.fromTo(dom.resonatorCard, 
        { opacity: 0, scale: 0.94, y: 15 }, 
        { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'power3.out' }
      );
    } else {
      dom.resonatorModal.style.opacity = '1';
    }
  }

  function closeResonatorModal() {
    if (!dom.resonatorModal || !isResonatorOpen) return;
    isResonatorOpen = false;

    if (window.audioManager) {
      window.audioManager.playModalClose();
    }

    if (window.puzzleManager) {
      window.puzzleManager.resetPuzzleInput('key_01');
    }

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.resonatorCard, {
        opacity: 0,
        scale: 0.94,
        y: 10,
        duration: 0.2,
        ease: 'power2.in'
      });
      gsap.to(dom.resonatorModal, {
        opacity: 0,
        duration: 0.25,
        onComplete: () => {
          dom.resonatorModal.classList.remove('active');
          dom.resonatorModal.setAttribute('aria-hidden', 'true');
        }
      });
    } else {
      dom.resonatorModal.classList.remove('active');
      dom.resonatorModal.setAttribute('aria-hidden', 'true');
    }
  }

  function handleResonatorNodeClick(nodeCard) {
    if (isNodeProcessing || !window.puzzleManager) return;
    const nodeId = nodeCard.dataset.nodeId;
    const audioIdx = parseInt(nodeId, 10);

    if (window.audioManager) {
      window.audioManager.playResonanceNodeTone(audioIdx);
    }

    const result = window.puzzleManager.inputResonatorNode(nodeId);

    // Secret Room Trigger via Inverted Resonance
    if (result.status === 'secret_trigger') {
      isNodeProcessing = true;
      nodeCard.classList.add('active-step');

      dom.resStreamDisplay.innerHTML = '<span class="text-warning fw-bold">// ANOMALY: SECTOR 02 LINK DETECTED</span>';

      setTimeout(() => {
        closeResonatorModal();
        isNodeProcessing = false;
        enterSector02();
      }, 750);
      return;
    }

    if (result.status === 'progress') {
      nodeCard.classList.add('active-step');
      dom.resStreamDisplay.textContent = `INPUT: ${result.input.join(' → ')}`;
    } else if (result.status === 'desync') {
      isNodeProcessing = true;
      nodeCard.classList.add('active-step');

      if (window.audioManager) {
        window.audioManager.playResonanceDesync();
      }

      dom.resStreamDisplay.innerHTML = '<span class="text-danger fw-bold">RESONANCE DESYNC &bull; CALIBRATION RESET</span>';
      dom.resNodeCards.forEach(c => c.classList.add('desync-flash'));

      if (result.showHint && dom.resHintBox) {
        dom.resHintBox.textContent = result.hintText;
        dom.resHintBox.classList.remove('d-none');
      }

      setTimeout(() => {
        dom.resNodeCards.forEach(c => c.classList.remove('desync-flash', 'active-step'));
        dom.resStreamDisplay.textContent = 'WAITING FOR SEQUENCE...';
        isNodeProcessing = false;
      }, 500);
    } else if (result.status === 'success') {
      isNodeProcessing = true;
      nodeCard.classList.add('active-step');
      dom.resStreamDisplay.innerHTML = '<span class="text-success fw-bold">RESONANCE STABLE &bull; ACCESS GRANTED</span>';

      dom.resStatusBadge.textContent = 'STATUS: STABLE';
      dom.resStatusBadge.classList.add('stable');

      if (window.audioManager) {
        window.audioManager.playResonanceSuccess();
      }

      setTimeout(() => {
        if (window.audioManager) {
          window.audioManager.playKeyExtractChime();
        }
        dom.keyExtractStage.classList.add('active');

        if (typeof gsap !== 'undefined') {
          gsap.fromTo(dom.keyExtractStage, 
            { opacity: 0, scale: 0.9 }, 
            { opacity: 1, scale: 1, duration: 0.55, ease: 'back.out(1.2)' }
          );
        } else {
          dom.keyExtractStage.style.opacity = '1';
        }
        isNodeProcessing = false;
      }, 600);
    }
  }

  function handleClaimKey() {
    if (!window.gameManager) return;
    window.gameManager.collectKey('key_01');

    closeResonatorModal();
    updateHUD();
    updateLobbyVisuals();
  }

  // =========================================================================
  // STANDARD INSPECTION MODAL (FOR OBJECT DIAGNOSTICS)
  // =========================================================================

  function openModal(title, bodyHtml, diagHtml) {
    if (!dom.modalOverlay || !dom.modalCard || isEscapeSequenceActive) return;
    isModalOpen = true;

    dom.modalTitle.textContent = title;
    dom.modalBody.innerHTML = bodyHtml;
    dom.modalDiagLog.innerHTML = diagHtml;

    dom.modalOverlay.classList.add('active');
    dom.modalOverlay.setAttribute('aria-hidden', 'false');

    if (typeof gsap !== 'undefined') {
      gsap.fromTo(dom.modalOverlay, { opacity: 0 }, { opacity: 1, duration: 0.25 });
      gsap.fromTo(dom.modalCard, 
        { opacity: 0, scale: 0.94, y: 15 }, 
        { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'power3.out' }
      );
    } else {
      dom.modalOverlay.style.opacity = '1';
    }
  }

  function closeModal() {
    if (!dom.modalOverlay || !isModalOpen) return;
    isModalOpen = false;

    if (window.audioManager) {
      window.audioManager.playModalClose();
    }

    if (typeof gsap !== 'undefined') {
      gsap.to(dom.modalCard, {
        opacity: 0,
        scale: 0.94,
        y: 10,
        duration: 0.2,
        ease: 'power2.in'
      });
      gsap.to(dom.modalOverlay, {
        opacity: 0,
        duration: 0.25,
        onComplete: () => {
          dom.modalOverlay.classList.remove('active');
          dom.modalOverlay.setAttribute('aria-hidden', 'true');
        }
      });
    } else {
      dom.modalOverlay.classList.remove('active');
      dom.modalOverlay.setAttribute('aria-hidden', 'true');
    }
  }

  /**
   * Setup UI Event Listeners (Bound once for complete lifecycle safety)
   */
  function setupEventListeners() {
    // 1. Cinematic Intro Button
    if (dom.btnEnter) {
      dom.btnEnter.addEventListener('click', transitionToGameWorld);
      dom.btnEnter.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
    }

    // 2. HUD Audio Toggle
    if (dom.btnToggleAudio) {
      dom.btnToggleAudio.addEventListener('click', () => {
        if (window.audioManager) {
          const soundOn = window.audioManager.toggleGlobalAudio();
          if (dom.audioStatusLabel) {
            dom.audioStatusLabel.textContent = soundOn ? 'ON' : 'OFF';
          }
        }
      });
    }

    // 3. Central Door Click (Escape Sequence Trigger when 3/3 keys recovered)
    if (dom.nodeDoor) {
      dom.nodeDoor.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.nodeDoor.addEventListener('click', () => {
        const state = window.gameManager?.getState();
        const hasAllKeys = state && state.keysCollected.length >= 3;

        if (hasAllKeys) {
          triggerFinalEscapeSequence();
        } else {
          if (window.audioManager) window.audioManager.playLockedSound();
          openModal(
            '// SECURITY BARRIER // GATE-0',
            `<h4 class="h5 fw-bold text-light mb-2 font-monospace">ACCESS LEVEL: UNKNOWN</h4>
             <p class="text-secondary small mb-0">A massive reinforced blast door seals the chamber threshold. The multi-lock biometric ring refuses your clearance.</p>`,
            `<div class="text-muted">// Gate Diagnostics:</div>
             <div>&gt; Barrier Status: <span class="text-danger fw-bold">LOCKED</span></div>
             <div>&gt; Encryption Integrity: 100%</div>
             <div>&gt; Keys Synchronized: ${state.keysCollected.length} / 3</div>
             <div class="text-warning mt-2">&gt; "Collect all 3 cipher keys to override the barrier."</div>`
          );
        }
      });
      dom.nodeDoor.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          dom.nodeDoor.click();
        }
      });
    }

    // 4. Mainframe Terminal Click
    if (dom.nodeTerminal) {
      dom.nodeTerminal.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.nodeTerminal.addEventListener('click', openTerminalModal);
      dom.nodeTerminal.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          dom.nodeTerminal.click();
        }
      });
    }

    // Terminal Input & Quick Chip controls
    if (dom.termInput) {
      dom.termInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleTerminalSubmit();
        } else if (e.key === 'ArrowUp') {
          if (cmdHistory.length > 0 && historyIndex > 0) {
            historyIndex--;
            dom.termInput.value = cmdHistory[historyIndex] || '';
          }
        } else if (e.key === 'ArrowDown') {
          if (historyIndex < cmdHistory.length - 1) {
            historyIndex++;
            dom.termInput.value = cmdHistory[historyIndex] || '';
          } else {
            historyIndex = cmdHistory.length;
            dom.termInput.value = '';
          }
        } else {
          if (window.audioManager && e.key.length === 1) {
            window.audioManager.playTerminalKeystroke();
          }
        }
      });
    }

    if (dom.btnTermSend) {
      dom.btnTermSend.addEventListener('click', () => handleTerminalSubmit());
    }

    if (dom.termChips) {
      dom.termChips.forEach(chip => {
        chip.addEventListener('click', () => {
          const cmd = chip.dataset.cmd;
          if (cmd) handleTerminalSubmit(cmd);
        });
      });
    }

    if (dom.btnTermClose) dom.btnTermClose.addEventListener('click', closeTerminalModal);
    if (dom.btnClaimKey2) dom.btnClaimKey2.addEventListener('click', handleClaimKey2);

    // 5. Strange Resonator Click
    if (dom.nodeStrangeObject) {
      dom.nodeStrangeObject.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.nodeStrangeObject.addEventListener('click', openResonatorModal);
      dom.nodeStrangeObject.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          dom.nodeStrangeObject.click();
        }
      });
    }

    dom.resNodeCards.forEach(nodeCard => {
      nodeCard.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      nodeCard.addEventListener('click', () => {
        handleResonatorNodeClick(nodeCard);
      });
      nodeCard.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleResonatorNodeClick(nodeCard);
        }
      });
    });

    if (dom.btnResClose) dom.btnResClose.addEventListener('click', closeResonatorModal);
    if (dom.btnClaimKey) dom.btnClaimKey.addEventListener('click', handleClaimKey);

    // 6. Arcade Console Click
    if (dom.nodeArcade) {
      dom.nodeArcade.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.nodeArcade.addEventListener('click', openArcadeModal);
      dom.nodeArcade.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          dom.nodeArcade.click();
        }
      });
    }

    if (dom.btnArcadeClose) dom.btnArcadeClose.addEventListener('click', closeArcadeModal);
    if (dom.btnClaimKey3) dom.btnClaimKey3.addEventListener('click', handleClaimKey3);
    if (dom.btnArcadeRetry) dom.btnArcadeRetry.addEventListener('click', () => {
      dom.arcadeSummaryStage.classList.remove('active');
      startArcadeCountdown();
    });

    // 7. Sector 02 Interactions
    if (dom.btnLeaveSector02) {
      dom.btnLeaveSector02.addEventListener('click', leaveSector02);
    }

    if (dom.obsWindowCard) {
      dom.obsWindowCard.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.obsWindowCard.addEventListener('click', () => {
        if (window.audioManager) window.audioManager.playMonitorGlitch();
        openModal(
          '// OBSERVATION WINDOW // FEED 0x00',
          `<h4 class="h5 fw-bold text-info mb-2 font-monospace">SURVEILLANCE FEED: ROOM 01 [LOBBY]</h4>
           <p class="text-secondary small mb-0">You are staring directly through one-way glass into the Lobby chamber you supposedly escaped. The blast door is sealed tight. A ghostly silhouette sits frozen at the terminal.</p>`,
          `<div class="text-muted">// Telemetry Mismatch:</div>
           <div>&gt; Subject Position: <span class="text-warning fw-bold">SIMULTANEOUS</span></div>
           <div>&gt; Chamber Integrity: LOCKED</div>
           <div class="text-info mt-2">&gt; "Who is looking at whom?"</div>`
        );
      });
    }

    if (dom.obsMonitorCard) {
      dom.obsMonitorCard.addEventListener('mouseenter', () => {
        if (window.audioManager) window.audioManager.playHoverSound();
      });
      dom.obsMonitorCard.addEventListener('click', () => {
        if (window.audioManager) window.audioManager.playMonitorGlitch();
        openModal(
          '// OBSERVATION RECORD // LOG #0x88F',
          `<h4 class="h5 fw-bold text-warning mb-2 font-monospace">SUBJECT ARCHIVE: ACTIVE</h4>
           <p class="text-secondary small mb-0">The observation logs record infinite recursive escape attempts.</p>`,
          `<div class="text-muted">// Archive Log:</div>
           <div>&gt; Subject: <span class="text-light">PLAYER</span></div>
           <div>&gt; Exit Status: <span class="text-danger fw-bold">SIMULATED</span></div>
           <div>&gt; Iteration: CURRENT INSTANCE</div>
           <div class="text-warning mt-2">&gt; "The website does not let you leave. It just builds another room."</div>`
        );
      });
    }

    if (dom.obsInput) {
      dom.obsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleObservationTerminalCommand();
        } else {
          if (window.audioManager && e.key.length === 1) {
            window.audioManager.playTerminalKeystroke();
          }
        }
      });
    }

    if (dom.obsChips) {
      dom.obsChips.forEach(chip => {
        chip.addEventListener('click', () => {
          const cmd = chip.dataset.cmd;
          if (cmd) handleObservationTerminalCommand(cmd);
        });
      });
    }

    if (dom.btnRevealReturnLobby) {
      dom.btnRevealReturnLobby.addEventListener('click', () => {
        dom.obsRevealStage.classList.remove('active');
        leaveSector02();
      });
    }

    if (dom.btnRevealPlayAgain) {
      dom.btnRevealPlayAgain.addEventListener('click', handlePlayAgain);
    }

    // 8. Results Screen Buttons & Explore Secret Handler
    if (dom.btnPlayAgain) dom.btnPlayAgain.addEventListener('click', handlePlayAgain);
    if (dom.btnShareScore) dom.btnShareScore.addEventListener('click', handleShareScore);
    if (dom.btnExploreSecret) {
      dom.btnExploreSecret.addEventListener('click', () => {
        const state = window.gameManager ? window.gameManager.getState() : null;
        if (state && state.secretDiscovered) {
          enterSector02();
        } else {
          showToast('// ACCESS RESTRICTED • SECTOR 02 LOCKED');
        }
      });
    }

    // 9. Standard Modal Close Controls
    if (dom.btnModalClose) dom.btnModalClose.addEventListener('click', closeModal);
    if (dom.btnModalAction) dom.btnModalAction.addEventListener('click', closeModal);
    if (dom.modalOverlay) {
      dom.modalOverlay.addEventListener('click', (e) => {
        if (e.target === dom.modalOverlay) closeModal();
      });
    }

    // Escape Key Handler
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !isEscapeSequenceActive) {
        if (inSector02 && dom.obsRevealStage && dom.obsRevealStage.classList.contains('active')) {
          dom.obsRevealStage.classList.remove('active');
          return;
        }
        if (inSector02) leaveSector02();
        if (isArcadeOpen) closeArcadeModal();
        if (isTerminalOpen) closeTerminalModal();
        if (isResonatorOpen) closeResonatorModal();
        if (isModalOpen) closeModal();
      }
    });
  }

  /**
   * Environmental Parallax Engine
   */
  function initParallaxEngine(bgLayer, mgLayer) {
    if (!bgLayer || !mgLayer) return;
    if (window.matchMedia('(hover: none) or (pointer: coarse) or (prefers-reduced-motion: reduce)').matches) {
      return;
    }

    let targetX = 0;
    let targetY = 0;
    let currentBgX = 0;
    let currentBgY = 0;
    let currentMgX = 0;
    let currentMgY = 0;

    window.addEventListener('mousemove', (e) => {
      if (isEscapeSequenceActive || inSector02) return;
      const normX = (e.clientX / window.innerWidth) - 0.5;
      const normY = (e.clientY / window.innerHeight) - 0.5;
      targetX = normX;
      targetY = normY;
    }, { passive: true });

    function renderParallax() {
      if (!isEscapeSequenceActive && !inSector02) {
        currentBgX += (targetX * 8 - currentBgX) * 0.08;
        currentBgY += (targetY * 8 - currentBgY) * 0.08;
        bgLayer.style.transform = `translate3d(${currentBgX.toFixed(2)}px, ${currentBgY.toFixed(2)}px, 0)`;

        currentMgX += (targetX * -14 - currentMgX) * 0.08;
        currentMgY += (targetY * -14 - currentMgY) * 0.08;
        mgLayer.style.transform = `translate3d(${currentMgX.toFixed(2)}px, ${currentMgY.toFixed(2)}px, 0)`;
      }

      requestAnimationFrame(renderParallax);
    }

    renderParallax();
  }

  /**
   * Ambient Particle Canvas Background
   */
  function initAmbientCanvas(canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const particles = [];
    const isMobile = window.innerWidth < 768;
    const PARTICLE_COUNT = isMobile ? 20 : Math.min(Math.floor((width * height) / 24000), 50);

    class Particle {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.size = Math.random() * 1.6 + 0.4;
        this.vx = (Math.random() - 0.5) * 0.25;
        this.vy = (Math.random() - 0.5) * 0.25 - 0.06;
        this.alpha = Math.random() * 0.4 + 0.1;
        this.color = Math.random() > 0.35 ? '0, 240, 255' : '0, 255, 136';
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0) this.x = width;
        if (this.x > width) this.x = 0;
        if (this.y < 0) this.y = height;
        if (this.y > height) this.y = 0;
      }

      draw() {
        ctx.fillStyle = `rgba(${this.color}, ${this.alpha})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push(new Particle());
    }

    function render() {
      ctx.clearRect(0, 0, width, height);

      const grad = ctx.createRadialGradient(width / 2, height / 2, 40, width / 2, height / 2, width * 0.65);
      grad.addColorStop(0, 'rgba(6, 15, 35, 0.18)');
      grad.addColorStop(1, 'rgba(2, 4, 8, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();

        if (!isMobile) {
          for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 90) {
              ctx.strokeStyle = `rgba(0, 240, 255, ${0.08 * (1 - dist / 90)})`;
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.moveTo(particles[i].x, particles[i].y);
              ctx.lineTo(particles[j].x, particles[j].y);
              ctx.stroke();
            }
          }
        }
      }

      requestAnimationFrame(render);
    }

    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
      }, 100);
    }, { passive: true });

    render();
  }

  /**
   * Custom Desktop Cursor Glow
   */
  function initCustomCursor(dot, ring) {
    if (!dot || !ring || window.matchMedia('(hover: none) or (pointer: coarse)').matches) {
      return;
    }

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX;
    let ringY = mouseY;
    let active = false;

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      dot.style.left = `${mouseX}px`;
      dot.style.top = `${mouseY}px`;

      if (!active) {
        active = true;
        document.body.classList.add('cursor-active');
      }
    }, { passive: true });

    window.addEventListener('mouseleave', () => {
      document.body.classList.remove('cursor-active');
      active = false;
    });

    function updateCursorRing() {
      ringX += (mouseX - ringX) * 0.2;
      ringY += (mouseY - ringY) * 0.2;

      ring.style.left = `${ringX}px`;
      ring.style.top = `${ringY}px`;

      requestAnimationFrame(updateCursorRing);
    }
    updateCursorRing();

    function bindHoverListeners() {
      const interactives = document.querySelectorAll('button, a, [role="button"], input, .interactive-node, .resonance-node-card, .term-chip, .obs-chip');
      interactives.forEach((el) => {
        el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
        el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
      });
    }
    bindHoverListeners();
  }
});
