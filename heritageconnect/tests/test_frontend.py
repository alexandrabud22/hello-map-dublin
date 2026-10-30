from django.test import TestCase


class MapViewTests(TestCase):

    def test_map_view_loads(self):
        response = self.client.get('/map/')

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Cities Web Map'
        )

        self.assertContains(
            response,
            'leaflet'
        )

    def test_map_template_contains_search(self):
        response = self.client.get('/map/')

        self.assertContains(
            response,
            'searchInput'
        )

        self.assertContains(
            response,
            'resetBtn'
        )

    def test_map_template_loads_static_files(self):
        response = self.client.get('/map/')

        self.assertContains(
            response,
            '/static/js/map.js'
        )

        self.assertContains(
            response,
            '/static/css/styles.css'
        )