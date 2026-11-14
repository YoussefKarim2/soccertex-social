// Drives the review desk in a real browser against a pretend GitHub.  Run: node tests/test_desk.js  (needs playwright)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const OUT = path.resolve(__dirname, '..', 'out');
const SHOTS = path.join(require('os').tmpdir(), 'desk-shots'); fs.mkdirSync(SHOTS, { recursive: true });
const BASEQ = JSON.parse(fs.readFileSync(process.env.QUEUE || path.resolve(__dirname, '..', 'queue.json'), 'utf8'));
const TOKEN = 'github_pat_' + 'x'.repeat(82);
const clone = o => JSON.parse(JSON.stringify(o));

const srv = http.createServer((req, res) => {
  const p = path.join(OUT, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  fs.readFile(p, (e, b) => { if (e) { res.writeHead(404); return res.end(); }
    const t = { '.html': 'text/html', '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.txt': 'text/plain' }[path.extname(p)] || 'application/octet-stream';
    res.writeHead(200, { 'content-type': t, 'accept-ranges': 'bytes' }); res.end(b); });
}).listen(8765);

function fakeGitHub(opts = {}) {
  const g = { files: { 'queue.json': { data: clone(opts.queue || BASEQ), sha: 1 } }, puts: [], dispatches: [], mp4: [], covers: 0,
    slow: 0, failPut: false, readStatus: 200, rateLimited: false, dispatchStatus: 204, beforePut: null,
    runs: [{ id: 1, name: 'Publish due posts', path: '.github/workflows/publish.yml', status: 'completed', conclusion: 'success',
             created_at: new Date(Date.now() - 3 * 3600e3).toISOString(), updated_at: new Date(Date.now() - 3 * 3600e3).toISOString(), html_url: 'https://github.com/x' }],
    jobs: {}, commits: [
      { commit: { message: 'publish: 2026-11-14T16:55Z', author: { name: 'soccertex-bot', date: new Date(Date.now() - 3 * 3600e3).toISOString() } } },
      { commit: { message: 'Review desk: gsm--instagram--20261122-1700 — stopped', author: { name: 'YoussefKarim2', date: new Date(Date.now() - 5 * 3600e3).toISOString() } } },
      { commit: { message: 'agent(video-editor): re-rendered gsm--social after your comment', author: { name: 'Claude', date: new Date(Date.now() - 26 * 3600e3).toISOString() } } }] };
  g.q = () => g.files['queue.json'].data;
  g.fb = () => (g.files['feedback.json'] || { data: { threads: [] } }).data;
  g.set = (p, data) => { const f = g.files[p]; g.files[p] = { data, sha: f ? f.sha + 1 : 1 }; };
  const b64 = o => Buffer.from(JSON.stringify(o, null, 2)).toString('base64');
  g.route = async route => {
    const req = route.request(), u = new URL(req.url()), m = req.method();
    const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*',
                   'access-control-expose-headers': 'x-ratelimit-remaining' };
    if (m === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
    const json = (status, body, h = {}) => route.fulfill({ status, headers: { ...cors, 'content-type': 'application/json', ...h }, body: JSON.stringify(body) });
    if (u.host === 'raw.githubusercontent.com') {
      const p = u.pathname.split('/main/')[1];
      if (p === 'out/desk/preflight.txt') return route.fulfill({ status: 200, headers: cors, body: 'preflight 2026-11-14T13:48:47Z\n\n2 problem(s) would stop a post going out:\n  - x\nexit 0' });
      return g.files[p] ? json(200, g.files[p].data) : json(404, {});
    }
    const cm = u.pathname.match(/\/contents\/(.+)$/);
    if (cm && m === 'GET') {
      if (g.rateLimited) return json(403, { message: 'rate limit' }, { 'x-ratelimit-remaining': '0' });
      if (g.readStatus !== 200) return json(g.readStatus, { message: 'Bad credentials' });
      const f = g.files[cm[1]];
      return f ? json(200, { sha: 's' + f.sha, content: b64(f.data) }) : json(404, {});
    }
    if (cm && m === 'PUT') {
      if (g.slow) await new Promise(r => setTimeout(r, g.slow));
      if (g.failPut) return route.abort('internetdisconnected');
      if (g.beforePut) { const f = g.beforePut; g.beforePut = null; f(g); }
      const body = JSON.parse(req.postData()), f = g.files[cm[1]];
      if (f && body.sha !== 's' + f.sha) { g.puts.push({ conflict: true, path: cm[1] }); return json(f && !body.sha ? 422 : 409, { message: 'does not match' }); }
      g.set(cm[1], JSON.parse(Buffer.from(body.content, 'base64').toString('utf8')));
      g.puts.push({ message: body.message, path: cm[1] });
      return json(200, { content: { sha: 's' + g.files[cm[1]].sha } });
    }
    if (u.pathname.endsWith('/dispatches')) { g.dispatches.push(req.postData()); return route.fulfill({ status: g.dispatchStatus, headers: cors, body: '' }); }
    const jm = u.pathname.match(/\/actions\/runs\/(\d+)\/jobs$/);
    if (jm) return json(200, { jobs: g.jobs[jm[1]] || [] });
    if (u.pathname.endsWith('/actions/runs')) return json(200, { workflow_runs: g.runs });
    if (u.pathname.endsWith('/commits')) return json(200, g.commits);
    if (u.pathname === '/repos/YoussefKarim2/soccertex-social') {
      if (!(req.headers().authorization || '').includes('github_pat_')) return json(401, {});
      return json(200, { permissions: { push: true } });
    }
    return json(404, {});
  };
  return g;
}

const results = [];
const ok = (name, cond, extra = '') => { results.push([cond ? 'PASS' : 'FAIL', name]); console.log(cond ? 'PASS' : 'FAIL', name, cond ? '' : extra); };

async function open(browser, g, { token = true, viewport = { width: 1100, height: 1400 }, scheme = 'light', hash = '' } = {}) {
  const ctx = await browser.newContext({ viewport, colorScheme: scheme });
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(String(e)));
  page.errs = errs;
  await ctx.route('https://api.github.com/**', g.route);
  await ctx.route('https://raw.githubusercontent.com/**', g.route);
  await ctx.route('https://fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  page.on('request', r => { if (/\.mp4/.test(r.url())) g.mp4.push(r.url()); if (/cover\.jpg/.test(r.url())) g.covers++; });
  if (token) await ctx.addInitScript(t => localStorage.setItem('soccertex.desk.token', t), TOKEN);
  await page.goto('http://localhost:8765/desk/' + hash);
  await page.waitForSelector('.tabs');
  return page;
}
const item = (g, id) => g.q().items.find(i => i.id === id);
const card = (page, id) => page.locator(`.card[data-id="${id}"]`);
const settled = page => page.waitForFunction(() => document.querySelector('#stamp').textContent.includes('Updated'), null, { timeout: 15000 });
const tab = (page, k) => page.locator(`[data-act=tab][data-v=${k}]`).click();

(async () => {
  const browser = await chromium.launch();
  const future = BASEQ.items.filter(i => i.status === 'queued' && new Date(i.publish_at) > Date.now());
  const ig = future.filter(i => i.platform === 'instagram'), li = future.filter(i => i.platform === 'linkedin');
  const A = ig[0].id, B = ig[1].id, C = li[0].id, D = ig[2].id, VA = ig[0].video;

  // 1. looking only, no key
  let g = fakeGitHub(), page = await open(browser, g, { token: false });
  ok('no key: page renders with data', await page.locator('.card').count() > 0);
  ok('no key: says so and offers to add one', await page.locator('.banner:has-text("looking only")').count() === 1);
  ok('no key: no action buttons', await page.locator('.acts').count() === 0);
  await page.close();

  // 2. weight of the page
  g = fakeGitHub(); const t0 = Date.now(); page = await open(browser, g);
  const stats = await page.evaluate(() => ({ cards: document.querySelectorAll('.card').length, nodes: document.querySelectorAll('*').length,
    videos: [...document.querySelectorAll('video')].filter(v => v.src).length }));
  console.log('     ', JSON.stringify({ ...stats, mp4: g.mp4.length, covers: g.covers, ms: Date.now() - t0 }));
  ok('light page: no video loaded on open', stats.videos === 0 && g.mp4.length === 0);
  ok('shows one week, not the whole month', stats.cards <= 30 && stats.cards >= 20, 'cards ' + stats.cards);
  await page.screenshot({ path: SHOTS + '/desktop.png' });

  // 3. stop a post
  await card(page, A).locator('[data-act=veto]').click(); await settled(page);
  ok('stop: saved to the queue', item(g, A).status === 'vetoed' && g.puts.length === 1 && /^Review desk: /.test(g.puts[0].message), JSON.stringify(g.puts));
  ok('stop: button shows the new state', (await card(page, A).locator('[data-act=veto]').textContent()).includes('undo'));
  await card(page, A).locator('[data-act=veto]').click(); await settled(page);
  ok('undo: back on the schedule', item(g, A).status === 'queued');

  // 4. typing right after a save — the "Saved" label clearing used to reset the caret
  await card(page, A).locator('[data-act=edit-caption]').click();
  const ta = card(page, A).locator('textarea');
  await ta.fill('');
  await ta.pressSequentially('New hook for the reel. Typed slowly on purpose.', { delay: 110 });
  await page.evaluate(() => refresh());
  await page.waitForTimeout(500);
  ok('typing: text arrives in order through repaints and a refresh', await ta.inputValue() === 'New hook for the reel. Typed slowly on purpose.' &&
     await page.evaluate(() => document.activeElement.tagName) === 'TEXTAREA', await ta.inputValue());
  g.puts.length = 0; const orig = item(g, A).caption;
  await card(page, A).locator('[data-act=save-caption]').click(); await settled(page);
  ok('caption: saved once, original kept', item(g, A).caption.startsWith('New hook') && item(g, A).caption_original === orig && item(g, A).caption_edited === true && g.puts.length === 1);
  await card(page, A).locator('[data-act=edit-caption]').click();
  await card(page, A).locator('[data-act=restore-caption]').click(); await settled(page);
  ok('caption: restore puts the original back', item(g, A).caption === orig && !('caption_edited' in item(g, A)) && !('caption_original' in item(g, A)));

  // 5. three changes while a save is in flight — the old desk dropped the 2nd and 3rd
  g.slow = 700; g.puts.length = 0;
  await card(page, A).locator('[data-act=veto]').click();
  await card(page, B).locator('[data-act=manual]').click();
  await card(page, C).locator('[data-act=veto]').click();
  await settled(page);
  ok('rapid: all three changes landed', item(g, A).status === 'vetoed' && item(g, B).manual === true && item(g, C).status === 'vetoed', `${g.puts.length} commits`);
  ok('rapid: nothing left saying Saving', await page.locator('.save.busy').count() === 0);
  g.slow = 0;

  // 6. the publisher commits in between
  g.puts.length = 0;
  g.beforePut = gg => { const q = clone(gg.q()); const x = q.items.find(i => i.id === D); x.status = 'published'; x.result = { permalink: 'https://instagram.com/reel/x', late_minutes: 12 }; gg.set('queue.json', q); };
  await card(page, A).locator('[data-act=veto]').click(); await settled(page);
  ok('conflict: redone on top of the newer queue', g.puts.some(p => p.conflict) && item(g, A).status === 'queued' && item(g, D).status === 'published', JSON.stringify(g.puts));

  // 7. connection drops mid-save
  g.failPut = true;
  await card(page, A).locator('[data-act=veto]').click();
  await page.waitForSelector(`.card[data-id="${A}"] .state.stop:has-text("Not saved")`);
  ok('offline: says not saved, and does not pretend', item(g, A).status === 'queued' && !(await card(page, A).locator('[data-act=veto]').textContent()).includes('undo'));
  g.failPut = false;
  await card(page, A).locator('[data-act=retry-save]').click(); await settled(page);
  ok('offline: Try again saves it', item(g, A).status === 'vetoed');
  await card(page, A).locator('[data-act=veto]').click(); await settled(page);

  // 8. watch and comment
  ok('video: none loaded yet', g.mp4.length === 0);
  await card(page, A).locator('.thumb').click();
  await page.waitForTimeout(500);
  ok('video: plays in the viewer', await page.evaluate(() => document.querySelector('#player').open && /\.mp4$/.test(document.querySelector('#player video').src)) && g.mp4.length >= 1);
  await page.locator('#fb-like').pressSequentially('the opening number', { delay: 60 });
  await page.locator('#fb-change').pressSequentially('cut the intro, less text on screen', { delay: 60 });
  await page.evaluate(() => refresh()); await page.waitForTimeout(300);
  ok('comment: typing survives a refresh', await page.locator('#fb-change').inputValue() === 'cut the intro, less text on screen');
  await page.screenshot({ path: SHOTS + '/player.png' });
  g.puts.length = 0;
  await page.locator('[data-act=send-comment]').click(); await settled(page);
  let th = g.fb().threads[0];
  ok('comment: saved as its own file, addressed to the video', g.puts.length === 1 && g.puts[0].path === 'feedback.json' && th && th.video === VA &&
     th.like === 'the opening number' && th.change.startsWith('cut the intro') && th.status === 'open', JSON.stringify([g.puts, th]));
  ok('comment: shows as waiting, boxes cleared', await page.locator('#pside .thread .state:has-text("Waiting for the video editor")').count() === 1 && await page.locator('#fb-change').inputValue() === '');
  await page.locator('[data-act=close-player]').click();
  ok('video: unloaded on close', await page.evaluate(() => !document.querySelector('#player video').getAttribute('src')));
  ok('comment: the card carries a tag', await card(page, A).locator('.tag:has-text("comment waiting")').count() === 1);

  // 9. the editor agent picks it up — as the desk would see it
  const now = () => new Date().toISOString();
  let fb = clone(g.fb()); fb.threads[0].status = 'working'; g.set('feedback.json', fb);
  g.set('agents/status.json', { agents: { 'video-editor': { state: 'working', step: 'Re-rendering small-orders (Instagram cut)', started_at: now(), updated_at: now() } },
    log: [{ t: now(), agent: 'video-editor', text: 'picked up 1 comment' }, { t: now(), agent: 'video-editor', text: 'rewrote the opening of small-orders' }] });
  g.runs.unshift({ id: 9, name: 'Publish due posts', path: '.github/workflows/publish.yml', status: 'in_progress', conclusion: null, created_at: now(), run_started_at: now(), updated_at: now(), html_url: 'https://github.com/x/9' });
  g.jobs[9] = [{ steps: [{ name: 'Set up job', status: 'completed' }, { name: 'Run actions/checkout@v4', status: 'completed' }, { name: 'Publish', status: 'in_progress' }, { name: 'Record results', status: 'queued' }] }];
  await tab(page, 'agents'); await page.locator('#refresh').click(); await settled(page);
  await page.waitForSelector('.agent.live');
  const agentTxt = await page.locator('.agent.live').allTextContents();
  ok('agents: the editor shows live with its current step', agentTxt.some(t => t.includes('Video editor') && t.includes('Re-rendering small-orders')));
  ok('agents: the publisher shows live with its steps', agentTxt.some(t => t.includes('Publisher') && t.includes('Working now')) && await page.locator('.steps li.now:has-text("Publish")').count() === 1);
  ok('agents: tab badge counts who is working', (await page.locator('[data-act=tab][data-v=agents] .b').textContent()).trim() === '2 live');
  ok('agents: step log and change feed in plain words', await page.locator('.feed li:has-text("rewrote the opening")').count() === 1 &&
     await page.locator('.feed li:has-text("sent what was due")').count() === 1 && await page.locator('.feed li:has-text("You")').count() >= 1);
  ok('agents: one that never reported says so', (await page.locator('.agent:has-text("Quality pass")').textContent()).includes('Not started yet'));
  await page.screenshot({ path: SHOTS + '/agents.png', fullPage: true });

  // the agent finishes
  fb = clone(g.fb()); Object.assign(fb.threads[0], { status: 'done', done_at: now() });
  fb.threads[0].updates.push({ t: now(), by: 'editor', text: 'Cut the first beat and now open on the 300-piece number. Kept the pace.' });
  g.set('feedback.json', fb); g.set('agents/status.json', { agents: { 'video-editor': { state: 'idle', updated_at: now(), last_result: 'Changed 1 video' } }, log: [] });
  g.runs.shift();
  await tab(page, 'next'); await page.locator('#refresh').click(); await settled(page);
  ok('done: card says handled', await card(page, A).locator('.tag:has-text("1 comment handled")').count() === 1);
  g.mp4.length = 0;
  await card(page, A).locator('.thumb').click(); await page.waitForTimeout(400);
  ok('done: plays the new cut, not the cached one', g.mp4.some(u => u.includes('?v=')) , g.mp4.join(' '));
  ok('done: the editor\'s reply is on the thread', await page.locator('#pside .up:has-text("now open on the 300-piece number")').count() === 1);
  await page.locator('[data-act=close-player]').click();

  // the agent has a question
  fb = clone(g.fb()); fb.threads.push({ id: 'fb-q', video: ig[3].video, topic: ig[3].topic, variant: 'social', platform: 'instagram', created_at: now(),
    like: '', change: 'show our real factory', status: 'needs_you', updates: [{ t: now(), by: 'editor', text: 'There is no SoccerTex factory footage in the library. Can you film 20 seconds?' }] });
  g.set('feedback.json', fb);
  await page.locator('#refresh').click(); await settled(page);
  ok('question: lights up Needs you', (await page.locator('[data-act=tab][data-v=needs] .b').textContent()).trim() !== '0');
  await tab(page, 'needs');
  await page.locator('textarea[data-draft="reply:fb-q"]').fill('Yes, on Monday.');
  await page.locator('[data-act=reply][data-id=fb-q]').click(); await settled(page);
  th = g.fb().threads.find(t => t.id === 'fb-q');
  ok('question: the answer goes back and reopens it', th.status === 'open' && th.updates.slice(-1)[0].by === 'you' && th.updates.slice(-1)[0].text === 'Yes, on Monday.');

  // 10. library
  await tab(page, 'videos');
  const nv = await page.locator('.vid').count();
  ok('videos: the whole library as stills', nv >= 40 && nv <= 60, 'count ' + nv);
  await page.screenshot({ path: SHOTS + '/videos.png' });

  // 11. by hand, and history
  await tab(page, 'needs');
  await card(page, B).locator('[data-act=posted]').click(); await settled(page);
  ok('by hand: recorded as posted by you', item(g, B).status === 'published' && item(g, B).result.by_hand === true);
  await tab(page, 'done');
  ok('posted tab lists history with links', await page.locator('.row-h').count() >= 7 && await page.locator('.row-h a:has-text("See the post")').count() >= 7);
  ok('no script errors through all of that', page.errs.length === 0, page.errs.join(' | '));
  await page.close();

  // 12. a reel is due; Post now
  const q2 = clone(BASEQ);
  q2.items.find(i => i.id === A).publish_at = new Date(Date.now() - 3 * 3600e3).toISOString();
  q2.items.find(i => i.id === C).publish_at = new Date(Date.now() - 5 * 3600e3).toISOString();
  g = fakeGitHub({ queue: q2 }); page = await open(browser, g);
  ok('due: banner says 1 post due (LinkedIn is not an emergency)', await page.locator('.banner.warn:has-text("1 post due")').count() === 1);
  ok('due: LinkedIn described as not connected, not failing', (await page.locator('.hcard').nth(1).textContent()).includes('Not connected yet'));
  ok('due: Instagram described as waiting, not disconnected', /due and waiting/.test(await page.locator('.hcard').nth(0).textContent()));
  await page.locator('[data-act=post-ask]').click();
  ok('post now: asks first', g.dispatches.length === 0 && await page.locator('[data-act=post-go]').count() === 1);
  await page.locator('[data-act=post-go]').click();
  await page.waitForSelector('#toast.on');
  ok('post now: starts the publisher for real', g.dispatches.length === 1 && g.dispatches[0] === '{"ref":"main","inputs":{"dry_run":"false"}}', g.dispatches[0]);
  ok('post now: cannot be pressed twice', await page.locator('[data-act=post-ask]').count() === 0);
  await page.close();
  g = fakeGitHub({ queue: q2 }); g.dispatchStatus = 403; page = await open(browser, g);
  await page.locator('[data-act=post-ask]').click(); await page.locator('[data-act=post-go]').click();
  await page.waitForSelector('#sheet[open]');
  ok('post now: a read-only key gets told how to fix it', (await page.locator('#sheetbody').textContent()).includes('Read and write'));
  await page.close();

  // 13. key expired
  g = fakeGitHub(); g.readStatus = 401; page = await open(browser, g);
  ok('expired key: still shows the schedule, says the key died', await page.locator('.card').count() > 0 && await page.locator('.banner:has-text("stopped working")').count() === 1);
  await page.locator('[data-act=add-key]').click(); g.readStatus = 200;
  await page.locator('#tok').fill('hello'); await page.locator('[data-act=key-go]').click();
  ok('add key: rejects something that is not a token', (await page.locator('#tokerr').textContent()).includes('does not look like'));
  await page.locator('#tok').fill(TOKEN); await page.locator('[data-act=key-go]').click();
  await page.waitForSelector('.acts');
  ok('add key: desk becomes editable', await page.evaluate(() => !!localStorage.getItem('soccertex.desk.token')));
  await page.close();

  // 14. rate limit must not throw the key away (the old desk did)
  g = fakeGitHub(); page = await open(browser, g); g.rateLimited = true;
  await page.locator('#refresh').click();
  await page.waitForSelector('.banner.warn:has-text("limiting")');
  ok('rate limit: keeps the key and the data', await page.evaluate(() => !!localStorage.getItem('soccertex.desk.token')) && await page.locator('.card').count() > 0);
  await page.close();

  // 15. GitHub down on first open
  g = fakeGitHub(); g.readStatus = 500;
  { const ctx = await browser.newContext(); const p = await ctx.newPage();
    await ctx.route('https://api.github.com/**', g.route); await ctx.route('https://raw.githubusercontent.com/**', g.route); await ctx.route('https://fonts.googleapis.com/**', r => r.abort());
    await ctx.addInitScript(t => localStorage.setItem('soccertex.desk.token', t), TOKEN);
    await p.goto('http://localhost:8765/desk/'); await p.waitForSelector('.banner.bad');
    g.readStatus = 200; await p.locator('.banner [data-act=refresh]').click(); await p.waitForSelector('.tabs');
    ok('GitHub down: says so with a retry, and the retry recovers', await p.locator('.card').count() > 0); await ctx.close(); }

  // 16. phone, and dark
  g = fakeGitHub({ queue: q2 }); page = await open(browser, g, { viewport: { width: 390, height: 844 } });
  let overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  ok('phone: no sideways scroll', overflow <= 0, 'overflow ' + overflow);
  await page.screenshot({ path: SHOTS + '/phone.png' });
  await page.locator('.card .thumb').nth(1).click(); await page.waitForTimeout(500);
  await page.screenshot({ path: SHOTS + '/phone-player.png' });
  ok('phone: the comment box is reachable in the viewer', await page.locator('#fb-change').isVisible() || await page.evaluate(() => { const d = document.querySelector('#player'); return d.scrollHeight > d.clientHeight; }));
  await page.locator('[data-act=close-player]').click();
  await tab(page, 'agents'); await page.waitForTimeout(300);
  overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  ok('phone: agents tab fits', overflow <= 0, 'overflow ' + overflow);
  await page.screenshot({ path: SHOTS + '/phone-agents.png' });
  await page.close();
  g = fakeGitHub(); page = await open(browser, g, { scheme: 'dark', viewport: { width: 900, height: 1300 } });
  await page.screenshot({ path: SHOTS + '/dark.png' });
  await page.close();

  await browser.close(); srv.close();
  const failed = results.filter(r => r[0] === 'FAIL');
  console.log(`\n${results.length - failed.length} of ${results.length} passed`);
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
