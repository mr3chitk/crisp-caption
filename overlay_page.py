from __future__ import annotations


def qt_overlay_html(
    ws_url: str,
    font_px: int,
    *,
    hold_sec: float = 2.0,
    hold_per_char_sec: float = 0.04,
    fade_sec: float = 4.0,
) -> str:
    return subtitle_overlay_html(
        ws_url=ws_url,
        body_css="align-items: start; display: grid; padding: 8px 8px 8px;",
        main_font=f"{max(16, round(font_px * 0.85))}px",
        partial_font=f"{max(16, round(font_px * 0.7))}px",
        trans_font=f"{max(16, round(font_px * 1.0))}px",
        main_weight="650",
        main_line_height="1.2",
        main_margin_top="12px",
        partial_weight="650",
        partial_line_height="1.2",
        partial_margin_top="12px",
        trans_weight="650",
        trans_margin_top="4px",
        status_font="22px",
        status_weight="650",
        initial_status="",
        connected_status="",
        show_connected_briefly=True,
        hold_sec=hold_sec,
        hold_per_char_sec=hold_per_char_sec,
        fade_sec=fade_sec,
    )


def obs_overlay_html(
    ws_url: str,
    *,
    hold_sec: float = 2.0,
    hold_per_char_sec: float = 0.04,
    fade_sec: float = 4.0,
    font: float = 1.0,
    pos: str = "bottom",
    demo: bool = False,
) -> str:
    body_css = (
        "align-items: start; display: grid; padding: 9vh 7vw 0;"
        if pos == "top"
        else "align-items: end; display: grid; padding: 0 7vw 9vh;"
    )
    return subtitle_overlay_html(
        ws_url=ws_url,
        body_css=body_css,
        main_font=f"clamp({28 * font:.0f}px, {4.2 * font:.2f}vw, {58 * font:.0f}px)",
        partial_font=f"clamp({20 * font:.0f}px, {2.8 * font:.2f}vw, {38 * font:.0f}px)",
        trans_font=f"clamp({24 * font:.0f}px, {3.4 * font:.2f}vw, {48 * font:.0f}px)",
        main_weight="780",
        main_line_height="1.28",
        main_margin_top="10px",
        partial_weight="650",
        partial_line_height="1.32",
        partial_margin_top="10px",
        trans_weight="700",
        trans_margin_top="8px",
        status_font="22px",
        status_weight="700",
        initial_status="Waiting for subtitles",
        connected_status="Waiting for subtitles",
        show_connected_briefly=False,
        hold_sec=hold_sec,
        hold_per_char_sec=hold_per_char_sec,
        fade_sec=fade_sec,
        demo=demo,
    )


def subtitle_overlay_html(
    *,
    ws_url: str,
    body_css: str,
    main_font: str,
    partial_font: str,
    trans_font: str,
    main_weight: str,
    main_line_height: str,
    main_margin_top: str,
    partial_weight: str,
    partial_line_height: str,
    partial_margin_top: str,
    trans_weight: str,
    trans_margin_top: str,
    status_font: str,
    status_weight: str,
    initial_status: str,
    connected_status: str,
    show_connected_briefly: bool,
    hold_sec: float,
    hold_per_char_sec: float,
    fade_sec: float,
    show_partial: bool = False,
    demo: bool = False,
) -> str:
    render_delay_ms = 650 if show_connected_briefly else 0
    hold_ms = round(hold_sec * 1000)
    hold_per_char_ms = round(hold_per_char_sec * 1000)
    fade_ms = round(fade_sec * 1000)
    demo_js = "true" if demo else "false"
    show_partial_js = "true" if show_partial else "false"
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{
  box-sizing: border-box;
}}
html,
body {{
  background: rgba(0, 0, 0, 0.15);
  color: #fff;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  height: 100%;
  margin: 0;
  overflow: hidden;
}}
body {{
  {body_css}
}}
#status {{
  color: rgba(230, 230, 230, 1);
  font-size: {status_font};
  font-weight: {status_weight};
  text-align: center;
  text-shadow: 0 0 4px #000, 0 0 4px #000, 0 0 6px #000, 0 0 6px #000;
  width: 100%;
}}
#subtitle {{
  opacity: 1;
  text-align: center;
  text-shadow: 0 0 4px #000, 0 0 4px #000, 0 0 6px #000, 0 0 6px #000;
  transition: opacity 300ms ease;
  width: 100%;
}}
#subtitle.hidden {{
  opacity: 0;
}}
#main {{
  color: rgba(210, 210, 210, 1);
  font-size: {main_font};
  font-weight: {main_weight};
  line-height: {main_line_height};
  min-height: {main_line_height}em;
  margin-top: {main_margin_top};
  overflow-wrap: anywhere;
}}
#trans {{
  color: rgba(255, 255, 255, 1);
  font-size: {trans_font};
  font-weight: {trans_weight};
  line-height: {main_line_height};
  min-height: {main_line_height}em;
  margin-top: {trans_margin_top};
  overflow-wrap: anywhere;
}}
#partial {{
  color: rgba(210, 210, 210, 1);
  font-size: {partial_font};
  font-style: italic;
  font-weight: {partial_weight};
  line-height: {partial_line_height};
  min-height: {partial_line_height}em;
  margin-top: {partial_margin_top};
  overflow-wrap: anywhere;
}}
@keyframes lineIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
@keyframes partialIn {{
  from {{ opacity: .3; }}
  to {{ opacity: 1; }}
}}
</style>
</head>
<body>
<div id="status">{initial_status}</div>
<main id="subtitle">
  <div id="trans"></div>
  <div id="main"></div>
  <div id="partial"></div>
</main>
<script>
(() => {{
  const opts = {{
    wsUrl: {ws_url!r},
    initialStatus: {initial_status!r},
    connectedStatus: {connected_status!r},
    renderDelayMs: {render_delay_ms},
    holdMs: {hold_ms},
    holdPerCharMs: {hold_per_char_ms},
    fadeMs: {fade_ms},
    demo: {demo_js},
    showPartial: {show_partial_js},
  }};
  const status = document.getElementById('status');
  const mainLine = document.getElementById('main');
  const transLine = document.getElementById('trans');
  const partialLine = document.getElementById('partial');
  const subtitleEl = document.getElementById('subtitle');
  const rowsByKey = new Map();
  const finalSeqToKey = new Map();
  const MAX_ROWS = 50;
  const DEMO_LINES = [
    'これはサンプル字幕です',
    'This is a sample subtitle',
    '字幕は表示時間と大きさを調整できます',
  ];
  let lastEpoch = null;
  let mainShownAt = 0;
  let pendingQueue = [];
  let fadeTimer = 0, demoTimer = 0;
  let visible = true;
  let demoIdx = 0;
  let displayed = {{ main: '', trans: '', partial: '', sourceKey: null }};

  function rowKey(ev) {{
    return ev.utterance_id != null ? `u:${{ev.utterance_id}}` : `s:${{ev.seq}}`;
  }}

  function desired() {{
    const rows = Array.from(rowsByKey.values());
    const finals = rows.filter((r) => r.kind === 'final' && r.text && r.translation);
    let translatedRow = null;
    if (finals.length > 0) {{ translatedRow = finals[finals.length - 1]; }}
    let partialRow = null;
    if (opts.showPartial) {{ partialRow = rows.slice().reverse().find((row) => row.kind === 'partial' && row.text); }}
    return {{
      main: translatedRow?.text || '',
      trans: translatedRow?.translation || '',
      partial: partialRow?.text || '',
      sourceKey: (translatedRow || partialRow)?.key ?? null,
      partialMode: translatedRow === null && !!partialRow,
    }};
  }}

  function demoDesired() {{
    const line = DEMO_LINES[demoIdx % DEMO_LINES.length];
    demoIdx += 1;
    return {{ main: line, trans: '', partial: '', sourceKey: 'demo', partialMode: false }};
  }}

  function prune() {{
    while (rowsByKey.size > MAX_ROWS) {{
      rowsByKey.delete(rowsByKey.keys().next().value);
    }}
    while (finalSeqToKey.size > MAX_ROWS) {{
      finalSeqToKey.delete(finalSeqToKey.keys().next().value);
    }}
  }}

  function clearPending() {{
    for (const e of pendingQueue) clearTimeout(e.timer);
    pendingQueue = [];
  }}

  function prunePending() {{
    const now = Date.now();
    pendingQueue = pendingQueue.filter((e) => e.fireAt >= now - 1000);
  }}

  function schedulePending(d, startTime, now) {{
    prunePending();
    let entry = {{ fireAt: startTime, msg: {{ main: d.main, trans: d.trans, sourceKey: d.sourceKey }} }};
    entry.timer = setTimeout(() => {{
      pendingQueue = pendingQueue.filter((e) => e !== entry);
      apply({{ main: entry.msg.main, trans: entry.msg.trans, partial: d.partial, sourceKey: entry.msg.sourceKey }});
    }}, startTime - now);
    pendingQueue.push(entry);
  }}


  function commit() {{
    prune();
    const d = opts.demo ? demoDesired() : desired();
    const mainChanged = d.main !== displayed.main || d.trans !== displayed.trans;
    const partialChanged = d.partial !== displayed.partial;

    if (d.sourceKey === displayed.sourceKey) {{
      // clearPending();
      apply(d);
      return;
    }}

    let same = pendingQueue.find((e) => e.msg.sourceKey === d.sourceKey);
    if (same) {{
      same.msg = {{ main: d.main, trans: d.trans, sourceKey: d.sourceKey }};
      if (partialChanged) {{
        applyPartial({{ main: displayed.main, trans: displayed.trans, partial: d.partial, sourceKey: displayed.sourceKey }});
      }}
      return;
    }}

    const now = Date.now();
    if (mainShownAt > 0) {{
      let startTimeD = mainShownAt + opts.holdMs + (opts.holdPerCharMs*displayed.trans.length);
      let startTimeP = pendingQueue.reduce((m, e) => Math.max(m, e.fireAt + opts.holdMs + (opts.holdPerCharMs*e.msg.trans.length)), 0);
      let startTime = Math.max(startTimeD,startTimeP);
      if(now < startTime) {{
        schedulePending(d, startTime, now);
        return;
      }}
    }}

    // clearPending();
    apply(d);
  }}

  function applyPartial(d) {{
    if (displayed.main || displayed.trans) {{
      partialLine.textContent = d.partial;
      partialLine.style.visibility = d.partial ? 'visible' : 'hidden';
      displayed = {{ ...displayed, partial: d.partial }};
      restartFade();
      return;
    }}
    apply(d);
  }}

  function apply(d) {{
    if (d.main !== displayed.main || d.trans !== displayed.trans) {{
      mainShownAt = Date.now();
    }}
    displayed = d;
    const showMain = !!d.main;
    const showTrans = !!d.trans;
    const hasPartial = !!d.partial;
    mainLine.textContent = d.main;
    transLine.textContent = d.trans;
    partialLine.textContent = d.partial;
    mainLine.style.visibility = showMain ? 'visible' : 'hidden';
    transLine.style.visibility = showTrans ? 'visible' : 'hidden';
    partialLine.style.visibility = hasPartial ? 'visible' : 'hidden';
    status.style.display = showMain || showTrans || hasPartial ? 'none' : 'block';
    showSubtitle(!!(showMain || showTrans || hasPartial));
    restartFade();
  }}

  function showSubtitle(show) {{
    if (show === visible) return;
    visible = show;
    subtitleEl.classList.toggle('hidden', !show);
  }}

  function restartFade() {{
    clearTimeout(fadeTimer);
    if (opts.fadeMs <= 0) return;
    if (!displayed.main && !displayed.trans && !displayed.partial) return;
    showSubtitle(true);
    fadeTimer = setTimeout(() => showSubtitle(false), opts.fadeMs);
  }}

  function connect() {{
    rowsByKey.clear();
    finalSeqToKey.clear();
    status.style.display = 'block';
    status.textContent = opts.initialStatus;
    showSubtitle(false);
    const ws = new WebSocket(opts.wsUrl);
    window.__crispasrWs = ws;

    ws.onopen = () => {{
      status.textContent = opts.connectedStatus;
      setTimeout(commit, opts.renderDelayMs);
    }};

    ws.onmessage = (event) => {{
      const msg = JSON.parse(event.data);
      if (msg.type === 'transcript') {{
        const key = rowKey(msg);
        rowsByKey.set(key, {{ ...(rowsByKey.get(key) || {{}}), ...msg, key }});
        if (msg.kind === 'final' && msg.seq != null) finalSeqToKey.set(msg.seq, key);
        commit();
      }} else if (msg.type === 'translation') {{
        const key = finalSeqToKey.get(msg.seq) || `s:${{msg.seq}}`;
        rowsByKey.set(key, {{
          ...(rowsByKey.get(key) || {{ key, kind: 'final' }}),
          translation: msg.text || ''
        }});
        commit();
      }} else if (msg.type === 'translation_error') {{
        const key = finalSeqToKey.get(msg.seq) || `s:${{msg.seq}}`;
        rowsByKey.set(key, {{
          ...(rowsByKey.get(key) || {{ key, kind: 'final' }}),
          translation: msg.message || 'Translation failed'
        }});
        commit();
      }} else if (msg.type === 'health') {{
        if (msg.crisp_epoch != null && msg.crisp_epoch !== lastEpoch) {{
          lastEpoch = msg.crisp_epoch;
          rowsByKey.clear();
          finalSeqToKey.clear();
          commit();
        }}
      }}
    }};

    ws.onerror = () => {{
      status.style.display = 'block';
      status.textContent = 'CrispASR WebSocket error';
    }};

    ws.onclose = () => {{
      status.style.display = 'block';
      status.textContent = 'CrispASR disconnected; reconnecting...';
      showSubtitle(false);
      setTimeout(connect, 1500);
    }};
  }}

  window.addEventListener('beforeunload', () => {{
    if (window.__crispasrWs && window.__crispasrWs.readyState < 2) {{
      window.__crispasrWs.close(1000, 'overlay closed');
    }}
  }});

  if (opts.demo) {{
    demoTimer = setInterval(commit, 3000);
    commit();
  }} else {{
    connect();
  }}
}})();
</script>
</body>
</html>"""
