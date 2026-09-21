/* MoneyBTI 钱格 · 前端逻辑（四个面板 + 对比视图 + 调试抽屉 + 中英切换）。只调后端接口，不复制任何检索 / 指标逻辑。 */
(function () {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const I18N = window.MONEYBTI_I18N || { zh: {}, en: {} };
  const CAT_EMOJI = { C1: '🛵', C2: '🍲', C3: '🥬', C4: '🧋', C5: '📦', C6: '🛍️', C7: '🚇', C8: '🎮', C9: '🏠', C10: '📚', C11: '🐱', UNC: '❔' };
  const state = { lang: 'zh', tier: 'basic', compare: false, kb: null, sessions: {}, current: null, file: null, filterFlag: false, overrides: {}, samples: [], phase: 'idle', uploadMsg: ['uploadIdle', {}] };
  const PHASE_KEY = { idle: 'reportHeadIdle', busy: 'reportHeadBusy', ready: 'reportHeadReady' };
  function setPhase(phase) { state.phase = phase; $('#analysis-state-label').textContent = t(PHASE_KEY[phase]); $('#dropzone').dataset.state = phase; }
  function uploadStatus(key, vars) { state.uploadMsg = [key, vars || {}]; const el = $('#upload-status'); el.textContent = tf(key, vars || {}); el.classList.toggle('is-error', key === 'uploadFailed'); }
  try { state.lang = localStorage.getItem('moneybti.lang') || (navigator.language && !/^zh/i.test(navigator.language) ? 'en' : 'zh'); } catch (e) { /* ignore */ }

  // ---------------------------------------------------------------- i18n
  const T = () => I18N[state.lang] || I18N.zh;
  const t = (k) => (T()[k] != null ? T()[k] : (I18N.zh[k] != null ? I18N.zh[k] : k));
  const tf = (k, vars) => String(t(k)).replace(/\{(\w+)\}/g, (_, v) => (vars[v] != null ? vars[v] : ''));
  const en = () => state.lang === 'en';
  const catName = (c) => (T().cats || {})[c] || c;
  const copyOf = (code) => (window.MONEYBTI_TICKET_COPY || {})[code] || {};
  const pname = (c) => (en() ? (c.name_en || copyOf(c.code).englishName || c.name) : c.name);
  const ptraits = (c) => (en() && (c.traits_en || []).length ? c.traits_en : (c.traits || []));
  const plabel = (r) => (en() ? (r.label_en || r.label) : r.label);
  const warnText = (w) => { if (!en()) return w; const m = /规则只认出 (\S+) 的交易，(\d+) 笔未分类/.exec(w); return m ? `Rules recognised only ${m[1]} of rows, ${m[2]} unclassified: switch to VIP or label them in the table` : w; };
  const bname = (b) => (en() ? (b.name_en || b.name) : b.name);
  const bline = (b) => (en() ? (b.line_en || b.line) : b.line);
  const bimg = (b) => `cats/badge_${b.code}.webp`;
  const badgeChip = (b, cls) => `<span class="${cls} badge-chip" data-badge="${b.code}" title="${esc(bline(b))} · ${t('badgeClick')}" role="button" tabindex="0"><img src="${bimg(b)}" alt="">${b.emoji} ${esc(bname(b))}</span>`;
  function openBadge(code) {
    const b = ((state.kb && state.kb.badges) || []).find((x) => x.code === code);
    if (!b) return;
    const how = ((T().badgeHowText || {})[code]) || '';
    $('#badge-body').innerHTML = `<img src="${bimg(b)}" alt="${esc(bname(b))}"><div><p class="eyebrow">${b.emoji} ${b.code}</p><h3>${esc(bname(b))}</h3><p>${esc(bline(b))}</p>${b.slogan ? `<p class="badge-slogan">${esc(b.slogan)}</p>` : ''}${how ? `<p class="muted small"><b>${t('badgeHow')}</b>：${esc(how)}</p>` : ''}</div>`;
    $('#badge-modal').hidden = false;
  }
  const pax = (c) => (en() ? (c.axis_en || c.axis) : c.axis);
  const pinterp = (c) => (en() && c.interpretation_en ? c.interpretation_en : c.interpretation);
  const ptag = (c) => (en() && c.tagline_en ? c.tagline_en : c.tagline);
  const RARITY_EN = { '常见': 'Common', '少见': 'Uncommon', '稀有': 'Rare', '传说': 'Legendary' };
  const GROUP_EN = { '正常': 'normal', '模糊': 'ambiguous', '缺信息': 'missing info', '误导': 'misleading' };
  const rarity = (r) => (en() ? (RARITY_EN[r] || r) : r);
  const groupName = (g) => (en() ? (GROUP_EN[g] || g) : g);
  function applyStatic() {
    document.documentElement.lang = en() ? 'en' : 'zh-CN';
    $$('[data-i18n]').forEach((el) => { const v = t(el.dataset.i18n); if (v != null) el.textContent = v; });
    $$('[data-i18n-aria]').forEach((el) => { const v = t(el.dataset.i18nAria); if (v != null) el.setAttribute('aria-label', v); });
    $$('.language-switch__btn').forEach((b) => { const on = b.dataset.lang === state.lang; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
    setPhase(state.phase); uploadStatus(state.uploadMsg[0], state.uploadMsg[1]);
    document.title = t('title');
    $('#about-body').innerHTML = t('aboutHtml');
    $('#hero-date').textContent = new Date().toLocaleDateString(en() ? 'en-GB' : 'zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) + ' · ' + t('heroDate');
    $('#btn-filter-flag').textContent = state.filterFlag ? t('showAll') : t('filterFlag');
    updateFoldLabels();
  }
  function updateFoldLabels() {
    $$('.tk-fold').forEach((f) => { const b = $('[data-fold-toggle]', f); if (b) b.textContent = t(f.dataset.collapsed === 'true' ? 'foldExpand' : 'foldCollapse'); });
  }
  function setLang(lang) {
    state.lang = lang;
    try { localStorage.setItem('moneybti.lang', lang); } catch (e) { /* ignore */ }
    applyStatic();
    renderSamples();
    if (state.kb) renderGallery();
    const s = state.current;
    if (!s) { renderAnalysis(); return; }
    if (s.report) renderReport(s);
    renderAnalysis();
    if (s.txns) renderTable();
    if (s.metrics) renderMetrics(s);
    if (s.persona) { generate(false); return; }
    renderDrawer(s);
  }

  // ---------------------------------------------------------------- helpers
  const pct = (v, d = 1) => (v == null ? '—' : (v * 100).toFixed(d) + '%');
  const money = (v) => '¥' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const card = (code) => (state.kb ? state.kb.cards.find((c) => c.code === code) : null) || { code, name: code, emoji: '🐾', rarity: '', tagline: '' };
  let busyTimer = null;
  function stopTimer() { if (busyTimer) clearInterval(busyTimer); busyTimer = null; }
  function startTimer(est) {
    stopTimer(); const t0 = Date.now();
    const tick = () => { const els = $$('.status__time'); if (!els.length) return; const s = Math.round((Date.now() - t0) / 1000); const txt = tf('stElapsed', { s }) + (est ? ' · ' + tf('stEst', { s: est }) : ''); els.forEach((el) => { el.textContent = txt; }); };
    tick(); busyTimer = setInterval(tick, 1000);
  }
  const CATLAB = `<div class="catlab" aria-hidden="true"><div class="cat"><span class="cat__ear cat__ear--l"></span><span class="cat__ear cat__ear--r"></span><div class="cat__face"><span class="cat__eye"></span><span class="cat__eye"></span><span class="cat__nose"></span></div><span class="cat__paw"></span><span class="cat__tail"></span></div><div class="strip"><div>${'<i></i>'.repeat(12)}</div></div></div>`;
  // 小票弹窗的加载态：生成钱格时先弹出弹窗，放大版猫猫读账单动画 + 计时，生成完成后原地换成小票
  function ticketLoading(on) {
    const ld = $('#ticket-loading'); if (!ld) return;
    $$('#ticket-modal .ticket-modal__themes, #ticket-modal .ticket-modal__body, #ticket-modal .ticket-modal__actions').forEach((el) => { el.hidden = on; });
    ld.hidden = !on;
    if (on) {
      ld.innerHTML = `${CATLAB}<p class="ticket-loading__text">${esc(t('tkLoading'))}<span class="status__dots" aria-hidden="true"></span></p><p class="status__time ticket-loading__time"></p><div class="status__bar" aria-hidden="true"><i></i></div>`;
      $('#ticket-modal').hidden = false;
    } else ld.innerHTML = '';
  }
  function status(msg, kind, thinking, est) {
    const el = $('#status');
    stopTimer();
    if (!msg) { el.hidden = true; return; }
    el.hidden = false; el.className = 'status' + (kind ? ' status--' + kind : '') + (thinking ? ' status--thinking' : '');
    if (kind === 'busy' && thinking) {
      el.innerHTML = `${CATLAB}<div class="status__body"><span class="status__text">${esc(msg)}</span><span class="status__dots" aria-hidden="true"></span><span class="status__time"></span></div><div class="status__bar" aria-hidden="true"><i></i></div>`;
      startTimer(est);
    } else if (kind === 'busy') {
      el.innerHTML = `<span class="spinner" aria-hidden="true"></span><span class="status__text">${esc(msg)}</span><span class="status__dots" aria-hidden="true"></span><div class="status__bar" aria-hidden="true"><i></i></div>`;
    } else el.textContent = msg;
  }
  const BUSY_BTNS = '#upload-trigger, #btn-demo, #btn-confirm, #btn-generate, #btn-regenerate, .segmented__btn, #chk-compare';
  let cardTimer = null, cardT0 = 0;
  function cardProgress(pct) {
    const fill = $('#card-progress-fill'); if (!fill) return;
    fill.style.width = pct + '%'; $('#card-progress .card__progress-bar').setAttribute('aria-valuenow', String(pct));
  }
  function cardBusy(on, target) {
    const box = $('#card-progress'); if (!box) return;
    if (on) {
      if (!cardTimer) { cardT0 = Date.now(); cardProgress(4); }
      box.hidden = false;
      const tick = () => { $('#card-progress-time').textContent = tf('cardThinking', { s: Math.round((Date.now() - cardT0) / 1000) }); };
      tick(); if (!cardTimer) cardTimer = setInterval(tick, 1000);
      setTimeout(() => cardProgress(target), 60);
    } else {
      if (cardTimer) clearInterval(cardTimer); cardTimer = null;
      cardProgress(100);
      setTimeout(() => { if (!cardTimer) { box.hidden = true; cardProgress(0); } }, 700);
    }
  }
  function setBusy(on, active, target) {
    document.body.classList.toggle('is-busy', on);
    cardBusy(on, target || 90);
    $$(BUSY_BTNS).forEach((b) => { b.disabled = on; b.classList.toggle('is-loading', !!(on && active && b.matches(active))); });
    const cardEl = $('#analysis-card'); if (cardEl) cardEl.setAttribute('aria-busy', on ? 'true' : 'false');
  }
  function setStep(n) {
    $$('.step').forEach((s) => { const k = +s.dataset.step; s.classList.toggle('is-done', k < n); s.classList.toggle('is-active', k === n); });
  }
  async function api(path, body, isForm) {
    const r = await fetch(path, { method: body ? 'POST' : 'GET', headers: isForm ? undefined : { 'Content-Type': 'application/json' }, body: isForm ? body : body ? JSON.stringify(body) : undefined });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || r.statusText);
    return data;
  }
  function show(id, on = true) { const el = $(id); if (el) el.hidden = !on; if (on) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  function dimMeta(id) { const d = (state.kb && state.kb.dimensions.find((x) => x.id === id)) || { name: id, emoji: '' }; return { emoji: d.emoji, name: (T().dims || {})[id] || d.name }; }

  // ---------------------------------------------------------------- init
  async function init() {
    try {
      state.kb = await api('/api/personas');
      state.samples = await api('/api/samples');
    } catch (e) { status(tf('stBackend', { msg: e.message }), 'error'); }
    applyStatic(); renderSamples(); if (state.kb) renderGallery();
    $$('.language-switch__btn').forEach((b) => b.addEventListener('click', () => { if (b.dataset.lang !== state.lang) setLang(b.dataset.lang); }));
    $('#upload-trigger').addEventListener('click', () => $('#file-input').click());
    $('#tutorial-trigger').addEventListener('click', () => { $('#tutorial').hidden = false; $('#tutorial .modal__body').scrollTop = 0; });
    $$('[data-tut-tab]').forEach((b) => b.addEventListener('click', () => {
      const k = b.dataset.tutTab;
      $$('[data-tut-tab]').forEach((x) => { const on = x.dataset.tutTab === k; x.classList.toggle('pill--dark', on); x.classList.toggle('pill--ghost', !on); x.setAttribute('aria-selected', on ? 'true' : 'false'); });
      $$('.tut__pane').forEach((p) => { p.hidden = p.id !== 'tut-' + k; });
      $('#tutorial .modal__body').scrollTop = 0;
    }));
    $$('.segmented__btn').forEach((b) => b.addEventListener('click', () => { $$('.segmented__btn').forEach((x) => { x.classList.remove('is-active'); x.setAttribute('aria-checked', 'false'); }); b.classList.add('is-active'); b.setAttribute('aria-checked', 'true'); state.tier = b.dataset.tier; }));
    $('#chk-compare').addEventListener('change', (e) => { state.compare = e.target.checked; });
    $('#file-input').addEventListener('change', (e) => { if (e.target.files[0]) startUpload(e.target.files[0]); });
    const dz = $('#dropzone');
    ['dragenter', 'dragover'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('is-over'); }));
    ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('is-over'); }));
    dz.addEventListener('drop', (e) => { const f = e.dataTransfer.files[0]; if (f) startUpload(f); });
    $('#btn-demo').addEventListener('click', () => startDemo($('#sample-select').value));
    $('#btn-confirm').addEventListener('click', confirmAndMetrics);
    $('#btn-filter-flag').addEventListener('click', () => { state.filterFlag = !state.filterFlag; $('#btn-filter-flag').textContent = state.filterFlag ? t('showAll') : t('filterFlag'); renderTable(); });
    $('#btn-generate').addEventListener('click', () => generate(false));
    $('#btn-regenerate').addEventListener('click', () => generate(true));
    $('#btn-export').addEventListener('click', exportPng);
    $('#btn-copy').addEventListener('click', copyShare);
    $$('.themes .pill').forEach((b) => b.addEventListener('click', () => { const th = b.dataset.theme; $$('.themes .pill').forEach((x) => { const on = x.dataset.theme === th; x.classList.toggle('pill--dark', on); x.classList.toggle('pill--ghost', !on); x.setAttribute('aria-checked', on ? 'true' : 'false'); }); $$('#receipt, #receipt-modal').forEach((el) => { el.dataset.theme = th; }); }));
    $('#modal-export').addEventListener('click', () => exportPng($('#receipt-modal')));
    $('#modal-copy').addEventListener('click', copyShare);
    $('#modal-goto').addEventListener('click', () => { $('#ticket-modal').hidden = true; $('#panel-result').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    $$('[data-nav]').forEach((a) => a.addEventListener('click', (e) => { const n = a.dataset.nav; if (n === 'gallery') { e.preventDefault(); $('#gallery').hidden = false; } if (n === 'about') { e.preventDefault(); $('#about').hidden = false; } }));
    $$('[data-close]').forEach((b) => b.addEventListener('click', () => { b.closest('.modal, .drawer').hidden = true; }));
    document.addEventListener('click', (e) => { const el = e.target.closest('[data-badge]'); if (el) { e.preventDefault(); openBadge(el.dataset.badge); } });
    document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches && e.target.matches('[data-badge]')) openBadge(e.target.dataset.badge); });
    $('#btn-debug').addEventListener('click', () => { $('#drawer').hidden = !$('#drawer').hidden; });
    $$('[data-fold-toggle]').forEach((b) => b.addEventListener('click', () => { const f = b.closest('.tk-fold'); f.dataset.collapsed = f.dataset.collapsed === 'true' ? 'false' : 'true'; updateFoldLabels(); if (f.dataset.collapsed === 'true') f.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
  }
  function renderSamples() {
    const sel = $('#sample-select'); const cur = sel.value;
    sel.innerHTML = (state.samples || []).map((s) => {
      const exp = s.expected ? ' → ' + s.expected.map((c) => pname(card(c))).join('/') : '';
      const note = en() ? '' : ' · ' + esc((s.note || '').slice(0, 34));
      return `<option value="${s.id}" ${s.id === (cur || 'T06') ? 'selected' : ''}>${s.id} · ${esc(groupName(s.group || ''))}${note}${esc(exp)}</option>`;
    }).join('');
  }

  // ---------------------------------------------------------------- ① upload / demo
  async function startUpload(file) {
    state.file = file;
    uploadStatus('uploadSelected', { name: file.name });
    const run = async (tier) => { const fd = new FormData(); fd.append('file', file); fd.append('tier', tier); return api('/api/upload', fd, true); };
    await start(run, file.name);
  }
  async function startDemo(sample) {
    const run = (tier) => api('/api/demo', { sample, tier });
    await start(run, tf('demoBill', { id: sample }));
  }
  async function start(run, label) {
    state.sessions = {}; state.overrides = {}; state.current = null;
    ['#panel-classify', '#panel-metrics', '#panel-result'].forEach((id) => { $(id).hidden = true; });
    renderAnalysis();
    $('#compare-grid').hidden = true;
    setStep(1);
    setPhase('busy'); uploadStatus('uploadReading');
    setBusy(true, '#upload-trigger, #btn-demo', 35);
    try {
      if (state.compare) {
        status(tf('stCompareParse', { label }), 'busy');
        state.sessions.basic = await run('basic');
        status(t('stCompareVip'), 'busy', true);
        state.sessions.vip = await run('vip');
        state.current = state.sessions[state.tier] || state.sessions.basic;
      } else {
        status(tf(state.tier === 'vip' ? 'stParseVip' : 'stParseBasic', { label }), 'busy', state.tier === 'vip');
        state.sessions[state.tier] = await run(state.tier);
        state.current = state.sessions[state.tier];
      }
      status('');
      uploadStatus('uploadDone', { name: label });
      renderReport(state.current);
      renderAnalysis();
      renderTable();
      setStep(2);
      show('#panel-classify');
      renderDrawer(state.current);
    } catch (e) { status(tf('stError', { msg: e.message }), 'error'); setPhase('idle'); uploadStatus('uploadFailed'); }
    finally { setBusy(false); }
  }
  function renderAnalysis() {
    const s = state.current, empty = $('#analysis-empty'), content = $('#analysis-content'), cardEl = $('#analysis-card');
    if (!s || !s.metrics) {
      empty.hidden = false; content.hidden = true;
      $('#analysis-waiting-text').textContent = s && s.report ? tf('analysisRead', { count: s.report.valid }) + (en() ? '. ' : '，') + t('analysisWaitingText') : t('analysisWaitingText');
      cardEl.dataset.state = s ? 'loading' : 'idle';
      return;
    }
    empty.hidden = true; content.hidden = false;
    const m = s.metrics, p = s.persona;
    if (p) {
      const c = card(p.primary_persona), cand = (s.retrieval.candidates || []).find((x) => x.code === p.primary_persona) || {};
      $('#persona-name').textContent = pname(c); $('#persona-emoji').textContent = c.emoji || '🐾';
      $('#persona-code').textContent = c.code; $('#persona-subtitle').textContent = ptag(c) ? ' · ' + ptag(c) : '';
      $('#persona-badge').textContent = 'MATCH ' + (cand.match != null ? Math.round(cand.match) : 100) + '%'; $('#persona-badge').hidden = false;
      $('#persona-summary').textContent = p.summary || '';
      cardEl.dataset.state = 'success';
    } else {
      $('#persona-name').textContent = t('analysisWaitingTitle'); $('#persona-emoji').textContent = '';
      $('#persona-code').textContent = ''; $('#persona-subtitle').textContent = '';
      $('#persona-badge').hidden = true;
      $('#persona-summary').textContent = tf('analysisRead', { count: m.txn_count }) + (en() ? '. ' : '，') + t('analysisWaitingText');
      cardEl.dataset.state = 'loading';
    }
    const shares = Object.entries(m.category_share || {}).filter(([c]) => c !== 'UNC').sort((a, b) => b[1] - a[1]).slice(0, 6);
    const maxv = shares.length ? shares[0][1] : 1;
    $('#category-stats').innerHTML = shares.map(([c, v], i) => `<div class="stat" data-category="${c}"><p class="stat__label">${CAT_EMOJI[c] || ''} ${esc(catName(c))}</p><p class="stat__value">${money(m.category_amount[c] || 0)}</p><div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(v * 100)}"><div class="bar__fill ${i % 3 === 1 ? 'bar__fill--mint' : i % 3 === 2 ? 'bar__fill--yellow' : ''}" style="width:${(v / maxv) * 100}%"></div></div><p class="stat__pct">${pct(v)}</p></div>`).join('');
    $('#total-label').textContent = t('analysisTotal');
    $('#total-amount').textContent = money(m.total);
  }
  function renderReport(s) {
    const r = s.report, ex = ['R1_not_expense', 'R2_refund_closed', 'R3_zero', 'R4_transfer'];
    const items = [[t('rSource'), r.source === 'wechat' ? t('wechat') : t('alipay')], [t('rTier'), s.tier === 'vip' ? t('vip') : t('basic')], [t('rRaw'), r.raw], [t('rValid'), r.valid],
      ...ex.filter((k) => r[k]).map((k) => [t(k), '−' + r[k]]),
      [t('rPeriod'), `${r.period_start} ~ ${r.period_end}（${tf('days', { n: r.period_days })}${r.period_from_header ? '' : t('fromTxns')}）`]];
    if (s.m3) items.push([t('rM3'), tf('m3Rows', { n: s.m3.llm_rows, low: (s.m3.low_confidence_ids || []).length })]);
    $('#report-body').innerHTML = `<p class="persona__kicker">${t('reportTitle')}</p><div class="report">${items.map(([k, v], i) => `<div class="report__item ${i >= items.length - (s.m3 ? 2 : 1) ? 'report__wide' : ''}"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('')}</div>`;
  }

  // ---------------------------------------------------------------- ② table
  const flagged = (tx) => !tx.category || (tx.confidence != null && tx.confidence < 0.5) || tx.ambiguous;
  function renderTable() {
    const s = state.current, vip = s.tier === 'vip', st = s.stats, L = T().layers || {};
    $('#classify-stats').textContent = tf('classifyStats', { rule: st.rule_rows, llm: st.llm_rows, unc: st.unclassified, low: st.low_confidence, amb: st.ambiguous });
    const cols = ['colTime', 'colMerchant', 'colDesc', 'colAmount', 'colCat', 'colSource', 'colConf'].concat(vip ? ['colBrand', 'colMeal', 'colScene', 'colImpulse'] : []);
    $('#txn-head').innerHTML = cols.map((c) => `<th>${t(c)}</th>`).join('');
    const opts = (cur) => `<option value="">${t('unclassified')}</option>` + Object.keys(T().cats || I18N.zh.cats).map((c) => `<option value="${c}" ${c === cur ? 'selected' : ''}>${c} ${catName(c)}</option>`).join('');
    const rows = s.txns.filter((tx) => !state.filterFlag || flagged(tx));
    $('#txn-body').innerHTML = rows.map((tx) => {
      const cur = state.overrides[tx.id] !== undefined ? state.overrides[tx.id] : tx.category || '';
      const src = state.overrides[tx.id] !== undefined ? `<span class="tag tag--user">${t('srcUser')}</span>` : tx.source_of_label === 'llm' ? `<span class="tag tag--llm">${t('srcLLM')}</span>` : `<span class="tag">${L[tx.layer] || tx.layer}${tx.rule_keyword ? ' · ' + esc(tx.rule_keyword) : ''}</span>`;
      const flags = [tx.ambiguous ? `<span class="tag tag--warn">${t('flagR8')}</span>` : '', tx.masked ? `<span class="tag">${t('flagMasked')}</span>` : '', tx.outlier ? `<span class="tag tag--warn">${t('flagR7')}</span>` : ''].join(' ');
      const v = tx.vip || {};
      return `<tr class="${state.overrides[tx.id] !== undefined ? 'is-user' : flagged(tx) ? 'is-flag' : ''}" data-id="${tx.id}">
        <td class="num">${tx.time.slice(5, 16).replace('T', ' ')}</td>
        <td>${esc(tx.merchant)} ${flags}</td>
        <td class="desc" title="${esc(tx.description)}">${esc(tx.description) || '—'}</td>
        <td class="num">${money(tx.amount)}</td>
        <td><select data-id="${tx.id}">${opts(cur)}</select></td>
        <td>${src}</td>
        <td class="num">${tx.confidence != null ? (tx.confidence * 100).toFixed(0) + '%' : '—'}</td>
        ${vip ? `<td>${esc(v.brand || '')}</td><td>${esc(v.meal_slot || '')}</td><td>${esc(v.scene || '')}</td><td class="num">${v.impulse != null ? v.impulse : ''}</td>` : ''}
      </tr>`;
    }).join('');
    $$('#txn-body select').forEach((sel) => sel.addEventListener('change', () => { const tx = s.txns.find((x) => x.id === sel.dataset.id); if (sel.value !== (tx.category || '')) state.overrides[sel.dataset.id] = sel.value; else delete state.overrides[sel.dataset.id]; renderTable(); }));
  }

  // ---------------------------------------------------------------- ③ metrics
  async function confirmAndMetrics() {
    const ov = {}; Object.entries(state.overrides).forEach(([k, v]) => { if (v) ov[k] = v; });
    setBusy(true, '#btn-confirm', 65);
    try {
      status(t('stMetrics'), 'busy');
      const jobs = state.compare ? ['basic', 'vip'] : [state.current.tier];
      for (const tier of jobs) {
        const r = await api('/api/confirm', { session_id: state.sessions[tier].session_id, overrides: tier === state.current.tier ? ov : {} });
        Object.assign(state.sessions[tier], r);
      }
      status('');
      renderMetrics(state.current);
      setStep(3);
      show('#panel-metrics');
      renderDrawer(state.current);
    } catch (e) { status(tf('stError', { msg: e.message }), 'error'); }
    finally { setBusy(false); }
  }
  function renderMetrics(s) {
    renderAnalysis();
    const m = s.metrics, ret = s.retrieval;
    $('#metrics-lead').textContent = tf('metricsLead', { n: m.txn_count, total: money(m.total), level: en() ? ({ '充足': 'sufficient', '勉强': 'marginal', '不足': 'insufficient' }[m.data_level] || m.data_level) : m.data_level }) + (s.warnings || []).map(warnText).join(en() ? '; ' : '；') + (ret.close_call ? t('closeCallNote') : '');
    const shares = Object.entries(m.category_share);
    const maxv = Math.max(...shares.map(([, v]) => v), 0.01);
    $('#cat-bars').innerHTML = shares.map(([c, v]) => `<div class="catbar"><span>${CAT_EMOJI[c]} ${catName(c)}</span><div class="bar"><div class="bar__fill" style="width:${(v / maxv) * 100}%"></div></div><span>${pct(v)}</span><span class="muted">${money(m.category_amount[c] || 0)}</span></div>`).join('')
      + (m.unclassified_amount ? `<div class="catbar"><span>❔ ${t('uncRow')}</span><div class="bar"></div><span>${tf('uncCount', { p: pct(m.unclassified_ratio, 0) })}</span><span class="muted">${money(m.unclassified_amount)}</span></div>` : '');
    $('#metrics-total').innerHTML = `<span class="total__label">${t('total')} · ${m.period_start} ~ ${m.period_end}</span><span class="total__value">${money(m.total)}</span>`;
    const chips = [[t('cTxn'), `${m.txn_count} / ${m.txn_per_day}`], [t('cActive'), `${m.active_days} / ${m.period_days}`], [t('cMedian'), money(m.median_amount)], [t('cSmall'), pct(m.small_txn_ratio, 0)], [t('cBig'), pct(m.big_ticket_share, 0)], [t('cOnline'), pct(m.online_share, 0)], [t('cNec'), pct(m.necessity_share, 0)], [t('cLate'), pct(m.late_night_ratio, 0)], [t('cDelivery'), pct(m.delivery_ratio, 0)], [t('cBev'), m.beverage_per_week], [t('cCommute'), pct(m.commute_count_ratio, 0)], [t('cWeekend'), pct(m.weekend_share, 0)], [t('cMaxDay'), tf('cMaxDayV', { d: m.max_day, p: pct(m.max_day_share, 0), n: m.max_day_txn_count })]];
    if (m.impulse_share != null) chips.push([t('cImpulse'), pct(m.impulse_share, 0)], [t('cMeal'), Object.entries(m.meal_slot_dist || {}).map(([k, v]) => `${k} ${pct(v, 0)}`).join(' ')], [t('cScene'), Object.entries(m.scene_dist || {}).slice(0, 3).map(([k, v]) => `${k} ${pct(v, 0)}`).join(' ')]);
    if (m.outliers && m.outliers.length) chips.push([t('cOutlier'), m.outliers.map((o) => `${o.date.slice(5)} ${o.merchant} ${money(o.amount)}`).join('；')]);
    $('#metric-chips').innerHTML = chips.map(([k, v]) => `<div class="chip">${esc(k)}<strong>${esc(v)}</strong></div>`).join('');
    const topCard = ret.cards.find((c) => c.explain && c.explain.dims);
    $('#radar').innerHTML = radarSvg(m.dimensions, topCard);
    const badges = (ret.badges || []).map((b) => badgeChip(b, 'pill pill--yellow')).join(' ');
    $('#cands').innerHTML = ret.cards.map((c, i) => candHtml(c, i === 0)).join('') + (badges ? `<div class="badges"><span class="small muted">${t('badges')}</span> ${badges}</div>` : '');
  }
  function radarSvg(dims, protoCard) {
    const keys = Object.keys(dims); const n = keys.length; const R = 120, cx = 170, cy = 160;
    const pt = (i, r) => { const a = -Math.PI / 2 + (2 * Math.PI * i) / n; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; };
    const ring = (v, cls) => `<polygon class="ring ${cls}" points="${keys.map((_, i) => pt(i, (R * v) / 100).join(',')).join(' ')}"/>`;
    const poly = `<polygon class="poly" points="${keys.map((k, i) => pt(i, (R * dims[k]) / 100).join(',')).join(' ')}"/>`;
    let proto = '';
    if (protoCard) { const pm = {}; protoCard.explain.dims.forEach((d) => { pm[d.dim] = d.proto; }); proto = `<polygon class="proto" points="${keys.map((k, i) => pt(i, (R * (pm[k] != null ? pm[k] : 0)) / 100).join(',')).join(' ')}"/>`; }
    const labels = keys.map((k, i) => { const [x, y] = pt(i, R + 22); const d = dimMeta(k); return `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle">${d.emoji}${d.name} ${dims[k]}</text>`; }).join('');
    return `<svg class="radar" viewBox="0 0 340 320">${ring(100, '')}${ring(60, 'ring60')}${ring(30, '')}${proto}${poly}${labels}</svg>` + (protoCard ? `<p class="muted small" style="text-align:center">${tf('radarCaption', { name: protoCard.emoji + ' ' + pname(protoCard) })}</p>` : '');
  }
  function fmtVal(v) { return v == null ? '—' : typeof v === 'number' ? (v <= 1 && v > 0 && !Number.isInteger(v) ? pct(v, 0) : Math.round(v * 100) / 100) : esc(String(v)); }
  function condRow(r) {
    const thr = Array.isArray(r.threshold) ? r.threshold.join('/') : (typeof r.threshold === 'number' && r.threshold <= 1 && !Number.isInteger(r.threshold) ? pct(r.threshold, 0) : r.threshold);
    if (!r.available) return `<div class="fit is-low"><span>${esc(plabel(r))}</span><div class="bar"></div><span class="muted">${t('needHistory')}</span></div>`;
    return `<div class="fit ${r.ok ? '' : 'is-low'}"><span>${r.ok ? '✓' : '✗'} ${esc(plabel(r))}</span><div class="bar"><div class="bar__fill" style="width:${r.score}%"></div><div class="bar__mark" style="left:60%"></div></div><span>${fmtVal(r.value)} / ${thr}</span></div>`;
  }
  function candHtml(c, top) {
    const ex = c.explain || {};
    let body = '';
    if (ex.mode === 'count') body = `<p class="small muted">${tf('condSummary', { ok: ex.ok_count, n: ex.available, need: ex.min_required })}</p>` + ex.conditions.map(condRow).join('');
    else if (ex.mode === 'any') body = ex.groups.map((g) => `<div class="group ${g.hit ? 'is-hit' : ''}"><p class="small muted">${tf('group', { i: g.index + 1 })}${g.index === 0 ? t('groupMain') : t('groupAlt')} · ${g.hit ? t('hit') : t('miss')} · ${g.match}</p>${g.conditions.map(condRow).join('')}</div>`).join('');
    const fits = (ex.dims || []).map((d) => `<div class="fit ${d.proto < 50 ? 'is-low' : ''}"><span>${d.emoji} ${dimMeta(d.dim).name}</span><div class="bar"><div class="bar__fill" style="width:${d.score}%"></div><div class="bar__mark" style="left:${d.proto}%"></div></div><span>${d.score} / ${d.proto}</span></div>`).join('');
    const meta = c.override ? t('override') : c.co_display ? t('coDisplay') : c.hit ? t('hit') : t('near');
    return `<div class="cand ${top ? 'is-top' : ''}"><div class="cand__head"><span class="cand__name">${c.emoji} ${esc(pname(c))}</span><span class="cand__match">${c.match}%</span></div>
      <div class="cand__meta">${c.code} · ${esc(rarity(c.rarity))} · ${meta}${c.group === 'special' ? ' · ' + t('special') : ''}</div>
      <p class="small muted">${esc(ptag(c) || '')}</p>${body}${fits}</div>`;
  }

  // ---------------------------------------------------------------- ④ generate
  async function generate(regen) {
    setBusy(true, regen ? '#btn-regenerate' : '#btn-generate', 92);
    try {
      ticketLoading(true);
      status(t(regen ? 'stRegen' : 'stGenerate'), 'busy', true, 10);
      const jobs = state.compare ? ['basic', 'vip'] : [state.current.tier];
      for (const tier of jobs) {
        const r = await api('/api/generate', { session_id: state.sessions[tier].session_id, regenerate: regen, lang: state.lang });
        Object.assign(state.sessions[tier], r);
      }
      status('');
      ticketLoading(false);
      renderResult(state.current);
      if (state.compare) renderCompare();
      setStep(4);
      show('#panel-result');
      renderDrawer(state.current);
      $('#ticket-modal').hidden = false; $('#ticket-modal .modal__box').scrollTop = 0;
    } catch (e) { ticketLoading(false); $('#ticket-modal').hidden = true; status(tf('stError', { msg: e.message }), 'error'); }
    finally { setBusy(false); }
  }
  function renderResult(s) {
    setPhase('ready'); renderAnalysis();
    const p = s.persona, c = card(p.primary_persona), sec = p.secondary_persona ? card(p.secondary_persona) : null, ret = s.retrieval;
    const cand = ret.candidates.find((x) => x.code === p.primary_persona) || {};
    const rv = s.review || {};
    $('#result-lead').textContent = tf('resultLead', { tier: t(s.tier === 'vip' ? 'tierVipName' : 'tierBasicName'), pass: t(rv.pass ? 'passed' : 'failed'), n: rv.attempts });
    const catImg = copyOf(c.code).image;
    $('#persona-col').innerHTML = `<article class="card persona-card"><div class="card__head"><span class="card__head-label">${t('cardHead')} · ${s.tier === 'vip' ? 'VIP 👑' : 'BASIC'}</span><span class="card__paw">🐾</span></div>
      <div class="card__body"><div class="persona"><div><p class="persona__kicker">${t('moneyType')}</p><h2 class="persona__name">${esc(pname(c))} ${c.emoji}</h2><p class="persona__code">${c.code} · ${esc(ptag(c))}</p></div>${catImg ? `<img class="persona__cat" src="${catImg}" alt="">` : ''}<span class="badge">MATCH ${cand.match != null ? cand.match : 100}%</span></div>
      <p class="persona__summary">${esc(p.summary)}</p><p class="persona__code" style="margin-top:8px">「${esc(p.one_liner)}」 · ${t('keyword')} ${esc(p.keyword || '')} · ${t('rarity')} ${esc(rarity(p.rarity || c.rarity))} · ${t('confidence')} ${esc((T().confVal || {})[p.confidence] || p.confidence)}</p>
      ${pinterp(c) ? `<p class="persona__interp">${esc(pinterp(c))}</p>` : ''}
      ${ptraits(c).length ? `<div class="pills">${ptraits(c).map((x) => `<span class="tag">${esc(x)}</span>`).join('')}</div>` : ''}
      ${(ret.badges || []).length ? `<div class="pills">${ret.badges.map((b) => badgeChip(b, 'pill pill--yellow')).join('')}</div>` : ''}
      <ul class="evidence">${(p.evidence || []).map((e) => `<li><span>${esc(e.text)}</span><span class="val">${esc(e.value)}</span></li>`).join('')}</ul>
      ${sec ? `<p class="persona__kicker" style="margin-top:14px">${t('secondary')}</p><p><strong>${sec.emoji} ${esc(pname(sec))}</strong> · ${t('matchLabel')} ${(ret.candidates.find((x) => x.code === sec.code) || {}).match || '—'}%</p>` : ''}
      ${(p.modifier_tags || []).length ? `<div class="pills">${p.modifier_tags.map((x) => `<span class="pill pill--yellow">${esc(x)}</span>`).join('')}</div>` : ''}
      ${(p.highlights || []).length ? `<p class="persona__kicker" style="margin-top:14px">${t('highlights')}</p>${p.highlights.map((h) => `<div class="hl"><div class="hl__meta">${esc(h.date)} · ${esc(h.brand)} · ${money(h.amount)}</div>${esc(h.text)}</div>`).join('')}` : ''}
      <p class="review-note ${rv.pass ? '' : 'review-note--warn'}">${t(rv.pass ? 'reviewOk' : 'reviewFallback')}${(rv.violations || []).length ? ' · ' + rv.violations.slice(0, 3).map(esc).join('；') : ''}</p>
      </div></article>`;
    renderReceipt(s);
  }
  function renderReceipt(s) {
    const p = s.persona, c = card(p.primary_persona), m = s.metrics, ret = s.retrieval, cp = s.copy || {};
    const copy = copyOf(c.code);
    const cand = ret.candidates.find((x) => x.code === c.code) || {};
    const match = cand.match != null ? Math.round(cand.match) : 100;
    const idx = state.kb ? state.kb.cards.findIndex((x) => x.code === c.code) + 1 : 0;
    const number = String(4870 + Math.max(idx, 0)).padStart(6, '0');
    const period = (m.period_start || '').slice(0, 7);
    const secCode = p.secondary_persona, sec = secCode ? card(secCode) : null;
    const secCand = secCode ? ret.candidates.find((x) => x.code === secCode) : null;
    const badges = ret.badges || [];
    const title = copy.title && copy.title.length ? copy.title : [c.name, ''];
    const longest = Math.max(...title.map((x) => String(x).length));
    const quote = copy.quote && copy.quote.length === 2 ? copy.quote : [c.tagline_en || c.tagline || '', ''];
    const ex = (ret.cards.find((x) => x.code === c.code) || {}).explain || {};
    let rows = ex.conditions || (ex.groups ? (ex.groups[ex.group_index || 0] || ex.groups[0]).conditions : []);
    rows = (rows || []).filter((r) => r.available).slice(0, 6);
    // 小票只放 3 条：按得分取最高的三条特征
    let indices = rows.map((r) => ({ label: String(plabel(r)).replace(/（[^）]*）|\([^)]*\)/g, '').trim(), score: Math.round(r.score), ok: r.ok })).sort((a, b) => b.score - a.score).slice(0, 3);
    if (!indices.length) indices = Object.entries(m.dimensions).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => ({ label: dimMeta(k).emoji + dimMeta(k).name, score: v, ok: v >= 60 }));
    const top = (m.top_merchants || [])[0] || ['—', ''];
    const signal = (p.evidence && p.evidence[0] && p.evidence[0].text) || p.keyword || '—';
    const traits = ptraits(c).map((x) => `<span>${esc(x)}</span>`).join('');
    const tags = (p.modifier_tags || []).map((x) => `<span>${esc(x)}</span>`).join('');
    const evidence = (p.evidence || []).slice(0, 4).map((e) => `<li>${esc(e.text)} <b>${esc(e.value)}</b></li>`).join('');
    const highlights = (p.highlights || []).map((h) => `<li>${esc(h.date)} · ${esc(h.brand)} · ${money(h.amount)}：${esc(h.text)}</li>`).join('');
    const findingTitle = en() ? (copy.findingTitle || c.tagline_en || c.tagline) : (c.tagline || p.one_liner);
    const findingBody = en() ? (c.interpretation_en || copy.description || c.interpretation) : (c.interpretation || p.summary);
    const findingExtra = en() ? '' : (copy.description ? `<p class="tk-en">${esc(copy.description)}</p>` : '');
    const html = `
      <div class="grain" aria-hidden="true"></div>
      <header class="tk-head">
        <div class="tk-inst"><span class="tk-seal" aria-hidden="true">¥</span><div><p class="tk-brand">${t('brandName')}</p><small>${t('tkArchive')}</small></div></div>
        <div class="tk-filing"><span>${t('tkFile')} / ${String(idx).padStart(2, '0')}—${c.code}</span><span>${t('tkIssued')} / ${period}</span><span>${t(s.tier === 'vip' ? 'tkVip' : 'tkBasic')}</span></div>
      </header>
      <section class="tk-hero">
        <p class="tk-eyebrow">${t('tkPersona')} · ${esc(copy.category || pax(c) || '')}</p>
        <div class="tk-lockup"><h1><span>${esc(title[0])}</span><span>${esc(title[1] || '')}</span></h1><p class="tk-code"><b>${c.code}</b><i>${t('tkNo')} ${number}</i></p></div>
        <figure class="tk-cat">${copy.image ? `<img src="${copy.image}" alt="${esc(copy.alt || c.name)}">` : `<span class="tk-cat-empty">${c.emoji}</span>`}<figcaption>${esc(copy.caption || 'FIG. — ' + c.name)}</figcaption></figure>
        <blockquote class="tk-quote"><span>${esc(quote[0])}</span>${quote[1] ? `<span>${esc(quote[1])}</span>` : ''}</blockquote>
        <div class="tk-reg" aria-hidden="true">＋ ＋ ＋</div>
      </section>
      <section class="tk-stub">
        <div><span>${t('tkType')}</span><b>${c.emoji} ${esc(pname(c))}${sec ? `<small>${secCand && secCand.co_display ? t('tkCoDisplay') : t('tkSecondary')} ${sec.emoji} ${esc(pname(sec))}${secCand ? ' · ' + Math.round(secCand.match) + '%' : ''}</small>` : ''}</b></div>
        <div class="tk-match"><span>${t('tkMatch')}</span><strong><span>${match}</span><sup>%</sup></strong></div>
        <div><span>${t('tkRarity')}</span><b>${esc(rarity(p.rarity || c.rarity))}${badges.length ? `<small>${badges.map((b) => b.emoji).join(' ')} ${tf('tkBadgeCount', { n: badges.length })}</small>` : ''}</b></div>
        <div class="tk-cut" aria-hidden="true">${t('tkCut')}</div>
      </section>
      <section class="tk-ledger">
        <div class="tk-sect"><div><span>${t('tkExtract')}</span><h2>${t('tkSnapshot')}</h2></div><span>${esc(m.period_start || '')} ~ ${esc(m.period_end || '')}</span></div>
        <dl class="tk-facts">
          <div><dt>${t('tkTotal')}</dt><dd>${money(m.total)}</dd></div>
          <div><dt>${t('tkTxns')}</dt><dd>${tf('tkTxnsV', { n: m.txn_count, d: m.active_days })}</dd></div>
          <div><dt>${t('tkStop')}</dt><dd>${esc(top[0])}${top[1] ? ' × ' + top[1] : ''}</dd></div>
          <div><dt>${t('tkSignal')}</dt><dd>${esc(signal)}</dd></div>
        </dl>
        <span class="tk-label">${t('tkTraits')}</span><div class="tk-chips">${traits || '<span>—</span>'}</div>
        ${badges.length ? `<span class="tk-label">${t('tkBadges')}</span><div class="tk-chips">${badges.map((b) => badgeChip(b, 'tk-badge')).join('')}</div>` : ''}
        ${tags ? `<span class="tk-label">${t('tkTags')}</span><div class="tk-chips">${tags}</div>` : ''}
        <span class="tk-label">${t('tkIndices')}</span>
        <div class="tk-indices">${indices.map((r) => `<div class="tk-index ${r.ok ? 'is-ok' : ''}" style="--score:${r.score}%"><p><span>${esc(r.label)}</span><b>${r.score}</b></p><i aria-hidden="true"></i></div>`).join('')}</div>
        <div class="tk-note"><span class="tk-label">${t('tkNote')}</span>${esc(p.summary)}${evidence ? `<ul>${evidence}</ul>` : ''}${highlights ? `<ul>${highlights}</ul>` : ''}</div>
      </section>
      <section class="tk-finding">
        <p class="tk-vnote">${t('tkObservation')} ${number}</p>
        <div><span class="tk-kicker">${t('tkFinding')}</span><h2>${esc(findingTitle)}</h2><p>${esc(findingBody)}</p>${findingExtra}</div>
      </section>
      <footer class="tk-foot">
        <div class="tk-barcode" aria-hidden="true"></div>
        <div><p>${esc(cp.slogan || copy.tagline || '')}</p><span>${period.replace('-', '')} · ${c.code} · ${esc(cp.thank_you_line || '')} · ${t('tkFootTail')}</span></div>
        <span class="tk-endmark">Mβ</span>
      </footer>`;
    // 面板 ④ 的小票 + 首屏右栏（数据质量报告下方）的同一张小票
    $$('#receipt, #receipt-modal').forEach((el) => { el.dataset.titleSize = longest > 13 ? 'long' : longest > 9 ? 'medium' : 'short'; el.innerHTML = html; });
    updateFoldLabels();
  }
  function renderCompare() {
    const b = state.sessions.basic, v = state.sessions.vip;
    if (!b || !v || !b.persona || !v.persona) return;
    const col = (s, title) => { const p = s.persona, c = card(p.primary_persona), sec = p.secondary_persona ? card(p.secondary_persona) : null, m = s.metrics, calls = (s.llm_calls || []).filter((x) => !x.error);
      const tok = calls.reduce((a, x) => a + (x.prompt_tokens || 0) + (x.completion_tokens || 0), 0);
      return `<div class="compare__col"><h3>${title}</h3><div class="compare__kv"><span>${t('cmpPrimary')}</span><span>${c.emoji} ${esc(pname(c))} · ${(s.retrieval.candidates.find((x) => x.code === c.code) || {}).match || 100}%</span></div>
        <div class="compare__kv"><span>${t('cmpSecondary')}</span><span>${sec ? sec.emoji + esc(pname(sec)) : '—'} ${(p.modifier_tags || []).join(' ')}</span></div>
        <div class="compare__kv"><span>${t('cmpUnc')}</span><span>${pct(m.unclassified_ratio, 0)}</span></div>
        <div class="compare__kv"><span>${t('cmpDims')}</span><span>${Object.keys(m.dimensions).length}</span></div>
        <div class="compare__kv"><span>${t('cmpHl')}</span><span>${tf('cmpHlV', { n: (p.highlights || []).length })}</span></div>
        <div class="compare__kv"><span>${t('cmpLLM')}</span><span>${calls.length} / ${tok}</span></div>
        <p style="margin-top:10px;font-size:12px">${esc(p.summary)}</p></div>`; };
    $('#compare-grid').innerHTML = col(b, t('cmpBasic')) + col(v, t('cmpVip'));
    $('#compare-grid').hidden = false;
  }
  async function exportPng(target) {
    const el = target && target.nodeType === 1 ? target : $('#receipt');
    try { const canvas = await html2canvas(el, { scale: 2, backgroundColor: null, useCORS: true }); const a = document.createElement('a'); a.download = `moneybti_${state.current.persona.primary_persona}.png`; a.href = canvas.toDataURL('image/png'); a.click(); }
    catch (e) { status(tf('stExportFail', { msg: e.message }), 'error'); }
  }
  async function copyShare() {
    const p = state.current.persona, c = card(p.primary_persona), cand = state.current.retrieval.candidates.find((x) => x.code === c.code) || {};
    const text = tf('shareText', { emoji: c.emoji, name: pname(c), match: cand.match || 100, summary: p.summary, line: p.one_liner });
    try { await navigator.clipboard.writeText(text); status(t('stCopied')); setTimeout(() => status(''), 1500); } catch { status(text); }
  }

  // ---------------------------------------------------------------- gallery / drawer
  function renderGallery() {
    const kb = state.kb;
    const lab = (x) => (en() ? (x.label_en || x.label) : x.label);
    const sig = (c) => c.mode === 'count' ? tf('gCount', { n: c.min_conditions }) + c.conditions.map((x) => lab(x) + (x.requires_history ? '*' : '')).join(en() ? '; ' : '；') : (c.rule_groups || []).map((g, i) => tf('gGroup', { i: i + 1 }) + g.map(lab).join(t('gAnd'))).join(en() ? ' | ' : '｜');
    $('#gallery-grid').innerHTML = kb.cards.map((c) => `<div class="gcard">${copyOf(c.code).image ? `<img class="gthumb" src="${copyOf(c.code).image}" alt="" loading="lazy">` : ''}<div class="gcard__name">${c.emoji} ${esc(pname(c))}</div><div class="gcard__meta">${c.code} · ${c.group}${c.override ? ' · override' : ''} · ${esc(pax(c) || '')} · ${esc(rarity(c.rarity))}</div><div>${esc(ptag(c))}</div>${ptraits(c).length ? `<div class="pills">${ptraits(c).map((x) => `<span class="tag">${esc(x)}</span>`).join('')}</div>` : ''}<div class="gcard__sig">${esc(sig(c))}</div></div>`).join('')
      + (kb.badges || []).map((b) => `<div class="gcard gcard--badge" data-badge="${b.code}"><img class="gthumb" src="${bimg(b)}" alt="" loading="lazy"><div class="gcard__name">${b.emoji} ${esc(bname(b))} <span class="tag">${t('gBadge')}</span></div><div>${esc(bline(b) || '')}</div><div class="gcard__sig">${esc((T().badgeHowText || {})[b.code] || '')}</div></div>`).join('')
      + `<div class="gcard" style="grid-column:1/-1"><div class="gcard__name">${t('gDims')}</div><div class="gcard__sig">${kb.dimensions.map((d) => `${d.emoji}${dimMeta(d.id).name}${d.vip_only ? ' (VIP)' : ''}`).join(' ｜ ')}</div></div>`;
  }
  function renderDrawer(s) {
    const dec = (s.decisions || []).map((d) => `<li><b>${esc(d.point)}</b> → ${esc(d.branch)} ${esc(JSON.stringify(Object.fromEntries(Object.entries(d).filter(([k]) => !['point', 'branch'].includes(k)))))}</li>`).join('');
    const calls = (s.llm_calls || []).map((c, i) => c.error ? `<details><summary>#${i + 1} ${esc(c.module)} · ${t('dError')}</summary><pre>${esc(c.error)}</pre></details>` : `<details><summary>#${i + 1} ${esc(c.module)}${c.attempt ? ' · ' + t('dAttempt') + ' ' + c.attempt + (t('dAttemptUnit') || '') : ''} · ${c.cached ? t('dCached') : c.latency + 's'} · ${c.prompt_tokens}+${c.completion_tokens} tokens${c.model ? ' · ' + esc(c.model) : ''}</summary><p>SYSTEM</p><pre>${esc(c.system)}</pre><p>USER</p><pre>${esc(c.user)}</pre><p>RAW</p><pre>${esc(c.raw)}</pre></details>`).join('');
    $('#drawer-body').innerHTML = `<p>${t('dDecisions')}</p><ul class="dlist">${dec || '<li>—</li>'}</ul><p>${tf('dCalls', { n: (s.llm_calls || []).length })}</p>${calls || `<p>${t('dNone')}</p>`}`;
  }

  init();
})();
