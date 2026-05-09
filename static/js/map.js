const mapEl = document.getElementById("map");

mapEl.addEventListener("arcgisViewReadyChange", (e) => {
  const view = e.target.view;
  console.log("Map ready", view);
});
