const map = L.map("map").setView([53.3498, -6.2603], 13);

L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
        attribution: "Tiles &copy; Esri",
        maxZoom: 19
    }
).addTo(map);

const heritageUserData =
    document.getElementById(
        "heritageUserData"
    );

const currentUser = {
    isAuthenticated:
        heritageUserData?.dataset.authenticated ===
        "true",

    username:
        heritageUserData?.dataset.username || ""
};
/* =========================================================
   MAP LAYERS
========================================================= */

const artisanLayer = L.layerGroup().addTo(map);
const regionLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);


/* =========================================================
   APPLICATION STATE
========================================================= */

let artisanData = [];
let artisanMarkers = [];

let selectedLocation = null;
let selectedLocationMarker = null;
let searchRadiusCircle = null;

let artisanLocationMap = null;
let artisanLocationMarker = null;
let newArtisanLocation = null;

let editingArtisanId = null;

let addressSearchTimer = null;


/* =========================================================
   PAGE ELEMENTS
========================================================= */

const mapStatus =
    document.getElementById("mapStatus");

const resultsContainer =
    document.getElementById("results");

const searchInput =
    document.getElementById("searchInput");

const craftFilter =
    document.getElementById("craftFilter");

const regionFilter =
    document.getElementById("regionFilter");

const radiusSelect =
    document.getElementById("radiusSelect");

const selectedLocationInfo =
    document.getElementById("selectedLocationInfo");

const toggleArtisans =
    document.getElementById("toggleArtisans");

const toggleRegions =
    document.getElementById("toggleRegions");

const toggleRoutes =
    document.getElementById("toggleRoutes");


/* =========================================================
   ARTISAN MODAL ELEMENTS
========================================================= */

const artisanModal =
    document.getElementById("artisanModal");

const artisanModalTitle =
    document.getElementById("artisanModalTitle");

const saveArtisanBtn =
    document.getElementById("saveArtisanBtn");

const openAddArtisanBtn =
    document.getElementById("openAddArtisanBtn");

const closeArtisanModalBtn =
    document.getElementById("closeArtisanModalBtn");

const cancelArtisanBtn =
    document.getElementById("cancelArtisanBtn");

const artisanForm =
    document.getElementById("artisanForm");

const artisanLocationDisplay =
    document.getElementById("artisanLocationDisplay");

const artisanFormMessage =
    document.getElementById("artisanFormMessage");

const artisanAddressInput =
    document.getElementById("artisanAddress");


/* =========================================================
   GENERAL HELPERS
========================================================= */

function setStatus(message) {
    mapStatus.textContent = message;
}


/*
 * Escape text before inserting it into HTML.
 * Artisan details are typed by users, so without this a name like
 * <img src=x onerror=alert(1)> would run as code (stored XSS).
 */
function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}


/*
 * Turn a Django REST Framework error response into readable text.
 * e.g. {"phone": ["Phone may only contain..."]} -> "phone: Phone may only contain..."
 */
function formatApiErrors(data) {
    if (!data || typeof data !== "object") {
        return "";
    }

    if (data.error) {
        return data.error;
    }

    if (data.detail) {
        return data.detail;
    }

    const source = data.properties || data;

    return Object.entries(source)
        .map(([field, messages]) => {
            const text = Array.isArray(messages)
                ? messages.join(" ")
                : typeof messages === "object"
                    ? formatApiErrors(messages)
                    : String(messages);

            return field === "non_field_errors"
                ? text
                : `${field.replace(/_/g, " ")}: ${text}`;
        })
        .join(" ");
}


function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (
                cookie.substring(
                    0,
                    name.length + 1
                ) === `${name}=`
            ) {
                cookieValue = decodeURIComponent(
                    cookie.substring(
                        name.length + 1
                    )
                );

                break;
            }
        }
    }

    return cookieValue;
}


function getApiHeaders() {
    const headers = {
        "Content-Type": "application/json"
    };

    const csrfToken =
        getCookie("csrftoken");

    if (csrfToken) {
        headers["X-CSRFToken"] =
            csrfToken;
    }

    return headers;
}


/* =========================================================
   ARTISAN POPUPS
========================================================= */

function createArtisanPopup(feature) {
    const properties =
        feature.properties;

    return `
        <h5>${escapeHtml(properties.name)}</h5>

        <p>
            <strong>Artisan:</strong>
            ${escapeHtml(properties.artisan_name)}
        </p>

        <p>
            <strong>Craft:</strong>
            ${escapeHtml(properties.craft_type_display)}
        </p>

        <p>
            <strong>Address:</strong>
            ${escapeHtml(properties.address)}
        </p>

        <p>
            <strong>Region:</strong>
            ${escapeHtml(properties.region_name || "None")}
        </p>

        <p>
            <strong>Hours:</strong>
            ${escapeHtml(properties.opening_hours || "Not available")}
        </p>
    `;
}


/* =========================================================
   DISPLAY ARTISANS
========================================================= */

function displayArtisans(features) {
    if (
        toggleArtisans &&
        toggleArtisans.checked &&
        !map.hasLayer(artisanLayer)
    ) {
        map.addLayer(artisanLayer);
    }

    artisanLayer.clearLayers();
    artisanMarkers = [];

    features.forEach((feature) => {
        if (
            !feature.geometry ||
            !feature.geometry.coordinates
        ) {
            return;
        }

        const coordinates =
            feature.geometry.coordinates;

        const marker =
            L.marker([
                coordinates[1],
                coordinates[0]
            ]);

        marker.bindPopup(
            createArtisanPopup(feature)
        );

        marker.addTo(
            artisanLayer
        );

        artisanMarkers.push({
            feature: feature,
            marker: marker
        });
    });

    updateResults(features);
}


/* =========================================================
   RESULTS PANEL
========================================================= */

function updateResults(features) {
    resultsContainer.innerHTML = "";

    if (features.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-results">
                <p>
                    No artisans found in this area.
                </p>
            </div>
        `;

        return;
    }

    features.forEach((feature) => {
        const properties =
            feature.properties;

        const canManageArtisan =
            currentUser.isAuthenticated &&
            properties.owner_username ===
                currentUser.username;

        const managementButtons =
            canManageArtisan
                ? `
                    <div class="result-actions">

                        <button
                            type="button"
                            class="edit-artisan-btn"
                        >
                            Edit
                        </button>

                        <button
                            type="button"
                            class="delete-artisan-btn"
                        >
                            Delete
                        </button>

                    </div>
                `
                : "";

        const result =
            document.createElement("div");

        result.className =
            "result-item";

        result.innerHTML = `
            <div class="result-category">
                ${escapeHtml(properties.craft_type_display)}
            </div>

            <h6>
                ${escapeHtml(properties.name)}
            </h6>

            <p class="artisan-name">
                ${escapeHtml(properties.artisan_name)}
            </p>

            <p class="result-address">
                ${escapeHtml(properties.address)}
            </p>

            <p class="result-description">
                ${escapeHtml(properties.description || "")}
            </p>

            <div class="result-footer">

                <span>
                    ${
                        escapeHtml(properties.region_name ||
                        "Independent artisan")
                    }
                </span>

                ${managementButtons}

            </div>
        `;

        const editButton =
            result.querySelector(
                ".edit-artisan-btn"
            );

        const deleteButton =
            result.querySelector(
                ".delete-artisan-btn"
            );

        if (editButton) {
            editButton.addEventListener(
                "click",
                function (event) {
                    event.stopPropagation();

                    openEditArtisanModal(
                        feature
                    );
                }
            );
        }

        if (deleteButton) {
            deleteButton.addEventListener(
                "click",
                function (event) {
                    event.stopPropagation();

                    deleteArtisan(
                        feature
                    );
                }
            );
        }

        result.addEventListener(
            "click",
            function () {
                const coordinates =
                    feature.geometry.coordinates;

                map.setView(
                    [
                        coordinates[1],
                        coordinates[0]
                    ],
                    16
                );

                const markerObject =
                    artisanMarkers.find(
                        (item) =>
                            item.feature.id ===
                            feature.id
                    );

                if (markerObject) {
                    markerObject
                        .marker
                        .openPopup();
                }
            }
        );

        resultsContainer.appendChild(
            result
        );
    });
}


/* =========================================================
   LOAD ARTISANS
========================================================= */

async function loadArtisans() {
    try {
        setStatus(
            "Loading artisans..."
        );

        const response =
            await fetch(
                "/api/heritage/artisans/"
            );

        if (!response.ok) {
            throw new Error(
                "Unable to load artisans."
            );
        }

        const data =
            await response.json();

        artisanData =
            data.results?.features ||
            data.features ||
            [];

        displayArtisans(
            artisanData
        );

        setStatus(
            `${artisanData.length} artisans loaded`
        );
    } catch (error) {
        console.error(error);

        setStatus(
            "Error loading artisans."
        );
    }
}


/* =========================================================
   LOAD CULTURAL REGIONS
========================================================= */

async function loadRegions() {
    try {
        const response =
            await fetch(
                "/api/heritage/regions/"
            );

        if (!response.ok) {
            throw new Error(
                "Unable to load regions."
            );
        }

        const data =
            await response.json();

        const features =
            data.results?.features ||
            data.features ||
            [];

        regionLayer.clearLayers();

        L.geoJSON(
            features,
            {
                style: {
                    color: "#70866c",
                    weight: 2,
                    opacity: 0.8,
                    fillColor: "#a8b7a3",
                    fillOpacity: 0.16
                },

                onEachFeature:
                    function (
                        feature,
                        layer
                    ) {
                        layer.bindPopup(`
                            <h5>
                                ${escapeHtml(feature.properties.name)}
                            </h5>

                            <p>
                                ${escapeHtml(feature.properties.region_type)}
                            </p>

                            <p>
                                ${escapeHtml(feature.properties.description)}
                            </p>
                        `);

                        layer.on(
                            "click",
                            function (event) {
                                selectMapLocation(
                                    event.latlng.lat,
                                    event.latlng.lng
                                );
                            }
                        );
                    }
            }
        ).addTo(
            regionLayer
        );
    } catch (error) {
        console.error(error);
    }
}


/* =========================================================
   LOAD HERITAGE ROUTES
========================================================= */

async function loadRoutes() {
    try {
        const response =
            await fetch(
                "/api/heritage/routes/"
            );

        if (!response.ok) {
            throw new Error(
                "Unable to load routes."
            );
        }

        const data =
            await response.json();

        const features =
            data.results?.features ||
            data.features ||
            [];

        routeLayer.clearLayers();

        L.geoJSON(
            features,
            {
                style: {
                    color: "#b85f36",
                    weight: 4,
                    opacity: 0.9,
                    dashArray: "7, 5"
                },

                onEachFeature:
                    function (
                        feature,
                        layer
                    ) {
                        layer.bindPopup(`
                            <h5>
                                ${escapeHtml(feature.properties.name)}
                            </h5>

                            <p>
                                ${escapeHtml(feature.properties.route_type_display)}
                            </p>

                            <p>
                                ${escapeHtml(feature.properties.description)}
                            </p>

                            <p>
                                <strong>
                                    Distance:
                                </strong>

                                ${
                                    escapeHtml(feature.properties.distance_km ||
                                    "N/A")
                                } km
                            </p>
                        `);

                        layer.on(
                            "click",
                            function (event) {
                                selectMapLocation(
                                    event.latlng.lat,
                                    event.latlng.lng
                                );
                            }
                        );
                    }
            }
        ).addTo(
            routeLayer
        );
    } catch (error) {
        console.error(error);
    }
}


/* =========================================================
   SEARCH + CRAFT FILTER
========================================================= */

function applyFilters() {
    const searchValue =
        searchInput.value
            .toLowerCase()
            .trim();

    const craftValue =
        craftFilter.value;

    const filtered =
        artisanData.filter(
            (feature) => {
                const properties =
                    feature.properties;

                const name =
                    properties.name || "";

                const artisanName =
                    properties.artisan_name || "";

                const address =
                    properties.address || "";

                const craftName =
                    properties.craft_type_display || "";

                const matchesSearch =
                    name
                        .toLowerCase()
                        .includes(
                            searchValue
                        ) ||

                    artisanName
                        .toLowerCase()
                        .includes(
                            searchValue
                        ) ||

                    address
                        .toLowerCase()
                        .includes(
                            searchValue
                        ) ||

                    craftName
                        .toLowerCase()
                        .includes(
                            searchValue
                        );

                const matchesCraft =
                    !craftValue ||
                    properties.craft_type ===
                        craftValue;

                return (
                    matchesSearch &&
                    matchesCraft
                );
            }
        );

    displayArtisans(
        filtered
    );

    setStatus(
        `${filtered.length} matching artisans`
    );
}


/* =========================================================
   CULTURAL REGION FILTER
========================================================= */

async function filterByRegion() {
    const regionId =
        regionFilter.value;

    if (!regionId) {
        displayArtisans(
            artisanData
        );

        setStatus(
            `${artisanData.length} artisans loaded`
        );

        return;
    }

    try {
        setStatus(
            "Loading region artisans..."
        );

        const response =
            await fetch(
                `/api/heritage/regions/${regionId}/artisans/`
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to load region artisans."
            );
        }

        const features =
            data.artisans?.features ||
            [];

        displayArtisans(
            features
        );

        if (
            !map.hasLayer(
                regionLayer
            )
        ) {
            map.addLayer(
                regionLayer
            );
        }

        if (toggleRegions) {
            toggleRegions.checked =
                true;
        }

        setStatus(
            `${data.count} artisans in ${data.region.name}`
        );
    } catch (error) {
        console.error(error);

        setStatus(
            error.message
        );
    }
}


/* =========================================================
   SELECT LOCATION ON MAIN MAP
========================================================= */

function selectMapLocation(
    lat,
    lng
) {
    selectedLocation = {
        lat: lat,
        lng: lng
    };

    if (
        selectedLocationMarker
    ) {
        map.removeLayer(
            selectedLocationMarker
        );
    }

    selectedLocationMarker =
        L.circleMarker(
            [lat, lng],
            {
                radius: 9,
                color: "#3f4a3d",
                weight: 3,
                fillColor: "#b85f36",
                fillOpacity: 1
            }
        ).addTo(map);

    selectedLocationMarker
        .bindPopup(
            "<strong>Selected search location</strong>"
        );

    if (
        selectedLocationInfo
    ) {
        selectedLocationInfo
            .classList
            .add("active");

        selectedLocationInfo.innerHTML = `
            <strong>
                Search location selected
            </strong>
            <br>
            ${lat.toFixed(5)},
            ${lng.toFixed(5)}
        `;
    }

    setStatus(
        "Search location selected."
    );
}


map.on(
    "click",
    function (event) {
        selectMapLocation(
            event.latlng.lat,
            event.latlng.lng
        );
    }
);


/* =========================================================
   NEARBY SEARCH
========================================================= */

async function runNearbySearch(
    lat,
    lng
) {
    const radius =
        radiusSelect.value;

    try {
        setStatus(
            "Searching nearby artisans..."
        );

        const response =
            await fetch(
                `/api/heritage/artisans/within_radius/?lat=${lat}&lng=${lng}&radius=${radius}`
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Radius search failed."
            );
        }

        const features =
            data.results?.features ||
            [];

        displayArtisans(
            features
        );

        if (
            searchRadiusCircle
        ) {
            map.removeLayer(
                searchRadiusCircle
            );
        }

        searchRadiusCircle =
            L.circle(
                [lat, lng],
                {
                    radius:
                        Number(radius) *
                        1000,

                    color:
                        "#b85f36",

                    weight: 2,
                    opacity: 0.7,

                    fillColor:
                        "#b85f36",

                    fillOpacity:
                        0.06
                }
            ).addTo(map);

        map.fitBounds(
            searchRadiusCircle
                .getBounds(),
            {
                padding:
                    [20, 20]
            }
        );

        setStatus(
            `${data.count} artisans within ${radius} km`
        );
    } catch (error) {
        console.error(error);

        setStatus(
            error.message
        );
    }
}


function findNearbyArtisans() {
    if (selectedLocation) {
        runNearbySearch(
            selectedLocation.lat,
            selectedLocation.lng
        );

        return;
    }

    setStatus(
        "Getting your location..."
    );

    navigator.geolocation
        .getCurrentPosition(
            (position) => {
                const lat =
                    position.coords
                        .latitude;

                const lng =
                    position.coords
                        .longitude;

                selectMapLocation(
                    lat,
                    lng
                );

                runNearbySearch(
                    lat,
                    lng
                );
            },

            () => {
                setStatus(
                    "Click the map to choose a search location."
                );
            }
        );
}


/* =========================================================
   NEAREST ARTISAN
========================================================= */

async function runNearestSearch(
    lat,
    lng
) {
    try {
        setStatus(
            "Finding nearest artisan..."
        );

        const response =
            await fetch(
                `/api/heritage/artisans/nearest/?lat=${lat}&lng=${lng}`
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Nearest search failed."
            );
        }

        const feature =
            data.artisan;

        displayArtisans(
            [feature]
        );

        const coordinates =
            feature.geometry
                .coordinates;

        map.fitBounds(
            [
                [
                    lat,
                    lng
                ],

                [
                    coordinates[1],
                    coordinates[0]
                ]
            ],
            {
                padding:
                    [80, 80]
            }
        );

        if (
            artisanMarkers.length >
            0
        ) {
            artisanMarkers[0]
                .marker
                .openPopup();
        }

        setStatus(
            `Nearest artisan: ${data.distance_km} km away`
        );
    } catch (error) {
        console.error(error);

        setStatus(
            error.message
        );
    }
}


function findNearestArtisan() {
    if (selectedLocation) {
        runNearestSearch(
            selectedLocation.lat,
            selectedLocation.lng
        );

        return;
    }

    setStatus(
        "Getting your location..."
    );

    navigator.geolocation
        .getCurrentPosition(
            (position) => {
                const lat =
                    position.coords
                        .latitude;

                const lng =
                    position.coords
                        .longitude;

                selectMapLocation(
                    lat,
                    lng
                );

                runNearestSearch(
                    lat,
                    lng
                );
            },

            () => {
                setStatus(
                    "Click the map to choose a search location."
                );
            }
        );
}


/* =========================================================
   ADD ARTISAN MODAL
========================================================= */

function openArtisanModal() {
    editingArtisanId =
        null;

    artisanModalTitle
        .textContent =
        "Add Artisan";

    saveArtisanBtn
        .textContent =
        "Save Artisan";

    artisanForm.reset();

    resetArtisanLocationPicker();

    artisanFormMessage
        .textContent =
        "";

    artisanFormMessage
        .classList
        .remove(
            "error",
            "success"
        );

    artisanModal
        .classList
        .add("open");

    setTimeout(
        () => {
            initialiseArtisanLocationMap();
        },
        150
    );
}


function closeArtisanModal() {
    artisanModal
        .classList
        .remove("open");

    artisanFormMessage
        .textContent =
        "";

    artisanFormMessage
        .classList
        .remove(
            "error",
            "success"
        );

    clearTimeout(
        addressSearchTimer
    );
}


/* =========================================================
   ARTISAN LOCATION MAP
========================================================= */

function initialiseArtisanLocationMap() {
    const mapElement =
        document.getElementById(
            "artisanLocationMap"
        );

    if (!mapElement) {
        console.error(
            "artisanLocationMap element was not found."
        );

        return;
    }

    if (!artisanLocationMap) {
        artisanLocationMap =
            L.map(
                "artisanLocationMap"
            ).setView(
                [53.3498, -6.2603],
                13
            );

        L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            {
                attribution:
                    "Tiles &copy; Esri",

                maxZoom: 19
            }
        ).addTo(
            artisanLocationMap
        );

        artisanLocationMap.on(
            "click",
            function (event) {
                selectArtisanFormLocation(
                    event.latlng.lat,
                    event.latlng.lng
                );
            }
        );
    }

    artisanLocationMap
        .invalidateSize();

    if (
        newArtisanLocation
    ) {
        artisanLocationMap
            .setView(
                [
                    newArtisanLocation.lat,
                    newArtisanLocation.lng
                ],
                15
            );
    }
}


/* =========================================================
   SELECT ARTISAN FORM LOCATION
========================================================= */

function selectArtisanFormLocation(
    lat,
    lng
) {
    newArtisanLocation = {
        lat: lat,
        lng: lng
    };

    if (
        artisanLocationMarker
    ) {
        artisanLocationMap
            .removeLayer(
                artisanLocationMarker
            );
    }

    artisanLocationMarker =
        L.circleMarker(
            [lat, lng],
            {
                radius: 9,
                color: "#3f4a3d",
                weight: 3,
                fillColor: "#b85f36",
                fillOpacity: 1
            }
        ).addTo(
            artisanLocationMap
        );

    artisanLocationMarker
        .bindPopup(
            "<strong>Artisan location</strong>"
        );

    artisanLocationDisplay
        .textContent =
        `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}


function updateArtisanLocationDisplay() {
    if (
        !artisanLocationDisplay
    ) {
        return;
    }

    if (
        !newArtisanLocation
    ) {
        artisanLocationDisplay
            .textContent =
            "No location selected";

        return;
    }

    artisanLocationDisplay
        .textContent =
        `${newArtisanLocation.lat.toFixed(5)}, ` +
        `${newArtisanLocation.lng.toFixed(5)}`;
}


function resetArtisanLocationPicker() {
    newArtisanLocation =
        null;

    if (
        artisanLocationMap &&
        artisanLocationMarker
    ) {
        artisanLocationMap
            .removeLayer(
                artisanLocationMarker
            );
    }

    artisanLocationMarker =
        null;

    if (
        artisanLocationDisplay
    ) {
        artisanLocationDisplay
            .textContent =
            "No location selected";
    }

    if (
        artisanLocationMap
    ) {
        artisanLocationMap
            .setView(
                [53.3498, -6.2603],
                13
            );
    }
}


/* =========================================================
   ADDRESS GEOCODING
========================================================= */

async function geocodeArtisanAddress() {
    const address =
        artisanAddressInput
            .value
            .trim();

    if (
        address.length < 3
    ) {
        return;
    }

    if (
        !artisanLocationMap
    ) {
        initialiseArtisanLocationMap();
    }

    try {
        artisanFormMessage
            .textContent =
            "Finding address...";

        artisanFormMessage
            .classList
            .remove(
                "error",
                "success"
            );

        const query =
            encodeURIComponent(
                `${address}, Ireland`
            );

        const response =
            await fetch(
                `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=ie&q=${query}`,
                {
                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );

        if (!response.ok) {
            throw new Error(
                "Address search failed."
            );
        }

        const results =
            await response.json();

        if (
            results.length === 0
        ) {
            artisanFormMessage
                .textContent =
                "Address not found. Choose the location manually on the map.";

            artisanFormMessage
                .classList
                .add("error");

            return;
        }

        const lat =
            Number(
                results[0].lat
            );

        const lng =
            Number(
                results[0].lon
            );

        selectArtisanFormLocation(
            lat,
            lng
        );

        artisanLocationMap
            .setView(
                [lat, lng],
                16
            );

        artisanFormMessage
            .textContent =
            "Address located on the map.";

        artisanFormMessage
            .classList
            .add("success");
    } catch (error) {
        console.error(error);

        artisanFormMessage
            .textContent =
            "Unable to locate the address. Choose the location manually on the map.";

        artisanFormMessage
            .classList
            .add("error");
    }
}


/* =========================================================
   OPEN EDIT ARTISAN
========================================================= */

function openEditArtisanModal(
    feature
) {
    const properties =
        feature.properties;

    const coordinates =
        feature.geometry.coordinates;

    editingArtisanId =
        feature.id;

    artisanModalTitle
        .textContent =
        "Edit Artisan";

    saveArtisanBtn
        .textContent =
        "Update Artisan";

    artisanFormMessage
        .textContent =
        "";

    artisanFormMessage
        .classList
        .remove(
            "error",
            "success"
        );

    document
        .getElementById(
            "artisanBusinessName"
        )
        .value =
        properties.name || "";

    document
        .getElementById(
            "artisanName"
        )
        .value =
        properties.artisan_name || "";

    document
        .getElementById(
            "artisanCraftType"
        )
        .value =
        properties.craft_type || "";

    document
        .getElementById(
            "artisanAddress"
        )
        .value =
        properties.address || "";

    document
        .getElementById(
            "artisanDescription"
        )
        .value =
        properties.description || "";

    document
        .getElementById(
            "artisanOpeningHours"
        )
        .value =
        properties.opening_hours || "";

    document
        .getElementById(
            "artisanPhone"
        )
        .value =
        properties.phone || "";

    document
        .getElementById(
            "artisanWebsite"
        )
        .value =
        properties.website || "";

    document
        .getElementById(
            "artisanRegion"
        )
        .value =
        properties.region || "";

    newArtisanLocation = {
        lat:
            coordinates[1],

        lng:
            coordinates[0]
    };

    artisanModal
        .classList
        .add("open");

    updateArtisanLocationDisplay();

    setTimeout(
        () => {
            initialiseArtisanLocationMap();

            selectArtisanFormLocation(
                coordinates[1],
                coordinates[0]
            );

            artisanLocationMap
                .setView(
                    [
                        coordinates[1],
                        coordinates[0]
                    ],
                    16
                );
        },
        150
    );
}


/* =========================================================
   SAVE / UPDATE ARTISAN
========================================================= */

async function saveArtisan(
    event
) {
    event.preventDefault();

    artisanFormMessage
        .textContent =
        "";

    artisanFormMessage
        .classList
        .remove(
            "error",
            "success"
        );

    if (
        !newArtisanLocation
    ) {
        artisanFormMessage
            .textContent =
            "Please choose the artisan location using the address or the map.";

        artisanFormMessage
            .classList
            .add("error");

        return;
    }

    const name =
        document
            .getElementById(
                "artisanBusinessName"
            )
            .value
            .trim();

    const artisanName =
        document
            .getElementById(
                "artisanName"
            )
            .value
            .trim();

    const craftType =
        document
            .getElementById(
                "artisanCraftType"
            )
            .value;

    const address =
        artisanAddressInput
            .value
            .trim();

    const description =
        document
            .getElementById(
                "artisanDescription"
            )
            .value
            .trim();

    const openingHours =
        document
            .getElementById(
                "artisanOpeningHours"
            )
            .value
            .trim();

    const phone =
        document
            .getElementById(
                "artisanPhone"
            )
            .value
            .trim();

    const website =
        document
            .getElementById(
                "artisanWebsite"
            )
            .value
            .trim();

    const regionValue =
        document
            .getElementById(
                "artisanRegion"
            )
            .value;

    if (
        !name ||
        !artisanName ||
        !craftType ||
        !address
    ) {
        artisanFormMessage
            .textContent =
            "Please complete all required fields.";

        artisanFormMessage
            .classList
            .add("error");

        return;
    }

    const payload = {
        type: "Feature",

        geometry: {
            type: "Point",

            coordinates: [
                newArtisanLocation.lng,
                newArtisanLocation.lat
            ]
        },

        properties: {
            name:
                name,

            artisan_name:
                artisanName,

            craft_type:
                craftType,

            description:
                description,

            address:
                address,

            phone:
                phone,

            website:
                website,

            opening_hours:
                openingHours,

            region:
                regionValue
                    ? Number(
                        regionValue
                    )
                    : null
        }
    };

    const isEditing =
        editingArtisanId !==
        null;

    const requestUrl =
        isEditing
            ? `/api/heritage/artisans/${editingArtisanId}/`
            : "/api/heritage/artisans/";

    const requestMethod =
        isEditing
            ? "PATCH"
            : "POST";

    try {
        artisanFormMessage
            .textContent =
            isEditing
                ? "Updating artisan..."
                : "Saving artisan...";

        const response =
            await fetch(
                requestUrl,
                {
                    method:
                        requestMethod,

                    headers:
                        getApiHeaders(),

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );

        let data = {};

        try {
            data =
                await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error(
                "Artisan save error:",
                data
            );

            throw new Error(
                formatApiErrors(data) ||
                "Unable to save artisan. Check the form values."
            );
        }

        artisanFormMessage
            .textContent =
            isEditing
                ? "Artisan updated successfully."
                : "Artisan added successfully.";

        artisanFormMessage
            .classList
            .add("success");

        artisanForm.reset();

        resetArtisanLocationPicker();

        editingArtisanId =
            null;

        await loadArtisans();

        setStatus(
            isEditing
                ? "Artisan updated successfully."
                : "New artisan added successfully."
        );

        setTimeout(
            () => {
                closeArtisanModal();
            },
            700
        );
    } catch (error) {
        console.error(error);

        artisanFormMessage
            .textContent =
            error.message;

        artisanFormMessage
            .classList
            .add("error");
    }
}


/* =========================================================
   DELETE ARTISAN
========================================================= */

async function deleteArtisan(
    feature
) {
    const properties =
        feature.properties;

    const confirmed =
        window.confirm(
            `Delete "${properties.name}"?\n\nThis action cannot be undone.`
        );

    if (!confirmed) {
        return;
    }

    try {
        setStatus(
            `Deleting ${properties.name}...`
        );

        const response =
            await fetch(
                `/api/heritage/artisans/${feature.id}/`,
                {
                    method:
                        "DELETE",

                    headers:
                        getApiHeaders()
                }
            );

        if (!response.ok) {
            let data = {};

            try {
                data =
                    await response.json();
            } catch {
                data = {};
            }

            console.error(
                "Delete artisan error:",
                data
            );

            throw new Error(
                "Unable to delete artisan."
            );
        }

        await loadArtisans();

        setStatus(
            "Artisan deleted successfully."
        );
    } catch (error) {
        console.error(error);

        setStatus(
            error.message
        );
    }
}


/* =========================================================
   RESET MAIN MAP
========================================================= */

function resetMap() {
    searchInput.value =
        "";

    craftFilter.value =
        "";

    regionFilter.value =
        "";

    selectedLocation =
        null;

    if (
        selectedLocationMarker
    ) {
        map.removeLayer(
            selectedLocationMarker
        );

        selectedLocationMarker =
            null;
    }

    if (
        searchRadiusCircle
    ) {
        map.removeLayer(
            searchRadiusCircle
        );

        searchRadiusCircle =
            null;
    }

    if (
        selectedLocationInfo
    ) {
        selectedLocationInfo
            .classList
            .remove("active");

        selectedLocationInfo
            .textContent =
            "Click anywhere on the map to choose a search location.";
    }

    if (
        toggleArtisans
    ) {
        toggleArtisans.checked =
            true;

        if (
            !map.hasLayer(
                artisanLayer
            )
        ) {
            map.addLayer(
                artisanLayer
            );
        }
    }

    if (
        toggleRegions
    ) {
        toggleRegions.checked =
            true;

        if (
            !map.hasLayer(
                regionLayer
            )
        ) {
            map.addLayer(
                regionLayer
            );
        }
    }

    if (
        toggleRoutes
    ) {
        toggleRoutes.checked =
            true;

        if (
            !map.hasLayer(
                routeLayer
            )
        ) {
            map.addLayer(
                routeLayer
            );
        }
    }

    displayArtisans(
        artisanData
    );

    map.setView(
        [53.3498, -6.2603],
        13
    );

    setStatus(
        `${artisanData.length} artisans loaded`
    );
}


/* =========================================================
   MAIN EVENT LISTENERS
========================================================= */

searchInput.addEventListener(
    "input",
    applyFilters
);


craftFilter.addEventListener(
    "change",
    applyFilters
);


regionFilter.addEventListener(
    "change",
    filterByRegion
);


document
    .getElementById(
        "findNearbyBtn"
    )
    .addEventListener(
        "click",
        findNearbyArtisans
    );


document
    .getElementById(
        "findNearestBtn"
    )
    .addEventListener(
        "click",
        findNearestArtisan
    );


document
    .getElementById(
        "resetBtn"
    )
    .addEventListener(
        "click",
        resetMap
    );


/* =========================================================
   MAP LAYER TOGGLES
========================================================= */

toggleArtisans.addEventListener(
    "change",
    function () {
        if (this.checked) {
            map.addLayer(
                artisanLayer
            );
        } else {
            map.removeLayer(
                artisanLayer
            );
        }
    }
);


toggleRegions.addEventListener(
    "change",
    function () {
        if (this.checked) {
            map.addLayer(
                regionLayer
            );
        } else {
            map.removeLayer(
                regionLayer
            );
        }
    }
);


toggleRoutes.addEventListener(
    "change",
    function () {
        if (this.checked) {
            map.addLayer(
                routeLayer
            );
        } else {
            map.removeLayer(
                routeLayer
            );
        }
    }
);


/* =========================================================
   ARTISAN MODAL EVENTS
========================================================= */

openAddArtisanBtn.addEventListener(
    "click",
    openArtisanModal
);


closeArtisanModalBtn.addEventListener(
    "click",
    closeArtisanModal
);


cancelArtisanBtn.addEventListener(
    "click",
    closeArtisanModal
);


artisanForm.addEventListener(
    "submit",
    saveArtisan
);


/* Prevent Enter from submitting form */
artisanForm.addEventListener(
    "keydown",
    function (event) {
        if (
            event.key ===
                "Enter" &&
            event.target
                .tagName !==
                "TEXTAREA"
        ) {
            event.preventDefault();
        }
    }
);


/* Automatically geocode after user pauses typing */
artisanAddressInput.addEventListener(
    "input",
    function () {
        clearTimeout(
            addressSearchTimer
        );

        const address =
            artisanAddressInput
                .value
                .trim();

        if (
            address.length < 3
        ) {
            return;
        }

        addressSearchTimer =
            setTimeout(
                geocodeArtisanAddress,
                700
            );
    }
);


/* Geocode immediately when leaving address field */
artisanAddressInput.addEventListener(
    "blur",
    function () {
        clearTimeout(
            addressSearchTimer
        );

        const address =
            artisanAddressInput
                .value
                .trim();

        if (
            address.length >= 3
        ) {
            geocodeArtisanAddress();
        }
    }
);


const modalBackdrop =
    artisanModal.querySelector(
        ".artisan-modal-backdrop"
    );


modalBackdrop.addEventListener(
    "click",
    closeArtisanModal
);


document.addEventListener(
    "keydown",
    function (event) {
        if (
            event.key ===
                "Escape" &&
            artisanModal
                .classList
                .contains("open")
        ) {
            closeArtisanModal();
        }
    }
);


/* =========================================================
   INITIALISE APPLICATION
========================================================= */

async function initialiseMap() {
    await loadArtisans();
    await loadRegions();
    await loadRoutes();
}


initialiseMap();