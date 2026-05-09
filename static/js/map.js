const mapEl = document.getElementById("map");

mapEl.addEventListener("arcgisViewReadyChange", async (e) => {
  window.__view = e.target.view;
  console.log("Map ready", window.__view);
});
