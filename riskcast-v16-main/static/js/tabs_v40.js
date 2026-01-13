(() => {
  const tabs = document.querySelector("[data-tabs]");
  if (!tabs) return;

  const triggers = Array.from(tabs.querySelectorAll(".tab-trigger"));
  const indicator = tabs.querySelector(".tab-indicator");
  const panels = Array.from(document.querySelectorAll("[data-tab-panel]"));
  const mainScroll = document.querySelector(".main-scroll");

  const activate = (targetId) => {
    triggers.forEach((btn, idx) => {
      const isActive = btn.dataset.tabTarget === targetId;
      btn.classList.toggle("is-active", isActive);
      if (isActive && indicator) {
        const percent = 100 / triggers.length;
        indicator.style.transform = `translateX(${idx * percent}%)`;
      }
    });

    panels.forEach((panel) => {
      const isActive = panel.dataset.tabPanel === targetId;
      panel.classList.toggle("is-active", isActive);
    });

    if (mainScroll) {
      mainScroll.scrollTo({ top: 0, behavior: "smooth" });
    }

    const hash = `#${targetId}`;
    if (window.location.hash !== hash) {
      history.replaceState({}, "", hash);
    }
  };

  const targetFromHash = () => {
    const id = window.location.hash.replace("#", "");
    return triggers.find((btn) => btn.dataset.tabTarget === id) ? id : triggers[0].dataset.tabTarget;
  };

  triggers.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tabTarget;
      activate(target);
    });
  });

  window.addEventListener("hashchange", () => activate(targetFromHash()));

  activate(targetFromHash());
})();




