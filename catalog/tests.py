from django.test import TestCase

# Create your tests here.


class SubscribeTests(TestCase):
    def test_normalize(self):
        from .subscribe import normalize

        self.assertEqual(normalize("+971", "050 123 4567"), ("+971501234567", "+971"))
        self.assertEqual(normalize("1", "(415) 555-0132"), ("+14155550132", "+1"))
        for bad in (("+971", "12"), ("abc", "5551234567"), ("+1", "")):
            with self.assertRaises(ValueError):
                normalize(*bad)

    def test_endpoint_accepts_and_stores(self):
        from unittest import mock

        from . import subscribe
        from .models import Subscriber

        with mock.patch.object(subscribe, "submit", side_effect=lambda *a, **k: subscribe.store(*a, **k)):
            r = self.client.post("/api/subscribe/", {"country_code": "+44", "phone": "07911 123456"}, content_type="application/json")
            self.assertEqual(r.status_code, 202)
            self.client.post("/api/subscribe/", {"country_code": "+44", "phone": "7911123456"}, content_type="application/json")
        self.assertEqual(Subscriber.objects.filter(phone="+447911123456").count(), 1)
        bad = self.client.post("/api/subscribe/", {"country_code": "+44", "phone": "1"}, content_type="application/json")
        self.assertEqual(bad.status_code, 400)
