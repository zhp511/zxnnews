#!/usr/bin/env python3
"""
Build data/spaces.json (the X Spaces section + in-page player) from SAVED x-tool output.
Nothing is invented: titles, hosts, listener counts and times are copied as X returned them.
X does not allow embedding Spaces audio; the page links to the official Space on X
(https://x.com/i/spaces/<id>). Do not scrape or rip audio.

HOW THE REFRESH ROUTINE SHOULD FETCH (2 X reads; do not resume a paused routine from here)
------------------------------------------------------------------------------------------
1. get_spaces_by_creator_ids
     user_ids=["2011476148178599939"]
     expansions=creator_id,host_ids,speaker_ids,topic_ids
     space.fields=created_at,ended_at,id,is_ticketed,lang,participant_count,scheduled_start,started_at,state,subscriber_count,title,updated_at
     user.fields=name,username,profile_image_url,verified,verified_type,public_metrics
     topic.fields=id,name,description
   Save as data/spaces_raw/creator.json:
     {"fetched_at": ISO, "tool": "get_spaces_by_creator_ids", "args": {...},
      "data": [...], "includes": {"users": [...], "topics": [...]}, "meta": {...}}
   (A raw API response with data/includes/meta is accepted too. Empty data is fine.)

2. search_spaces
     query="politics"
     state=live
     max_results=15
     (same expansions / space.fields / user.fields / topic.fields as above)
   Save as data/spaces_raw/search.json, same wrapper shape.
   Optional extra searches: data/spaces_raw/search_*.json, merged and filtered.

3. Run:  python3 spaces.py   -> data/spaces.json
   Publish data/spaces.json (and data/spaces_raw/) with the rest of the site.

Rules: own Spaces by @zxnbluehandus (live, scheduled, and ended if the API returned
them) are listed first and drive the player and the red LIVE badge. Other live Spaces
are clearly labeled "Also live on X · news & politics". English; politics/news keywords
required for the also-live list; sports/adult/crypto terms and profanity excluded;
handles in site_config.json "xlive_block_handles" are dropped; one also-live Space per
account; max 5, US-politics ranked first, at least ALSO_MIN_LISTENERS listening.

OWNER RECORDINGS / DOWNLOAD MP3
-------------------------------
Only @zxnbluehandus's own Spaces ever get a Download MP3 button. Source files must
already be recordings he owns (not ripped from someone else's Space, and not
scraped from x.com). Places the refresh should look when they are reachable:
  - media/spaces/<space-id>.webm or .mp3 in this repo
  - Music\\ZXN Space Recordings\\*.webm on his Windows PC (copy in, then convert)
  - A Google Drive folder of his own Space recordings, if one is present
Convert with ffmpeg to media/spaces/<space-id>.mp3, keep each file under ~50MB,
or put a larger file on Drive and do not commit it. Other people's also-live
Spaces stay 'Listen on X' only.
If the creator has no Spaces, the page shows: "No live Spaces right now — follow @zxnbluehandus".
"""
import datetime, html, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(ROOT, "data", "spaces_raw")
CREATOR_RAW = os.path.join(RAW_DIR, "creator.json")
OUT = os.path.join(ROOT, "data", "spaces.json")
MEDIA = os.path.join(ROOT, "media", "spaces")
MAX_MP3_BYTES = 50 * 1024 * 1024  # GitHub/Pages soft cap per file
CFG = os.path.join(ROOT, "data", "site_config.json")
POSTS = os.path.join(ROOT, "data", "posts.json")
OWN_ID = "2011476148178599939"
OWN = "zxnbluehandus"
ALSO_MAX = 5
ALSO_MIN_LISTENERS = 5
NEWS = re.compile(
    r"\b(news|breaking|politic\w*|geopolitic\w*|election\w*|ballot|vote|trump|president\w*|"
    r"congress|senate|debate\w*|white house|america\w*|maga|governor|campaign|democrat\w*|"
    r"republican\w*|midterm\w*|capitol|house hearing|supreme court)\b",
    re.I,
)
BLOCK = re.compile(
    r"\b(nfl|mlb|nba|nhl|ipl|cricket|postgame|pregame|football|baseball|soccer|mls|ncaa|"
    r"ufc|onlyfans|of live|nsfw|18\+|porn|sex|crypto|nft|bitcoin|memecoin|altcoin|"
    r"giveaway|casino|betting|watchalong)\b",
    re.I,
)
CASHTAG = re.compile(r"(?<![\w$])\$[A-Z]{2,6}\b|(?i:\b(xrp|bitcoin|btc|ethereum|solana|dogecoin|memecoin|altcoin|nfts?)\b)")
PROFANE = re.compile(r"(f+u+c+k|sh[i1]t\b|bitch|cunt|whore|slut|motherf|\bdick\b|\bcock\b|\bpussy\b|\bfag)", re.I)
US = re.compile(
    r"\b(trump|election\w*|ballot|vote|congress|senate|white house|america\w*|maga|"
    r"supreme court|governor|midterm\w*|capitol)\b",
    re.I,
)


def load_raw(path):
    if not os.path.exists(path):
        return {"data": [], "includes": {}, "fetched_at": None}
    d = json.load(open(path, encoding="utf-8"))
    if "data" not in d and "spaces" in d:
        d = {**d, "data": d["spaces"]}
    return d


def users_of(d):
    inc = d.get("includes") or {}
    out = {u["id"]: u for u in (inc.get("users") or d.get("users") or [])}
    return out


def topics_of(d):
    inc = d.get("includes") or {}
    return {t["id"]: t for t in (inc.get("topics") or d.get("topics") or [])}


def avatar(url):
    if not url:
        return None
    return url.replace("_normal.", "_400x400.").replace("_normal.", "_bigger.")


def host_from(space, users, fallback=None):
    cid = space.get("creator_id") or (space.get("host_ids") or [None])[0]
    u = users.get(cid) or fallback or {}
    handle = u.get("username") or ""
    return {
        "id": u.get("id") or cid,
        "name": u.get("name") or handle or "X user",
        "username": handle,
        "avatar": avatar(u.get("profile_image_url")),
        "verified_type": u.get("verified_type"),
    }


def shape(space, users, topics, source, fallback_host=None):
    topic_names = []
    for tid in space.get("topic_ids") or []:
        t = topics.get(tid) or {}
        if t.get("name"):
            topic_names.append(t["name"])
    sid = space.get("id")
    return {
        "id": sid,
        "title": html.unescape((space.get("title") or "").strip()) or "X Space",
        "state": space.get("state") or "",
        "url": f"https://x.com/i/spaces/{sid}" if sid else None,
        "started_at": space.get("started_at"),
        "scheduled_start": space.get("scheduled_start"),
        "ended_at": space.get("ended_at"),
        "created_at": space.get("created_at"),
        "participant_count": space.get("participant_count") or 0,
        "subscriber_count": space.get("subscriber_count") or 0,
        "is_ticketed": bool(space.get("is_ticketed")),
        "lang": space.get("lang") or "",
        "host": host_from(space, users, fallback_host),
        "topics": topic_names,
        "source": source,
    }


def own_fallback_host():
    host = {"id": OWN_ID, "name": "ZXN “ we are bluehand ” AND patriot one network",
            "username": OWN, "avatar": "images/avatar.jpg", "verified_type": None}
    if os.path.exists(POSTS):
        u = (json.load(open(POSTS, encoding="utf-8")).get("user") or {})
        if u:
            host["name"] = u.get("name") or host["name"]
            host["username"] = u.get("username") or OWN
            host["id"] = u.get("id") or OWN_ID
            if u.get("avatar_local"):
                host["avatar"] = u["avatar_local"]
            elif u.get("profile_image_url"):
                host["avatar"] = avatar(u["profile_image_url"])
    return host


def also_ok(space, handle, blocked, seen_auth, seen_id):
    if not handle or handle.lower() == OWN or handle.lower() in blocked:
        return False
    if handle.lower() in seen_auth or space.get("id") in seen_id:
        return False
    if (space.get("lang") or "en").lower() not in ("en", "en-gb", "en-us", ""):
        return False
    title = html.unescape((space.get("title") or "").strip())
    if re.search(r"[\u0900-\u097F]", title):
        return False
    if BLOCK.search(title) or CASHTAG.search(title) or PROFANE.search(title) or not NEWS.search(title):
        return False
    if (space.get("participant_count") or 0) < ALSO_MIN_LISTENERS:
        return False
    return True



def attach_own_downloads(own):
    """Attach a Download MP3 link only for the creator's own Spaces when a
    recording he owns is already on disk (media/spaces/<space-id>.mp3).
    Optional source .webm files in the same folder are converted with ffmpeg.
    Never attaches downloads to also-live (other people's) Spaces.
    """
    os.makedirs(MEDIA, exist_ok=True)
    # Convert any owner .webm next to an id-named file.
    for name in os.listdir(MEDIA):
        if not name.lower().endswith(".webm"):
            continue
        src = os.path.join(MEDIA, name)
        dest = os.path.splitext(src)[0] + ".mp3"
        if os.path.isfile(dest) and os.path.getsize(dest) > 0:
            continue
        import shutil, subprocess
        if not shutil.which("ffmpeg"):
            print(f"  ! ffmpeg missing; left {name} unconverted")
            continue
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", src, "-vn", "-ac", "2", "-ar", "44100", "-b:a", "128k", dest],
                check=True, capture_output=True,
            )
            print(f"  converted {name} -> {os.path.basename(dest)}")
        except subprocess.CalledProcessError as e:
            print(f"  ! ffmpeg failed on {name}: {e}")
    for s in own:
        mp3 = os.path.join(MEDIA, f"{s['id']}.mp3")
        if not os.path.isfile(mp3) or os.path.getsize(mp3) <= 0:
            continue
        size = os.path.getsize(mp3)
        if size > MAX_MP3_BYTES:
            print(f"  ! {s['id']}.mp3 is {size} bytes (>50MB); not attaching to the repo copy")
            s["download_skipped"] = "mp3 exceeds 50MB GitHub/Pages limit; host on Drive instead"
            continue
        s["download"] = {
            "url": f"media/spaces/{s['id']}.mp3",
            "filename": f"zxn-space-{s['id']}.mp3",
            "bytes": size,
            "source": "owner-recording",
        }


def main():
    cfg = json.load(open(CFG, encoding="utf-8")) if os.path.exists(CFG) else {}
    blocked = {h.lower().lstrip("@") for h in (cfg.get("xlive_block_handles") or [])}
    fallback = own_fallback_host()

    creator = load_raw(CREATOR_RAW)
    own_users = users_of(creator)
    own_topics = topics_of(creator)
    own = []
    seen_own = set()
    for sp in creator.get("data") or []:
        if not sp.get("id") or sp["id"] in seen_own:
            continue
        # Keep spaces created by the official account (creator_id or first host).
        cid = sp.get("creator_id") or ""
        hosts = sp.get("host_ids") or []
        hu = own_users.get(cid) or (own_users.get(hosts[0]) if hosts else {})
        handle = (hu.get("username") or "").lower()
        if cid and cid != OWN_ID and handle and handle != OWN and OWN_ID not in hosts:
            continue
        seen_own.add(sp["id"])
        own.append(shape(sp, own_users, own_topics, "own", fallback))

    state_rank = {"live": 0, "scheduled": 1, "ended": 2}
    own.sort(key=lambda s: (state_rank.get(s["state"], 9), -(s.get("participant_count") or 0)))

    also, seen_auth, seen_id = [], set(), set(seen_own)
    fetched_search = []
    search_files = []
    if os.path.isdir(RAW_DIR):
        for name in sorted(os.listdir(RAW_DIR)):
            if name == "search.json" or (name.startswith("search_") and name.endswith(".json")):
                search_files.append(os.path.join(RAW_DIR, name))
    picked = []
    for path in search_files:
        raw = load_raw(path)
        fetched_search.append(raw.get("fetched_at"))
        users, topics = users_of(raw), topics_of(raw)
        for sp in raw.get("data") or []:
            if (sp.get("state") or "") != "live":
                continue
            u = users.get(sp.get("creator_id") or (sp.get("host_ids") or [None])[0]) or {}
            handle = u.get("username") or ""
            if not also_ok(sp, handle, blocked, seen_auth, seen_id):
                continue
            title = html.unescape((sp.get("title") or "").strip())
            seen_auth.add(handle.lower())
            seen_id.add(sp["id"])
            item = shape(sp, users, topics, "search")
            item["_rank"] = (1 if US.search(title) else 0, item["participant_count"] or 0)
            picked.append(item)
    picked.sort(key=lambda p: p["_rank"], reverse=True)
    for p in picked[:ALSO_MAX]:
        p.pop("_rank")
        also.append(p)

    now = datetime.datetime.now(datetime.timezone.utc)
    times = [creator.get("fetched_at"), *[t for t in fetched_search if t]]
    host_live = any(s["state"] == "live" for s in own)
    out = {
        "built_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "searched_at": next((t for t in times if t), None),
        "creator": {
            "id": fallback["id"],
            "username": fallback["username"],
            "name": fallback["name"],
            "avatar": fallback["avatar"],
        },
        "host_live": host_live,
        "own": own,
        "also_live": also,
        "also_label": "Also live on 𝕏 · news & politics",
        "empty_message": "No live Spaces right now — follow @zxnbluehandus",
        "note": "X does not allow embedding Spaces audio. Listen and replay open the official Space on X. Recordings are only available if X still has one.",
        "download_policy": "Download MP3 is only offered for @zxnbluehandus's own Spaces when an owner-made recording is already on file (media/spaces/<id>.mp3, converted from a .webm he owns such as Music\\ZXN Space Recordings). Other people's Spaces are Listen on X only — never ripped.",
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(own)} own, {len(also)} also-live, host_live={host_live}")
    for s in own:
        print(f"  own @{s['host']['username']} [{s['state']}]: {s['title'][:70]!r}")
    for s in also:
        print(f"  also @{s['host']['username']}: {s['title'][:70]!r}")


if __name__ == "__main__":
    main()
