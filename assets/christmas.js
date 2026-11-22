// ZXN Christmas overlay: lights, light snow, a header accent, and a spoken "Merry Christmas!".
// Decorations use pointer-events: none. Turn off with "christmas_theme": false in data/site_config.json.
(function () {
  const CONFIG = "data/site_config.json";
  const PLAYED_KEY = "zxn_xmas_greeting_played";
  const COLORS = ["c-red", "c-green", "c-gold", "c-blue"];
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function el(tag, cls, attrs) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (attrs) Object.keys(attrs).forEach((k) => n.setAttribute(k, attrs[k]));
    return n;
  }

  function bulb(color, style) {
    const b = el("span", "zxn-xmas-bulb " + color);
    b.setAttribute("aria-hidden", "true");
    Object.assign(b.style, style);
    // 1.7–2.2s per cycle (well under 3 flashes/sec), staggered so they twinkle, not blink in unison.
    const dur = (1.7 + Math.random() * 0.5).toFixed(2) + "s";
    const delay = (-Math.random() * 2).toFixed(2) + "s";
    b.style.animationDuration = dur;
    b.style.animationDelay = delay;
    return b;
  }

  function buildLights() {
    const bar = el("div", "zxn-xmas-lights", { id: "zxn-xmas-lights", "aria-hidden": "true" });
    bar.appendChild(el("div", "zxn-xmas-wire"));
    const count = Math.max(18, Math.min(40, Math.round(window.innerWidth / 36)));
    for (let i = 0; i < count; i++) {
      const x = ((i + 0.5) / count) * 100;
      const hang = 2 + Math.sin(i * 0.9) * 3;
      bar.appendChild(bulb(COLORS[i % COLORS.length], { left: x + "%", top: 6 + hang + "px" }));
    }
    document.body.insertBefore(bar, document.body.firstChild);

    if (window.innerWidth >= 1100) {
      ["left", "right"].forEach((side) => {
        const col = el("div", "zxn-xmas-side " + side, { "aria-hidden": "true" });
        col.appendChild(el("div", "zxn-xmas-wire"));
        const n = 10;
        for (let i = 0; i < n; i++) {
          col.appendChild(bulb(COLORS[(i + (side === "right" ? 2 : 0)) % COLORS.length], {
            top: (6 + i * 8.5) + "%"
          }));
        }
        document.body.appendChild(col);
      });
    }
  }

  function buildSnow() {
    const layer = el("div", "zxn-xmas-snow", { id: "zxn-xmas-snow", "aria-hidden": "true" });
    const n = reduce ? 8 : 28;
    for (let i = 0; i < n; i++) {
      const f = el("span", "zxn-xmas-flake");
      const size = 3 + Math.random() * 5;
      f.style.left = (Math.random() * 100) + "%";
      f.style.width = size + "px";
      f.style.height = size + "px";
      f.style.setProperty("--dx", (Math.random() * 60 - 30) + "px");
      f.style.animationDuration = (reduce ? 36 : 10 + Math.random() * 12) + "s";
      f.style.animationDelay = (-Math.random() * 16) + "s";
      f.style.opacity = String(0.3 + Math.random() * 0.4);
      layer.appendChild(f);
    }
    document.body.appendChild(layer);
  }

  function buildHeaderAccent() {
    const brand = document.querySelector("header.masthead .brand");
    if (brand && !brand.querySelector(".zxn-xmas-accent")) {
      const accent = el("div", "zxn-xmas-accent");
      accent.textContent = "Merry Christmas from ZXN News";
      brand.appendChild(accent);
    }

    const btn = el("button", "zxn-xmas-speak", { type: "button", id: "zxn-xmas-speak" });
    btn.setAttribute("aria-label", "Play Merry Christmas greeting");
    btn.textContent = "🔊 Merry Christmas";
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      playGreeting(true);
    });

    const date = document.querySelector("header.masthead .mast-date");
    if (date) date.appendChild(btn);
    else {
      const inner = document.querySelector("header.masthead .mast-inner");
      if (inner) inner.appendChild(btn);
      else document.body.appendChild(btn);
    }
  }

  function makeAudio() {
    const audio = el("audio", "zxn-xmas-audio", { id: "zxn-xmas-audio", preload: "auto" });
    audio.setAttribute("playsinline", "");
    const ogg = el("source", "", { src: "assets/merry-christmas.ogg", type: "audio/ogg" });
    const mp3 = el("source", "", { src: "assets/merry-christmas.mp3", type: "audio/mpeg" });
    audio.appendChild(ogg);
    audio.appendChild(mp3);
    document.body.appendChild(audio);
    return audio;
  }

  function speakFallback() {
    try {
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance("Merry Christmas!");
      u.rate = 0.95;
      u.pitch = 1.05;
      u.lang = "en-US";
      window.speechSynthesis.speak(u);
    } catch (e) { /* ignore */ }
  }

  let audioEl, listening = false;

  function markPlayed() {
    try { sessionStorage.setItem(PLAYED_KEY, "1"); } catch (e) { /* ignore */ }
  }
  function alreadyPlayed() {
    try { return sessionStorage.getItem(PLAYED_KEY) === "1"; } catch (e) { return false; }
  }

  function playGreeting(force) {
    if (!force && alreadyPlayed()) return;
    const a = audioEl || (audioEl = document.getElementById("zxn-xmas-audio") || makeAudio());
    let usedFallback = false;
    const fail = function () {
      if (usedFallback) return;
      usedFallback = true;
      speakFallback();
    };
    a.onerror = fail;
    try {
      a.pause();
      a.currentTime = 0;
    } catch (e) { /* ignore */ }
    const p = a.play();
    if (p && typeof p.then === "function") {
      p.then(function () { markPlayed(); }).catch(fail);
    } else {
      markPlayed();
    }
    if (force) markPlayed();
  }

  function armFirstGesture() {
    if (alreadyPlayed() || listening) return;
    listening = true;
    const once = function () {
      document.removeEventListener("pointerdown", once, true);
      document.removeEventListener("keydown", once, true);
      listening = false;
      playGreeting(false);
    };
    document.addEventListener("pointerdown", once, true);
    document.addEventListener("keydown", once, true);
  }

  function start() {
    if (document.body.classList.contains("zxn-xmas")) return;
    document.body.classList.add("zxn-xmas");
    buildLights();
    buildSnow();
    buildHeaderAccent();
    audioEl = makeAudio();
    armFirstGesture();
  }

  function init() {
    fetch(CONFIG, { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (cfg) {
        // On unless explicitly turned off, so a missing flag still shows the seasonal overlay.
        if (cfg && cfg.christmas_theme === false) return;
        start();
      })
      .catch(function () { start(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
