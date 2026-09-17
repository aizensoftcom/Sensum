DASHBOARD_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Sensum Live</title>
  <style>
    :root { font-family: Inter, ui-sans-serif, system-ui, sans-serif; color-scheme: dark; }
    body { margin: 0; background: #0a0d12; color: #f3f6fb; }
    main { max-width: 1420px; margin: 0 auto; padding: 28px; }
    h1 { margin: 0 0 6px; font-size: 30px; }
    .sub { color: #9da8b8; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    .card { background: #111722; border: 1px solid #202a39; border-radius: 14px; padding: 16px; }
    .label { color: #8f9caf; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
    .value { font-size: 30px; margin-top: 8px; font-variant-numeric: tabular-nums; }
    .layout { display: grid; grid-template-columns: 1fr 1.05fr .75fr; gap: 12px; margin-top: 12px; }
    pre { white-space: pre-wrap; word-break: break-word; margin: 0; }
    #events, #traces, #world { height: 470px; overflow: auto; font-size: 12px; }
    .event, .trace { padding: 10px 0; border-bottom: 1px solid #202a39; }
    .kind { font-weight: 700; }
    .meta { color: #8f9caf; margin-top: 4px; }
    .reason { color: #c2ccda; margin-top: 5px; line-height: 1.45; }
    .status { display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #4ade80; }
    .badge { display: inline-block; border-radius: 999px; padding: 2px 7px; margin-left: 7px; font-size: 10px; font-weight: 700; }
    .wake { background: #16351f; color: #86efac; }
    .quiet { background: #30251a; color: #fdba74; }
    .fused { background: #22254b; color: #c4b5fd; }
    @media (max-width: 1000px) { .grid, .layout { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Sensum Live</h1>
  <div class=\"sub\"><span class=\"status\"></span> perception runtime · see what AI receives, what it ignores, and why</div>
  <section class=\"grid\">
    <div class=\"card\"><div class=\"label\">Raw observations</div><div class=\"value\" id=\"raw\">0</div></div>
    <div class=\"card\"><div class=\"label\">Semantic events</div><div class=\"value\" id=\"semantic\">0</div></div>
    <div class=\"card\"><div class=\"label\">AI wake-ups</div><div class=\"value\" id=\"reasoning\">0</div></div>
    <div class=\"card\"><div class=\"label\">Suppressed</div><div class=\"value\" id=\"suppressed\">0</div></div>
    <div class=\"card\"><div class=\"label\">Reasoning reduction</div><div class=\"value\" id=\"reduction\">0%</div></div>
  </section>
  <section class=\"layout\">
    <div class=\"card\"><div class=\"label\">Events sent to AI</div><div id=\"events\"></div></div>
    <div class=\"card\"><div class=\"label\">Perception Trace · why?</div><div id=\"traces\"></div></div>
    <div class=\"card\"><div class=\"label\">World state</div><pre id=\"world\">{}</pre></div>
  </section>
</main>
<script>
  const fmt = n => Number(n || 0).toLocaleString();

  function textNode(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value == null ? '' : String(value);
    return node;
  }

  function renderTraces(traces) {
    const container = document.getElementById('traces');
    container.replaceChildren();
    for (const trace of traces) {
      const row = document.createElement('div');
      row.className = 'trace';
      const title = document.createElement('div');
      title.appendChild(textNode('span', 'kind', trace.kind));
      title.appendChild(textNode(
        'span',
        `badge ${trace.significant ? 'wake' : 'quiet'}`,
        trace.significant ? 'AI WAKE' : 'FILTERED'
      ));
      if (trace.fused) title.appendChild(textNode('span', 'badge fused', 'FUSED'));
      row.appendChild(title);
      row.appendChild(textNode(
        'div',
        'meta',
        `${trace.modality} · ${trace.source} · attention ${Number(trace.attention_score).toFixed(3)}`
      ));
      row.appendChild(textNode('div', 'reason', (trace.attention_reasons || []).join(' · ')));
      if ((trace.parent_event_ids || []).length) {
        row.appendChild(textNode('div', 'meta', `caused by: ${trace.parent_event_ids.join(', ')}`));
      }
      container.appendChild(row);
    }
  }

  async function refresh() {
    const [statsRes, worldRes, tracesRes] = await Promise.all([
      fetch('/stats'), fetch('/world'), fetch('/traces?limit=80')
    ]);
    const stats = await statsRes.json();
    const world = await worldRes.json();
    const traces = await tracesRes.json();
    const totals = stats.totals || {};
    const runtime = stats.runtime || {};
    document.getElementById('raw').textContent = fmt(totals.raw_observations);
    document.getElementById('semantic').textContent = fmt(totals.semantic_events);
    document.getElementById('reasoning').textContent = fmt(totals.reasoning_events);
    document.getElementById('suppressed').textContent = fmt(runtime.suppressed);
    document.getElementById('reduction').textContent =
      `${((totals.reasoning_reduction_ratio || 0) * 100).toFixed(2)}%`;
    document.getElementById('world').textContent = JSON.stringify(world, null, 2);
    renderTraces(traces);
  }

  const events = document.getElementById('events');
  const source = new EventSource('/events');
  source.addEventListener('sensory', message => {
    const event = JSON.parse(message.data);
    const row = document.createElement('div');
    row.className = 'event';
    row.appendChild(textNode('div', 'kind', event.kind));
    row.appendChild(textNode('div', '', event.summary || ''));
    const attention = event.metadata?.attention?.score;
    const meta = `${event.modality || ''} · ${event.source || ''}` +
      `${attention == null ? '' : ` · attention ${attention}`}`;
    row.appendChild(textNode('div', 'meta', meta));
    events.prepend(row);
    while (events.children.length > 100) events.lastChild.remove();
    refresh();
  });

  setInterval(refresh, 1000);
  refresh();
</script>
</body>
</html>
"""
