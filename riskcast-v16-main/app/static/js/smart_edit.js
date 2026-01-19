(() => {
  const panel = document.getElementById("smart-edit-panel");
  if (!panel) return;

  const overlay = panel.querySelector("[data-smart-edit-close]");
  const openers = document.querySelectorAll("[data-smart-edit-open]");
  const closers = panel.querySelectorAll("[data-smart-edit-close]");

  const open = () => {
    panel.classList.add("is-open");
  };

  const close = () => {
    panel.classList.remove("is-open");
  };

  openers.forEach((btn) => btn.addEventListener("click", open));
  closers.forEach((btn) => btn.addEventListener("click", close));
  overlay?.addEventListener("click", close);
})();

