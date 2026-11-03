# Tests use a separate temporary database, not the saved workshop data.
from django.contrib.auth.models import User
from django.contrib.gis.geos import LineString, Point, Polygon
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ArtisanLocation, CulturalRegion, HeritageRoute

def square(min_lng, min_lat, max_lng, max_lat):
    return Polygon(
        (
            (min_lng, min_lat), (max_lng, min_lat), (max_lng, max_lat),
            (min_lng, max_lat), (min_lng, min_lat),
        ),
        srid=4326,
    )

def artisan_feature(lng, lat, **properties):

    data = {
        "name": "Test Workshop",
        "artisan_name": "Test Maker",
        "craft_type": "POTTERY",
        "address": "Dublin",
    }
    data.update(properties)
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": data,
    }

# Reuse the same sample users, regions and workshops across the tests.
class HeritageTestData(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user("owner", password="pass12345!")
        cls.other = User.objects.create_user("other", password="pass12345!")
        cls.staff = User.objects.create_user(
            "staff", password="pass12345!", is_staff=True
        )

        cls.region_a = CulturalRegion.objects.create(
            name="Region A", region_type="Test",
            boundary=square(-6.272, 53.343, -6.258, 53.347),
        )
        cls.region_b = CulturalRegion.objects.create(
            name="Region B", region_type="Test",
            boundary=square(-6.290, 53.337, -6.272, 53.343),
        )

        cls.route = HeritageRoute.objects.create(
            name="Test Route", route_type="WALKING",
            path=LineString((-6.271, 53.3455), (-6.259, 53.3455), srid=4326),
        )

        cls.near = ArtisanLocation.objects.create(
            name="Near", artisan_name="A", craft_type="POTTERY",
            address="x", location=Point(-6.265, 53.3460, srid=4326),
            owner=cls.owner,
        )

        cls.liberties = ArtisanLocation.objects.create(
            name="Liberties", artisan_name="B", craft_type="WEAVING",
            address="x", location=Point(-6.280, 53.3410, srid=4326),
        )

        cls.far = ArtisanLocation.objects.create(
            name="Far", artisan_name="C", craft_type="OTHER",
            address="x", location=Point(-6.066, 53.387, srid=4326),
        )

class ModelTests(HeritageTestData):

    def test_region_is_detected_from_location(self):
        self.assertEqual(self.near.region, self.region_a)
        self.assertEqual(self.liberties.region, self.region_b)
        self.assertIsNone(self.far.region)

    def test_route_length_is_calculated_in_km(self):

        self.assertIsNotNone(self.route.distance_km)
        self.assertAlmostEqual(float(self.route.distance_km), 0.80, delta=0.05)

# Check what visitors, owners and staff are allowed to change.
class PermissionTests(HeritageTestData):

    def test_anyone_can_read(self):
        for url in ("/api/heritage/artisans/", "/api/heritage/regions/",
                    "/api/heritage/routes/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_anonymous_cannot_create_artisan(self):
        response = self.client.post(
            "/api/heritage/artisans/", artisan_feature(-6.26, 53.345),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logged_in_user_creates_artisan_and_becomes_owner(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(
            "/api/heritage/artisans/",
            artisan_feature(-6.262, 53.345, owner=self.staff.id),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = ArtisanLocation.objects.get(id=response.data["id"])

        self.assertEqual(created.owner, self.other)
        self.assertEqual(created.region, self.region_a)

    def test_only_owner_can_edit(self):
        url = f"/api/heritage/artisans/{self.near.id}/"
        body = {"properties": {"name": "Changed"}}

        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.patch(url, body, format="json").status_code, 403
        )

        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.patch(url, body, format="json").status_code, 200
        )

    def test_staff_can_moderate_any_artisan(self):
        self.client.force_authenticate(self.staff)
        response = self.client.delete(f"/api/heritage/artisans/{self.near.id}/")
        self.assertEqual(response.status_code, 204)

    def test_only_staff_can_change_regions_and_routes(self):
        url = f"/api/heritage/routes/{self.route.id}/"

        self.assertEqual(self.client.delete(url).status_code, 403)

        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(url).status_code, 403)

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(url).status_code, 204)

class ValidationTests(HeritageTestData):

    def assert_bad_request(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400, url)
        self.assertIn("error", response.data)

    def test_radius_query_rejects_bad_parameters(self):
        base = "/api/heritage/artisans/within_radius/"
        self.assert_bad_request(base)
        self.assert_bad_request(base + "?lat=abc&lng=-6.26&radius=1")
        self.assert_bad_request(base + "?lat=999&lng=-6.26&radius=1")
        self.assert_bad_request(base + "?lat=53.3&lng=-6.26&radius=0")
        self.assert_bad_request(base + "?lat=53.3&lng=-6.26&radius=500")

    def test_intersection_rejects_bad_region_id(self):
        base = "/api/heritage/routes/intersecting_region/"
        self.assert_bad_request(base + "?region_id=abc")
        self.assertEqual(
            self.client.get(base + "?region_id=99999").status_code, 404
        )

    def test_buffer_rejects_bad_distance(self):
        url = f"/api/heritage/routes/{self.route.id}/artisans_nearby/"
        self.assert_bad_request(url + "?distance=5")
        self.assert_bad_request(url + "?distance=99999")

    def test_artisan_outside_ireland_is_rejected(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/heritage/artisans/", artisan_feature(2.35, 48.85),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_artisan_with_bad_phone_or_blank_name_is_rejected(self):
        self.client.force_authenticate(self.owner)
        for bad in ({"phone": "call me"}, {"name": "   "}):
            response = self.client.post(
                "/api/heritage/artisans/",
                artisan_feature(-6.262, 53.345, **bad), format="json",
            )
            self.assertEqual(response.status_code, 400, bad)

    def test_artisan_must_be_inside_chosen_region(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/heritage/artisans/",
            artisan_feature(-6.262, 53.345, region=self.region_b.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

# Bad input should return an error response rather than crash the API.
class RobustnessTests(HeritageTestData):

    def post_artisan(self, body, **kwargs):
        self.client.force_authenticate(self.owner)
        return self.client.post("/api/heritage/artisans/", body, **kwargs)

    def test_wrong_geometry_type_is_rejected(self):
        body = artisan_feature(-6.26, 53.345)
        body["geometry"] = {
            "type": "LineString",
            "coordinates": [[-6.26, 53.345], [-6.25, 53.346]],
        }
        response = self.post_artisan(body, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("location", str(response.data))

    def test_missing_geometry_is_rejected(self):
        body = artisan_feature(-6.26, 53.345)
        del body["geometry"]
        self.assertEqual(self.post_artisan(body, format="json").status_code, 400)

    def test_garbage_coordinates_are_rejected(self):
        body = artisan_feature(-6.26, 53.345)
        body["geometry"] = {"type": "Point", "coordinates": ["abc", None]}
        self.assertEqual(self.post_artisan(body, format="json").status_code, 400)

    def test_swapped_lat_lng_is_rejected(self):

        response = self.post_artisan(
            artisan_feature(53.345, -6.26), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_broken_json_returns_400_not_500(self):
        response = self.post_artisan(
            '{"type": "Feature", "geometry": ',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_self_intersecting_region_is_rejected(self):
        self.client.force_authenticate(self.staff)
        bow_tie = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-6.27, 53.34], [-6.25, 53.36], [-6.25, 53.34],
                    [-6.27, 53.36], [-6.27, 53.34],
                ]],
            },
            "properties": {"name": "Bow tie", "region_type": "Test"},
        }
        response = self.client.post(
            "/api/heritage/regions/", bow_tie, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid geometry", str(response.data))

    def test_route_must_be_a_line_with_two_points(self):
        self.client.force_authenticate(self.staff)
        body = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-6.26, 53.345]},
            "properties": {"name": "Not a line", "route_type": "WALKING"},
        }
        response = self.client.post(
            "/api/heritage/routes/", body, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_staff_can_create_valid_route_and_length_is_calculated(self):
        self.client.force_authenticate(self.staff)
        body = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-6.271, 53.344], [-6.259, 53.344]],
            },
            "properties": {"name": "New route", "route_type": "CRAFT"},
        }
        response = self.client.post(
            "/api/heritage/routes/", body, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertAlmostEqual(
            float(response.data["properties"]["distance_km"]), 0.80,
            delta=0.05,
        )

    def test_radius_query_with_no_results_returns_empty_list(self):

        response = self.client.get(
            "/api/heritage/artisans/within_radius/?lat=50&lng=-20&radius=5"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_nearest_with_no_artisans_returns_404(self):
        ArtisanLocation.objects.all().delete()
        response = self.client.get(
            "/api/heritage/artisans/nearest/?lat=53.35&lng=-6.26"
        )
        self.assertEqual(response.status_code, 404)

# Check which workshops and routes each spatial search returns.
class SpatialQueryTests(HeritageTestData):

    @staticmethod
    def names(features):
        return [f["properties"]["name"] for f in features]

    def test_1_within_radius(self):
        response = self.client.get(
            "/api/heritage/artisans/within_radius/"
            "?lat=53.3460&lng=-6.265&radius=2"
        )
        self.assertEqual(response.status_code, 200)
        names = self.names(response.data["results"]["features"])
        self.assertEqual(names, ["Near", "Liberties"])
        self.assertNotIn("Far", names)

    def test_1b_radius_combined_with_craft_filter(self):
        response = self.client.get(
            "/api/heritage/artisans/within_radius/"
            "?lat=53.3460&lng=-6.265&radius=2&craft_type=WEAVING"
        )
        self.assertEqual(
            self.names(response.data["results"]["features"]), ["Liberties"]
        )

    def test_2b_nearest_combined_with_craft_filter(self):
        response = self.client.get(
            "/api/heritage/artisans/nearest/"
            "?lat=53.3460&lng=-6.265&craft_type=WEAVING"
        )
        self.assertEqual(
            response.data["artisan"]["properties"]["name"], "Liberties"
        )

    def test_2_nearest(self):
        response = self.client.get(
            "/api/heritage/artisans/nearest/?lat=53.387&lng=-6.07"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["artisan"]["properties"]["name"], "Far")
        self.assertLess(response.data["distance_km"], 1)

    def test_3_containment(self):
        response = self.client.get(
            f"/api/heritage/regions/{self.region_b.id}/artisans/"
        )
        self.assertEqual(
            self.names(response.data["artisans"]["features"]), ["Liberties"]
        )

    def test_4_intersection(self):
        url = "/api/heritage/routes/intersecting_region/?region_id={}"
        self.assertEqual(self.client.get(url.format(self.region_a.id))
                         .data["count"], 1)
        self.assertEqual(self.client.get(url.format(self.region_b.id))
                         .data["count"], 0)

    def test_5_buffer_along_route(self):
        url = f"/api/heritage/routes/{self.route.id}/artisans_nearby/"

        narrow = self.client.get(url + "?distance=200").data
        self.assertEqual(self.names(narrow["artisans"]["features"]), ["Near"])
        self.assertEqual(narrow["buffer"]["type"], "Polygon")
        self.assertLess(
            narrow["artisans"]["features"][0]["properties"]
            ["distance_to_route_m"], 200,
        )

        wide = self.client.get(url + "?distance=1000").data
        self.assertEqual(
            self.names(wide["artisans"]["features"]), ["Near", "Liberties"]
        )

class PageTests(TestCase):

    def test_home_redirects_to_map(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/heritage/", fetch_redirect_response=False)

    def test_map_page_loads_leaflet(self):
        response = self.client.get("/heritage/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "leaflet")
        self.assertContains(response, 'id="map"')
