const modal = document.getElementById('alertModal');
const modalContent = document.getElementById('modalContent');
const modalClose = document.getElementById('modalClose');

// 10秒后自动弹出红色恐怖警告
setTimeout(() => {
  modalContent.textContent = "您被发现，正在反入侵";
  modal.classList.remove('hidden');
}, 10000);

modalClose.addEventListener('click', () => {
  modal.classList.add('hidden');
});
