export function copyCodeBlocks() {
  const codeBlocks = document.querySelectorAll('pre');
  codeBlocks.forEach((block) => {
    if (block.querySelector('.copy-btn')) return; // 避免重复添加

    const button = document.createElement('button');
    button.className = 'copy-btn';
    button.textContent = '复制';
    button.style.cssText = `
      position: absolute;
      top: 5px;
      right: 5px;
      background: #34495e;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 12px;
      cursor: pointer;
    `;

    button.addEventListener('click', () => {
      const code = block.querySelector('code');
      navigator.clipboard.writeText(code.textContent).then(() => {
        button.textContent = '已复制！';
        setTimeout(() => {
          button.textContent = '复制';
        }, 2000);
      });
    });

    block.style.position = 'relative';
    block.appendChild(button);
  });
}