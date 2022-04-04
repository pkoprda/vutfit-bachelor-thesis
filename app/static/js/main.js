function updateCoords(points, delete_inputs = false){
    if(delete_inputs){
        document.getElementById("borders_form").reset();
        return;
    }
    let lats = [points[0][0]["lat"], points[0][1]["lat"], points[0][2]["lat"], points[0][3]["lat"]];
    let longs = [points[0][0]["lng"], points[0][1]["lng"], points[0][2]["lng"], points[0][3]["lng"]];
    let borders = {
        "north": Math.max(...lats),
        "south": Math.min(...lats),
        "east": Math.max(...longs),
        "west": Math.min(...longs)
    }

    $.ajax({
        type: 'POST',
        url: '/',
        data: borders,
    })
    .done(function(data) {
        $("#north_id").val(data['borders']['north']);
        $("#south_id").val(data['borders']['south']);
        $("#east_id").val(data['borders']['east']);
        $("#west_id").val(data['borders']['west']);
    });
}

folium_map.on('draw:created', function (e) {
    layer = e.layer;
    let points = layer._latlngs;
    updateCoords(points);
    $('.leaflet-draw-draw-rectangle').parent().hide()
});

folium_map.on('draw:edited', function (e) {
    let layers = e.layers;
    layers.eachLayer(function (layer) {
        let points = layer._latlngs;
        updateCoords(points);
    });
});

folium_map.on('draw:deleted', function (e) {
    let layers = e.layers;
    layers.eachLayer(function () {
        let points = layer._latlngs;
        $('.leaflet-draw-draw-rectangle').parent().show();
        updateCoords(points, true)
    });
});
