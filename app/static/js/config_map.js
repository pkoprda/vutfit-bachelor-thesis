var folium_map = L.map("folium_map", {
	center: [48.491565, 14.478394999999999], zoom: 15,
    crs: L.CRS.EPSG3857,
    zoomControl: true,
    preferCanvas: false,
});
L.control.scale().addTo(folium_map);

var tile_layer_id = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {"attribution": "Map data \u0026copy; \u003ca href=\"http://openstreetmap.org\"\u003eOpenStreetMap\u003c/a\u003e contributors, under \u003ca href=\"http://www.openstreetmap.org/copyright\"\u003eODbL\u003c/a\u003e.", "detectRetina": false, "maxNativeZoom": 19, "maxZoom": 19, "minZoom": 2, "noWrap": false, "opacity": 1, "subdomains": "abc", "tms": false}
).addTo(folium_map);

var options = {
    position: "topleft",
    draw: {"circle": false, "circlemarker": false, "marker": false, "polygon": false, "polyline": false},
    edit: {"featureGroup": drawnItems, "edit": false, "remove": false},
}
// FeatureGroup is to store editable layers.
var drawnItems = new L.featureGroup().addTo(folium_map);
options.edit.featureGroup = drawnItems;
var draw_control = new L.Control.Draw(
    options
).addTo(folium_map);
