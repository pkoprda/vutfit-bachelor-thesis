function updateNorthCoord(val){
    document.getElementById('north').value = val; 
}

function updateSouthCoord(val){
    document.getElementById('south').value = val;
}

function updateEastCoord(val){
    document.getElementById('east').value = val;
}

function updateWestCoord(val){
    document.getElementById('west').value = val;
}

function validateCoords(){
    var north_coord = parseFloat(document.getElementById('north').value);
    var south_coord = parseFloat(document.getElementById('south').value);
    if(north_coord <= south_coord){
        alert('North coordinate must be greater than south coordinate');
        return false;
    }

    var east_coord = parseFloat(document.getElementById('east').value);
    var west_coord = parseFloat(document.getElementById('west').value);
    if(east_coord <= west_coord){
        alert('East coordinate must be greater than west coordinate');
        return false;
    }
    return true;
}