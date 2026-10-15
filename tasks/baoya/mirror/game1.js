const codePool = document.getElementById('codePool');
const targetArea = document.getElementById('targetArea');
const btnCheck = document.getElementById('btnCheck');
const btnHint = document.getElementById('btnHint');
const btnReset = document.getElementById('btnReset');
const hintBox = document.getElementById('hintBox');
const attemptsCount = document.getElementById('attemptsCount');
const terminal = document.getElementById('termOut');
const breachArea = document.getElementById('breachArea');

let attempts = 0;

const correctSequence = ['Δ10011', 'Θ11100', 'Σ100101']; 
let codes = ['Δ10011', 'Θ11100', 'Σ100101', 'Λ01001010', 'Ξ1111000', 'Π001011']; 

// 随机打乱数组
function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

// 初始化池
function initPool() {
  codePool.innerHTML = '';
  shuffle(codes).forEach(code => {
    const div = document.createElement('div');
    div.className = 'code';
    div.textContent = code;
    div.addEventListener('click', () => placeCode(div.textContent));
    codePool.appendChild(div);
  });
}

// 放置代码
function placeCode(code) {
  const emptySlot = Array.from(targetArea.children).find(s => !s.dataset.value);
  if (!emptySlot) return;
  emptySlot.textContent = code;
  emptySlot.dataset.value = code;
}

// 检查答案
btnCheck.addEventListener('click', () => {
  attempts++;
  attemptsCount.textContent = attempts;

  const userSequence = Array.from(targetArea.children).map(s => s.dataset.value);
  if (userSequence.includes(undefined)) {
    hintBox.textContent = '请填满所有槽位！';
    return;
  }

  let correctCount = 0;
  for (let i = 0; i < correctSequence.length; i++) {
    if (userSequence[i] === correctSequence[i]) correctCount++;
  }

  if (correctCount === correctSequence.length) {
    // 入侵成功逻辑
    hintBox.textContent = '验证通过！入侵成功…';
    terminal.textContent += '\n> ACCESS GRANTED';
    breachArea.classList.remove('hidden');

    // 可选：隐藏左侧面板，制造“系统切换”效果
    document.querySelector('.hp-left').style.display = 'none';

    // 2 秒后跳转到 map.html
    setTimeout(() => {
      window.location.href = 'map.html';
    }, 2000);
  } else {
    hintBox.textContent = `验证失败，正确数量：${correctCount}/${correctSequence.length}`;
  }
});

// 提示
btnHint.addEventListener('click', () => {
  attempts++;
  attemptsCount.textContent = attempts;
  for (let i = 0; i < correctSequence.length; i++) {
    const slot = targetArea.children[i];
    if (slot.dataset.value !== correctSequence[i]) {
      hintBox.textContent = `提示：第 ${i + 1} 个代码片段是 "${correctSequence[i]}"`;
      return;
    }
  }
});

// 重置
btnReset.addEventListener('click', () => {
  Array.from(targetArea.children).forEach(s => {
    s.textContent = parseInt(s.dataset.slot) + 1;
    delete s.dataset.value;
  });
  hintBox.textContent = '';
  attempts = 0;
  attemptsCount.textContent = 0;
  terminal.textContent = '▉ WUSHAN_CTRL_CORE / ADMIN_PORT_4421\n> AUTH CHANNEL READY...';
  breachArea.classList.add('hidden');
  document.querySelector('.hp-left').style.display = 'block';
  initPool();
});

// 初始化
initPool();
