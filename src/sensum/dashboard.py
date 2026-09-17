DASHBOARD_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Sensum Live</title>
  <style>
    :root { font-family: Inter, ui-sans-serif, system-ui, sans-serif; color-scheme: dark; }
    body { margin: 0; background: #0a0d12; color: #f3f6fb; }
    main { max-width: 1180px; margin: 0 auto; padding: 28px; }
    h1 { margin: 0 0 6px; font-size: 30px; }
    .sub { color: #9da8b8; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .card { background: #111722; border: 1px solid #202a39; border-radius: 14px; padding: 16px; }
    .label { color: #8f9caf; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
    .value { font-size: 30px; margin-top: 8px; font-variant-numeric: tabular-nums; }
    .layout { display: grid; grid-template-columns: 1.35fr .65fr; gap: 12px; margin-top: 12px; }
    pre { white-space: pre-wrap; word-break: break-word; margin: 0; }
    #events { height: 430px; overflow: auto; font-size: 12px; }
    #world { height: 430px; overflow: auto; font-size: 12px; }
    .event { padding: 10px 0; border-bottom: 1px solid #202a39; }
    .kind { font-weight: 700; }
    .meta { color: #8f9caf; margin-top: 4px; }
    .status { display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #4ade80; }
    @media (max-width: 800px) { .grid, .layout { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Sensum Live</h1>
  <div class=\"sub\"><span class=\"status\"></span> continuous perception without continuous LLM inference</div>
  <section class=\"grid\">
    <div class=\"card\"><div class=\"label\">Raw observations</div><div class=\"value\" id=\"raw\">0</div></div>
    <div class=\"card\"><div class=\"label\">Semantic events</div><div class=\"value\" id=\"semantic\">0</div></div>
    <div class=\"card\"><div class=\"label\">Reasoning events</div><div class=\"value\" id=\"reasoning\">0</div></div>
    <div class=\"card\"><div class=\"label\">Reasoning reduction</div><div class=\"value\" id=\"reduction\">0%</div></div>
  </section>
  <section class=\"layout\">
    <div class=\"card\"><div class=\"label\">Live sensory events</div><div id=\"events\"></div></div>
    <div class=\"card\"><div class=\"label\">World state</div><pre id=\"world\">{}</pre></div>
  </section>
</main>
<script>
  const fmt = n => Number(n || 0).toLocaleString();

  async function refresh() {
    const [statsRes, worldRes] = await Promise.all([fetch('/stats'), fetch('/world')]);
    const stats = await statsRes.json();
    const world = await worldRes.json();
    const totals = stats.totals || {};
    document.getElementById('raw').textContent = fmt(totals.raw_observations);
    document.getElementById('semantic').textContent = fmt(totals.semantic_events);
    document.getElementById('reasoning').textContent = fmt(totals.reasoning_events);
    document.getElementById('reduction').textContent =
      `${((totals.reasoning_reduction_ratio || 0) * 100).toFixed(2)}%`;
    document.getElementById('world').textContent = JSON.stringify(world, null, 2);
  }

  const events = document.getElementById('events');
  const source = new EventSource('/events');
  source.addEventListener('sensory', message => {
    const event = JSON.parse(message.data);
    const row = document.createElement('div');
    row.className = 'event';
    const attention = event.metadata?.attention?.score;
    row.innerHTML = `<div class=\"kind\">${event.kind}</div>` +
      `<div>${event.summary || ''}</div>` +
      `<div class=\"meta\">${event.modality} · ${event.source}` +
      `${attention == null ? '' : ` · attention ${attention}`}</div>`;
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
