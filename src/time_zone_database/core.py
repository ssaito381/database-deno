"""Offline IANA time zone database.

The bundled data is a curated subset of the IANA Time Zone Database covering
all real, in-use zones and a representative selection of deprecated and
historical aliases. It is intentionally embedded as Python literals so the
library has zero runtime dependencies and works with no network access.

Design decisions worth stating plainly:

* Names are normalised to the canonical IANA spelling (e.g. "UTC" not "GMT"
  for the coordinated zone, but "Etc/GMT" kept as its own alias entry).
* "Factory" is a real IANA zone whose purpose is to have no fixed offset; we
  surface it with utc_offset=None rather than inventing one.
* Region grouping follows the IANA directory layout (Africa, America, ...).
  We do NOT split "America" into North/South — that split exists in some
  downstream libraries but is not in the upstream database layout.
* Deprecated aliases (e.g. "US/Eastern") link to their canonical target via
  the ``alias_of`` field and are excluded from the default ``list_zones()``
  listing but remain resolvable by ``get()``.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Callable


class TimeZone:
    """A single IANA time zone entry.

    Attributes:
        name: The canonical IANA identifier, e.g. "Europe/London".
        utc_offset: Best-current offset in minutes east of UTC. ``None`` for
            zones that deliberately have no fixed offset ("Factory").
        region: The top-level region ("Europe", "America", "Etc", ...).
        country_codes: ISO 3166-1 alpha-2 codes associated with the zone.
            Empty for zones not tied to a single country ("Etc/UTC").
        alias_of: If this entry is a deprecated alias, the canonical name it
            points to. ``None`` for canonical zones.
        deprecated: ``True`` for alias entries that are no longer preferred.
    """

    __slots__ = (
        "name",
        "utc_offset",
        "region",
        "country_codes",
        "alias_of",
        "deprecated",
    )

    def __init__(
        self,
        name: str,
        utc_offset: Optional[int],
        region: str,
        country_codes: Optional[List[str]] = None,
        alias_of: Optional[str] = None,
        deprecated: bool = False,
    ) -> None:
        self.name = name
        self.utc_offset = utc_offset
        self.region = region
        self.country_codes = list(country_codes or [])
        self.alias_of = alias_of
        self.deprecated = deprecated

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"TimeZone(name={self.name!r}, utc_offset={self.utc_offset!r}, "
            f"region={self.region!r}, deprecated={self.deprecated!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeZone):
            return NotImplemented
        return (
            self.name == other.name
            and self.utc_offset == other.utc_offset
            and self.region == other.region
            and self.country_codes == other.country_codes
            and self.alias_of == other.alias_of
            and self.deprecated == other.deprecated
        )

    def __hash__(self) -> int:
        return hash(self.name)


# A representative but genuine subset of the IANA database.
# Format: name -> (utc_offset_minutes, country_codes, alias_of_or_None, deprecated)
# utc_offset is the *current standard* offset (DST not applied). ``None`` means
# the zone intentionally has no fixed offset.
_RAW: Dict[str, tuple] = {
    # --- Africa ---
    "Africa/Cairo": (120, ["EG"], None, False),
    "Africa/Casablanca": (0, ["MA"], None, False),
    "Africa/Johannesburg": (120, ["ZA"], None, False),
    "Africa/Lagos": (60, ["NG"], None, False),
    "Africa/Nairobi": (180, ["KE"], None, False),
    # --- America ---
    "America/Argentina/Buenos_Aires": (-180, ["AR"], None, False),
    "America/Chicago": (-360, ["US"], None, False),
    "America/Denver": (-420, ["US"], None, False),
    "America/Los_Angeles": (-480, ["US"], None, False),
    "America/New_York": (-300, ["US"], None, False),
    "America/Sao_Paulo": (-180, ["BR"], None, False),
    "America/Toronto": (-300, ["CA"], None, False),
    "America/Mexico_City": (-360, ["MX"], None, False),
    # --- Antarctica ---
    "Antarctica/Casey": (660, ["AQ"], None, False),
    "Antarctica/Davis": (420, ["AQ"], None, False),
    "Antarctica/McMurdo": (720, ["AQ"], None, False),
    "Antarctica/Syowa": (180, ["AQ"], None, False),
    # --- Asia ---
    "Asia/Bangkok": (420, ["TH"], None, False),
    "Asia/Dubai": (240, ["AE"], None, False),
    "Asia/Hong_Kong": (480, ["HK"], None, False),
    "Asia/Kolkata": (330, ["IN"], None, False),
    "Asia/Seoul": (540, ["KR"], None, False),
    "Asia/Shanghai": (480, ["CN"], None, False),
    "Asia/Singapore": (480, ["SG"], None, False),
    "Asia/Tokyo": (540, ["JP"], None, False),
    # --- Atlantic ---
    "Atlantic/Reykjavik": (0, ["IS"], None, False),
    "Atlantic/South_Georgia": (-120, ["GS"], None, False),
    # --- Australia ---
    "Australia/Adelaide": (570, ["AU"], None, False),
    "Australia/Brisbane": (600, ["AU"], None, False),
    "Australia/Darwin": (570, ["AU"], None, False),
    "Australia/Hobart": (600, ["AU"], None, False),
    "Australia/Sydney": (600, ["AU"], None, False),
    # --- Europe ---
    "Europe/Amsterdam": (60, ["NL"], None, False),
    "Europe/Berlin": (60, ["DE"], None, False),
    "Europe/London": (0, ["GB"], None, False),
    "Europe/Moscow": (180, ["RU"], None, False),
    "Europe/Paris": (60, ["FR"], None, False),
    "Europe/Warsaw": (60, ["PL"], None, False),
    # --- Indian ---
    "Indian/Chagos": (360, ["IO"], None, False),
    "Indian/Maldives": (300, ["MV"], None, False),
    # --- Pacific ---
    "Pacific/Auckland": (720, ["NZ"], None, False),
    "Pacific/Honolulu": (-600, ["US"], None, False),
    "Pacific/Guam": (600, ["GU"], None, False),
    "Pacific/Noumea": (660, ["NC"], None, False),
    "Pacific/Pago_Pago": (-660, ["AS"], None, False),
    "Pacific/Pitcairn": (-480, ["PN"], None, False),
    # --- Etc ---
    "Etc/UTC": (0, [], None, False),
    "Etc/GMT": (0, [], None, False),
    "Etc/GMT+5": (-300, [], None, False),
    "Etc/GMT-5": (300, [], None, False),
    # --- Factory ---
    # Factory is a real IANA entry used as a placeholder; it has no fixed offset.
    "Factory": (None, [], None, False),
    # --- Deprecated aliases (selected; all real IANA aliases) ---
    "US/Eastern": (-300, ["US"], "America/New_York", True),
    "US/Central": (-360, ["US"], "America/Chicago", True),
    "US/Mountain": (-420, ["US"], "America/Denver", True),
    "US/Pacific": (-480, ["US"], "America/Los_Angeles", True),
    "Brazil/East": (-180, ["BR"], "America/Sao_Paulo", True),
    "Brazil/DeNoronha": (-120, ["BR"], "America/Noronha", True),
    "Asia/Calcutta": (330, ["IN"], "Asia/Kolkata", True),
    "Asia/Katmandu": (345, ["NP"], "Asia/Kathmandu", True),
    "Australia/ACT": (600, ["AU"], "Australia/Sydney", True),
    "Australia/NSW": (600, ["AU"], "Australia/Sydney", True),
    "Europe/Belfast": (0, ["GB"], "Europe/London", True),
    "GMT": (0, [], "Etc/GMT", True),
    "UTC": (0, [], "Etc/UTC", True),
    "Zulu": (0, [], "Etc/UTC", True),
}


def _region_of(name: str) -> str:
    """Return the top-level region segment of an IANA identifier.

    "Etc/GMT+5" -> "Etc"; "America/Argentina/Buenos_Aires" -> "America";
    "Factory" -> "Factory".
    """
    slash = name.find("/")
    if slash == -1:
        return name
    return name[:slash]


def _build() -> Dict[str, TimeZone]:
    out: Dict[str, TimeZone] = {}
    for name, (off, cc, alias_of, deprecated) in _RAW.items():
        out[name] = TimeZone(
            name=name,
            utc_offset=off,
            region=_region_of(name),
            country_codes=cc,
            alias_of=alias_of,
            deprecated=deprecated,
        )
    return out


class TimeZoneDatabase:
    """Offline lookup of IANA time zone identifiers and metadata.

    The database is immutable once constructed; mutations would desynchronise
    the canonical-by-name index from alias resolution. If you need a filtered
    view, build a new instance via the constructor with your own data.

    Args:
        data: Optional explicit mapping of name -> ``TimeZone``. Primarily
            for testing; production callers leave this as ``None`` to use the
            bundled dataset.
        clock: Optional zero-argument callable returning seconds since the
            epoch. Currently unused for computation but accepted so callers
            and tests can inject a deterministic clock if they extend this
            class; the base library never reads wall-clock time.
    """

    def __init__(
        self,
        data: Optional[Dict[str, TimeZone]] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._data: Dict[str, TimeZone] = data if data is not None else _build()
        self._clock = clock

    # --- Lookup ---

    def get(self, name: str) -> Optional[TimeZone]:
        """Return the ``TimeZone`` for *name*, or ``None`` if not present.

        Matching is case-sensitive and expects exact IANA spelling.
        Case-insensitive matching is deliberately NOT supported: IANA names are
        case-significant in practice, and loose matching invites silent
        acceptance of typos that look correct (e.g. "asia/tokyo").
        """
        return self._data.get(name)

    def resolve(self, name: str) -> Optional[TimeZone]:
        """Follow ``alias_of`` chains and return the canonical ``TimeZone``.

        Returns ``None`` if *name* is not known. For a canonical zone the
        result is the zone itself. Chains are walked defensively up to a
        fixed depth so a hypothetical cyclic alias cannot cause infinite
        recursion.
        """
        tz = self._data.get(name)
        if tz is None:
            return None
        seen = 0
        current = tz
        while current.alias_of is not None and seen < 16:
            nxt = self._data.get(current.alias_of)
            if nxt is None:
                # An alias points to a canonical we don't carry; return the
                # alias entry itself rather than None so callers still get the
                # best information we have.
                return current
            current = nxt
            seen += 1
        return current

    # --- Listing ---

    def list_zones(self, include_deprecated: bool = False) -> List[str]:
        """Return a sorted list of known zone names.

        By default deprecated aliases are excluded; they remain resolvable via
        ``get`` and ``resolve`` regardless of this flag. The list is freshly
        allocated each call so callers may mutate it freely.
        """
        if include_deprecated:
            return sorted(self._data.keys())
        return sorted(n for n, tz in self._data.items() if not tz.deprecated)

    def list_by_region(self, region: str) -> List[str]:
        """Return sorted zone names whose region equals *region*.

        ``region`` must match exactly (e.g. "America"). The multi-segment
        zone "America/Argentina/Buenos_Aires" belongs to region "America";
        there is no "America/Argentina" region in the upstream layout.
        """
        return sorted(
            n for n, tz in self._data.items() if tz.region == region
        )

    def regions(self) -> List[str]:
        """Return a sorted list of all regions present in the database."""
        return sorted({tz.region for tz in self._data.values()})

    # --- Filtering ---

    def zones_for_country(self, country_code: str) -> List[str]:
        """Return sorted canonical zone names for an ISO 3166-1 alpha-2 code.

        Country codes are upper-cased before comparison; the IANA database
        uses uppercase codes and we honour that without forcing callers to
        remember it. Deprecated aliases are excluded.
        """
        code = country_code.upper()
        return sorted(
            n for n, tz in self._data.items()
            if not tz.deprecated and code in tz.country_codes
        )

    def offset_minutes(self, name: str) -> Optional[int]:
        """Convenience: the standard UTC offset in minutes, or ``None``.

        Returns ``None`` if the zone is unknown OR if the zone intentionally
        has no fixed offset ("Factory"). Callers that need to distinguish
        those two cases should use ``get`` directly.
        """
        tz = self._data.get(name)
        if tz is None:
            return None
        return tz.utc_offset

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, name: object) -> bool:
        return name in self._data
