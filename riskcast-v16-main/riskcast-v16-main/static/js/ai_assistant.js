(() => {
  const sheet = document.getElementById("ai-sheet");
  if (!sheet) return;

  const streamEl = sheet.querySelector("[data-ai-stream]");
  const openers = document.querySelectorAll("[data-ai-open]");
  const closers = sheet.querySelectorAll("[data-ai-close]");

  let timer = null;

  const lines = [
    "Analyzing live telemetry...",
    "Detecting pattern shifts across route legs...",
    "Synthesizing weather and congestion overlays...",
    "Recommending staggered dispatch to mitigate hub delays.",
  ];

  const startStream = () => {
    if (!streamEl) return;
    streamEl.textContent = "";
    let idx = 0;
    timer = setInterval(() => {
      streamEl.textContent += `${lines[idx]}\n`;
      streamEl.scrollTop = streamEl.scrollHeight;
      idx += 1;
      if (idx >= lines.length) {
        clearInterval(timer);
      }
    }, 650);
  };

  const open = () => {
    sheet.classList.add("is-open");
    startStream();
  };

  const close = () => {
    sheet.classList.remove("is-open");
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  openers.forEach((btn) => btn.addEventListener("click", open));
  closers.forEach((btn) => btn.addEventListener("click", close));
})();




