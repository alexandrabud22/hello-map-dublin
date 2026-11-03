const map = L.map("map", {
    scrollWheelZoom: false
}).setView([53.3498, -6.2603], 13);

map.on("click focus", () => map.scrollWheelZoom.enable());
map.on("mouseout blur", () => map.scrollWheelZoom.disable());

// Keep the OpenStreetMap credit visible on the map.
const OSM_TILE_URL =
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

const OSM_ATTRIBUTION =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

L.tileLayer(
    OSM_TILE_URL,
    {
        attribution: OSM_ATTRIBUTION,
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

const artisanLayer = (
    typeof L.markerClusterGroup === "function"
        ? L.markerClusterGroup({
            showCoverageOnHover: false,
            maxClusterRadius: 45,
            spiderfyOnMaxZoom: true,

            disableClusteringAtZoom: 16,
        })
        : L.layerGroup()
).addTo(map);
const regionLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);

const bufferLayer = L.layerGroup().addTo(map);

const routeLayersById = {};

const resultsSubtitle =
    document.getElementById("resultsSubtitle");

const DEFAULT_RESULTS_SUBTITLE =
    "Discover makers from your selected area.";

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

function setStatus(message) {
    mapStatus.textContent = message;
}

// Follow API pages so every workshop, region and route is loaded.
async function fetchAllFeatures(url, errorMessage) {
    const allFeatures = [];
    let nextUrl = url;

    while (nextUrl) {
        const response = await fetch(nextUrl);

        if (!response.ok) {
            throw new Error(errorMessage);
        }

        const data = await response.json();

        allFeatures.push(
            ...(data.results?.features || data.features || [])
        );

        nextUrl = data.next;
    }

    return allFeatures;
}

// Treat workshop text as text, not HTML.
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

// Include the CSRF token when sending changes to Django.
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

function createArtisanPopup(feature) {
    const properties =
        feature.properties;

    return `
        <h3>${escapeHtml(properties.name)}</h3>

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

function updateResults(features) {
    resultsContainer.innerHTML = "";

    const resultsPanel = document.getElementById("resultsPanel");
    if (resultsPanel) {
        resultsPanel.scrollTop = 0;
    }

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
                ${
                    properties.distance_to_route_m !== undefined
                        ? `<span class="route-distance">· ${escapeHtml(properties.distance_to_route_m)} m from route</span>`
                        : ""
                }
            </div>

            <h3>
                ${escapeHtml(properties.name)}
            </h3>

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

                resultsContainer
                    .querySelectorAll(".result-item.selected")
                    .forEach((item) => item.classList.remove("selected"));
                result.classList.add("selected");

                const mapCard = document.getElementById("explore");
                const mapBox = mapCard.getBoundingClientRect();
                const headerHeight = 80;

                if (mapBox.top < headerHeight || mapBox.bottom > window.innerHeight) {
                    mapCard.scrollIntoView({ behavior: "smooth", block: "start" });
                }

                const markerObject =
                    artisanMarkers.find(
                        (item) =>
                            item.feature.id ===
                            feature.id
                    );

                if (!markerObject) {
                    map.setView([coordinates[1], coordinates[0]], 16);
                    return;
                }

                const marker = markerObject.marker;

                if (!map.hasLayer(artisanLayer)) {
                    map.addLayer(artisanLayer);
                    if (toggleArtisans) {
                        toggleArtisans.checked = true;
                    }
                }

                const latLng = marker.getLatLng();
                const openIfStillShown = () => {
                    if (artisanLayer.hasLayer(marker)) {
                        marker.openPopup();
                    }
                };

                map.stop();

                if (map.getZoom() >= 16 && map.getBounds().contains(latLng)) {
                    openIfStillShown();
                } else {
                    map.once("moveend", openIfStillShown);
                    map.setView(latLng, 17);
                }
            }
        );

        result.tabIndex = 0;
        result.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && event.target === result) {
                event.preventDefault();
                result.click();
            }
        });

        resultsContainer.appendChild(
            result
        );
    });
}

async function loadArtisans() {
    try {
        setStatus(
            "Loading artisans..."
        );

        artisanData = await fetchAllFeatures(
            "/api/heritage/artisans/",
            "Unable to load artisans."
        );

        showResults(
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

async function loadRegions() {
    try {
        const features = await fetchAllFeatures(
            "/api/heritage/regions/",
            "Unable to load regions."
        );

        populateRegionSelects(features);

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
                            <h3>
                                ${escapeHtml(feature.properties.name)}
                            </h3>

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

async function loadRoutes() {
    try {
        const features = await fetchAllFeatures(
            "/api/heritage/routes/",
            "Unable to load routes."
        );

        routeLayer.clearLayers();

        renderRouteCards(features);

        L.geoJSON(
            features,
            {
                style: {
                    color: "#a2512e",
                    weight: 4,
                    opacity: 0.9,
                    dashArray: "7, 5"
                },

                onEachFeature:
                    function (
                        feature,
                        layer
                    ) {
                        routeLayersById[feature.id] = layer;

                        layer.bindPopup(`
                            <h3>
                                ${escapeHtml(feature.properties.name)}
                            </h3>

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

                            <div class="route-buffer-actions">
                                <span>Artisans along this route:</span>
                                <button type="button" class="route-buffer-btn"
                                    data-route-id="${escapeHtml(feature.id)}"
                                    data-distance="200">within 200 m</button>
                                <button type="button" class="route-buffer-btn"
                                    data-route-id="${escapeHtml(feature.id)}"
                                    data-distance="500">within 500 m</button>
                            </div>
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

let baseFeatures = [];

function getActiveFilters() {
    return {
        search: searchInput.value.toLowerCase().trim(),
        craft: craftFilter.value,
        region: regionFilter.value,
    };
}

function matchesActiveFilters(feature) {
    const { search, craft, region } = getActiveFilters();
    const p = feature.properties;

    const searchableText = [
        p.name,
        p.artisan_name,
        p.address,
        p.description,
        p.craft_type_display,
    ].join(" ").toLowerCase();

    return (
        (!search || searchableText.includes(search)) &&
        (!craft || p.craft_type === craft) &&
        (!region || String(p.region) === region)
    );
}

function filterQueryString() {
    const { search, craft, region } = getActiveFilters();
    const params = new URLSearchParams();

    if (search) params.set("search", search);
    if (craft) params.set("craft_type", craft);
    if (region) params.set("region", region);

    const text = params.toString();
    return text ? `&${text}` : "";
}

function updateFilterNote(shown, total) {
    const note = document.getElementById("filterNote");

    if (!note) {
        return;
    }

    const { search, craft, region } = getActiveFilters();
    const active = [];

    if (search) active.push(`"${search}"`);
    if (craft) active.push(craftFilter.selectedOptions[0].text.trim());
    if (region) active.push(regionFilter.selectedOptions[0].text.trim());

    note.textContent = active.length
        ? `Showing ${shown} of ${total} - filters: ${active.join(", ")}`
        : "";
}

// Keep the current search results so filters work on the same set of workshops.
function showResults(features) {
    baseFeatures = features;

    const filtered = baseFeatures.filter(matchesActiveFilters);

    displayArtisans(filtered);
    updateFilterNote(filtered.length, baseFeatures.length);

    return filtered;
}

function applyFilters() {
    const filtered = showResults(baseFeatures);

    setStatus(
        `${filtered.length} matching artisans`
    );
}

async function filterByRegion() {
    bufferLayer.clearLayers();

    const regionId =
        regionFilter.value;

    if (!regionId) {
        showResults(
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

        showResults(
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
                fillColor: "#a2512e",
                fillOpacity: 1,
                interactive: false
            }
        ).addTo(map);

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
                `/api/heritage/artisans/within_radius/?lat=${lat}&lng=${lng}&radius=${radius}${filterQueryString()}`
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

        showResults(
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
                        "#a2512e",

                    weight: 2,
                    opacity: 0.7,

                    fillColor:
                        "#a2512e",

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
                `/api/heritage/artisans/nearest/?lat=${lat}&lng=${lng}${filterQueryString()}`
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

        showResults(
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

    activateModalFocus();

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

    deactivateModalFocus();

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
            OSM_TILE_URL,
            {
                attribution:
                    OSM_ATTRIBUTION,

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
                fillColor: "#a2512e",
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

        const parts = address
            .split(",")
            .map((part) => part.trim())
            .filter(Boolean);

        // Try a shorter address if the full address is not found.
        const candidates = [
            address,
            address.replace(/^\s*\d+[a-zA-Z]?\s+/, ""),
            parts.slice(1).join(", "),
            parts.slice(-1).join(", "),
        ].filter(
            (candidate, index, list) =>
                candidate && list.indexOf(candidate) === index
        );

        let match = null;
        let usedCandidate = "";

        for (const candidate of candidates) {
            const query = encodeURIComponent(`${candidate}, Ireland`);

            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=ie&q=${query}`,
                { headers: { "Accept": "application/json" } }
            );

            if (!response.ok) {
                throw new Error("Address search failed.");
            }

            const results = await response.json();

            if (results.length > 0) {
                match = results[0];
                usedCandidate = candidate;
                break;
            }

            // Wait a second before trying another address with Nominatim.
            await new Promise((resolve) => setTimeout(resolve, 1000));
        }

        if (!match) {
            artisanFormMessage
                .textContent =
                "Address not found. Click the map to place the artisan.";

            artisanFormMessage
                .classList
                .add("error");

            return;
        }

        const exact = usedCandidate === address;
        const lat = Number(match.lat);
        const lng = Number(match.lon);

        selectArtisanFormLocation(
            lat,
            lng
        );

        artisanLocationMap
            .setView(
                [lat, lng],
                exact ? 17 : 15
            );

        artisanFormMessage
            .textContent =
            exact
                ? "Address located on the map."
                : `Exact address not in OpenStreetMap - placed near "${usedCandidate}". Click the map to adjust the pin.`;

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

    activateModalFocus();

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

// POST creates a workshop; PATCH updates an existing one.
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

// Ask before deleting the selected workshop.
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

function resetMap() {
    bufferLayer.clearLayers();

    if (resultsSubtitle) {
        resultsSubtitle.textContent = DEFAULT_RESULTS_SUBTITLE;
    }

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

    showResults(
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

artisanForm.addEventListener(
    "keydown",
    function (event) {
        if (
            event.key === "Enter" &&
            event.target.tagName === "INPUT"
        ) {
            event.preventDefault();
        }
    }
);

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

let focusBeforeModal = null;

const FOCUSABLE_SELECTOR = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled]):not([type='hidden'])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
].join(",");

function getModalFocusableElements() {
    return [...artisanModal.querySelectorAll(FOCUSABLE_SELECTOR)]
        .filter((element) => element.offsetParent !== null);
}

// Move keyboard focus into the dialog and return it when closed.
function activateModalFocus() {

    focusBeforeModal = document.activeElement;

    artisanModal.setAttribute("aria-hidden", "false");

    setTimeout(() => {
        document.getElementById("artisanBusinessName")?.focus();
    }, 50);
}

function deactivateModalFocus() {
    artisanModal.setAttribute("aria-hidden", "true");

    if (focusBeforeModal && typeof focusBeforeModal.focus === "function") {
        focusBeforeModal.focus();
    }

    focusBeforeModal = null;
}

// Keep Tab navigation inside the open dialog.
artisanModal.addEventListener("keydown", (event) => {
    if (event.key !== "Tab" || !artisanModal.classList.contains("open")) {
        return;
    }

    const focusable = getModalFocusableElements();

    if (focusable.length === 0) {
        return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
});

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

function populateRegionSelects(features) {
    const sortedRegions = [...features].sort((a, b) =>
        a.properties.name.localeCompare(b.properties.name)
    );

    const fillSelect = (select, firstLabel) => {
        if (!select) {
            return;
        }

        const previousValue = select.value;

        select.innerHTML = "";
        select.add(new Option(firstLabel, ""));

        sortedRegions.forEach((feature) => {

            select.add(
                new Option(feature.properties.name, String(feature.id))
            );
        });

        if ([...select.options].some((o) => o.value === previousValue)) {
            select.value = previousValue;
        }
    };

    fillSelect(regionFilter, "All regions");
    fillSelect(
        document.getElementById("artisanRegion"),
        "Detect from location"
    );
}

// Draw the route buffer and show the workshops inside it.
async function showArtisansAlongRoute(routeId, distanceMetres) {
    try {
        setStatus("Finding artisans along the route...");

        const response = await fetch(
            `/api/heritage/routes/${encodeURIComponent(routeId)}/artisans_nearby/?distance=${encodeURIComponent(distanceMetres)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                formatApiErrors(data) || "Unable to run the route search."
            );
        }

        bufferLayer.clearLayers();

        const corridor = L.geoJSON(data.buffer, {
            style: {
                color: "#a2512e",
                weight: 1,
                dashArray: "4, 4",
                fillColor: "#a2512e",
                fillOpacity: 0.08,
            },
            interactive: false,
        }).addTo(bufferLayer);

        const features = data.artisans?.features || [];

        showResults(features);

        map.closePopup();
        map.fitBounds(corridor.getBounds(), { padding: [30, 30] });

        if (resultsSubtitle) {
            resultsSubtitle.textContent =
                `Within ${data.buffer_m} m of ${data.route.name}`;
        }

        setStatus(
            `${data.count} artisan${data.count === 1 ? "" : "s"} within ` +
            `${data.buffer_m} m of ${data.route.name}`
        );
    } catch (error) {
        console.error(error);
        setStatus(error.message);
    }
}

map.on("popupopen", (event) => {
    const popupElement = event.popup.getElement();

    if (!popupElement) {
        return;
    }

    popupElement
        .querySelectorAll(".route-buffer-btn")
        .forEach((button) => {
            button.addEventListener("click", (clickEvent) => {
                clickEvent.stopPropagation();

                showArtisansAlongRoute(
                    button.dataset.routeId,
                    button.dataset.distance
                );
            });
        });
});

function renderRouteCards(features) {
    const container = document.getElementById("routeCards");

    if (!container) {
        return;
    }

    if (features.length === 0) {
        container.innerHTML =
            '<p class="text-muted">No heritage routes yet.</p>';
        return;
    }

    container.innerHTML = features.map((feature) => {
        const p = feature.properties;

        return `
            <article class="route-card">
                <div class="result-category">
                    ${escapeHtml(p.route_type_display)}
                    <span class="route-distance">· ${escapeHtml(p.distance_km ?? "?")} km</span>
                </div>
                <h3>${escapeHtml(p.name)}</h3>
                <p>${escapeHtml(p.description)}</p>
                <div class="route-card-actions">
                    <button type="button" class="route-card-btn"
                        data-action="show" data-route-id="${escapeHtml(feature.id)}">
                        Show on map
                    </button>
                    <button type="button" class="route-card-btn primary"
                        data-action="buffer" data-route-id="${escapeHtml(feature.id)}">
                        Artisans within 200 m
                    </button>
                </div>
            </article>
        `;
    }).join("");
}

document.getElementById("routeCards")?.addEventListener("click", (event) => {
    const button = event.target.closest(".route-card-btn");

    if (!button) {
        return;
    }

    const routeId = button.dataset.routeId;

    document.getElementById("explore").scrollIntoView({ behavior: "smooth" });

    if (button.dataset.action === "buffer") {
        showArtisansAlongRoute(routeId, 200);
        return;
    }

    const layer = routeLayersById[routeId];

    if (layer) {
        if (toggleRoutes && !toggleRoutes.checked) {
            toggleRoutes.checked = true;
            map.addLayer(routeLayer);
        }

        map.fitBounds(layer.getBounds(), { padding: [40, 40] });
        layer.openPopup(layer.getCenter());
    }
});

const navToggle = document.getElementById("navToggle");
const topbar = document.querySelector(".topbar");

navToggle?.addEventListener("click", () => {
    const isOpen = topbar.classList.toggle("nav-open");

    navToggle.setAttribute("aria-expanded", String(isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
});

document.querySelectorAll("#mainNav a").forEach((link) => {
    link.addEventListener("click", () => {
        document.querySelectorAll("#mainNav a")
            .forEach((a) => a.classList.remove("active"));
        link.classList.add("active");

        topbar.classList.remove("nav-open");
        navToggle?.setAttribute("aria-expanded", "false");
    });
});

const mapLegend = document.getElementById("mapLegend");
const legendToggle = document.getElementById("legendToggle");

function setLegendCollapsed(collapsed) {
    mapLegend?.classList.toggle("collapsed", collapsed);
    legendToggle?.setAttribute("aria-expanded", String(!collapsed));
}

legendToggle?.addEventListener("click", () => {
    setLegendCollapsed(!mapLegend.classList.contains("collapsed"));
});

setLegendCollapsed(window.matchMedia("(max-width: 820px)").matches);

async function initialiseMap() {
    await loadArtisans();
    await loadRegions();
    await loadRoutes();
}

initialiseMap();
