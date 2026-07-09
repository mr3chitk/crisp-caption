from __future__ import annotations


def qt_overlay_html(ws_url: str, font_px: int) -> str:
    return subtitle_overlay_html(
        ws_url=ws_url,
        body_css="align-items: end; display: grid; padding: 28px 42px 34px;",
        main_font=f"{font_px}px",
        partial_font=f"{font_px}px",
        main_weight="630",
        main_line_height="1.20",
        partial_weight="630",
        partial_line_height="1.20",
        partial_margin_top="4px",
        status_font="24px",
        status_weight="630",
        initial_status="Connecting to CrispASR...",
        connected_status="CrispASR connected",
        show_connected_briefly=True,
    )


def obs_overlay_html(ws_url: str) -> str:
    return subtitle_overlay_html(
        ws_url=ws_url,
        body_css="align-items: end; box-sizing: border-box; display: grid; padding: 0 7vw 9vh;",
        main_font="clamp(28px, 4.2vw, 58px)",
        partial_font="clamp(20px, 2.8vw, 38px)",
        main_weight="780",
        main_line_height="1.28",
        partial_weight="650",
        partial_line_height="1.32",
        partial_margin_top="10px",
        status_font="22px",
        status_weight="700",
        initial_status="Waiting for subtitles",
        connected_status="Waiting for subtitles",
        show_connected_briefly=False,
    )


def subtitle_overlay_html(
    *,
    ws_url: str,
    body_css: str,
    main_font: str,
    partial_font: str,
    main_weight: str,
    main_line_height: str,
    partial_weight: str,
    partial_line_height: str,
    partial_margin_top: str,
    status_font: str,
    status_weight: str,
    initial_status: str,
    connected_status: str,
    show_connected_briefly: bool,
) -> str:
    render_delay_ms = 650 if show_connected_briefly else 0
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
  background: transparent;
  color: #fff;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  height: 100%;
  margin: 0;
  overflow: hidden;
}}
body {{
  {body_css}
}}
#subtitle {{
  text-align: left;
  text-shadow: 0 2px 4px #000, 0 0 8px #000, 0 0 16px #000, 0 0 24px #000;
  height: 100%;
  display: block;
  flex-direction: column;
  justify-content: flex-end;
}}
#main {{
  color: rgba(240, 240, 240, 1.0);
  font-size: {main_font};
  font-weight: {main_weight};
  line-height: {main_line_height};
  overflow-wrap: anywhere;
}}
</style>
</head>
<body>
<main id="subtitle">
  <div id="main"></div>
</main>
<script>
(() => {{
  const wsUrl = {ws_url!r};
  const mainLine = document.getElementById('main');
  const subTitle = document.getElementById('subtitle');
  const rowsByKey = new Map();
  const finalSeqToKey = new Map();
  var timeoutId;

  function rowKey(ev) {{
    return ev.utterance_id != null ? `u:${{ev.utterance_id}}` : `s:${{ev.seq}}`;
  }}

  function render() {{
    const rows = Array.from(rowsByKey.values());
    const finalId = rows.slice().findLastIndex((row) => row.kind === 'final' && (row.translation || row.error));
    var main = finalId >= 0 ? rows.at(finalId).translation:'';
    const partial1 = finalId >= 1 ? rows.at(finalId-1).translation:'';
    const partial2 = finalId >= 2 ? rows.at(finalId-2).translation:'';
    const partial3 = finalId >= 3 ? rows.at(finalId-3).translation:'';
    mainLine.innerHTML = partial3 + "<br/>" + partial2 + "<br/>" + partial1 + "<br/>" + main;
    subTitle.style.display = "flex";
    clearTimeout(timeoutId);
    timeoutId = setTimeout(function() {{ subTitle.style.display = "none"; }}, 90000);
  }}

  function connect() {{
    const ws = new WebSocket(wsUrl);
    window.__crispasrWs = ws;

    ws.onopen = () => {{
      setTimeout(render, {render_delay_ms});
    }};

    ws.onmessage = (event) => {{
      const msg = JSON.parse(event.data);
      if (msg.type === 'transcript') {{
        const key = rowKey(msg);
        rowsByKey.set(key, {{ ...(rowsByKey.get(key) || {{}}), ...msg, key }});
        if (msg.kind === 'final' && msg.seq != null) finalSeqToKey.set(msg.seq, key);
        render();
      }} else if (msg.type === 'translation') {{
        const key = finalSeqToKey.get(msg.seq) || `s:${{msg.seq}}`;
        rowsByKey.set(key, {{
          ...(rowsByKey.get(key) || {{ key, kind: 'final' }}),
          translation: msg.text || ''
        }});
        render();
      }} else if (msg.type === 'translation_error') {{
        const key = finalSeqToKey.get(msg.seq) || `s:${{msg.seq}}`;
        rowsByKey.set(key, {{
          ...(rowsByKey.get(key) || {{ key, kind: 'final' }}),
          translation: msg.message || 'Translation failed'
        }});
        render();
      }}
    }};

    ws.onerror = () => {{
      mainLine.textContent = 'CrispASR WebSocket error';
    }};

    ws.onclose = () => {{
      mainLine.textContent = 'CrispASR disconnected; reconnecting...';
      setTimeout(connect, 1500);
    }};
  }}

  window.addEventListener('beforeunload', () => {{
    if (window.__crispasrWs && window.__crispasrWs.readyState < 2) {{
      window.__crispasrWs.close(1000, 'overlay closed');
    }}
  }});

  connect();
}})();
</script>
</body>
</html>"""
