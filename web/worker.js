/**
 * SoccerTex Review Desk — Cloudflare Worker.
 *
 * Why a Worker rather than Render or Railway: this is a page plus four small
 * GitHub calls. Workers' free tier does not sleep, so opening the desk is
 * instant; Render's free tier spins down after 15 idle minutes and takes about
 * a minute to wake, and Railway has no real free tier any more.
 *
 * What it does that the artifact version cannot:
 *   - reads queue.json and the workflow runs live, instead of a snapshot
 *   - writes decisions straight back into queue.json, so a veto takes effect
 *     on the next hourly publish run with nobody in the loop
 *
 * Secrets (wrangler secret put / Pages dashboard):
 *   GH_TOKEN        fine-grained PAT, Contents: read+write on THIS REPO ONLY
 *   APP_PASSWORD    what you type to get in
 *   SESSION_SECRET  any long random string; signs the session cookie
 *
 * The token can edit one repository and nothing else. That is deliberate: a
 * compromise of this Worker must not reach the rest of the account.
 */

const REPO = "YoussefKarim2/soccertex-social";
const BRANCH = "main";
const PAGES = "https://youssefkarim2.github.io/soccertex-social";
const API = "https://api.github.com";
const SESSION_HOURS = 24 * 14;

const enc = new TextEncoder();

/* ---------- session cookie: HMAC(expiry) so it cannot be forged ---------- */

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(msg));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function mintSession(env) {
  const exp = Date.now() + SESSION_HOURS * 3600_000;
  return `${exp}.${await hmac(env.SESSION_SECRET, String(exp))}`;
}

async function validSession(env, cookieHeader) {
  const raw = (cookieHeader || "").split(/;\s*/).find(c => c.startsWith("sx="));
  if (!raw) return false;
  const [exp, sig] = decodeURIComponent(raw.slice(3)).split(".");
  if (!exp || !sig || Number(exp) < Date.now()) return false;
  const want = await hmac(env.SESSION_SECRET, exp);
  // constant-time-ish compare
  if (want.length !== sig.length) return false;
  let diff = 0;
  for (let i = 0; i < want.length; i++) diff |= want.charCodeAt(i) ^ sig.charCodeAt(i);
  return diff === 0;
}

/* ---------- GitHub ---------- */

function gh(env, path, init = {}) {
  return fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Authorization": `Bearer ${env.GH_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "soccertex-review-desk",
      "X-GitHub-Api-Version": "2022-11-28",
      ...(init.headers || {}),
    },
  });
}

async function readQueue(env) {
  const r = await gh(env, `/repos/${REPO}/contents/queue.json?ref=${BRANCH}`);
  if (!r.ok) throw new Error(`queue read failed: ${r.status}`);
  const j = await r.json();
  // atob gives latin1; round-trip through bytes so non-ASCII captions survive
  const bytes = Uint8Array.from(atob(j.content.replace(/\n/g, "")), c => c.charCodeAt(0));
  return { queue: JSON.parse(new TextDecoder().decode(bytes)), sha: j.sha };
}

async function writeQueue(env, queue, sha, message) {
  const bytes = enc.encode(JSON.stringify(queue, null, 2) + "\n");
  let bin = "";
  bytes.forEach(b => { bin += String.fromCharCode(b); });
  const r = await gh(env, `/repos/${REPO}/contents/queue.json`, {
    method: "PUT",
    body: JSON.stringify({ message, content: btoa(bin), sha, branch: BRANCH }),
  });
  if (!r.ok) throw new Error(`queue write failed: ${r.status} ${await r.text()}`);
  return (await r.json()).content.sha;
}

async function runs(env) {
  const r = await gh(env, `/repos/${REPO}/actions/runs?per_page=8`);
  if (!r.ok) return [];
  const j = await r.json();
  return (j.workflow_runs || []).map(w => ({
    name: w.name, status: w.status, conclusion: w.conclusion,
    at: w.updated_at, url: w.html_url,
  }));
}

/* ---------- API ---------- */

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function handleState(env) {
  const [{ queue }, r] = await Promise.all([readQueue(env), runs(env)]);
  const items = (queue.items || [])
    .slice()
    .sort((a, b) => a.publish_at.localeCompare(b.publish_at));
  const counts = { queued: 0, vetoed: 0, manual: 0, published: 0, failed: 0 };
  for (const i of items) {
    if (i.manual && i.status === "queued") counts.manual++;
    else if (counts[i.status] !== undefined) counts[i.status]++;
  }
  return json({
    pages: PAGES,
    generated: new Date().toISOString(),
    counts,
    runs: r,
    items: items.map(i => ({
      id: i.id, platform: i.platform, at: i.publish_at, topic: i.topic,
      pillar: i.pillar, caption: i.caption, status: i.status,
      manual: !!i.manual, note: i.review_note || "",
      video: `${PAGES}/${i.video}`,
      permalink: i.result && i.result.permalink,
      error: i.last_error,
    })),
  });
}

async function handleDecide(env, request) {
  const body = await request.json();
  const { id, veto, manual, note } = body || {};
  if (!id) return json({ error: "id required" }, 400);

  const { queue, sha } = await readQueue(env);
  const it = (queue.items || []).find(i => i.id === id);
  if (!it) return json({ error: "unknown id" }, 404);
  if (it.status === "published") return json({ error: "already published" }, 409);

  const was = { status: it.status, manual: !!it.manual, note: it.review_note || "" };
  if (typeof veto === "boolean") it.status = veto ? "vetoed" : "queued";
  if (typeof manual === "boolean") {
    if (manual) it.manual = true; else delete it.manual;
  }
  if (typeof note === "string") {
    if (note.trim()) it.review_note = note.trim(); else delete it.review_note;
  }
  const now = { status: it.status, manual: !!it.manual, note: it.review_note || "" };
  if (JSON.stringify(was) === JSON.stringify(now)) return json({ ok: true, unchanged: true });

  const what = [];
  if (was.status !== now.status) what.push(now.status === "vetoed" ? "vetoed" : "un-vetoed");
  if (was.manual !== now.manual) what.push(now.manual ? "held for manual posting" : "back to auto");
  if (was.note !== now.note) what.push(now.note ? "note added" : "note cleared");
  await writeQueue(env, queue, sha, `Review desk: ${id} — ${what.join(", ")}`);
  return json({ ok: true, item: { id, ...now } });
}

/* ---------- router ---------- */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/api/login" && request.method === "POST") {
      const { password } = await request.json().catch(() => ({}));
      if (!password || password !== env.APP_PASSWORD) {
        return json({ error: "Wrong password" }, 401);
      }
      const tok = await mintSession(env);
      return new Response(JSON.stringify({ ok: true }), {
        headers: {
          "content-type": "application/json",
          "set-cookie": `sx=${encodeURIComponent(tok)}; Path=/; HttpOnly; Secure; ` +
                        `SameSite=Lax; Max-Age=${SESSION_HOURS * 3600}`,
        },
      });
    }

    if (path === "/api/logout") {
      return new Response(null, {
        status: 204,
        headers: { "set-cookie": "sx=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0" },
      });
    }

    const authed = await validSession(env, request.headers.get("cookie"));

    if (path.startsWith("/api/")) {
      if (!authed) return json({ error: "not signed in" }, 401);
      try {
        if (path === "/api/state") return await handleState(env);
        if (path === "/api/decide" && request.method === "POST") {
          return await handleDecide(env, request);
        }
      } catch (e) {
        return json({ error: String(e.message || e) }, 502);
      }
      return json({ error: "not found" }, 404);
    }

    return new Response(PAGE(authed), {
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  },
};

/* ---------- the page ---------- */

const PAGE = (authed) => `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>SoccerTex Review Desk</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Secular+One&family=Source+Sans+3:wght@400;600&family=Roboto+Condensed:wght@400;700&display=swap">
<style>
:root{
  --pitch:#0E7A3C;--bone:#FAF8F3;--surface:#fff;--raise:#F1F4EF;--line:#DFE4DB;
  --ink:#131A14;--muted:#5C6A5E;--faint:#8A968C;--amber:#B4740E;--red:#A8281F;
  --display:'Secular One',Impact,sans-serif;--body:'Source Sans 3',system-ui,sans-serif;
  --data:'Roboto Condensed','Arial Narrow',sans-serif;
  --shadow:0 1px 2px rgba(19,26,20,.05),0 6px 18px rgba(19,26,20,.05);
}
@media (prefers-color-scheme:dark){:root{
  --pitch:#3FBE74;--bone:#0C110D;--surface:#141B15;--raise:#1B241C;--line:#2A352B;
  --ink:#E8EFE9;--muted:#9BAA9E;--faint:#6E7D71;--amber:#E0A542;--red:#F08B82;
  color-scheme:dark;--shadow:0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.3);
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bone);color:var(--ink);font-family:var(--body);
  font-size:16px;line-height:1.55}
.wrap{max-width:980px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 56px}
h1,h2,h3{font-family:var(--display);font-weight:400;margin:0}
.num{font-family:var(--data);font-variant-numeric:tabular-nums}
header{background:var(--pitch);color:#fff}
.hd{max-width:980px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 22px;
  display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap}
.hd h1{font-size:clamp(22px,5vw,29px);line-height:1.1}
.hd .live{font-size:12.5px;opacity:.9;margin-left:auto}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#B6F2CE;
  margin-right:6px;vertical-align:1px}
.rail{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;
  margin:18px 0 24px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 13px}
.tile .k{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
.tile .v{font-family:var(--data);font-size:25px;line-height:1.2}
.tile.warn .v{color:var(--amber)} .tile.bad .v{color:var(--red)}
h2.sec{font-size:17px;margin:26px 0 3px}
.sub{font-size:14px;color:var(--muted);margin:0 0 14px}
.runs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.run{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:4px 11px;
  background:var(--surface);color:var(--muted);text-decoration:none}
.run.ok{border-color:var(--pitch);color:var(--pitch)}
.run.fail{border-color:var(--red);color:var(--red)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  box-shadow:var(--shadow);margin-bottom:14px;overflow:hidden;
  display:grid;grid-template-columns:200px 1fr}
@media (max-width:640px){.card{grid-template-columns:1fr}}
.media{background:#0A0F0B;min-width:0}
video{width:100%;display:block;aspect-ratio:9/16;object-fit:cover;background:#0A0F0B}
@media (max-width:640px){video{aspect-ratio:9/12}}
.body{padding:14px 15px 15px;min-width:0;display:flex;flex-direction:column;gap:9px}
.meta{display:flex;gap:9px;flex-wrap:wrap;align-items:center;font-size:12.5px}
.chip{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  padding:3px 8px;border-radius:5px;color:#fff}
.chip-instagram{background:#B5317E}.chip-linkedin{background:#0A66C2}
.when{color:var(--muted)}.when b{color:var(--ink);font-weight:600}
.pillar{color:var(--faint)}
.hook{font-size:17px;line-height:1.25;text-wrap:balance}
details summary{font-size:13px;color:var(--pitch);cursor:pointer;width:fit-content}
details p{font-size:14px;color:var(--muted);white-space:pre-wrap;margin:7px 0 0}
.state{font-size:13px;padding:7px 10px;border-radius:7px;background:var(--raise);
  border-left:3px solid var(--faint);color:var(--muted)}
.state.manual{border-left-color:var(--amber);color:var(--amber)}
.state.veto{border-left-color:var(--red);color:var(--red)}
.state.done{border-left-color:var(--pitch);color:var(--pitch)}
label.nl{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}
textarea{width:100%;font:inherit;font-size:14.5px;color:var(--ink);background:var(--raise);
  border:1px solid var(--line);border-radius:8px;padding:8px 10px;resize:vertical}
textarea:focus-visible{outline:2px solid var(--pitch);outline-offset:1px}
.acts{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button{font:inherit;font-size:13px;cursor:pointer;border-radius:8px;padding:7px 12px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink)}
button:hover{border-color:var(--pitch)}
button:focus-visible{outline:2px solid var(--pitch);outline-offset:2px}
button[aria-pressed="true"]{background:var(--pitch);border-color:var(--pitch);color:#fff}
button.veto[aria-pressed="true"]{background:var(--red);border-color:var(--red)}
button:disabled{opacity:.5;cursor:not-allowed}
.saved{font-size:12px;color:var(--pitch);opacity:0;transition:opacity .2s}
.saved.on{opacity:1}
.card.off{opacity:.6}
.login{max-width:330px;margin:16vh auto;text-align:center;display:flex;
  flex-direction:column;gap:11px;padding:0 20px}
.login input{font:inherit;padding:10px 12px;border:1px solid var(--line);border-radius:8px;
  background:var(--surface);color:var(--ink)}
.login .err{color:var(--red);font-size:13.5px;min-height:19px}
.empty{color:var(--faint);padding:30px 0;text-align:center}
footer{margin-top:30px;padding-top:15px;border-top:1px solid var(--line);
  font-size:13px;color:var(--faint)}
a{color:var(--pitch)}
</style></head><body>
<div id="root"></div>
<script>
const AUTHED = ${authed ? "true" : "false"};
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function login(msg = "") {
  $("#root").innerHTML = \`<div class="login">
    <h1 style="font-family:var(--display);font-size:26px">SoccerTex Review Desk</h1>
    <p style="color:var(--muted);font-size:14px;margin:0">Enter the desk password.</p>
    <input id="pw" type="password" autocomplete="current-password" placeholder="Password">
    <button id="go">Open the desk</button>
    <div class="err">\${esc(msg)}</div></div>\`;
  const go = async () => {
    const r = await fetch("/api/login", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ password: $("#pw").value }),
    });
    if (r.ok) load(); else login("That password did not work.");
  };
  $("#go").onclick = go;
  $("#pw").onkeydown = e => { if (e.key === "Enter") go(); };
  $("#pw").focus();
}

const fmt = iso => {
  const d = new Date(iso);
  return { day: d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" }),
           time: d.toISOString().slice(11, 16) };
};

function stateLine(it) {
  if (it.status === "published") {
    return ['done', it.permalink
      ? \`Published. <a href="\${esc(it.permalink)}" target="_blank" rel="noopener">See the post</a>\`
      : "Published."];
  }
  if (it.status === "failed") return ['veto', "Failed: " + esc(it.error || "no detail")];
  if (it.status === "vetoed") return ['veto', "Stopped. This will not publish."];
  if (it.manual) return ['manual', "Held back for you to post in the app with a trending sound."];
  if (it.note) return ['', "Change requested. Still scheduled until it is reworked."];
  return ['', ""];
}

function card(it) {
  const { day, time } = fmt(it.at);
  const [cls, text] = stateLine(it);
  const done = it.status === "published";
  const hook = (it.caption || "").trim().split("\\n")[0];
  return \`<article class="card \${it.status === 'vetoed' ? 'off' : ''}" data-id="\${esc(it.id)}">
    <div class="media"><video src="\${esc(it.video)}" preload="metadata" controls playsinline muted></video></div>
    <div class="body">
      <div class="meta">
        <span class="chip chip-\${esc(it.platform)}">\${it.platform === 'instagram' ? 'Instagram' : 'LinkedIn'}</span>
        <span class="when"><b>\${esc(day)}</b> <span class="num">\${esc(time)}</span> UTC</span>
        <span class="pillar">\${esc((it.pillar || '').replace(/^\\d\\s/, ''))}</span>
      </div>
      <h3 class="hook">\${esc(hook)}</h3>
      <details><summary>Full caption</summary><p>\${esc(it.caption)}</p></details>
      \${text ? \`<div class="state \${cls}">\${text}</div>\` : ""}
      <label class="nl" for="n-\${esc(it.id)}">Changes you want</label>
      <textarea id="n-\${esc(it.id)}" rows="2" \${done ? "disabled" : ""}
        placeholder="e.g. cut the intro, lead with the 150 GSM number">\${esc(it.note)}</textarea>
      <div class="acts">
        <button class="manual" data-k="manual" aria-pressed="\${!!it.manual}" \${done ? "disabled" : ""}>Trending sound — I'll post this one</button>
        <button class="veto" data-k="veto" aria-pressed="\${it.status === 'vetoed'}" \${done ? "disabled" : ""}>Don't post this</button>
        <span class="saved"></span>
      </div>
    </div></article>\`;
}

async function decide(id, patch, el) {
  const saved = $(".saved", el);
  saved.textContent = "Saving"; saved.classList.add("on");
  const r = await fetch("/api/decide", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ id, ...patch }),
  });
  if (!r.ok) { saved.textContent = "Not saved"; return; }
  saved.textContent = "Saved";
  setTimeout(() => saved.classList.remove("on"), 1400);
  return r.json();
}

function wire() {
  document.querySelectorAll(".card").forEach(el => {
    const id = el.dataset.id;
    el.querySelectorAll("button[data-k]").forEach(b => b.onclick = async () => {
      const on = b.getAttribute("aria-pressed") !== "true";
      b.setAttribute("aria-pressed", String(on));
      if (b.dataset.k === "veto") el.classList.toggle("off", on);
      await decide(id, { [b.dataset.k]: on }, el);
    });
    const ta = $("textarea", el);
    let t;
    if (ta) ta.oninput = () => {
      clearTimeout(t);
      t = setTimeout(() => decide(id, { note: ta.value }, el), 700);
    };
  });
}

async function load() {
  const r = await fetch("/api/state");
  if (r.status === 401) return login();
  if (!r.ok) {
    $("#root").innerHTML = '<div class="wrap"><p class="empty">Could not reach GitHub. Try again in a moment.</p></div>';
    return;
  }
  const s = await r.json();
  const upcoming = s.items.filter(i => i.status !== "published").slice(0, 40);
  const runs = s.runs.slice(0, 5).map(w =>
    \`<a class="run \${w.conclusion === 'success' ? 'ok' : w.conclusion ? 'fail' : ''}"
        href="\${esc(w.url)}" target="_blank" rel="noopener">\${esc(w.name)} — \${esc(w.conclusion || w.status)}</a>\`).join("");
  $("#root").innerHTML = \`
<header><div class="hd"><h1>SoccerTex Review Desk</h1>
  <span class="live"><span class="dot"></span>live · read \${new Date(s.generated).toISOString().slice(11,16)} UTC</span>
</div></header>
<div class="wrap">
  <div class="rail">
    <div class="tile"><div class="k">Scheduled</div><div class="v num">\${s.counts.queued}</div></div>
    <div class="tile warn"><div class="k">Held for you</div><div class="v num">\${s.counts.manual}</div></div>
    <div class="tile"><div class="k">Published</div><div class="v num">\${s.counts.published}</div></div>
    <div class="tile \${s.counts.failed ? 'bad' : ''}"><div class="k">Failed</div><div class="v num">\${s.counts.failed}</div></div>
    <div class="tile"><div class="k">Stopped</div><div class="v num">\${s.counts.vetoed}</div></div>
  </div>
  <h2 class="sec">Pipeline</h2>
  <p class="sub">Last runs, straight from GitHub Actions.</p>
  <div class="runs">\${runs || '<span class="run">no runs yet</span>'}</div>
  <h2 class="sec">Going out next</h2>
  <p class="sub">Times are UTC. A change here is written to the queue immediately — the next hourly run obeys it.</p>
  \${upcoming.length ? upcoming.map(card).join("") : '<p class="empty">Nothing scheduled.</p>'}
  <footer>Media served from GitHub Pages. Stock factory footage is stamped as library
    footage, never as SoccerTex's own floor. <a href="/api/logout" onclick="fetch('/api/logout').then(()=>location.reload());return false;">Sign out</a></footer>
</div>\`;
  wire();
}

AUTHED ? load() : login();
</script></body></html>`;
