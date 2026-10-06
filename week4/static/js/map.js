console.log("Week 4 map.js loaded");

/* ---------------------------------------------------------
   MAP INITIALISATION
--------------------------------------------------------- */

const map = L.map("map").setView(
    [53.3498, -6.2603],
    5
);


/* ---------------------------------------------------------
   OPENSTREETMAP BASE LAYER
--------------------------------------------------------- */
L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
        attribution:
            "Tiles &copy; Esri",

        maxZoom: 19
    }
).addTo(map);


let citiesData = [];

let markers = {};


const API_URL = "/api/cities/";

async function initMap() {

    showLoading(true);

    try {

        console.log(
            "Fetching city data from:",
            API_URL
        );

        const response = await fetch(API_URL);

        console.log(
            "API response status:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `HTTP error: ${response.status}`
            );

        }


        const data = await response.json();

        console.log(
            "API data received:",
            data
        );


        /*
        The Week 3 endpoint is paginated.

        Therefore city records are normally
        contained inside data.results.
        */

        citiesData =
            data.results || data;


        document
            .getElementById("cityCount")
            .textContent =
                citiesData.length;


        addMarkersToMap(
            citiesData
        );


        fitMapToCities(
            citiesData
        );

    }

    catch (error) {

        console.error(
            "Error loading cities:",
            error
        );

        alert(
            "Failed to load city data. " +
            "Check the browser console and API."
        );

    }

    finally {

        showLoading(false);

    }
}


/* ---------------------------------------------------------
   ADD CITY MARKERS
--------------------------------------------------------- */

function addMarkersToMap(cities) {

    clearMarkers();


    cities.forEach(city => {

        const lat =
            parseFloat(city.latitude);

        const lng =
            parseFloat(city.longitude);


        if (
            Number.isNaN(lat) ||
            Number.isNaN(lng)
        ) {

            console.warn(
                `Invalid coordinates for ${city.name}`
            );

            return;

        }


        const marker =
            L.circleMarker(
                [lat, lng],
                {
                    radius: 7,

                    fillColor: "#007bff",

                    color: "#004b9a",

                    weight: 2,

                    opacity: 1,

                    fillOpacity: 0.8
                }
            );


        marker.addTo(map);


        marker.bindPopup(
            createPopupContent(city)
        );


        markers[city.id] =
            marker;

    });
}


/* ---------------------------------------------------------
   CLEAR EXISTING MARKERS
--------------------------------------------------------- */

function clearMarkers() {

    Object.values(markers)
        .forEach(marker => {

            map.removeLayer(marker);

        });


    markers = {};
}


/* ---------------------------------------------------------
   POPUP CONTENT
--------------------------------------------------------- */

function createPopupContent(city) {

    const population =
        city.population
            ? formatNumber(city.population)
            : "Unknown";


    const latitude =
        parseFloat(city.latitude);


    const longitude =
        parseFloat(city.longitude);


    return `
        <div class="city-popup">

            <h3>${city.name}</h3>

            <p>
                <strong>Country:</strong>
                ${city.country}
            </p>

            ${
                city.region
                    ? `
                    <p>
                        <strong>Region:</strong>
                        ${city.region}
                    </p>
                    `
                    : ""
            }

            <p>
                <strong>Population:</strong>
                ${population}
            </p>

            <p>
                <strong>Coordinates:</strong>
                ${latitude.toFixed(4)},
                ${longitude.toFixed(4)}
            </p>

            ${
                city.is_capital
                    ? `
                    <p>
                        <strong>Capital:</strong>
                        Yes
                    </p>
                    `
                    : ""
            }

        </div>
    `;
}


/* ---------------------------------------------------------
   NUMBER FORMATTING
--------------------------------------------------------- */

function formatNumber(number) {

    return Number(number)
        .toLocaleString();

}


/* ---------------------------------------------------------
   FIT MAP TO CITY MARKERS
--------------------------------------------------------- */

function fitMapToCities(cities) {

    if (!cities.length) {

        return;

    }


    const coordinates =
        cities
            .map(city => [

                parseFloat(city.latitude),

                parseFloat(city.longitude)

            ])
            .filter(position =>

                !Number.isNaN(position[0]) &&
                !Number.isNaN(position[1])

            );


    if (!coordinates.length) {

        return;

    }


    const bounds =
        L.latLngBounds(coordinates);


    map.fitBounds(
        bounds,
        {
            padding: [40, 40]
        }
    );
}


/* ---------------------------------------------------------
   SEARCH
--------------------------------------------------------- */

document
    .getElementById("searchInput")
    .addEventListener(
        "input",
        function(event) {

            const query =
                event
                    .target
                    .value
                    .trim()
                    .toLowerCase();


            const resultsDiv =
                document
                    .getElementById(
                        "results"
                    );


            if (!query) {

                resultsDiv.innerHTML =
                    "";

                addMarkersToMap(
                    citiesData
                );

                fitMapToCities(
                    citiesData
                );

                return;

            }


            const filtered =
                citiesData.filter(city => {

                    const cityName =
                        city.name
                            .toLowerCase();


                    const country =
                        city.country
                            .toLowerCase();


                    return (
                        cityName.includes(query) ||
                        country.includes(query)
                    );

                });


            addMarkersToMap(
                filtered
            );


            if (
                filtered.length === 0
            ) {

                resultsDiv.innerHTML =
                    `
                    <p class="no-results">
                        No cities found.
                    </p>
                    `;

                return;

            }


            resultsDiv.innerHTML =
                filtered
                    .map(city => `

                        <div
                            class="search-result"
                            onclick="goToCity(${city.id})"
                        >

                            <strong>
                                ${city.name}
                            </strong>

                            <br>

                            ${city.country}

                        </div>

                    `)
                    .join("");


            fitMapToCities(
                filtered
            );

        }
    );


/* ---------------------------------------------------------
   GO TO SELECTED CITY
--------------------------------------------------------- */

function goToCity(cityId) {

    const city =
        citiesData.find(
            item =>
                item.id === cityId
        );


    if (!city) {

        return;

    }


    const lat =
        parseFloat(city.latitude);


    const lng =
        parseFloat(city.longitude);


    map.setView(
        [lat, lng],
        10
    );


    if (markers[cityId]) {

        markers[cityId]
            .openPopup();

    }
}


/* ---------------------------------------------------------
   RESET BUTTON
--------------------------------------------------------- */

document
    .getElementById("resetBtn")
    .addEventListener(
        "click",
        function() {

            document
                .getElementById(
                    "searchInput"
                )
                .value = "";


            document
                .getElementById(
                    "results"
                )
                .innerHTML = "";


            addMarkersToMap(
                citiesData
            );


            fitMapToCities(
                citiesData
            );

        }
    );


/* ---------------------------------------------------------
   LOADING MESSAGE
--------------------------------------------------------- */

function showLoading(show) {

    document
        .getElementById("loading")
        .style
        .display =
            show
                ? "block"
                : "none";

}


/* ---------------------------------------------------------
   START APPLICATION
--------------------------------------------------------- */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "DOM loaded. Starting map..."
        );

        initMap();

    }
);