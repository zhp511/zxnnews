// ZXN holiday banner: renders data/site_config.json "holiday_banner" at the top of the homepage.
// Turn off by setting holiday_banner.enabled to false, or holiday_banner to null.
(function () {
  const CONFIG = "data/site_config.json";
  const mount = document.getElementById("holiday-banner");
  if (!mount) return;

  function show(cfg) {
    const b = cfg && cfg.holiday_banner;
    if (!b || b.enabled === false || !b.src) return;
    const alt = b.alt || "Holiday greeting from ZXN News";
    const w = b.width ? String(b.width) : "";
    const h = b.height ? String(b.height) : "";
    const fallback = b.src_fallback || b.src;
    const dims = (w ? ` width="${w}"` : "") + (h ? ` height="${h}"` : "");
    let media;
    if (b.src_fallback && b.src !== b.src_fallback) {
      const type = /\.webp$/i.test(b.src) ? "image/webp" : (/\.jpe?g$/i.test(b.src) ? "image/jpeg" : "");
      media = `<picture><source srcset="${esc(b.src)}"${type ? ` type="${type}"` : ""}><img src="${esc(fallback)}" alt="${esc(alt)}"${dims} decoding="async"></picture>`;
    } else {
      media = `<img src="${esc(b.src)}" alt="${esc(alt)}"${dims} decoding="async">`;
    }
    mount.innerHTML = `<div class="holiday-banner-inner">${media}</div>`;
    mount.hidden = false;
    mount.removeAttribute("hidden");
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  fetch(CONFIG, { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(show)
    .catch(function () { /* leave the banner hidden */ });
})();
