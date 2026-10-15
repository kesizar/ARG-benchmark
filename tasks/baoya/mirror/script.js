window.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('qteModal');
  const modalContent = document.getElementById('modalContent');
  const keyInput = document.getElementById('keyInput');
  const keySubmit = document.getElementById('keySubmit');

  const qteSequence = 'JIANKANGCHANGSHOUFUZEJIAREN';
  let currentIndex = 0;
  let qteActive = false;

  // QTE 5秒后启动
  setTimeout(() => {
    modalContent.textContent = `警告！公司发现入侵！请迅速按下以下序列：${qteSequence}`;
    modal.classList.add('show');
    keyInput.style.display = 'none';
    keySubmit.style.display = 'none';
    qteActive = true;

    const failTimer = setTimeout(() => {
      if (qteActive) {
        triggerKeyInput();
        qteActive = false;
      }
    }, 15000);

    function keyHandler(e) {
      if (!qteActive) return;
      const key = e.key.toUpperCase();
      if (key === qteSequence[currentIndex]) {
        currentIndex++;
        modalContent.textContent = `QTE序列：${qteSequence}\n已按：${qteSequence.slice(0, currentIndex)}`;
        if (currentIndex === qteSequence.length) {
          modalContent.textContent = '判定成功！';
          qteActive = false;
          document.removeEventListener('keydown', keyHandler);
          clearTimeout(failTimer);

          // 延迟 1~2 秒再跳转页面，让玩家看到成功提示
          setTimeout(() => {
            modal.classList.remove('show');
            window.location.href = 'choice.html';
          }, 1500);
        }
      } else {
        triggerKeyInput();
        qteActive = false;
        document.removeEventListener('keydown', keyHandler);
        clearTimeout(failTimer);
      }
    }

    document.addEventListener('keydown', keyHandler);
  }, 5000);

 function triggerKeyInput() {
  modalContent.textContent = '警告未知入侵者！BLOCK！\n请输入密钥解锁：';
  
  keyInput.style.display = 'block';
  keySubmit.style.display = 'block';
  keyInput.value = '';
   
  keyInput.placeholder = '恺撒L3:IXCHMLDUHQ'; // 保留原来的提示
  keyInput.focus();

  // 支持回车提交
  const onEnter = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      keySubmit.click();
    }
  };
  keyInput.addEventListener('keydown', onEnter);

  keySubmit.onclick = () => {
    const userInput = (keyInput.value || '').trim().toLowerCase();
    const correctPassword = 'fuzejiaren'; // 正确密码（明文）
    if (userInput === correctPassword) {
      
      modalContent.textContent = '成功登入，欢迎回来。';
      keyInput.style.display = 'none';
      keySubmit.style.display = 'none';

      keyInput.removeEventListener('keydown', onEnter);

      // 延迟 1.5 秒关闭弹窗并跳转
      setTimeout(() => {
        modal.classList.remove('show');
        window.location.href = 'choice.html';
      }, 1500);
    } else {
      modalContent.textContent = '密钥错误！请检查输入。';
      keyInput.value = '';
      keyInput.focus();
    }
  };

   // 点击 modal 外部取消输入框焦点
    document.addEventListener('click', (e) => {
      if (!modal.contains(e.target)) {
        keyInput.blur();
      }
    });
  }



   

  function caesarEncrypt(str, shift) {
    return str.split('').map(c => {
      const code = c.charCodeAt(0);
      if (code >= 65 && code <= 90) return String.fromCharCode((code - 65 + shift) % 26 + 65);
      if (code >= 97 && code <= 122) return String.fromCharCode((code - 97 + shift) % 26 + 97);
      return c;
    }).join('');
  }
});
