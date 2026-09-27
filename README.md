# time-zone-database

Offline access to a curated subset of the IANA time zone identifiers and their metadata, with no third-party dependencies.

```python
from time_zone_database import TimeZoneDatabase

db = TimeZoneDatabase()

london = db.get("Europe/London")
print(london.utc_offset)   # 0
print(london.region)       # "Europe"

resolved = db.resolve("US/Eastern")
print(resolved.name)       # "America/New_York"

for name in db.list_by_region("America"):
    print(name)

print(db.zones_for_country("us"))   # case-insensitive input
```

## Why this exists

The standard library's `zoneinfo` resolves zone names to OS-provided data, but it gives you no structured metadata: no region grouping, no country codes, no alias relationships, and no way to enumerate zones without scraping files. This library fills that gap with a small, embedded dataset so the same code runs identically on Linux, Windows, and a sandboxed container with no tzdata installed.

The trade-off is currency: the bundled data is a fixed snapshot. If you need DST rules for historical years, use `zoneinfo` or `tzdata`. This library carries only the *current standard* offset per zone, not the full transition history, because maintaining transition tables offline would balloon the package and still go stale.

## Edge cases you will hit

- **`Factory`** is a real IANA zone with no fixed offset. Its `utc_offset` is `None`, not `0`. `offset_minutes("Factory")` also returns `None`; if you need to distinguish "unknown zone" from "no fixed offset", call `get()` and inspect the object.
- **Deprecated aliases** (`US/Eastern`, `GMT`, `UTC`, `Asia/Calcutta`, ...) are resolvable via `get` and `resolve` but excluded from `list_zones()` unless you pass `include_deprecated=True`.
- **Dangling aliases**: `Brazil/DeNoronha` points at `America/Noronha`, which this subset does not include. `resolve()` returns the alias entry itself in that case rather than `None`, so you always get the best information available.
- **Matching is case-sensitive.** IANA names are case-significant; `db.get("europe/london")` returns `None` by design.
- **Regions follow the IANA directory layout.** `America/Argentina/Buenos_Aires` is in region `America`; there is no `America/Argentina` region. `list_by_region("America")` returns nested zones.

## Exported names

- `TimeZoneDatabase` — the lookup class.
- `TimeZone` — the value object returned by `get()` and `resolve()`.

`TimeZoneDatabase` methods: `get`, `resolve`, `list_zones`, `list_by_region`, `regions`, `zones_for_country`, `offset_minutes`, plus `__len__` and `__contains__`.
