(() => {
  const tiles = document.querySelectorAll(".breadcrumb-tile");
  const resetButton = document.getElementById("breadcrumbHomeReset");
  const celebrationPlayedKey = "breadcrumbHomeCelebrationPlayed";

  if (localStorage.getItem(celebrationPlayedKey) !== "true") {
    localStorage.setItem(celebrationPlayedKey, "true");
    const celebrate = new Audio("/step2/images/celebrate.mp3");
    const applause = new Audio("/step2/images/applause.mp3");
    let started = false;

    const removeFallback = () => {
      document.removeEventListener("pointerdown", startSequence);
      document.removeEventListener("keydown", startSequence);
    };

    const startSequence = () => {
      if (started) return;
      started = true;
      removeFallback();
      celebrate.play().catch(() => {
        started = false;
        document.addEventListener("pointerdown", startSequence, { once: true });
        document.addEventListener("keydown", startSequence, { once: true });
      });
    };

    celebrate.addEventListener("ended", () => {
      applause.play().catch(() => {});
    }, { once: true });

    document.addEventListener("pointerdown", startSequence, { once: true });
    document.addEventListener("keydown", startSequence, { once: true });
    startSequence();
  }

  const applyTransform = (image) => {
    const x = Number(image.dataset.x || "0");
    const y = Number(image.dataset.y || "0");
    const scale = Number(image.dataset.scale || "1");
    const rotate = Number(image.dataset.rotate || "0");
    image.style.transform = `translate(${x}px, ${y}px) scale(${scale}) rotate(${rotate}deg)`;
  };

  const activateTile = (activeTile) => {
    tiles.forEach((tile) => {
      tile.classList.toggle("is-active", tile === activeTile);
    });
  };

  const resetBreadcrumbHome = () => {
    tiles.forEach((tile) => {
      tile.classList.remove("is-active");
      const image = tile.querySelector("img");
      image.dataset.x = "0";
      image.dataset.y = "0";
      image.dataset.scale = "1";
      image.dataset.rotate = "0";
      applyTransform(image);
    });
  };

  if (resetButton) {
    resetButton.addEventListener("click", resetBreadcrumbHome);
  }

  tiles.forEach((tile) => {
    const image = tile.querySelector("img");
    let mode = "";
    let startX = 0;
    let startY = 0;
    let baseX = 0;
    let baseY = 0;
    let baseScale = 1;
    let baseRotate = 0;
    let centerX = 0;
    let centerY = 0;
    let startAngle = 0;

    image.dataset.x = "0";
    image.dataset.y = "0";
    image.dataset.scale = "1";
    image.dataset.rotate = "0";
    applyTransform(image);

    const startInteraction = (event, nextMode) => {
      event.preventDefault();
      activateTile(tile);
      mode = nextMode;
      tile.setPointerCapture(event.pointerId);
      startX = event.clientX;
      startY = event.clientY;
      baseX = Number(image.dataset.x || "0");
      baseY = Number(image.dataset.y || "0");
      baseScale = Number(image.dataset.scale || "1");
      baseRotate = Number(image.dataset.rotate || "0");

      const rect = tile.getBoundingClientRect();
      centerX = rect.left + rect.width / 2;
      centerY = rect.top + rect.height / 2;
      startAngle = Math.atan2(event.clientY - centerY, event.clientX - centerX) * 180 / Math.PI;
    };

    tile.addEventListener("pointerdown", (event) => {
      const control = event.target.closest("[data-action]");
      if (control) {
        startInteraction(event, control.dataset.action);
        return;
      }

      startInteraction(event, "move");
    });

    tile.addEventListener("pointermove", (event) => {
      if (!mode) return;

      if (mode === "move") {
        image.dataset.x = String(baseX + event.clientX - startX);
        image.dataset.y = String(baseY + event.clientY - startY);
      }

      if (mode === "zoom") {
        const delta = (startY - event.clientY) * 0.006;
        image.dataset.scale = String(Math.max(0.25, baseScale + delta));
      }

      if (mode === "rotate") {
        const angle = Math.atan2(event.clientY - centerY, event.clientX - centerX) * 180 / Math.PI;
        image.dataset.rotate = String(baseRotate + angle - startAngle);
      }

      applyTransform(image);
    });

    const stopInteraction = (event) => {
      if (!mode) return;
      mode = "";
      if (tile.hasPointerCapture(event.pointerId)) {
        tile.releasePointerCapture(event.pointerId);
      }
    };

    tile.addEventListener("pointerup", stopInteraction);
    tile.addEventListener("pointercancel", stopInteraction);
    tile.addEventListener("click", () => activateTile(tile));
  });
})();
