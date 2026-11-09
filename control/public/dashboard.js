'use strict';
/* SoccerTex Control — dashboard front end.
   Polls /api/status every 4s; every button hits a real endpoint. */

const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const PLAT = { instagram: 'ig', tiktok: 'tt', linkedin: 'li' };
const SHORT = { instagram: 'IG', tiktok: 'TikTok', linkedin: 'LinkedIn' };

let STATE = null, busy = false;

function when(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-GB', { weekday: 'short', day: 'numeric',
    month: 'short', hour: '2-digit', minute: '2-digit' });
}
function overdue(iso) { return new Date(iso) <= new Date(); }

async function get(path) {
  const r = await fetch(path, { cache: 'no-store' });
  if (!r.ok) throw new Error(path + ' → ' + r.status);
  return r.json();
}
async function post(path, body) {
  const r = await fetch(path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {})
  });
  return r.json();
}

/* ───────────────────────────── render ───────────────────────────── */
function stats(s) {
  const tiles = [
    ['Going out', (s.in_window || []).length, 'queued — veto any of them', 'hero'],
    ['Vetoed', s.vetoed || 0, 'stopped by you', (s.vetoed ? 'warn' : '')],
    ['Published', s.published, `of ${s.total} scheduled`, ''],
    ['Videos', s.videos_rendered, s.videos_missing_n ? `${s.videos_missing_n} missing` : 'all rendered',
      s.videos_missing_n ? 'warn' : ''],
    ['Failed', s.failed, s.failed ? 'needs a look' : 'none', s.failed ? 'bad' : ''],
  ];
  $('stats').innerHTML = tiles.map(([k, v, t, c]) =>
    `<div class="stat ${c}"><div class="k">${esc(k)}</div>
     <div class="v">${esc(v)}</div><div class="t">${esc(t)}</div></div>`).join('');
}

function countdown(iso) {
  const ms = new Date(iso) - new Date();
  if (ms <= 0) return 'now';
  const h = Math.floor(ms / 3.6e6), m = Math.floor((ms % 3.6e6) / 6e4);
  return h >= 24 ? `in ${Math.floor(h / 24)}d ${h % 24}h` : (h ? `in ${h}h ${m}m` : `in ${m}m`);
}

function manualTable(s) {
  const items = (s.in_window || []);
  if (!items.length) {
    $('manual').innerHTML = '<tr><td class="empty">Nothing queued.</td></tr>';
    return;
  }
  $('manual').innerHTML =
    `<thead><tr><th>Goes out</th><th>Where</th><th>Topic</th><th></th></tr></thead><tbody>` +
    items.map(i => `<tr>
      <td style="white-space:nowrap">
        <span class="num">${esc(countdown(i.publish_at))}</span><br>
        <span style="font-size:11px;color:var(--faint)">${esc(when(i.publish_at))}</span></td>
      <td><span class="chip ${PLAT[i.platform]}">${esc(SHORT[i.platform])}</span></td>
      <td><strong>${esc(i.topic)}</strong>
        <div style="font-size:11.5px;color:var(--muted);margin-top:3px;max-height:40px;overflow:hidden">
          ${esc((i.caption || '').slice(0, 110))}…</div></td>
      <td style="white-space:nowrap">
        <button data-preview="${esc(i.video)}">Watch</button>
        <button class="danger" data-veto="${esc(i.id)}">Veto</button></td>
    </tr>`).join('') + '</tbody>';
}

function vetoedTable() {
  const items = (STATE.queue || []).filter(i => i.status === 'vetoed').slice(0, 20);
  const el = $('vetoed');
  if (!el) return;
  el.innerHTML = !items.length
    ? '<tr><td class="empty">Nothing vetoed.</td></tr>'
    : `<thead><tr><th>Was due</th><th>Where</th><th>Topic</th><th></th></tr></thead><tbody>` +
      items.map(i => `<tr>
        <td class="num" style="white-space:nowrap">${esc(when(i.publish_at))}</td>
        <td><span class="chip ${PLAT[i.platform]}">${esc(SHORT[i.platform])}</span></td>
        <td>${esc(i.topic)}</td>
        <td><button data-unveto="${esc(i.id)}">Put back</button></td>
      </tr>`).join('') + '</tbody>';
}

function upcomingTable(s) {
  const items = s.upcoming || [];
  if (!items.length) {
    $('upcoming').innerHTML = '<tr><td class="empty">Schedule is empty — roll it forward.</td></tr>';
    return;
  }
  $('upcoming').innerHTML =
    `<thead><tr><th>When</th><th>Where</th><th>Topic</th><th>How</th></tr></thead><tbody>` +
    items.map(i => `<tr>
      <td class="num" style="white-space:nowrap">${esc(when(i.publish_at))}</td>
      <td><span class="chip ${PLAT[i.platform]}">${esc(SHORT[i.platform])}</span></td>
      <td>${esc(i.topic)}</td>
      <td><span class="chip ${i.status === 'queued' ? 'auto' : 'hand'}">
          ${i.status === 'queued' ? 'auto' : esc(i.status)}</span></td>
    </tr>`).join('') + '</tbody>';
}

function publishedTable(s) {
  const items = s.recent_published || [];
  if (!items.length) {
    $('published').innerHTML = '<tr><td class="empty">Nothing published yet.</td></tr>';
    return;
  }
  $('published').innerHTML =
    `<thead><tr><th>When</th><th>Where</th><th>Topic</th><th>Link</th></tr></thead><tbody>` +
    items.map(i => {
      const link = i.result && i.result.permalink;
      return `<tr>
        <td class="num" style="white-space:nowrap">${esc(when(i.publish_at))}</td>
        <td><span class="chip ${PLAT[i.platform]}">${esc(SHORT[i.platform])}</span></td>
        <td>${esc(i.topic)}</td>
        <td>${link ? `<a href="${esc(link)}" target="_blank" rel="noopener">open</a>`
                   : '<span style="color:var(--faint)">—</span>'}</td>
      </tr>`;
    }).join('') + '</tbody>';
}

function envPanel(s) {
  const e = s.env || {};
  const yn = v => v ? '<span class="yes">yes</span>' : '<span class="no">no</span>';
  $('env').innerHTML = `
    <div><b>ffmpeg</b>${yn(e.ffmpeg)}</div>
    <div><b>Instagram id</b>${e.ig_user_id ? '<span class="yes">pinned</span>' : 'auto'}</div>
    <div><b>Instagram token</b>${e.ig_token ? '<span class="yes">set</span> ' + esc(e.ig_token_hint) : '<span class="no">missing</span>'}</div>
    <div><b>LinkedIn token</b>${yn(e.li_token)}</div>
    <div><b>Media base URL</b>${e.media_base_url ? esc(e.media_base_url) : '<span class="no">unset</span>'}</div>
    <div><b>Python</b>${esc(e.python || '')}</div>`;

  const f = s.failures || [];
  $('failures').innerHTML = !f.length ? '' :
    `<div class="note" style="margin-top:12px"><strong>${f.length} failed.</strong><br>` +
    f.map(i => `${esc(i.topic)} (${esc(i.platform)}) — ${esc(i.last_error || 'no detail')}`).join('<br>') +
    `</div>`;
  const missing = [];
  if (!e.ig_token) missing.push('IG_ACCESS_TOKEN');
  if (!e.li_token) missing.push('LI_ACCESS_TOKEN');
  if (!e.media_base_url) missing.push('MEDIA_BASE_URL');
  if (missing.length) {
    $('failures').innerHTML += `<div class="note" style="margin-top:12px">
      Publishing is off until ${missing.map(m => '<code>' + m + '</code>').join(', ')}
      ${missing.length > 1 ? 'are' : 'is'} set in the environment you start this from.
      <code>IG_USER_ID</code> is optional — the publisher finds the account from the token.
      See SETUP.md.</div>`;
  }
}

function jobsPanel(s) {
  const jobs = s.jobs || {};
  const names = Object.keys(jobs);
  if (!names.length) { $('jobout').innerHTML = ''; return; }
  $('jobout').innerHTML = names.map(n => {
    const j = jobs[n];
    const head = j.running ? `running…` : (j.rc === 0 ? 'finished' : `exited ${j.rc}`);
    if (!j.lines.length && !j.running) return '';
    return `<div style="margin-top:12px">
      <div style="font-size:12px;color:var(--muted);margin-bottom:5px">
        <strong>${esc(n)}</strong> — ${esc(head)}</div>
      <pre class="log" style="max-height:180px">${esc(j.lines.join('\n') || '…')}</pre></div>`;
  }).join('');
}

async function refresh() {
  try {
    const [s, q, l] = await Promise.all([
      get('/api/status'), get('/api/queue?limit=400'), get('/api/log')
    ]);
    STATE = s; STATE.queue = q.items;
    $('dot').className = 'dot';
    $('pulse').textContent = 'live · ' + new Date().toLocaleTimeString('en-GB');
    stats(s); manualTable(s); vetoedTable(); upcomingTable(s); publishedTable(s);
    envPanel(s); jobsPanel(s);
    $('log').textContent = (l.lines || []).slice(-60)
      .map(x => `${x.t.slice(5, 16).replace('T', ' ')}  ${x.level.padEnd(5)}  ${x.msg}`)
      .join('\n') || 'nothing yet';
  } catch (e) {
    $('dot').className = 'dot bad';
    $('pulse').textContent = 'server not reachable';
  }
}

/* ───────────────────────────── actions ──────────────────────────── */
document.addEventListener('click', async ev => {
  const act = ev.target.closest('[data-act]');
  const mark = ev.target.closest('[data-mark]');

  const veto = ev.target.closest('[data-veto]');
  const unveto = ev.target.closest('[data-unveto]');
  const prev = ev.target.closest('[data-preview]');

  if (prev) { showPreview(prev.dataset.preview); return; }
  if (veto) {
    veto.disabled = true;
    await post('/api/mark', { id: veto.dataset.veto, status: 'vetoed' });
    await refresh(); return;
  }
  if (unveto) {
    unveto.disabled = true;
    await post('/api/mark', { id: unveto.dataset.unveto, status: 'queued' });
    await refresh(); return;
  }
  if (mark) {
    mark.disabled = true;
    await post('/api/mark', { id: mark.dataset.mark, status: 'published' });
    await refresh();
    return;
  }
  if (!act || busy) return;

  const a = act.dataset.act;
  busy = true; act.disabled = true;
  try {
    if (a === 'publish-dry') await post('/api/publish', { dry_run: true });
    else if (a === 'publish') {
      if (!confirmLive()) { busy = false; act.disabled = false; return; }
      await post('/api/publish', { dry_run: false });
    }
    else if (a === 'render') await post('/api/render', {});
    else if (a === 'reschedule') await post('/api/reschedule', {});
    await refresh();
  } finally {
    busy = false; act.disabled = false;
  }
});

/* The sandbox blocks window.confirm in hosted pages; this panel is local, but
   keep our own confirmation so the behaviour is identical either way. */
function confirmLive() {
  const n = STATE ? STATE.due_now : 0;
  const el = document.createElement('div');
  el.className = 'note';
  el.style.cssText = 'border-left-color:var(--red);margin-top:12px';
  el.innerHTML = `<strong>Publish ${n} post${n === 1 ? '' : 's'} to Instagram for real?</strong>
     This cannot be undone. Click again within 5 seconds to confirm.`;
  const panel = document.querySelector('.panel');
  if (!panel.dataset.armed) {
    panel.appendChild(el);
    panel.dataset.armed = '1';
    setTimeout(() => { el.remove(); delete panel.dataset.armed; }, 5000);
    return false;
  }
  delete panel.dataset.armed;
  panel.querySelectorAll('.note').forEach(x => x.remove());
  return true;
}

refresh();
setInterval(refresh, 4000);


/* Inline preview so a post can be watched before it is vetoed. */
function showPreview(rel) {
  const name = rel.split('/').pop();
  let box = document.getElementById('preview');
  if (!box) {
    box = document.createElement('div');
    box.id = 'preview';
    box.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:99;' +
      'display:flex;align-items:center;justify-content:center;padding:20px';
    box.addEventListener('click', e => { if (e.target === box) box.remove(); });
    document.body.appendChild(box);
  }
  box.innerHTML = `<div style="max-width:380px;width:100%">
    <video src="/video/${encodeURIComponent(name)}" controls autoplay playsinline
           style="width:100%;border-radius:12px;background:#000"></video>
    <div style="text-align:center;margin-top:10px">
      <button onclick="document.getElementById('preview').remove()">Close</button>
    </div></div>`;
}
