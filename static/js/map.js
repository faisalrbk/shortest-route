const mapEl = document.getElementById("map");

mapEl.addEventListener("arcgisViewReadyChange", async (e) => {
  window.__view = e.target.view;
  console.log("Map ready", window.__view);
});

// ── Calculate button ───────────────────────────────────────────────────────────
document.getElementById("calculate-btn").addEventListener("click", async () => {
  const originCombo = document.getElementById("origin-port");
  const destCombo = document.getElementById("destination-port");

  const originItem = originCombo.querySelector(
    "calcite-combobox-item[selected]",
  );
  const destItem = destCombo.querySelector("calcite-combobox-item[selected]");

  if (!originItem || !destItem) {
    const alert = document.getElementById("port-alert");
    alert.open = true;
    setTimeout(() => (alert.open = false), 3000);
    return;
  }

  const originId = originItem.value;
  const destId = destItem.value;

  // Show loading state
  const btn = document.getElementById("calculate-btn");
  btn.loading = true;
  btn.disabled = true;

  try {
    const res = await fetch(
      `/api/route?origin_id=${originId}&destination_id=${destId}`,
    );
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Route calculation failed");

    // Draw route on map
    await drawRoute(data.geojson);

    // Show results in dialog
    showResultDialog(data);
  } catch (err) {
    console.error(err);
    const alert = document.getElementById("port-alert");
    alert.querySelector("[slot='message']").textContent = err.message;
    alert.open = true;
    setTimeout(() => (alert.open = false), 4000);
  } finally {
    btn.loading = false;
    btn.disabled = false;
  }
});

// ── Draw route on map ──────────────────────────────────────────────────────────
async function drawRoute(geojson) {
  const view = window.__view;
  if (!view) return;

  const [
    GraphicsLayer,
    Graphic,
    Polyline,
    SimpleLineSymbol,
    SimpleMarkerSymbol,
  ] = await Promise.all([
    $arcgis.import("@arcgis/core/layers/GraphicsLayer.js"),
    $arcgis.import("@arcgis/core/Graphic.js"),
    $arcgis.import("@arcgis/core/geometry/Polyline.js"),
    $arcgis.import("@arcgis/core/symbols/SimpleLineSymbol.js"),
    $arcgis.import("@arcgis/core/symbols/SimpleMarkerSymbol.js"),
  ]);

  // Remove old route layer if exists
  const existing = view.map.findLayerById("route-layer");
  if (existing) view.map.remove(existing);

  const routeLayer = new GraphicsLayer({ id: "route-layer" });

  // Route line
  const polyline = new Polyline({
    paths: [geojson.geometry.coordinates],
    spatialReference: { wkid: 4326 },
  });

  routeLayer.add(
    new Graphic({
      geometry: polyline,
      symbol: new SimpleLineSymbol({
        color: [255, 140, 0, 0.9], // orange
        width: 3,
        style: "dash",
      }),
    }),
  );

  // Origin dot (green)
  const originCoord = geojson.geometry.coordinates[0];
  const destCoord =
    geojson.geometry.coordinates[geojson.geometry.coordinates.length - 1];

  const dotSymbol = (color) =>
    new SimpleMarkerSymbol({
      style: "circle",
      color,
      size: 12,
      outline: { color: [255, 255, 255], width: 2 },
    });

  routeLayer.add(
    new Graphic({
      geometry: {
        type: "point",
        longitude: originCoord[0],
        latitude: originCoord[1],
      },
      symbol: dotSymbol([34, 197, 94]), // green
    }),
  );
  routeLayer.add(
    new Graphic({
      geometry: {
        type: "point",
        longitude: destCoord[0],
        latitude: destCoord[1],
      },
      symbol: dotSymbol([239, 68, 68]), // red
    }),
  );

  view.map.add(routeLayer);

  // Zoom to route
  await view.goTo(polyline.extent.expand(1.3));
}

// ── Show result dialog ─────────────────────────────────────────────────────────
function showResultDialog(data) {
  const { origin, destination, distance, duration, speed_knot } = data;

  // Populate dialog fields
  document.getElementById("dlg-origin").textContent =
    `${origin.name}, ${origin.country}`;
  document.getElementById("dlg-destination").textContent =
    `${destination.name}, ${destination.country}`;
  document.getElementById("dlg-km").textContent =
    `${distance.km.toLocaleString()} km`;
  document.getElementById("dlg-nm").textContent =
    `${distance.nm.toLocaleString()} NM`;
  document.getElementById("dlg-mi").textContent =
    `${distance.mi.toLocaleString()} mi`;
  document.getElementById("dlg-days").textContent = `${duration.days} days`;
  document.getElementById("dlg-hours").textContent =
    `${duration.hours.toLocaleString()} hrs`;
  document.getElementById("dlg-speed").textContent = `${speed_knot} knots`;

  document.getElementById("route-dialog").open = true;
}
