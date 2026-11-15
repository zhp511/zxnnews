// ZXN X Spaces: styled in-page player. Audio is not embedded (X does not allow it);
// the Listen / Replay button opens the official Space on X.
(function () {
  const el = document.getElementById("zxn-spaces");
  if (!el) return;
  const root = document.getElementById("sp-root");
  const updatedEl = document.getElementById("sp-updated");
  const POLL_MS = 60 * 1000;
  const CT = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago", weekday: "short", month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit"
  });
  const CT_TIME = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago", hour: "numeric", minute: "2-digit"
  });
  const CT_DAY = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago", year: "numeric", month: "numeric", day: "numeric"
  });
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  let data = null;
  let selectedId = null;

  function when(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const sameDay = CT_DAY.format(d) === CT_DAY.format(new Date());
    return (sameDay ? CT_TIME.format(d) : CT.format(d)) + " CT";
  }

  function listenLabel(s) {
    if (s.state === "live") return "▶ Listen on 𝕏";
    if (s.state === "scheduled") return "Open on 𝕏";
    return "▶ Replay on 𝕏";
  }

  function listeners(s) {
    const n = Number(s.participant_count || 0);
    const num = n.toLocaleString("en-US");
    if (s.state === "live") return n ? num + " listening" : "";
    if (s.state === "ended") return n ? num + " listened" : "";
    const sub = Number(s.subscriber_count || 0);
    return sub ? sub.toLocaleString("en-US") + " subscribed" : "";
  }

  function timeLine(s) {
    if (s.state === "live" && s.started_at) return "Started " + when(s.started_at);
    if (s.state === "scheduled" && s.scheduled_start) return "Starts " + when(s.scheduled_start);
    if (s.state === "ended" && s.ended_at) return "Ended " + when(s.ended_at);
    if (s.started_at) return "Started " + when(s.started_at);
    return "";
  }

  function featured() {
    const own = (data && data.own) || [];
    if (selectedId && own.some((s) => s.id === selectedId)) return own.find((s) => s.id === selectedId);
    return own.find((s) => s.state === "live") || own.find((s) => s.state === "scheduled") || own[0] || null;
  }

  function render() {
    if (!data || !root) return;
    const own = data.own || [];
    const also = data.also_live || [];
    const host = data.creator || {};
    const feat = featured();
    selectedId = feat ? feat.id : null;
    const live = !!(data.host_live);

    if (updatedEl) {
      const t = data.searched_at || data.built_at;
      updatedEl.textContent = t ? "Updated " + when(t) : "";
    }

    let html = "";
    if (live && feat && feat.state === "live") {
      html += `<div class="sp-livebar" role="status"><span class="sp-dot" aria-hidden="true"></span><b>LIVE</b>
        <span>@${esc(host.username || "zxnbluehandus")} is hosting a Space</span></div>`;
    }

    if (feat) {
      const k = feat.state === "live" ? "live" : feat.state === "scheduled" ? "scheduled" : "ended";
      const kicker = feat.state === "live" ? "● Live" : feat.state === "scheduled" ? "Scheduled" : "Ended";
      const meta = [listeners(feat), timeLine(feat), feat.is_ticketed ? "Ticketed" : ""].filter(Boolean);
      const av = feat.host && feat.host.avatar ? feat.host.avatar : (host.avatar || "images/avatar.jpg");
      const hname = (feat.host && feat.host.name) || host.name || "ZXN";
      const huser = (feat.host && feat.host.username) || host.username || "zxnbluehandus";
      html += `<div class="sp-player${feat.state === "live" ? " is-live" : ""}">
        <div class="sp-eq" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
        <div class="sp-main">
          <span class="sp-kicker ${k}">${kicker}</span>
          <h3>${esc(feat.title)}</h3>
          <div class="sp-host">
            <img src="${esc(av)}" alt="" width="40" height="40">
            <div class="sp-who"><b>${esc(hname)}</b><a href="https://x.com/${esc(huser)}" target="_blank" rel="noopener">@${esc(huser)}</a></div>
          </div>
          <div class="sp-meta">${meta.map((m) => `<span>${esc(m)}</span>`).join("")}</div>
          <div class="sp-actions-row">
            <a class="sp-listen" href="${esc(feat.url)}" target="_blank" rel="noopener">${listenLabel(feat)}</a>
            ${feat.download && feat.download.url ? `<a class="sp-download" href="${esc(feat.download.url)}" download="${esc(feat.download.filename || "zxn-space.mp3")}">Download MP3</a>` : ""}
          </div>
          <p class="sp-note">${feat.state === "ended"
            ? "If X saved a recording, it will play on 𝕏. A Download MP3 button appears only when @zxnbluehandus has an owner-made recording on file."
            : "Spaces audio plays on 𝕏. This page does not embed or rip the stream."}</p>
        </div>
      </div>`;
    } else {
      const av = host.avatar || "images/avatar.jpg";
      const msg = data.empty_message || "No live Spaces right now — follow @zxnbluehandus";
      html += `<div class="sp-player is-empty">
        <div class="sp-eq" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
        <div class="sp-main sp-empty-copy">
          <span class="sp-kicker">X Spaces</span>
          <h3>${esc(msg)}</h3>
          <div class="sp-host">
            <img src="${esc(av)}" alt="" width="40" height="40">
            <div class="sp-who"><b>${esc(host.name || "ZXN")}</b><a href="https://x.com/${esc(host.username || "zxnbluehandus")}" target="_blank" rel="noopener">@${esc(host.username || "zxnbluehandus")}</a></div>
          </div>
          <p>When @${esc(host.username || "zxnbluehandus")} goes live or schedules a Space, it will show up here with a Listen on 𝕏 button.</p>
          <a class="spx-follow" href="https://x.com/${esc(host.username || "zxnbluehandus")}" target="_blank" rel="noopener">Follow @${esc(host.username || "zxnbluehandus")} on 𝕏</a>
        </div>
      </div>`;
    }

    if (own.length > 1) {
      html += `<div class="sp-own" role="listbox" aria-label="Spaces from @${esc(host.username || "zxnbluehandus")}">`;
      for (const s of own) {
        const meta = [s.state === "live" ? "LIVE" : s.state === "scheduled" ? "Scheduled" : "Ended", listeners(s), timeLine(s)].filter(Boolean);
        html += `<button type="button" role="option" data-id="${esc(s.id)}" aria-selected="${s.id === selectedId}">
          <span class="sp-chip ${esc(s.state)}">${s.state === "live" ? "LIVE" : s.state === "scheduled" ? "Upcoming" : "Ended"}</span>
          <b>${esc(s.title)}</b>
          <em>${esc(meta.slice(1).join(" · "))}</em>
        </button>`;
      }
      html += `</div>`;
    }

    if (also.length) {
      html += `<div class="sp-also">
        <h3>${esc(data.also_label || "Also live on 𝕏 · news & politics")}</h3>
        <p class="sp-also-note">These are not ZXN Spaces. They are live rooms on 𝕏 matching a news and politics search, shown as X listed them.</p>
        <div class="sp-also-list">`;
      for (const s of also) {
        const huser = (s.host && s.host.username) || "";
        const hname = (s.host && s.host.name) || huser;
        const meta = [listeners(s), timeLine(s)].filter(Boolean);
        html += `<article class="sp-also-card">
          <span class="sp-chip live">LIVE</span>
          <b>${esc(s.title)}</b>
          <div class="sp-ahost">${esc(hname)}${huser ? ` · <a href="https://x.com/${esc(huser)}" target="_blank" rel="noopener">@${esc(huser)}</a>` : ""}</div>
          <div class="sp-ameta">${esc(meta.join(" · "))}</div>
          <a class="sp-listen" href="${esc(s.url)}" target="_blank" rel="noopener">▶ Listen on 𝕏</a>
        </article>`;
      }
      html += `</div></div>`;
    }

    html += `<p class="sp-footnote">X does not allow embedding Spaces audio here. Listen and replay open the official Space on 𝕏. A recording is only available if X still has one.</p>`;
    root.innerHTML = html;

    root.querySelectorAll(".sp-own button").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectedId = btn.getAttribute("data-id");
        render();
        const player = root.querySelector(".sp-player");
        if (player) player.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    });
  }

  async function poll() {
    try {
      const r = await fetch("data/spaces.json?t=" + Date.now(), { cache: "no-store" });
      if (!r.ok) throw new Error("spaces.json " + r.status);
      data = await r.json();
      // If the previously selected own Space disappeared, fall back.
      const ids = new Set((data.own || []).map((s) => s.id));
      if (selectedId && !ids.has(selectedId)) selectedId = null;
      render();
    } catch (e) {
      if (!data && root) {
        root.innerHTML = `<div class="sp-player is-empty"><div class="sp-eq" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
          <div class="sp-main sp-empty-copy"><span class="sp-kicker">X Spaces</span>
          <h3>No live Spaces right now — follow @zxnbluehandus</h3>
          <a class="spx-follow" href="https://x.com/zxnbluehandus" target="_blank" rel="noopener">Follow @zxnbluehandus on 𝕏</a></div></div>`;
      }
    }
  }
  poll();
  setInterval(poll, POLL_MS);
})();
