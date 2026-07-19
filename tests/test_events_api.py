from datetime import datetime, timedelta, timezone

from tests.base import ApiTestCase


class CreateEventTestCase(ApiTestCase):
    def test_requires_authentication(self):
        res = self.client.post("/events/", json={
            "title": "X", "description": "Y", "category": "IT",
            "event_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        })
        self.assertEqual(res.status_code, 401)

    def test_success(self):
        headers, _ = self.auth_headers("alice")
        res = self.create_event(headers, title="Party")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["title"], "Party")

    def test_event_in_the_past_rejected(self):
        headers, _ = self.auth_headers("alice")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        res = self.create_event(headers, event_date=past)
        self.assertEqual(res.status_code, 400)


class UpdateEventTestCase(ApiTestCase):
    def test_owner_can_update(self):
        headers, _ = self.auth_headers("alice")
        event = self.create_event(headers).json()
        res = self.client.patch(f"/events/{event['id']}", json={"title": "Updated"}, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["title"], "Updated")

    def test_non_owner_cannot_update(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        res = self.client.patch(f"/events/{event['id']}", json={"title": "Hack"}, headers=headers_b)
        self.assertEqual(res.status_code, 404)


class DeleteEventTestCase(ApiTestCase):
    def test_owner_can_delete(self):
        headers, _ = self.auth_headers("alice")
        event = self.create_event(headers).json()
        res = self.client.delete(f"/events/{event['id']}", headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_non_owner_cannot_delete(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        res = self.client.delete(f"/events/{event['id']}", headers=headers_b)
        self.assertEqual(res.status_code, 404)


class JoinLeaveEventTestCase(ApiTestCase):
    def test_join_and_leave(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()

        res_join = self.client.post(f"/events/{event['id']}/join", headers=headers_b)
        self.assertEqual(res_join.status_code, 200)

        res_leave = self.client.delete(f"/events/{event['id']}/leave", headers=headers_b)
        self.assertEqual(res_leave.status_code, 200)

    def test_leave_without_joining_returns_404(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        res = self.client.delete(f"/events/{event['id']}/leave", headers=headers_b)
        self.assertEqual(res.status_code, 404)

    def test_join_nonexistent_event_returns_404(self):
        headers, _ = self.auth_headers("alice")
        res = self.client.post("/events/9999/join", headers=headers)
        self.assertEqual(res.status_code, 404)


class SearchEventsTestCase(ApiTestCase):
    def test_search_by_title(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="Python Meetup", category="IT")
        self.create_event(headers, title="Football", category="Спорт")

        res = self.client.get("/events/search/", params={"q": "Python"}, headers=headers)
        titles = [e["title"] for e in res.json()]
        self.assertIn("Python Meetup", titles)
        self.assertNotIn("Football", titles)

    def test_search_by_single_category(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="Python Meetup", category="IT")
        self.create_event(headers, title="Football", category="Спорт")

        res = self.client.get("/events/search/", params={"category": "Спорт"}, headers=headers)
        titles = [e["title"] for e in res.json()]
        self.assertEqual(titles, ["Football"])

    def test_search_without_category_filter_returns_all(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="A", category="IT")
        self.create_event(headers, title="B", category="Спорт")

        res = self.client.get("/events/search/", params={"category": ""}, headers=headers)
        self.assertEqual(len(res.json()), 2)

    def test_sort_by_name(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="Zeta", category="IT")
        self.create_event(headers, title="Alpha", category="IT")

        res = self.client.get("/events/search/", params={"sort_by": "name"}, headers=headers)
        titles = [e["title"] for e in res.json()]
        self.assertEqual(titles, ["Alpha", "Zeta"])

    def test_sort_by_date_is_default(self):
        headers, _ = self.auth_headers("alice")
        later = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        sooner = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        self.create_event(headers, title="Later", event_date=later)
        self.create_event(headers, title="Sooner", event_date=sooner)

        res = self.client.get("/events/search/", headers=headers)
        titles = [e["title"] for e in res.json()]
        self.assertEqual(titles, ["Sooner", "Later"])

    def test_search_works_without_authentication(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="Public Event", is_private=False)

        res = self.client.get("/events/search/")  # без токена
        self.assertEqual(res.status_code, 200)
        titles = [e["title"] for e in res.json()]
        self.assertIn("Public Event", titles)

    def test_private_event_hidden_from_others(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        self.create_event(headers_a, title="Secret", is_private=True)

        res_other = self.client.get("/events/search/", headers=headers_b)
        self.assertNotIn("Secret", [e["title"] for e in res_other.json()])

        res_owner = self.client.get("/events/search/", headers=headers_a)
        self.assertIn("Secret", [e["title"] for e in res_owner.json()])

    def test_private_event_hidden_from_anonymous(self):
        headers_a, _ = self.auth_headers("alice")
        self.create_event(headers_a, title="Secret", is_private=True)

        res = self.client.get("/events/search/")
        self.assertNotIn("Secret", [e["title"] for e in res.json()])


class MyEventsTestCase(ApiTestCase):
    def test_get_my_events_created_and_participated(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        self.client.post(f"/events/{event['id']}/join", headers=headers_b)

        res_a = self.client.get("/users/me/events/", headers=headers_a)
        self.assertEqual(len(res_a.json()["created"]), 1)
        self.assertEqual(len(res_a.json()["participated"]), 0)

        res_b = self.client.get("/users/me/events/", headers=headers_b)
        self.assertEqual(len(res_b.json()["created"]), 0)
        self.assertEqual(len(res_b.json()["participated"]), 1)

    def test_get_participating_events(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        self.client.post(f"/events/{event['id']}/join", headers=headers_b)

        res = self.client.get("/users/me/participating/", headers=headers_b)
        self.assertEqual(len(res.json()), 1)


class UserStatsTestCase(ApiTestCase):
    def test_stats_for_existing_user(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        event = self.create_event(headers_a).json()
        self.client.post(f"/events/{event['id']}/join", headers=headers_b)

        res = self.client.get("/users/alice/stats/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["created_events"], 1)

    def test_stats_for_missing_user_returns_404(self):
        res = self.client.get("/users/ghost/stats/")
        self.assertEqual(res.status_code, 404)


class RemindersTestCase(ApiTestCase):
    def test_reminder_within_next_hour_included(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        soon = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        event = self.create_event(headers_a, event_date=soon).json()
        self.client.post(f"/events/{event['id']}/join", headers=headers_b)

        res = self.client.get("/events/reminders/", headers=headers_b)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

    def test_reminder_far_in_future_excluded(self):
        headers_a, _ = self.auth_headers("alice")
        headers_b, _ = self.auth_headers("bob")
        far = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        event = self.create_event(headers_a, event_date=far).json()
        self.client.post(f"/events/{event['id']}/join", headers=headers_b)

        res = self.client.get("/events/reminders/", headers=headers_b)
        self.assertEqual(res.json(), [])


class SearchEventsCacheTestCase(ApiTestCase):
    def test_search_result_is_cached(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers, title="Cached Event")

        from backend.app import cache
        version_before = cache.get_version("events")

        self.client.get("/events/search/", headers=headers)

        keys = self.fake_redis.keys(f"events:search:v{version_before}:*")
        self.assertTrue(keys, "ожидался хотя бы один ключ кэша после поиска")

    def test_creating_event_invalidates_search_cache(self):
        headers, _ = self.auth_headers("alice")
        from backend.app import cache

        self.client.get("/events/search/", headers=headers)
        version_before = cache.get_version("events")

        self.create_event(headers, title="New Event")
        version_after = cache.get_version("events")

        self.assertEqual(version_after, version_before + 1)

    def test_search_reflects_new_event_after_cache_invalidation(self):
        headers, _ = self.auth_headers("alice")
        self.client.get("/events/search/", headers=headers)  # прогреваем кэш пустым результатом

        self.create_event(headers, title="Fresh Event")
        res = self.client.get("/events/search/", headers=headers)
        titles = [e["title"] for e in res.json()]
        self.assertIn("Fresh Event", titles)


class UserStatsCacheTestCase(ApiTestCase):
    def test_stats_are_cached_until_new_event(self):
        headers, _ = self.auth_headers("alice")
        self.client.get("/users/alice/stats/")

        from backend.app import cache
        version_before = cache.get_version("stats")

        self.create_event(headers)
        version_after = cache.get_version("stats")

        self.assertEqual(version_after, version_before + 1)

    def test_stats_reflect_new_event_after_invalidation(self):
        headers, _ = self.auth_headers("alice")
        self.create_event(headers)

        res = self.client.get("/users/alice/stats/")
        self.assertEqual(res.json()["created_events"], 1)


if __name__ == "__main__":
    import unittest
    unittest.main()
