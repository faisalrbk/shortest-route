/* Initialize ArcGIS Map - external JS file (no inline scripts) */
require(["esri/config", "esri/Map", "esri/views/MapView"], function (
  esriConfig,
  Map,
  MapView,
) {
  esriConfig.apiKey =
    "AAPTxy8BH1VEsoebNVZXo8HurJ4OtrIn0er_IZWYxlE4RtW8u6P1z7B3ah8P3TOhJIqvI701l8IsWNaTzxE3UUVjMeAFBwxGqyUPaJCOO-7aIFECet3csLjfzQJhvt0SHFsomEsjX0lOxXR3qO3uu17gN_YEYCpBUWrjikzbBRpY-Eq7PE6f30mxno58y7cHM-kMX-p_jOk1_TPuQYhSna3JEidGX26I-DzkWuB-FBB2Zq4.AT1_bOok1pTC";

  const map = new Map({
    basemap: "arcgis-navigation",
  });

  const view = new MapView({
    container: "viewDiv",
    map: map,
    center: [0, 20],
    zoom: 2,
  });
});
