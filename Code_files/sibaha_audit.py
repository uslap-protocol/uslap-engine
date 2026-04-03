#!/usr/bin/env python3
"""
sibaha_audit.py — Self-audit for sun/moon position calculations.

Recalculates solar position from first principles for all 4 cities,
flags any anomalies in azimuth/altitude, and produces corrected data.

Solar position algorithm: NOAA Solar Calculator
(based on Jean Meeus, "Astronomical Algorithms")
"""

import math
import json
import sys
from datetime import datetime, timedelta

# ─── Cities ───────────────────────────────────────────────────────
CITIES = {
    'Berlin':        {'lat': 52.52,  'lon': 13.405,  'tz': 1,  'color': '#ffa500'},
    'Makkah-Madinah':{'lat': 21.4225,'lon': 39.8262, 'tz': 3,  'color': '#ffd700'},
    'Delhi':         {'lat': 28.6139,'lon': 77.209,  'tz': 5.5,'color': '#44ff88'},
    'Sydney':        {'lat':-33.8688,'lon': 151.2093,'tz': 10, 'color': '#44aaff'},
}

# ─── Core solar position (NOAA / Meeus) ──────────────────────────
def julian_day(year, month, day, hour=12):
    """Julian Day Number from calendar date."""
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour/24.0 + B - 1524.5
    return JD

def julian_century(jd):
    return (jd - 2451545.0) / 36525.0

def sun_geometric_mean_longitude(T):
    """Degrees"""
    L0 = 280.46646 + T * (36000.76983 + 0.0003032 * T)
    return L0 % 360

def sun_geometric_mean_anomaly(T):
    """Degrees"""
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    return M

def earth_orbit_eccentricity(T):
    return 0.016708634 - T * (0.000042037 + 0.0000001267 * T)

def sun_equation_of_center(T):
    """Degrees"""
    M = math.radians(sun_geometric_mean_anomaly(T))
    C = (math.sin(M) * (1.914602 - T * (0.004817 + 0.000014 * T))
       + math.sin(2*M) * (0.019993 - 0.000101 * T)
       + math.sin(3*M) * 0.000289)
    return C

def sun_true_longitude(T):
    return sun_geometric_mean_longitude(T) + sun_equation_of_center(T)

def sun_apparent_longitude(T):
    O = sun_true_longitude(T)
    omega = 125.04 - 1934.136 * T
    return O - 0.00569 - 0.00478 * math.sin(math.radians(omega))

def mean_obliquity_ecliptic(T):
    """Degrees"""
    seconds = 21.448 - T * (46.8150 + T * (0.00059 - T * 0.001813))
    return 23 + (26 + seconds / 60) / 60

def obliquity_correction(T):
    e0 = mean_obliquity_ecliptic(T)
    omega = 125.04 - 1934.136 * T
    return e0 + 0.00256 * math.cos(math.radians(omega))

def sun_declination(T):
    """Degrees"""
    e = math.radians(obliquity_correction(T))
    lam = math.radians(sun_apparent_longitude(T))
    return math.degrees(math.asin(math.sin(e) * math.sin(lam)))

def equation_of_time(T):
    """Minutes"""
    e = obliquity_correction(T)
    L0 = sun_geometric_mean_longitude(T)
    ecc = earth_orbit_eccentricity(T)
    M = sun_geometric_mean_anomaly(T)

    y = math.tan(math.radians(e) / 2) ** 2

    L0r = math.radians(L0)
    Mr = math.radians(M)

    EqT = (y * math.sin(2*L0r)
         - 2 * ecc * math.sin(Mr)
         + 4 * ecc * y * math.sin(Mr) * math.cos(2*L0r)
         - 0.5 * y * y * math.sin(4*L0r)
         - 1.25 * ecc * ecc * math.sin(2*Mr))

    return math.degrees(EqT) * 4  # convert to minutes

def solar_noon_minutes(lon, tz, eqt):
    """Minutes from midnight (local time) of solar noon."""
    return 720 - 4 * lon - eqt + tz * 60

def sun_position(lat, lon, tz, year, month, day, hour_local):
    """
    Returns (altitude_deg, azimuth_deg) for given location and time.
    Azimuth: 0=N, 90=E, 180=S, 270=W
    """
    # Julian day for the requested hour (convert local to UT)
    ut_hour = hour_local - tz
    jd = julian_day(year, month, day, ut_hour)
    T = julian_century(jd)

    decl = sun_declination(T)
    eqt = equation_of_time(T)

    # True solar time in minutes
    true_solar_time = (hour_local * 60 + eqt + 4 * lon - 60 * tz) % 1440

    # Hour angle
    if true_solar_time / 4 < 0:
        ha = true_solar_time / 4 + 180
    else:
        ha = true_solar_time / 4 - 180

    lat_r = math.radians(lat)
    decl_r = math.radians(decl)
    ha_r = math.radians(ha)

    # Solar zenith angle
    cos_zenith = (math.sin(lat_r) * math.sin(decl_r) +
                  math.cos(lat_r) * math.cos(decl_r) * math.cos(ha_r))
    cos_zenith = max(-1, min(1, cos_zenith))
    zenith = math.acos(cos_zenith)
    altitude = 90 - math.degrees(zenith)

    # Solar azimuth
    zenith_deg = math.degrees(zenith)
    if zenith_deg > 0.001:
        cos_az = (math.sin(decl_r) - math.sin(lat_r) * cos_zenith) / (math.cos(lat_r) * math.sin(zenith))
        cos_az = max(-1, min(1, cos_az))
        azimuth = math.degrees(math.acos(cos_az))
        if ha > 0:
            azimuth = 360 - azimuth
    else:
        # Sun essentially at zenith — azimuth is undefined
        azimuth = float('nan')

    return altitude, azimuth, decl

def zuhr_time(lat, lon, tz, year, month, day):
    """
    Solar noon (Zuhr) — the moment the sun crosses the meridian.
    Returns fractional hours (local time).
    """
    jd = julian_day(year, month, day, 12)
    T = julian_century(jd)
    eqt = equation_of_time(T)
    noon_min = solar_noon_minutes(lon, tz, eqt)
    return noon_min / 60.0


# ─── Moon position (simplified) ──────────────────────────────────
def moon_position(lat, lon, tz, year, month, day, hour_local):
    """
    Simplified lunar position. Good to ~1° for visualization.
    Returns (altitude_deg, azimuth_deg, phase_fraction).
    """
    ut_hour = hour_local - tz
    jd = julian_day(year, month, day, ut_hour)
    T = julian_century(jd)

    # Moon's mean elements (Meeus ch.47 simplified)
    Lp = (218.3165 + 481267.8813 * T) % 360  # mean longitude
    D  = (297.8502 + 445267.1115 * T) % 360  # mean elongation
    M  = (357.5291 + 35999.0503 * T)  % 360  # sun mean anomaly
    Mp = (134.9634 + 477198.8676 * T) % 360  # moon mean anomaly
    F  = (93.2720 + 483202.0175 * T)  % 360  # argument of latitude

    Dr, Mr, Mpr, Fr = [math.radians(x) for x in [D, M, Mp, F]]

    # Ecliptic longitude (truncated series — main terms)
    lon_moon = Lp + (6.289 * math.sin(Mpr)
                   - 1.274 * math.sin(2*Dr - Mpr)
                   + 0.658 * math.sin(2*Dr)
                   - 0.214 * math.sin(2*Mpr)
                   - 0.186 * math.sin(Mr)
                   - 0.114 * math.sin(2*Fr))

    # Ecliptic latitude
    lat_moon = (5.128 * math.sin(Fr)
              + 0.281 * math.sin(Mpr + Fr)
              - 0.278 * math.sin(Mpr - Fr)
              - 0.173 * math.sin(2*Dr - Fr))

    # Distance (km)
    dist = 385001 - 20905 * math.cos(Mpr)

    # Ecliptic to equatorial
    obliq = math.radians(obliquity_correction(T))
    lon_r = math.radians(lon_moon)
    lat_r_moon = math.radians(lat_moon)

    ra = math.atan2(
        math.sin(lon_r) * math.cos(obliq) - math.tan(lat_r_moon) * math.sin(obliq),
        math.cos(lon_r))
    decl = math.asin(
        math.sin(lat_r_moon) * math.cos(obliq) +
        math.cos(lat_r_moon) * math.sin(obliq) * math.sin(lon_r))

    # Hour angle
    # Greenwich sidereal time
    GMST = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    LST = math.radians(GMST + lon)
    HA = LST - ra

    # Alt/az
    lat_r = math.radians(lat)
    sin_alt = math.sin(lat_r)*math.sin(decl) + math.cos(lat_r)*math.cos(decl)*math.cos(HA)
    sin_alt = max(-1, min(1, sin_alt))
    alt = math.asin(sin_alt)

    cos_az = (math.sin(decl) - math.sin(lat_r)*sin_alt) / (math.cos(lat_r)*math.cos(alt)+1e-10)
    cos_az = max(-1, min(1, cos_az))
    az = math.acos(cos_az)
    if math.sin(HA) > 0:
        az = 2*math.pi - az

    # Phase (illumination fraction)
    # Phase angle = elongation
    sun_lon = math.radians(sun_apparent_longitude(T))
    elong = math.acos(max(-1, min(1,
        math.cos(lat_r_moon) * math.cos(lon_r - sun_lon))))
    phase = (1 - math.cos(elong)) / 2

    return math.degrees(alt), math.degrees(az), phase


# ─── AUDIT ────────────────────────────────────────────────────────
def audit_city(name, city, year=2025):
    """Compute Zuhr sun position for every day of the year. Return stats + data."""
    results = []
    alt_min, alt_max = 999, -999
    az_min, az_max = 999, -999
    overhead_days = 0
    nan_az_days = 0

    dt = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)

    while dt < end:
        y, m, d = dt.year, dt.month, dt.day
        noon_h = zuhr_time(city['lat'], city['lon'], city['tz'], y, m, d)
        alt, az, decl = sun_position(city['lat'], city['lon'], city['tz'], y, m, d, noon_h)

        is_overhead = alt > 88
        if is_overhead:
            overhead_days += 1
        if math.isnan(az):
            nan_az_days += 1

        results.append({
            'date': dt.strftime('%Y-%m-%d'),
            'doy': (dt - datetime(year, 1, 1)).days + 1,
            'noon_h': round(noon_h, 4),
            'alt': round(alt, 2),
            'az': round(az, 2) if not math.isnan(az) else None,
            'decl': round(decl, 2),
            'overhead': is_overhead
        })

        if alt < alt_min: alt_min = alt
        if alt > alt_max: alt_max = alt
        if not math.isnan(az):
            if az < az_min: az_min = az
            if az > az_max: az_max = az

        dt += timedelta(days=1)

    return {
        'name': name,
        'lat': city['lat'],
        'lon': city['lon'],
        'tz': city['tz'],
        'year': year,
        'days': len(results),
        'alt_range': [round(alt_min, 1), round(alt_max, 1)],
        'az_range': [round(az_min, 1), round(az_max, 1)] if az_min < 998 else [None, None],
        'overhead_days': overhead_days,
        'nan_az_days': nan_az_days,
        'data': results
    }


def audit_makkah_detail(city, year=2025):
    """Detailed Makkah audit — check azimuth behavior around overhead days."""
    print("\n═══ MAKKAH OVERHEAD ANALYSIS ═══")
    dt = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)

    overhead_periods = []
    in_overhead = False

    while dt < end:
        y, m, d = dt.year, dt.month, dt.day
        noon_h = zuhr_time(city['lat'], city['lon'], city['tz'], y, m, d)
        alt, az, decl = sun_position(city['lat'], city['lon'], city['tz'], y, m, d, noon_h)

        if alt > 85:
            if not in_overhead:
                in_overhead = True
                start_date = dt
            end_date = dt
            marker = "  *** OVERHEAD" if alt > 88 else "  * NEAR-OVERHEAD"
            az_str = f"{az:.1f}" if not math.isnan(az) else "NaN"
            print(f"  {dt.strftime('%m-%d')} | alt={alt:.2f}° | az={az_str}° | decl={decl:.2f}°{marker}")
        else:
            if in_overhead:
                in_overhead = False
                overhead_periods.append((start_date, end_date))

        dt += timedelta(days=1)

    if in_overhead:
        overhead_periods.append((start_date, end_date))

    print(f"\n  Overhead periods (alt>85°): {len(overhead_periods)}")
    for s, e in overhead_periods:
        days = (e - s).days + 1
        print(f"    {s.strftime('%b %d')} — {e.strftime('%b %d')} ({days} days)")


def audit_sydney_detail(city, year=2025):
    """Check Sydney azimuth — sun should transit NORTH."""
    print("\n═══ SYDNEY HEMISPHERE CHECK ═══")

    # Sample solstices + equinoxes
    test_dates = [
        (2025, 1, 15, "Mid-summer (Jan)"),
        (2025, 3, 20, "Equinox (Mar)"),
        (2025, 6, 21, "Mid-winter (Jun)"),
        (2025, 9, 23, "Equinox (Sep)"),
        (2025, 12, 21, "Mid-summer (Dec)"),
    ]

    for y, m, d, label in test_dates:
        noon_h = zuhr_time(city['lat'], city['lon'], city['tz'], y, m, d)
        alt, az, decl = sun_position(city['lat'], city['lon'], city['tz'], y, m, d, noon_h)
        az_str = f"{az:.1f}" if not math.isnan(az) else "NaN"
        direction = "NORTH" if (az < 90 or az > 270) else "SOUTH"
        correct = "✓" if direction == "NORTH" else "✗ WRONG — should be NORTH"
        print(f"  {label:25s} | alt={alt:.1f}° | az={az_str}° | transit={direction} {correct}")


def compare_with_reference():
    """Compare our algorithm with known reference values."""
    print("\n═══ REFERENCE COMPARISON ═══")
    print("  Using NOAA Solar Calculator reference values for 2025-06-21 12:00 UTC")

    # NOAA reference for 2025-06-21 12:00 UTC, Berlin
    # Declination should be ~23.44° (near solstice)
    jd = julian_day(2025, 6, 21, 12)
    T = julian_century(jd)
    decl = sun_declination(T)
    eqt = equation_of_time(T)
    print(f"  Summer solstice 2025-06-21 12:00 UT:")
    print(f"    Declination: {decl:.4f}° (expected ~23.44°)")
    print(f"    EqT: {eqt:.2f} min")

    # Berlin noon
    alt, az, _ = sun_position(52.52, 13.405, 1, 2025, 6, 21, 13.2)
    print(f"    Berlin ~13:12 CEST: alt={alt:.2f}° az={az:.2f}°")
    print(f"      Expected alt ≈ {90-52.52+23.44:.1f}° (= 90-lat+decl)")

    # Makkah noon
    alt, az, _ = sun_position(21.4225, 39.8262, 3, 2025, 6, 21, 12.3)
    print(f"    Makkah ~12:18 AST: alt={alt:.2f}° az={az:.2f}°")
    print(f"      Expected alt ≈ {90-abs(21.4225-23.44):.1f}° (sun nearly overhead)")


def main():
    print("=" * 70)
    print("  سِبَاحَة الشَّمْسِ — SOLAR POSITION AUDIT")
    print("=" * 70)

    all_data = {}

    for name, city in CITIES.items():
        print(f"\n{'─'*50}")
        print(f"  {name} ({city['lat']}°{'N' if city['lat']>=0 else 'S'}, {city['lon']}°E, UTC+{city['tz']})")
        print(f"{'─'*50}")

        result = audit_city(name, city)
        all_data[name] = result

        print(f"  Altitude range: {result['alt_range'][0]}° — {result['alt_range'][1]}°")
        print(f"  Azimuth range:  {result['az_range'][0]}° — {result['az_range'][1]}°")
        print(f"  Overhead days (>88°): {result['overhead_days']}")
        print(f"  NaN azimuth days:     {result['nan_az_days']}")

        # Sanity checks
        issues = []
        if city['lat'] > 0:  # Northern hemisphere
            if result['alt_range'][1] > 90.5:
                issues.append(f"ALTITUDE EXCEEDS 90° ({result['alt_range'][1]})")
        if city['lat'] < 0:  # Southern hemisphere
            # Check sun transits north
            mid_year = result['data'][180]  # ~July
            if mid_year['az'] is not None and 90 < mid_year['az'] < 270:
                issues.append("MID-YEAR TRANSIT IS SOUTH — should be NORTH for southern hemisphere")

        if name == 'Makkah-Madinah':
            # Check overhead logic
            if result['overhead_days'] == 0:
                issues.append("NO OVERHEAD DAYS — Makkah should have ~49 days with sun near zenith")
            if result['overhead_days'] > 80:
                issues.append(f"TOO MANY OVERHEAD DAYS ({result['overhead_days']})")

        if issues:
            print(f"  ⚠ ISSUES:")
            for i in issues:
                print(f"    → {i}")
        else:
            print(f"  ✓ Basic checks pass")

    # Detailed audits
    audit_makkah_detail(CITIES['Makkah-Madinah'])
    audit_sydney_detail(CITIES['Sydney'])
    compare_with_reference()

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name in CITIES:
        r = all_data[name]
        print(f"  {name:20s} | alt {r['alt_range'][0]:6.1f}° – {r['alt_range'][1]:5.1f}° "
              f"| az {str(r['az_range'][0]):>6s}° – {str(r['az_range'][1]):<6s}° "
              f"| overhead: {r['overhead_days']:2d} | NaN az: {r['nan_az_days']:2d}")

    # Export corrected data for visualization
    export = {}
    for name in CITIES:
        r = all_data[name]
        export[name] = {
            'lat': r['lat'], 'lon': r['lon'], 'tz': r['tz'],
            'altRange': r['alt_range'], 'azRange': r['az_range'],
            'overhead': r['overhead_days'],
            'points': [[d['doy'], d['alt'], d['az'], d['decl']] for d in r['data']]
        }

    out_path = 'Reports/Sibaha_alshams_alqamar/sibaha_audit_data.json'
    with open(out_path, 'w') as f:
        json.dump(export, f)
    print(f"\n  Corrected data exported to {out_path}")

    return all_data


if __name__ == '__main__':
    main()
