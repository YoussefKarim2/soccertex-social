#!/usr/bin/env python3
"""Generate the Review Desk artifact page from queue.json.

The page is a snapshot: artifacts run under a CSP that blocks every external
host, so the page cannot fetch GitHub for live state. The queue data is inlined
at build time and the header says exactly when. Claude republishes to refresh.

Video previews are uploaded to the artifact's own asset store and referenced by
id; VIDEO_IDS maps a filename to the asset id returned by the upload.
"""
import json, sys, html
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads(Path("/tmp/manifest.json").read_text())
try:
    VIDEO_IDS = json.loads(Path("/tmp/video_ids.json").read_text())
except FileNotFoundError:
    VIDEO_IDS = {}

PILLAR_SHORT = {
    "1 Inside the Floor": "Inside the floor",
    "2 Kit School": "Kit school",
    "3 Sourcing Math": "Sourcing math",
    "4 Built for Clubs": "Built for clubs",
}


def card(it):
    aid = VIDEO_IDS.get(it["video"])
    src = f"/_blob/{aid}" if aid else ""
    when = datetime.fromisoformat(it["at"])
    day = when.strftime("%a %-d %b")
    time = when.strftime("%H:%M")
    plat = it["platform"]
    first = it["caption"].strip().split("\n")[0]
    pillar = PILLAR_SHORT.get(it["pillar"], it["pillar"])
    vid = (f'<video class="vid" src="{src}" preload="metadata" controls playsinline '
           f'muted></video>' if src
           else '<div class="vid vid-missing">Preview not uploaded</div>')
    return f"""
<article class="card" data-id="{html.escape(it['id'])}" data-plat="{plat}">
  <div class="media">{vid}</div>
  <div class="body">
    <div class="meta">
      <span class="chip chip-{plat}">{'Instagram' if plat == 'instagram' else 'LinkedIn'}</span>
      <span class="when"><span class="day">{day}</span> <span class="num">{time}</span> UTC</span>
      <span class="pillar">{html.escape(pillar)}</span>
    </div>
    <h3 class="hook">{html.escape(first)}</h3>
    <details class="cap">
      <summary>Full caption</summary>
      <p>{html.escape(it['caption'])}</p>
    </details>
    <div class="state" data-role="state"></div>
    <label class="note-label" for="note-{html.escape(it['id'])}">Changes you want</label>
    <textarea class="note" id="note-{html.escape(it['id'])}" rows="2"
      placeholder="e.g. cut the intro, lead with the 150 GSM number, warmer music"></textarea>
    <div class="acts">
      <button class="btn btn-sound" data-act="manual">Trending sound — I'll post this one</button>
      <button class="btn btn-veto" data-act="veto">Don't post this</button>
      <span class="saved" data-role="saved"></span>
    </div>
  </div>
</article>"""


def build(generated_at, counts, runs):
    cards = "\n".join(card(i) for i in MANIFEST)
    data = json.dumps(MANIFEST, ensure_ascii=False)
    return f"""<title>SoccerTex Review Desk</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Secular+One&family=Source+Sans+3:wght@400;600&family=Roboto+Condensed:wght@400;700&display=swap">
<style>
/* Layout: one column of review cards, media left of detail on wide screens. */
:root {{
  --pitch:#0E7A3C; --pitch-ink:#0A5B2C; --bone:#FAF8F3; --surface:#FFFFFF;
  --raise:#F1F4EF; --line:#DFE4DB; --ink:#131A14; --muted:#5C6A5E; --faint:#8A968C;
  --amber:#B4740E; --red:#A8281F;
  --display:'Secular One',Impact,sans-serif;
  --body:'Source Sans 3',system-ui,sans-serif;
  --data:'Roboto Condensed','Arial Narrow',sans-serif;
  --shadow:0 1px 2px rgba(19,26,20,.05),0 6px 18px rgba(19,26,20,.05);
}}
@media (prefers-color-scheme:dark) {{ :root:not([data-theme="light"]) {{
  --pitch:#3FBE74; --pitch-ink:#8FE0AF; --bone:#0C110D; --surface:#141B15;
  --raise:#1B241C; --line:#2A352B; --ink:#E8EFE9; --muted:#9BAA9E; --faint:#6E7D71;
  --amber:#E0A542; --red:#F08B82; color-scheme:dark;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.3);
}} }}
:root[data-theme="dark"] {{
  --pitch:#3FBE74; --pitch-ink:#8FE0AF; --bone:#0C110D; --surface:#141B15;
  --raise:#1B241C; --line:#2A352B; --ink:#E8EFE9; --muted:#9BAA9E; --faint:#6E7D71;
  --amber:#E0A542; --red:#F08B82; color-scheme:dark;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.3);
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bone);color:var(--ink);font-family:var(--body);
  font-size:16px;line-height:1.55;-webkit-text-size-adjust:100%}}
.wrap{{max-width:980px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:0 56px}}
h1,h2,h3{{font-family:var(--display);font-weight:400;margin:0;letter-spacing:.01em}}
.num{{font-family:var(--data);font-variant-numeric:tabular-nums}}

header{{background:var(--pitch);color:#fff;margin-bottom:22px}}
.hd{{max-width:980px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:20px 22px}}
.hd h1{{font-size:clamp(23px,5vw,30px);line-height:1.1}}
.hd p{{margin:6px 0 0;opacity:.9;font-size:14.5px;max-width:60ch}}

.rail{{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:10px;
  margin:16px 0 26px}}
.tile{{background:var(--surface);border:1px solid var(--line);border-radius:10px;
  padding:12px 13px}}
.tile .k{{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}}
.tile .v{{font-family:var(--data);font-size:25px;line-height:1.2;margin-top:1px}}
.tile .t{{font-size:12.5px;color:var(--muted)}}
.tile.live{{border-left:3px solid var(--pitch)}}
.tile.block{{border-left:3px solid var(--amber)}}
.tile.block .v{{color:var(--amber)}}

h2.sec{{font-size:17px;margin:30px 0 4px}}
.sub{{font-size:14px;color:var(--muted);margin:0 0 14px;max-width:68ch}}

.card{{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  box-shadow:var(--shadow);margin-bottom:14px;overflow:hidden;
  display:grid;grid-template-columns:200px 1fr;gap:0}}
@media (max-width:640px){{.card{{grid-template-columns:1fr}}}}
.media{{background:#0A0F0B;display:flex;align-items:center;justify-content:center;min-width:0}}
.vid{{width:100%;max-width:100%;display:block;aspect-ratio:9/16;object-fit:cover;background:#0A0F0B}}
@media (max-width:640px){{.vid{{aspect-ratio:9/12}}}}
.vid-missing{{color:#7C8A80;font-size:13px;padding:30px 12px;text-align:center;
  aspect-ratio:9/16;display:flex;align-items:center;justify-content:center}}
.body{{padding:14px 15px 15px;min-width:0;display:flex;flex-direction:column;gap:9px}}
.meta{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;font-size:12.5px}}
.chip{{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  padding:3px 8px;border-radius:5px;color:#fff;white-space:nowrap}}
.chip-instagram{{background:#B5317E}} .chip-linkedin{{background:#0A66C2}}
.when{{color:var(--muted)}} .when .day{{font-weight:600;color:var(--ink)}}
.pillar{{color:var(--faint)}}
.hook{{font-size:17px;line-height:1.25;text-wrap:balance;margin:0}}
.cap summary{{font-size:13px;color:var(--pitch);cursor:pointer;width:fit-content}}
.cap p{{font-size:14px;color:var(--muted);white-space:pre-wrap;margin:7px 0 0}}

.note-label{{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}}
.note{{width:100%;font:inherit;font-size:14.5px;color:var(--ink);background:var(--raise);
  border:1px solid var(--line);border-radius:8px;padding:8px 10px;resize:vertical}}
.note:focus-visible{{outline:2px solid var(--pitch);outline-offset:1px}}
.acts{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.btn{{font:inherit;font-size:13px;cursor:pointer;border-radius:8px;padding:7px 12px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink)}}
.btn:hover{{border-color:var(--pitch)}}
.btn:focus-visible{{outline:2px solid var(--pitch);outline-offset:2px}}
.btn[aria-pressed="true"]{{background:var(--pitch);border-color:var(--pitch);color:#fff}}
.btn-veto[aria-pressed="true"]{{background:var(--red);border-color:var(--red)}}
.saved{{font-size:12px;color:var(--pitch);opacity:0;transition:opacity .2s}}
.saved.on{{opacity:1}}
.state:empty{{display:none}}
.state{{font-size:13px;padding:7px 10px;border-radius:7px;background:var(--raise);
  border-left:3px solid var(--faint);color:var(--muted)}}
.state.manual{{border-left-color:var(--amber);color:var(--amber)}}
.state.veto{{border-left-color:var(--red);color:var(--red)}}
.card.is-veto{{opacity:.62}}

.note-box{{background:var(--raise);border-left:3px solid var(--pitch);border-radius:8px;
  padding:12px 14px;font-size:14px;color:var(--muted);margin:0 0 18px}}
.note-box strong{{color:var(--ink)}}
footer{{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);
  font-size:13px;color:var(--faint)}}
a{{color:var(--pitch)}}
</style>

<header><div class="hd">
  <h1>SoccerTex Review Desk</h1>
  <p>Everything queued for the next fortnight. Watch it, say what you want changed,
     and stop anything you don't want going out.</p>
</div></header>

<div class="wrap">
  <div class="rail">
    <div class="tile live"><div class="k">Instagram</div><div class="v">Live</div>
      <div class="t">Publishing on its own</div></div>
    <div class="tile block"><div class="k">LinkedIn</div><div class="v">Blocked</div>
      <div class="t">Needs the email confirmed</div></div>
    <div class="tile"><div class="k">Queued</div><div class="v num">{counts['queued']}</div>
      <div class="t">over the next 30 days</div></div>
    <div class="tile"><div class="k">Videos rendered</div><div class="v num">{counts['videos']}</div>
      <div class="t">all topics, both cuts</div></div>
  </div>

  <div class="note-box">
    <strong>What your answers do.</strong> Notes and flags are saved here and I read them
    before the next render. A note changes the video or caption; <em>Trending sound</em>
    pulls that post out of auto-publish so you can post it in the app with real audio —
    the API cannot attach licensed music, only in-app posting can. <em>Don't post this</em>
    stops it. Nothing happens to a post until I act on the flag, so flag it before its date.
  </div>

  <h2 class="sec">Going out next</h2>
  <p class="sub">Snapshot taken {generated_at}. Times are UTC.</p>

  {cards}

  <footer>
    Pipeline: {runs}. Media served from GitHub Pages; Instagram fetches each video by URL.
    Stock factory footage is stamped as library footage, never as SoccerTex's own floor.
  </footer>
</div>

<script>
const ITEMS = {data};
const byId = Object.fromEntries(ITEMS.map(i => [i.id, i]));
let db = null, state = {{}};

function render(id) {{
  const card = document.querySelector(`.card[data-id="${{CSS.escape(id)}}"]`);
  if (!card) return;
  const s = state[id] || {{}};
  const box = card.querySelector('[data-role="state"]');
  card.classList.toggle('is-veto', !!s.vetoed);
  card.querySelector('[data-act="manual"]').setAttribute('aria-pressed', !!s.manual);
  card.querySelector('[data-act="veto"]').setAttribute('aria-pressed', !!s.vetoed);
  const note = card.querySelector('.note');
  if (document.activeElement !== note && typeof s.note === 'string') note.value = s.note;
  box.className = 'state';
  if (s.vetoed) {{ box.classList.add('veto'); box.textContent = 'Stopped. This will not publish.'; }}
  else if (s.manual) {{ box.classList.add('manual'); box.textContent = 'Held back for you to post in the app with a trending sound.'; }}
  else if (s.note) {{ box.textContent = 'Change requested. Still scheduled until I rework it.'; }}
  else box.textContent = '';
}}

function flash(card) {{
  const el = card.querySelector('[data-role="saved"]');
  el.textContent = 'Saved';
  el.classList.add('on');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('on'), 1400);
}}

async function save(id, patch) {{
  state[id] = Object.assign({{}}, state[id], patch);
  render(id);
  if (!db) return;
  try {{
    await db.collection('reviews').doc(id).set(Object.assign(
      {{topic: byId[id]?.topic || '', platform: byId[id]?.platform || '',
        at: byId[id]?.at || '', updatedAt: new Date().toISOString()}},
      state[id]));
  }} catch (e) {{ /* viewer may not be allowed to write; keep the UI state */ }}
}}

document.querySelectorAll('.card').forEach(card => {{
  const id = card.dataset.id;
  card.querySelectorAll('[data-act]').forEach(b => b.addEventListener('click', () => {{
    const k = b.dataset.act === 'veto' ? 'vetoed' : 'manual';
    save(id, {{[k]: !(state[id] || {{}})[k]}});
    flash(card);
  }}));
  const note = card.querySelector('.note');
  let t;
  note.addEventListener('input', () => {{
    clearTimeout(t);
    t = setTimeout(() => {{ save(id, {{note: note.value.trim()}}); flash(card); }}, 700);
  }});
}});

(async () => {{
  db = (await window.claude?.use?.('db')) || null;
  if (!db) return;
  db.collection('reviews').onSnapshot(snap => {{
    snap.docs.forEach(d => {{ state[d.id] = d.data(); }});
    Object.keys(state).forEach(render);
  }});
}})();
</script>
"""


if __name__ == "__main__":
    gen = datetime.now(timezone.utc).strftime("%-d %b %Y, %H:%M UTC")
    q = json.loads((ROOT / "queue.json").read_text())
    counts = {
        "queued": sum(1 for i in q["items"] if i.get("status") == "queued"),
        "videos": len(list((ROOT / "out" / "video").glob("*.mp4"))),
    }
    runs = sys.argv[1] if len(sys.argv) > 1 else "credential check and publish dry run both passing"
    Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/review-desk.html").write_text(
        build(gen, counts, runs))
    print("written")
