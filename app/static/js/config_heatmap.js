/**
 * Configuration file for heatmap
 * @author Peter Koprda
 */


/**
 * Update coordinates
 * @param {_latlngs} points - geographical points
 * @param {boolean} custom_area - get coords from custom area
 */
function updateCoords(points, custom_area = false){
    let borders = {};

    if(custom_area){            
        let lats = [points[0][0]["lat"], points[0][1]["lat"], points[0][2]["lat"], points[0][3]["lat"]];
        let longs = [points[0][0]["lng"], points[0][1]["lng"], points[0][2]["lng"], points[0][3]["lng"]];
        borders = {
            "north": Math.max(...lats),
            "south": Math.min(...lats),
            "east": Math.max(...longs),
            "west": Math.min(...longs)
        }
    }
    else{
        borders = {
            "north": points['_northEast']['lat'],
            "south": points['_southWest']['lat'],
            "east": points['_northEast']['lng'],
            "west": points['_southWest']['lng']
        }
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


/**
 * Removes drawn layer
 */
function remove_layer(){
    let layer = Object.values(drawnItems._layers)[0];
    folium_map.removeLayer(layer);
    $('.custom-area-create-tag').show();
    $('.custom-area-delete-tag').hide();
    drawnItems._layers = {};
    updateCoords(folium_map.getBounds());
};


folium_map.on(L.Draw.Event.CREATED, function (e){
    drawnItems.addLayer(e.layer);
    let points = Object.values(drawnItems._layers)[0]._latlngs;
    updateCoords(points, true);
    $('.custom-area-create-tag').hide();
    folium_map.fire(L.Draw.Event.EDITSTART);
    $('.custom-area-delete-tag').show();
});


folium_map.on(L.Draw.Event.EDITSTART, function(){
    let layer = Object.values(drawnItems._layers)[0];
    layer.editing.enable();
});


folium_map.on(`${L.Draw.Event.EDITMOVE} ${L.Draw.Event.EDITRESIZE}`, function(){
    let points = Object.values(drawnItems._layers)[0]._latlngs;
    updateCoords(points, true);
    folium_map.fire(L.Draw.Event.EDITSTOP);
});


folium_map.on('moveend zoom', function(){
    let layer = Object.values(drawnItems._layers)[0];
    try {
        folium_map.hasLayer(layer);
    } catch (error) {
        updateCoords(folium_map.getBounds());
    }
});
