async function initPorts() {
  const view = window.__view;
  if (!view) {
    setTimeout(initPorts, 100);
    return;
  }

  const [GraphicsLayer, Graphic, Point, PictureMarkerSymbol] =
    await Promise.all([
      $arcgis.import("@arcgis/core/layers/GraphicsLayer.js"),
      $arcgis.import("@arcgis/core/Graphic.js"),
      $arcgis.import("@arcgis/core/geometry/Point.js"),
      $arcgis.import("@arcgis/core/symbols/PictureMarkerSymbol.js"),
    ]);

  // ── 1. Fetch ports ─────────────────────────────────────────────────────────
  const res = await fetch("/api/ports");
  const data = await res.json();
  // API returns { ports: [...], count: N }  OR  plain array — handle both
  const ports = Array.isArray(data) ? data : data.ports;

  // ── 2. Populate both comboboxes ────────────────────────────────────────────
  const originCombo = document.getElementById("origin-port");
  const destCombo = document.getElementById("destination-port");

  ports.forEach((port) => {
    const label = `${port.name} — ${port.country}`;

    [originCombo, destCombo].forEach((combo) => {
      const item = document.createElement("calcite-combobox-item");
      item.value = String(port.id);
      item.setAttribute("heading", label);
      item.dataset.portId = String(port.id);
      combo.appendChild(item);
    });
  });

  // ── 3. Ship anchor SVG as data-URI for PictureMarkerSymbol ────────────────
  const anchorSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <circle cx="12" cy="12" r="11" fill="#003087" stroke="#ffffff" stroke-width="1.5"/>
    <text x="12" y="16.5" text-anchor="middle" font-size="13" font-family="Arial" fill="#ffffff">⚓</text>
  </svg>`;
  const iconUrl =
    "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(anchorSVG);

  // ── 4. Build GraphicsLayer ─────────────────────────────────────────────────
  const layer = new GraphicsLayer({ id: "ports-layer" });

  ports.forEach((port) => {
    layer.add(
      new Graphic({
        geometry: new Point({ longitude: port.lon, latitude: port.lat }),
        symbol: new PictureMarkerSymbol({
          url: iconUrl,
          width: "22px",
          height: "22px",
        }),
        attributes: port,
      }),
    );
  });

  view.map.add(layer);

  // ── 5. Helper: is combo filled? ────────────────────────────────────────────
  const isFilled = (combo) =>
    !!combo.querySelector("calcite-combobox-item[selected]");

  // ── 6. Helper: select item in combo ───────────────────────────────────────
  function selectPort(combo, portId) {
    combo.querySelectorAll("calcite-combobox-item[selected]").forEach((el) => {
      el.selected = false;
    });
    const target = combo.querySelector(
      `calcite-combobox-item[value="${portId}"]`,
    );
    if (target) target.selected = true;
  }

  // ── 7. Map click → fill combobox ──────────────────────────────────────────
  view.on("click", async (event) => {
    const response = await view.hitTest(event, { include: layer });
    if (!response.results.length) return;

    const port = response.results[0].graphic.attributes;
    if (!port?.id) return;

    if (!isFilled(originCombo)) {
      selectPort(originCombo, String(port.id));
    } else if (!isFilled(destCombo)) {
      selectPort(destCombo, String(port.id));
    } else {
      const alert = document.getElementById("port-alert");
      alert.open = true;
      setTimeout(() => (alert.open = false), 3000);
    }
  });
}

initPorts();
