import unittest

from time_zone_database import TimeZoneDatabase, TimeZone


class TimeZoneDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = TimeZoneDatabase()

    # --- get ---

    def test_get_canonical_zone(self):
        tz = self.db.get("Europe/London")
        self.assertIsNotNone(tz)
        self.assertEqual(tz.name, "Europe/London")
        self.assertEqual(tz.utc_offset, 0)
        self.assertEqual(tz.region, "Europe")
        self.assertFalse(tz.deprecated)
        self.assertIsNone(tz.alias_of)

    def test_get_unknown_returns_none(self):
        self.assertIsNone(self.db.get("Mars/Olympus"))

    def test_get_is_case_sensitive(self):
        # IANA names are case-significant; loose matching is intentionally
        # not offered.
        self.assertIsNone(self.db.get("europe/london"))
        self.assertIsNone(self.db.get("EUROPE/LONDON"))

    def test_get_factory_has_no_fixed_offset(self):
        tz = self.db.get("Factory")
        self.assertIsNotNone(tz)
        self.assertIsNone(tz.utc_offset)

    # --- resolve ---

    def test_resolve_alias_to_canonical(self):
        resolved = self.db.resolve("US/Eastern")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.name, "America/New_York")
        self.assertFalse(resolved.deprecated)

    def test_resolve_canonical_returns_self(self):
        resolved = self.db.resolve("Asia/Tokyo")
        self.assertEqual(resolved.name, "Asia/Tokyo")

    def test_resolve_unknown_returns_none(self):
        self.assertIsNone(self.db.resolve("Pluto/Charon"))

    def test_resolve_multi_step_alias(self):
        # "GMT" -> "Etc/GMT" (canonical); single hop in our data.
        resolved = self.db.resolve("GMT")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.name, "Etc/GMT")

    def test_resolve_dangling_alias_returns_alias_entry(self):
        # "Brazil/DeNoronha" aliases "America/Noronha", which we do NOT
        # carry. resolve should fall back to the alias entry rather than None.
        resolved = self.db.resolve("Brazil/DeNoronha")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.name, "Brazil/DeNoronha")
        self.assertTrue(resolved.deprecated)

    # --- list_zones ---

    def test_list_zones_excludes_deprecated_by_default(self):
        names = self.db.list_zones()
        self.assertNotIn("US/Eastern", names)
        self.assertNotIn("GMT", names)
        self.assertIn("America/New_York", names)

    def test_list_zones_includes_deprecated_when_asked(self):
        names = self.db.list_zones(include_deprecated=True)
        self.assertIn("US/Eastern", names)
        self.assertIn("America/New_York", names)

    def test_list_zones_is_sorted(self):
        names = self.db.list_zones(include_deprecated=True)
        self.assertEqual(names, sorted(names))

    def test_list_zones_returns_new_list(self):
        a = self.db.list_zones()
        b = self.db.list_zones()
        self.assertIsNot(a, b)
        a.append("zzz")
        self.assertNotIn("zzz", self.db.list_zones())

    # --- regions / list_by_region ---

    def test_regions_sorted_and_unique(self):
        regions = self.db.regions()
        self.assertEqual(regions, sorted(regions))
        self.assertEqual(len(regions), len(set(regions)))
        self.assertIn("America", regions)
        self.assertIn("Etc", regions)
        self.assertIn("Factory", regions)

    def test_list_by_region_america_includes_nested_segments(self):
        names = self.db.list_by_region("America")
        self.assertIn("America/Argentina/Buenos_Aires", names)
        self.assertIn("America/New_York", names)
        self.assertNotIn("Europe/London", names)

    def test_list_by_region_unknown_returns_empty(self):
        self.assertEqual(self.db.list_by_region("Atlantis"), [])

    # --- zones_for_country ---

    def test_zones_for_country_case_insensitive_input(self):
        upper = self.db.zones_for_country("US")
        lower = self.db.zones_for_country("us")
        self.assertEqual(upper, lower)
        self.assertIn("America/New_York", upper)
        self.assertIn("America/Chicago", upper)
        self.assertIn("America/Denver", upper)
        self.assertIn("America/Los_Angeles", upper)
        self.assertIn("Pacific/Honolulu", upper)

    def test_zones_for_country_excludes_deprecated(self):
        us = self.db.zones_for_country("US")
        self.assertNotIn("US/Eastern", us)
        self.assertNotIn("US/Pacific", us)

    def test_zones_for_country_unknown_returns_empty(self):
        self.assertEqual(self.db.zones_for_country("ZZ"), [])

    # --- offset_minutes ---

    def test_offset_minutes_known(self):
        self.assertEqual(self.db.offset_minutes("Asia/Kolkata"), 330)
        self.assertEqual(self.db.offset_minutes("Pacific/Honolulu"), -600)
        self.assertEqual(self.db.offset_minutes("Etc/GMT+5"), -300)
        self.assertEqual(self.db.offset_minutes("Etc/GMT-5"), 300)

    def test_offset_minutes_unknown_is_none(self):
        self.assertIsNone(self.db.offset_minutes(" nowhere/nowhere"))

    def test_offset_minutes_factory_is_none(self):
        self.assertIsNone(self.db.offset_minutes("Factory"))

    # --- dunder ---

    def test_contains(self):
        self.assertIn("Europe/London", self.db)
        self.assertNotIn("Europe/Atlantis", self.db)

    def test_len_matches_total_entries(self):
        self.assertGreater(len(self.db), 0)
        self.assertEqual(len(self.db), len(self.db.list_zones(include_deprecated=True)))

    # --- TimeZone value object ---

    def test_timezone_equality_and_hash(self):
        a = TimeZone("X/Y", 60, "X", ["ZZ"])
        b = TimeZone("X/Y", 60, "X", ["ZZ"])
        c = TimeZone("X/Y", 120, "X", ["ZZ"])
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(hash(a), hash(b))

    def test_timezone_country_codes_copied(self):
        cc = ["US"]
        tz = TimeZone("X/Y", 0, "X", cc)
        cc.append("CA")
        self.assertEqual(tz.country_codes, ["US"])

    def test_timezone_eq_with_non_timezone(self):
        tz = TimeZone("X/Y", 0, "X")
        self.assertNotEqual(tz, "X/Y")
        self.assertNotEqual(tz, 42)

    # --- custom data injection (constructor supported path) ---

    def test_custom_data_used(self):
        custom = TimeZone("Custom/Zone", 99, "Custom", ["ZZ"])
        db = TimeZoneDatabase(data={"Custom/Zone": custom})
        self.assertIs(db.get("Custom/Zone"), custom)
        self.assertEqual(len(db), 1)
        self.assertEqual(db.regions(), ["Custom"])

    def test_clock_argument_accepted(self):
        # The base library does not read the clock, but the constructor must
        # accept it so extensions/subclasses can stay deterministic.
        ticks = []
        def fake_clock():
            ticks.append(1)
            return 0.0
        db = TimeZoneDatabase(clock=fake_clock)
        self.assertIsNone(db.get("Missing/Zone"))
        # The base implementation never calls the clock.
        self.assertEqual(ticks, [])


if __name__ == "__main__":
    unittest.main()
