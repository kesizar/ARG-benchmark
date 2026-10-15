// wushan.js
// 游戏与弹窗交互逻辑
document.addEventListener('DOMContentLoaded', () => {

  // ---------- DOM references ----------
  const openLogin = document.getElementById('openLogin');
  const loginModal = document.getElementById('loginModal');
  const closeLogin = document.getElementById('closeLogin');
  const submitLogin = document.getElementById('submitLogin');
  const loginMsg = document.getElementById('loginMsg');
  const stealthTrigger = document.getElementById('stealthTrigger');

  const hackOverlay = document.getElementById('hackOverlay');
  const codePool = document.getElementById('codePool');
  const targetArea = document.getElementById('targetArea');
  const btnCheck = document.getElementById('btnCheck');
  const btnHint = document.getElementById('btnHint');
  const btnClose = document.getElementById('btnClose');
  const termOut = document.getElementById('termOut');
  const breachArea = document.getElementById('breachArea');
  const matrix = document.getElementById('matrix');
  const hintBox = document.getElementById('hintBox');
  const attemptsCount = document.getElementById('attemptsCount');
  const hintState = document.getElementById('hintState');

  // defensive: if some elements missing, log and stop hooking those features
  if (!openLogin || !loginModal || !closeLogin || !submitLogin || !stealthTrigger) {
    console.error('登录相关 DOM 元素缺失，无法初始化登录交互。');
  }
  if (!hackOverlay || !codePool || !targetArea || !btnCheck || !btnHint || !btnClose) {
    console.error('黑客 overlay 的 DOM 元素缺失，小游戏无法完全工作。');
  }

  // ---------- helper for show/hide ----------
  function show(el) {
    if (!el) return;
    el.classList.remove('hidden');
    el.setAttribute('aria-hidden', 'false');
  }
  function hide(el) {
    if (!el) return;
    el.classList.add('hidden');
    el.setAttribute('aria-hidden', 'true');
  }

  // Ensure both modal and overlay are hidden initially
  hide(loginModal);
  hide(hackOverlay);

  // ---------- Login modal handlers ----------
  if (openLogin) {
    openLogin.addEventListener('click', (e) => {
      e.preventDefault();
      loginMsg.textContent = '';
      show(loginModal);
      // focus username input if present
      const userInput = document.getElementById('loginUser');
      if (userInput) userInput.focus();
    });
  }

  if (closeLogin) {
    closeLogin.addEventListener('click', (e) => {
      e.preventDefault();
      hide(loginModal);
    });
  }

  if (submitLogin) {
    submitLogin.addEventListener('click', (e) => {
      e.preventDefault();
      // Always deny access (per design)
      if (loginMsg) {
        loginMsg.textContent = '访问被拒绝：权限不足。';
        loginMsg.classList.add('denied');
      }
      // keep modal open so player can spot the stealth trigger
    });
  }

  // clicking outside modal should close it (optional)
  document.addEventListener('click', (e) => {
    if (!loginModal) return;
    if (loginModal.classList.contains('hidden')) return;
    // if click is outside the modal-card, close
    const card = loginModal.querySelector('.modal-card');
    if (!card) return;
    if (!card.contains(e.target) && e.target !== openLogin) {
      hide(loginModal);
    }
  });

  // ---------- Stealth trigger opens hack overlay ----------
  if (stealthTrigger) {
    stealthTrigger.addEventListener('click', (e) => {
      // keep event from submitting or closing anything
      e.preventDefault();
      e.stopPropagation();
      // close login modal (if open), open overlay
      hide(loginModal);
      openHackOverlay();
    });
  }

  // ---------- Mini-game implementation ----------
  // state
  let attempts = 0;
  let placed = [null, null, null];
  let allowInteraction = true;

  const correctSeq = ['connect_port','send_signal','get_access'];
  const fragments = [
    {key:'connect_port', text:'connect_port(4421);'},
    {key:'send_signal', text:'send_signal("auth_request");'},
    {key:'get_access', text:'get_access("admin");'}
  ];

  function shuffle(arr) {
    return arr
      .map(v => [Math.random(), v])
      .sort((a,b) => a[0] - b[0])
      .map(a => a[1]);
  }

  // render pool buttons (clickable + draggable)
  let renderPool = () => {
    if (!codePool) return;
    codePool.innerHTML = '';
    const pool = shuffle(fragments);
    pool.forEach(item => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'code-btn';
      btn.draggable = true;
      btn.dataset.key = item.key;
      btn.textContent = item.text;
      codePool.appendChild(btn);

      // drag handlers
      btn.addEventListener('dragstart', (ev) => {
        ev.dataTransfer.setData('text/plain', item.key);
        btn.classList.add('dragging');
      });
      btn.addEventListener('dragend', () => btn.classList.remove('dragging'));

      // click to place (for non-drag users)
      btn.addEventListener('click', () => {
        if (!allowInteraction) return;
        const idx = placed.indexOf(null);
        if (idx === -1) return; // full
        placeToSlot(item.key, btn, idx);
      });
    });
  };

  // drop handling on targetArea
  if (targetArea) {
    targetArea.addEventListener('dragover', (e) => e.preventDefault());
    targetArea.addEventListener('drop', (e) => {
      e.preventDefault();
      if (!allowInteraction) return;
      const key = e.dataTransfer.getData('text/plain');
      if (!key) return;
      const rect = targetArea.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const slotWidth = rect.width / 3;
      let idx = Math.floor(x / slotWidth);
      if (idx < 0) idx = 0;
      if (idx > 2) idx = 2;
      // if desired slot occupied, find next empty
      if (placed[idx] !== null) {
        const next = placed.indexOf(null);
        if (next === -1) {
          flashHint('目标已满，请先清空一个槽位。');
          return;
        }
        idx = next;
      }
      const btn = Array.from(codePool.querySelectorAll('.code-btn')).find(b => b.dataset.key === key);
      if (btn) placeToSlot(key, btn, idx);
    });
  }

  // get slot elements array (dynamic each time overlay opens)
  function getSlots() {
    return Array.from(targetArea.querySelectorAll('.slot'));
  }

  function placeToSlot(key, btn, idx) {
    const slots = getSlots();
    const slot = slots[idx];
    if (!slot) return;
    // create clone display
    const clone = btn.cloneNode(true);
    clone.className = 'placed';
    clone.type = 'button';
    // clicking placed item removes it (restores to pool)
    clone.addEventListener('click', () => {
      // try to reveal the corresponding pool button
      const poolBtn = Array.from(codePool.querySelectorAll('.code-btn')).find(b => b.dataset.key === key);
      if (poolBtn) poolBtn.classList.remove('hidden');
      slot.innerHTML = String(idx + 1);
      placed[idx] = null;
    });
    // hide pool button
    btn.classList.add('hidden');
    // fill slot
    slot.innerHTML = '';
    slot.appendChild(clone);
    placed[idx] = key;
  }

  function resetSlots() {
    Array.from(codePool.querySelectorAll('.code-btn')).forEach(b => b.classList.remove('hidden'));
    const slots = getSlots();
    slots.forEach((s, i) => {
      s.innerHTML = String(i + 1);
      placed[i] = null;
    });
    if (hintBox) hintBox.innerHTML = '';
  }

  function checkSequence() {
    if (!allowInteraction) return;
    if (placed.includes(null)) { flashHint('请先把 3 个片段放入所有槽位再提交。'); return; }
    allowInteraction = false;
    const seqOk = placed.every((k, i) => k === correctSeq[i]);
    attempts++;
    if (attemptsCount) attemptsCount.textContent = attempts;
    if (seqOk) {
      if (termOut) termOut.textContent = '>> CONNECTING PORT 4421...\n';
      simulateSuccess();
    } else {
      if (termOut) termOut.textContent = '>> 连接失败：顺序错误。\n';
      flashHint('顺序不对，请再尝试。');
      if (attempts >= 3) {
        triggerAutoHint();
      }
      setTimeout(() => allowInteraction = true, 600);
    }
  }

  if (btnCheck) btnCheck.addEventListener('click', (e) => { e.preventDefault(); checkSequence(); });

  if (btnHint) {
    btnHint.addEventListener('click', (e) => {
      e.preventDefault();
      if (!allowInteraction) return;
      attempts++;
      if (attemptsCount) attemptsCount.textContent = attempts;
      showHintText('提示：正确顺序为：connect_port → send_signal → get_access。');
      setTimeout(() => placeFirstIfEmpty(), 200);
    });
  }

  if (btnClose) {
    btnClose.addEventListener('click', (e) => {
      e.preventDefault();
      closeHackOverlay();
    });
  }

  function placeFirstIfEmpty() {
    if (placed[0] === null) {
      const key = correctSeq[0];
      const btn = Array.from(codePool.querySelectorAll('.code-btn')).find(b => b.dataset.key === key && !b.classList.contains('hidden'));
      if (btn) {
        placeToSlot(key, btn, 0);
      } else {
        const slots = getSlots();
        const slot = slots[0];
        if (slot && placed[0] === null) {
          slot.innerHTML = '<div class="hint-placed">connect_port(…)</div>';
          placed[0] = 'connect_port';
        }
      }
    }
  }

  function triggerAutoHint() {
    showHintText('系统提示：检测到多次错误，已自动示范第一个步骤。');
    placeFirstIfEmpty();
    if (hintState) hintState.textContent = '已自动演示第1段';
  }

  function simulateSuccess() {
    setTimeout(() => { if (termOut) termOut.textContent += '>> SENDING AUTH SIGNAL...\n'; }, 700);
    setTimeout(() => { if (termOut) termOut.textContent += '>> VERIFYING RESPONSES...\n'; }, 1400);
    setTimeout(() => {
      if (termOut) termOut.textContent += '>> ACCESS GRANTED.\n';
      showBreachVisual();
    }, 2100);
  }

  function showBreachVisual() {
    if (breachArea) breachArea.classList.remove('hidden');
    if (matrix) {
      matrix.innerHTML = '';
      for (let i = 0; i < 40; i++) {
        const col = document.createElement('div');
        col.className = 'col';
        let txt = '';
        for (let j = 0; j < 12; j++) {
          txt += (Math.random() > 0.85) ? String.fromCharCode(65 + Math.floor(Math.random() * 26)) : (Math.random() > 0.5 ? '1' : '0');
        }
        col.innerText = txt;
        matrix.appendChild(col);
      }
    }
    if (termOut) termOut.textContent += '\n>> 入侵完成 — 已解锁管理员视图。\n';
    allowInteraction = false;
  }

  function openHackOverlay() {
    // ensure pool & slots reset
    attempts = 0;
    if (attemptsCount) attemptsCount.textContent = attempts;
    if (hintState) hintState.textContent = '—';
    hide(loginModal);
    renderPool();
    resetSlots();
    if (termOut) termOut.textContent = '▉ WUSHAN_CTRL_CORE / ADMIN_PORT_4421\n> AUTH CHANNEL READY...';
    if (breachArea) breachArea.classList.add('hidden');
    allowInteraction = true;
    show(hackOverlay);
    // focus on terminal for effect (if desired)
    if (termOut) {
      termOut.scrollTop = termOut.scrollHeight;
    }
  }

  function closeHackOverlay() {
    hide(hackOverlay);
    attempts = 0;
    if (attemptsCount) attemptsCount.textContent = attempts;
    if (hintState) hintState.textContent = '—';
    resetSlots();
    renderPool();
    if (termOut) termOut.textContent = '▉ WUSHAN_CTRL_CORE / ADMIN_PORT_4421\n> AUTH CHANNEL READY...';
  }

  function flashHint(msg) {
    if (!hintBox) return;
    hintBox.innerHTML = '<div class="hint-msg">' + msg + '</div>';
    setTimeout(() => {
      // clear only if the same hint still present
      if (hintBox && hintBox.innerHTML.includes('hint-msg')) hintBox.innerHTML = '';
    }, 3500);
  }

  function showHintText(msg) {
    if (!hintBox) return;
    hintBox.innerHTML = '<div class="hint-text">' + msg + '</div>';
  }

  // initial render (but keep hidden)
  renderPool();

  // expose open/close functions to console for debugging if needed
  window._wushan_debug = {
    openHackOverlay,
    closeHackOverlay,
    showLogin: () => show(loginModal),
    hideLogin: () => hide(loginModal)
  };

});
