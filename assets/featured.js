// ZXN featured video: keeps data/site_config.json "featured_video" on the homepage.
// The markup is also in index.html (restored by update.py) so the player is in the served HTML.
// Turn off by setting featured_video.enabled to false, or featured_video to null.
(function () {
  const CONFIG = "data/site_config.json";
  const mount = document.getElementById("featured-video");
  if (!mount) return;

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function fill(v) {
    const title = v.title || "ZXN News video";
    const caption = v.caption || "";
    const src = v.src || "";
    const poster = v.poster || "";
    const typ = v.type || "video/mp4";
    const w = v.width ? String(v.width) : "1280";
    const h = v.height ? String(v.height) : "720";
    const posterAttr = poster ? ` poster="${esc(poster)}"` : "";
    mount.setAttribute("aria-label", title);
    mount.innerHTML =
      `<div class="featured-video-inner">` +
      `<h2 class="section-label">${esc(title)}</h2>` +
      `<div class="featured-video-player">` +
      `<video controls playsinline preload="metadata"${posterAttr} width="${esc(w)}" height="${esc(h)}">` +
      `<source src="${esc(src)}" type="${esc(typ)}">` +
      `Sorry, your browser cannot play this video.</video>` +
      `</div>` +
      (caption ? `<p class="featured-video-caption">${esc(caption)}</p>` : "") +
      `</div>`;
  }

  fetch(CONFIG, { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (cfg) {
      const v = cfg && cfg.featured_video;
      if (!v || v.enabled === false || !v.src) {
        mount.hidden = true;
        mount.innerHTML = "";
        return;
      }
      if (!mount.querySelector("video")) fill(v);
      mount.hidden = false;
      mount.removeAttribute("hidden");
    })
    .catch(function () { /* keep any server-rendered markup */ });
})();
