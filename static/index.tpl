<html>
  <head>
    <title>Via Web UI</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==" crossorigin=""/>
    <!-- Make sure you put this AFTER Leaflet's CSS -->
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js" integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==" crossorigin=""></script>

    <style>
      #map_div {
        height: 85%;
        width: 95%;
      }
    </style>

  </head>

  <body>
    <div id="map_div"></div>

    <script>
      function getColour(value){
        //value from 0 to 1
        var hue=((1-value)*120).toString(10);
        return ["hsl(",hue,",100%,50%)"].join("");
      }

      // This map is global scope.
      var map = L.map('map_div').setView({{initial_coords}}, {{initial_zoom}});
      // Public token from Mapbox is here. It can be left in, it's not secret.
      L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoicGhvbmVtYW4iLCJhIjoiY2tzazlwendiMDZ3NTJvcG50dzBlZDIzZCJ9.L0wR8vdrRgO4RQR6yLF6UA', {
        // Attribution must be left in for ToS reasons.
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        maxZoom: 18,
        id: 'mapbox/streets-v11',
        tileSize: 512,
        zoomOffset: -1,
        accessToken: "REDACTED"
      }).addTo(map);

      // This is declared global scope so it can be deleted as needed.
      var geojson_layer = L.geoJson();


      function clear_geojson() {
        map.removeLayer(geojson_layer);
      }

      function load_geojson(data, clear_previous=false) {
        // Triggered on file upload with the GeoJSON object.
        if (clear_previous) {
          clear_geojson();
        }

        geojson_layer = L.geoJSON(
          data,
          {
            style: function(feature) {
              return {
                color: getColour(Math.max.apply(Math, [feature.properties.avg], 50) / 50),  // 50 is just a fairly high cap, TODO: get the actual height
                weight: 5
              };
            },
            onEachFeature: function(feature, layer) {
              // A general method run on each feature. These bind popups for on
              // layer click (default) and also on mouseover/out. Just the road
              // name for now which isn't always populated.

              layer.bindPopup(feature.properties.name + ": " + feature.properties.avg);

              layer.on('mouseover', function(e) {
                this.openPopup();
              });
              layer.on('mouseout', function(e) {
                this.closePopup();
              });
            }
          }
        )
        geojson_layer.addTo(map);
      }
    </script>

    <div>
      Learn more about this project <a href="https://github.com/RobertLucey/via">HERE</a> Download the latest Via.apk <a href="https://github.com/RobertLucey/via-app/releases/latest">HERE</a>
    </div>
    <hr>
    <div id="inputs_container">
      <form id="pull_journeys_form">
        <!-- Time ranges: -->
        <label for="earliest_date">Earliest:</label>
        <input type="date" id="earliest_date" name="earliest_date" min="2021-08-01" value="2021-08-01">

        <label for="latest_date">Latest:</label>
        <input type="date" id="latest_date" name="latest_date" max="2021-12-30" value="2021-12-30"><br/><br/>
        <!-- End time ranges -->

        <!-- Journey type: -->
        <input type="radio" id="all_journeys" name="journey_type" value="all">
        <label for="all">All Journeys</label><br>
        <input type="radio" checked="checked" id="bike" name="journey_type" value="bike">
        <label for="bike">Bike</label><br>
        <input type="radio" id="bus" name="journey_type" value="bus">
        <label for="bus">Bus</label><br>
        <input type="radio" id="car" name="journey_type" value="car">
        <label for="car">Car</label><br>
        <!-- End journey type -->

        <!-- Limit response: -->
        <label for="limit">Limit:</label>
        <input type="number" id="limit" name="limit" min="1" max="5000" value="10">
        <!-- End limit response -->

        <input type="submit" value="Submit">
      </form>
      
      <button id='update_journeys_button'>Update Journeys</button>
    </div>

    <!-- Handle form submission etc -->
    <script>
      function update_map_from_form() {
        $.get(
          'get_journeys',
          {
            'earliest_time': $('#earliest_date').val(),
            'latest_time': $('#latest_date').val(),
            'journey_type': $('input[name="journey_type"]:checked').val(),
            'limit': $('#limit').val()
          }
        ).done(function(resp) {
          console.log("get_journeys response:")
          console.log(resp);
          load_geojson(resp['resp']['geojson'], clear_previous=true);
        });
      }

      document.getElementById('pull_journeys_form').addEventListener('submit',
        function(e) {
          e.preventDefault();
          console.log("form submitted...");

          update_map_from_form();
        }
      );

      document.getElementById('update_journeys_button').onclick = function () { 
        $.get(
          'update_journeys',
          {}
        ).done(function(resp) {
          console.log("update_journeys response:");
          console.log(resp);
        });
      };


      // Call initially to have data show on map.
      update_map_from_form();
    </script>
  </body>
</html>
