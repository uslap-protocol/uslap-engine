#!/usr/bin/env python3
"""
sibaha_circadian.py — Maps the sun's annual trajectory to human circadian biology.

The figure-8 (sibaha al-shams) IS the circadian driver. This module computes:
1. Prayer times (5 salawat) for each day of the year
2. Hormone curves (melatonin, cortisol, serotonin, body temp)
3. Clock gene expression (PER/CRY, BMAL1/CLOCK)
4. Circadian state classification per day
5. Prayer-to-biology mapping (each salah = a biological state transition)

Uses NOAA/Meeus algorithm from sibaha_audit.py for all solar position calculations.
"""

import math
import json
import sys
from datetime import datetime, timedelta

# Import solar position engine
sys.path.insert(0, '/Users/mmsetubal/Documents/USLaP workplace/Code_files')
from sibaha_audit import (
    sun_position, zuhr_time, julian_day, julian_century,
    sun_declination, equation_of_time, moon_position, CITIES
)

# ═══════════════════════════════════════════════════════════════
# A. PRAYER TIME COMPUTATION
# ═══════════════════════════════════════════════════════════════

def find_sun_crossing(lat, lon, tz, year, month, day, target_alt, after_noon=False, fallback_alt=None):
    """
    Bisection search: find the hour (local time) when sun crosses target_alt.

    after_noon=False → search before solar noon (fajr, sunrise)
    after_noon=True  → search after solar noon (sunset, maghrib, isha)

    Returns fractional hours (local time), or None if sun never reaches target_alt.
    If fallback_alt is set, tries that if target_alt fails (high-latitude edge case).
    """
    noon = zuhr_time(lat, lon, tz, year, month, day)

    if after_noon:
        lo, hi = noon, 23.99
    else:
        lo, hi = 0.01, noon

    # Check if the target altitude is reachable
    alt_lo, _, _ = sun_position(lat, lon, tz, year, month, day, lo)
    alt_hi, _, _ = sun_position(lat, lon, tz, year, month, day, hi)

    if after_noon:
        # Sun goes from high (noon) to low — we want when it drops to target
        if alt_lo < target_alt and alt_hi < target_alt:
            # Sun never reaches target (already below at noon)
            if fallback_alt is not None:
                return find_sun_crossing(lat, lon, tz, year, month, day, fallback_alt, after_noon)
            return None
        if alt_hi > target_alt:
            # Sun never drops below target (white nights)
            if fallback_alt is not None:
                return find_sun_crossing(lat, lon, tz, year, month, day, fallback_alt, after_noon)
            return None
    else:
        # Sun goes from low (midnight) to high (noon) — we want when it rises to target
        if alt_lo > target_alt and alt_hi > target_alt:
            if fallback_alt is not None:
                return find_sun_crossing(lat, lon, tz, year, month, day, fallback_alt, after_noon)
            return None
        if alt_lo > target_alt:
            if fallback_alt is not None:
                return find_sun_crossing(lat, lon, tz, year, month, day, fallback_alt, after_noon)
            return None

    # Bisection: 20 iterations → precision ~0.1 seconds
    for _ in range(25):
        mid = (lo + hi) / 2
        alt_mid, _, _ = sun_position(lat, lon, tz, year, month, day, mid)

        if after_noon:
            if alt_mid > target_alt:
                lo = mid
            else:
                hi = mid
        else:
            if alt_mid < target_alt:
                lo = mid
            else:
                hi = mid

    return (lo + hi) / 2


def fajr_time(lat, lon, tz, year, month, day):
    """Fajr: sun at -18° (astronomical twilight). Fallback -15° for high latitudes."""
    return find_sun_crossing(lat, lon, tz, year, month, day, -18.0, after_noon=False, fallback_alt=-15.0)


def sunrise_time(lat, lon, tz, year, month, day):
    """Sunrise: sun at -0.833° (refraction-corrected horizon)."""
    return find_sun_crossing(lat, lon, tz, year, month, day, -0.833, after_noon=False)


def asr_time(lat, lon, tz, year, month, day, hanafi=False):
    """
    Asr: shadow length = object height + noon shadow length (Shafi'i)
         shadow length = 2 * object height + noon shadow length (Hanafi)

    Computes target altitude from noon shadow, then bisects.
    """
    noon_h = zuhr_time(lat, lon, tz, year, month, day)
    noon_alt, _, _ = sun_position(lat, lon, tz, year, month, day, noon_h)

    if noon_alt <= 0:
        return None  # Sun doesn't rise meaningfully

    # Shadow ratio at noon
    noon_shadow_ratio = 1.0 / math.tan(math.radians(noon_alt)) if noon_alt > 0.1 else 100

    # Target shadow ratio
    factor = 2 if hanafi else 1
    target_shadow_ratio = factor + noon_shadow_ratio

    # Convert back to altitude
    target_alt = math.degrees(math.atan(1.0 / target_shadow_ratio))

    return find_sun_crossing(lat, lon, tz, year, month, day, target_alt, after_noon=True)


def maghrib_time(lat, lon, tz, year, month, day):
    """Maghrib: sunset, sun at -0.833° (refraction-corrected)."""
    return find_sun_crossing(lat, lon, tz, year, month, day, -0.833, after_noon=True)


def isha_time(lat, lon, tz, year, month, day):
    """Isha: sun at -17°. Fallback -15° for high latitudes."""
    return find_sun_crossing(lat, lon, tz, year, month, day, -17.0, after_noon=True, fallback_alt=-15.0)


# ═══════════════════════════════════════════════════════════════
# B. HORMONE MODELS
# ═══════════════════════════════════════════════════════════════

def melatonin_curve(sunrise_h, sunset_h, resolution=96):
    """
    Melatonin: darkness hormone.
    - DLMO (dim-light melatonin onset): sunset + 2h
    - Offset: sunrise - 1h
    - Peak: midpoint of darkness
    - Amplitude scales with night length (longer nights → more melatonin)
    - Shape: raised cosine bell

    Returns list of (hour, level) tuples, level normalized 0-1.
    """
    dlmo = sunset_h + 2.0  # onset
    offset = sunrise_h - 1.0 + 24.0  # next morning, add 24 for continuity
    if dlmo > 24: dlmo -= 24

    # Night length determines amplitude
    night_length = (24.0 - sunset_h) + sunrise_h
    amplitude = min(1.0, night_length / 12.0)  # normalize: 12h night = max

    # Peak at midpoint of darkness
    peak = sunset_h + night_length / 2.0
    if peak > 24: peak -= 24

    # Half-width of the melatonin bell
    half_width = night_length / 2.0 * 0.85  # slightly narrower than full night

    curve = []
    for i in range(resolution):
        h = i * 24.0 / resolution
        # Distance from peak (circular)
        dist = abs(h - peak)
        if dist > 12: dist = 24 - dist

        if dist < half_width:
            level = amplitude * 0.5 * (1 + math.cos(math.pi * dist / half_width))
        else:
            level = 0.0
        curve.append((round(h, 2), round(level, 4)))

    return curve


def cortisol_curve(sunrise_h, fajr_h, resolution=96):
    """
    Cortisol: stress/awakening hormone.
    - Cortisol Awakening Response (CAR): peaks 30-45min after wake (≈sunrise)
    - Pre-dawn rise begins at fajr
    - Declines through day, trough at midnight
    - Small ultradian pulses ignored (simplified model)

    Returns list of (hour, level) tuples, level normalized 0-1.
    """
    peak_h = sunrise_h + 0.5  # CAR peak: 30 min after sunrise
    pre_dawn_start = fajr_h if fajr_h is not None else sunrise_h - 1.5

    curve = []
    for i in range(resolution):
        h = i * 24.0 / resolution

        # Distance from peak (forward direction)
        if h >= peak_h:
            hours_after_peak = h - peak_h
        else:
            hours_after_peak = h + 24 - peak_h

        if hours_after_peak < 0.5:
            # Rising phase (pre-dawn to peak)
            rise_duration = peak_h - pre_dawn_start
            if rise_duration <= 0: rise_duration = 2.0
            hours_before_peak = 0.5 - hours_after_peak
            if hours_before_peak < rise_duration:
                level = 0.15 + 0.85 * (1 - hours_before_peak / rise_duration)
            else:
                level = 0.05
        elif hours_after_peak <= 16:
            # Exponential decay through the day
            level = 1.0 * math.exp(-hours_after_peak / 5.0)
        else:
            # Overnight trough with pre-dawn rise
            hours_to_peak = 24 - hours_after_peak
            if hours_to_peak < (peak_h - pre_dawn_start):
                # Pre-dawn rise
                rise_frac = 1 - hours_to_peak / (peak_h - pre_dawn_start)
                level = 0.05 + 0.1 * rise_frac
            else:
                level = 0.05

        curve.append((round(h, 2), round(min(1.0, max(0, level)), 4)))

    return curve


def serotonin_curve(sunrise_h, sunset_h, zuhr_h, resolution=96):
    """
    Serotonin: mood/wakefulness neurotransmitter.
    - Rises with light exposure (sunrise)
    - Peaks at solar noon (zuhr) — max light intensity
    - Declines after sunset
    - Baseline at night (converted to melatonin in pineal gland)

    Returns list of (hour, level) tuples, level normalized 0-1.
    """
    curve = []
    day_length = sunset_h - sunrise_h

    for i in range(resolution):
        h = i * 24.0 / resolution

        if sunrise_h <= h <= sunset_h:
            # Daytime: bell curve centered on zuhr
            dist = abs(h - zuhr_h)
            half_day = day_length / 2
            if half_day > 0:
                level = 0.2 + 0.8 * math.exp(-(dist ** 2) / (2 * (half_day * 0.4) ** 2))
            else:
                level = 0.2
        elif h < sunrise_h:
            # Pre-dawn baseline
            hours_to_sunrise = sunrise_h - h
            level = 0.05 + 0.15 * max(0, 1 - hours_to_sunrise / 2)
        else:
            # Post-sunset decline
            hours_after_sunset = h - sunset_h
            level = 0.2 * math.exp(-hours_after_sunset / 1.5)

        curve.append((round(h, 2), round(min(1.0, max(0, level)), 4)))

    return curve


def body_temp_curve(sunrise_h, sunset_h, resolution=96):
    """
    Core body temperature: circadian marker.
    - Minimum: ~2h before sunrise (nadir)
    - Maximum: ~2h before sunset (late afternoon peak)
    - Sinusoidal with phase set by light exposure
    - Range: ~36.0°C (nadir) to ~37.2°C (peak), normalized 0-1

    Returns list of (hour, level) tuples, level normalized 0-1.
    """
    temp_min_h = sunrise_h - 2.0
    if temp_min_h < 0: temp_min_h += 24
    temp_max_h = sunset_h - 2.0

    curve = []
    for i in range(resolution):
        h = i * 24.0 / resolution
        # Sinusoidal: min at temp_min_h, max at temp_max_h
        # Phase: 0 at minimum, pi at maximum
        dist_from_min = h - temp_min_h
        if dist_from_min < 0: dist_from_min += 24
        if dist_from_min > 24: dist_from_min -= 24

        phase = 2 * math.pi * dist_from_min / 24.0
        level = 0.5 + 0.5 * math.sin(phase - math.pi / 2)

        curve.append((round(h, 2), round(level, 4)))

    return curve


def clock_genes(sunrise_h, sunset_h, resolution=96):
    """
    Simplified clock gene expression:
    - PER/CRY: peak in evening (~sunset), drive negative feedback
    - BMAL1/CLOCK: peak in morning (~sunrise), drive positive loop

    Returns dict with 'per_cry' and 'bmal1' curves.
    """
    per_peak = sunset_h  # PER/CRY peak at evening
    bmal_peak = sunrise_h + 2  # BMAL1 peak in morning

    per_curve = []
    bmal_curve = []

    for i in range(resolution):
        h = i * 24.0 / resolution

        # PER/CRY
        dist = abs(h - per_peak)
        if dist > 12: dist = 24 - dist
        per_level = 0.5 + 0.5 * math.cos(math.pi * dist / 12)
        per_curve.append((round(h, 2), round(per_level, 4)))

        # BMAL1/CLOCK
        dist = abs(h - bmal_peak)
        if dist > 12: dist = 24 - dist
        bmal_level = 0.5 + 0.5 * math.cos(math.pi * dist / 12)
        bmal_curve.append((round(h, 2), round(bmal_level, 4)))

    return {'per_cry': per_curve, 'bmal1': bmal_curve}


def sample_curve_at(curve, hour):
    """Sample a curve (list of (h, level) tuples) at a specific hour via interpolation."""
    if not curve:
        return 0
    n = len(curve)
    h_step = 24.0 / n
    idx = hour / h_step
    i0 = int(idx) % n
    i1 = (i0 + 1) % n
    frac = idx - int(idx)
    return curve[i0][1] * (1 - frac) + curve[i1][1] * frac


# ═══════════════════════════════════════════════════════════════
# C. CIRCADIAN STATE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

def classify_circadian_state(day_length, day_length_prev, day_length_next):
    """
    Classify the circadian state based on day length and its rate of change.

    Returns: (state_name, color_hex)
    """
    if day_length_prev is not None and day_length_next is not None:
        rate = (day_length_next - day_length_prev) / 2  # minutes per day change
    else:
        rate = 0

    abs_rate = abs(rate)

    # Threshold: >2 min/day change = significant circadian stress
    if abs_rate > 2.5:
        if rate > 0:
            return ('advancing', '#e67e22')   # orange: day lengthening fast
        else:
            return ('delaying', '#d4a017')    # amber: day shortening fast
    elif abs_rate > 1.5:
        if rate > 0:
            return ('mild_advance', '#f0c040')
        else:
            return ('mild_delay', '#c08030')
    else:
        # Near solstice: classify by absolute day length
        if day_length > 14:
            return ('peak_serotonergic', '#f1c40f')  # bright yellow: long days
        elif day_length < 10:
            return ('peak_melatonergic', '#3498db')   # blue: short days
        else:
            return ('balanced', '#9b59b6')            # violet: equinox zone


# ═══════════════════════════════════════════════════════════════
# D. ANNUAL COMPUTATION
# ═══════════════════════════════════════════════════════════════

def compute_annual_circadian(city_name, city, start_date, N=365):
    """Compute full circadian dataset for one city over N days."""

    lat, lon, tz = city['lat'], city['lon'], city['tz']

    # Arrays for prayer times (fractional hours)
    times = {k: [] for k in ['fajr', 'sunrise', 'zuhr', 'asr', 'sunset', 'isha']}

    # Day metrics
    day_lengths = []
    photoperiods = []

    # Hormone samples at each prayer time
    at_prayer = {}
    for prayer in ['fajr', 'zuhr', 'asr', 'maghrib', 'isha']:
        at_prayer[prayer] = {'mel': [], 'cort': [], 'sero': [], 'temp': []}

    # States
    states = []

    # Sample days (full 96-point curves)
    sample_indices = {}  # will map name → day_index

    eot_vals = []
    alt_vals = []

    for i in range(N):
        dt = start_date + timedelta(days=i)
        y, m, d = dt.year, dt.month, dt.day

        # Prayer times
        f = fajr_time(lat, lon, tz, y, m, d)
        sr = sunrise_time(lat, lon, tz, y, m, d)
        z = zuhr_time(lat, lon, tz, y, m, d)
        a = asr_time(lat, lon, tz, y, m, d)
        ss = maghrib_time(lat, lon, tz, y, m, d)
        ish = isha_time(lat, lon, tz, y, m, d)

        times['fajr'].append(round(f, 3) if f else None)
        times['sunrise'].append(round(sr, 3) if sr else None)
        times['zuhr'].append(round(z, 3))
        times['asr'].append(round(a, 3) if a else None)
        times['sunset'].append(round(ss, 3) if ss else None)
        times['isha'].append(round(ish, 3) if ish else None)

        # Day length
        if sr is not None and ss is not None:
            dl = (ss - sr) * 60  # minutes
        else:
            dl = 0
        day_lengths.append(round(dl, 1))

        # Photoperiod (fajr to isha)
        if f is not None and ish is not None:
            pp = (ish - f) * 60
        else:
            pp = dl
        photoperiods.append(round(pp, 1))

        # Generate hormone curves for this day
        sr_h = sr if sr else 6.0
        ss_h = ss if ss else 18.0
        f_h = f if f else sr_h - 1.5
        z_h = z

        mel = melatonin_curve(sr_h, ss_h)
        cort = cortisol_curve(sr_h, f_h)
        sero = serotonin_curve(sr_h, ss_h, z_h)
        temp = body_temp_curve(sr_h, ss_h)

        # Sample at prayer times
        prayer_hours = {
            'fajr': f_h,
            'zuhr': z_h,
            'asr': a if a else z_h + 3,
            'maghrib': ss_h,
            'isha': ish if ish else ss_h + 1.5,
        }

        for prayer, hour in prayer_hours.items():
            at_prayer[prayer]['mel'].append(round(sample_curve_at(mel, hour), 3))
            at_prayer[prayer]['cort'].append(round(sample_curve_at(cort, hour), 3))
            at_prayer[prayer]['sero'].append(round(sample_curve_at(sero, hour), 3))
            at_prayer[prayer]['temp'].append(round(sample_curve_at(temp, hour), 3))

        # EoT and altitude for figure-8 coordinates
        jd = julian_day(y, m, d, 12)
        T = julian_century(jd)
        eot_vals.append(equation_of_time(T))
        noon_h = zuhr_time(lat, lon, tz, y, m, d)
        alt, _, _ = sun_position(lat, lon, tz, y, m, d, noon_h)
        alt_vals.append(alt)

        # Mark sample days
        month_day = (dt.month, dt.day)
        if month_day == (6, 21):
            sample_indices['summer_solstice'] = i
        elif month_day == (12, 21):
            sample_indices['winter_solstice'] = i
        elif month_day == (3, 20):
            sample_indices['equinox_spring'] = i
        elif month_day == (9, 23):
            sample_indices['equinox_autumn'] = i

    # Rate of change (day-to-day)
    rates = [0]
    for i in range(1, N):
        rates.append(round(day_lengths[i] - day_lengths[i - 1], 2))

    # Classify circadian state
    for i in range(N):
        dl = day_lengths[i]
        dl_prev = day_lengths[i - 1] if i > 0 else dl
        dl_next = day_lengths[i + 1] if i < N - 1 else dl
        state, color = classify_circadian_state(dl, dl_prev, dl_next)
        states.append(state)

    # Generate full curves for sample days
    samples = {}
    for name, idx in sample_indices.items():
        sr_h = times['sunrise'][idx] or 6.0
        ss_h = times['sunset'][idx] or 18.0
        f_h = times['fajr'][idx] or sr_h - 1.5
        z_h = times['zuhr'][idx]

        mel = melatonin_curve(sr_h, ss_h)
        cort = cortisol_curve(sr_h, f_h)
        sero = serotonin_curve(sr_h, ss_h, z_h)
        temp = body_temp_curve(sr_h, ss_h)
        genes = clock_genes(sr_h, ss_h)

        samples[name] = {
            'day_index': idx,
            'date': (start_date + timedelta(days=idx)).strftime('%Y-%m-%d'),
            'mel': [p[1] for p in mel],
            'cort': [p[1] for p in cort],
            'sero': [p[1] for p in sero],
            'temp': [p[1] for p in temp],
            'per_cry': [p[1] for p in genes['per_cry']],
            'bmal1': [p[1] for p in genes['bmal1']],
            'times': {
                'fajr': times['fajr'][idx],
                'sunrise': times['sunrise'][idx],
                'zuhr': times['zuhr'][idx],
                'asr': times['asr'][idx],
                'sunset': times['sunset'][idx],
                'isha': times['isha'][idx],
            }
        }

    # Figure-8 3D coordinates (recomputed with ring topology)
    eot_absmax = max(abs(e) for e in eot_vals)
    alt_min = min(alt_vals)
    alt_max = max(alt_vals)
    alt_mid = (alt_min + alt_max) / 2
    alt_half = (alt_max - alt_min) / 2
    if alt_half < 0.1: alt_half = 0.1

    R = 0.3
    sun_3d = []
    for i in range(N):
        theta = 2 * math.pi * i / N
        x = round(eot_vals[i] / eot_absmax, 4)
        y_norm = round((alt_vals[i] - alt_mid) / alt_half, 4)
        z = round(R * math.sin(theta), 4)
        sun_3d.append([x, y_norm, z])

    # Manazil
    manazil_days = [round(k * 365 / 28) for k in range(28)]
    manazil_pts = []
    for k in range(28):
        day = min(manazil_days[k], N - 1)
        theta = 2 * math.pi * day / N
        x = round(eot_vals[day] / eot_absmax, 4)
        y_norm = round((alt_vals[day] - alt_mid) / alt_half, 4)
        z = round(R * math.sin(theta), 4)
        manazil_pts.append([x, y_norm, z, day, k + 1])

    return {
        'sun': sun_3d,
        'manazil': manazil_pts,
        'sAlt': [round(a, 1) for a in alt_vals],
        'altRange': [round(alt_min, 1), round(alt_max, 1)],
        'circadian': {
            'times': times,
            'day_length': day_lengths,
            'photoperiod': photoperiods,
            'rate_of_change': rates,
            'at_fajr': at_prayer['fajr'],
            'at_zuhr': at_prayer['zuhr'],
            'at_asr': at_prayer['asr'],
            'at_maghrib': at_prayer['maghrib'],
            'at_isha': at_prayer['isha'],
            'state': states,
            'samples': samples,
        }
    }


# ═══════════════════════════════════════════════════════════════
# E. MAIN: COMPUTE ALL CITIES + EXPORT JSON
# ═══════════════════════════════════════════════════════════════

def main():
    start_date = datetime(2025, 4, 2)
    N = 365

    print("=" * 70)
    print("  sibaha al-shams → Circadian Biology Computation")
    print("=" * 70)

    all_cities = {}
    dates = []
    city_meta = {}

    for city_name, city in CITIES.items():
        print(f"\n  Computing {city_name}...")

        result = compute_annual_circadian(city_name, city, start_date, N)
        all_cities[city_name] = result

        if not dates:
            dates = [(start_date + timedelta(days=i)).strftime('%d %b %Y') for i in range(N)]

        # Summary
        dl = result['circadian']['day_length']
        dl_min = min(d for d in dl if d > 0)
        dl_max = max(dl)
        rates = result['circadian']['rate_of_change']
        max_rate = max(abs(r) for r in rates)

        fajr_times = [t for t in result['circadian']['times']['fajr'] if t is not None]
        isha_times = [t for t in result['circadian']['times']['isha'] if t is not None]

        lat_abs = abs(city['lat'])
        hem = 'N' if city['lat'] >= 0 else 'S'
        overhead_count = sum(1 for a in result['sAlt'] if a > 88)

        if overhead_count > 0:
            desc = f"{lat_abs:.1f}{hem}. Sun OVERHEAD ({overhead_count} days)."
        elif city['lat'] > 0:
            desc = f"{lat_abs:.1f}{hem}. Sun always SOUTH at Zuhr."
        else:
            desc = f"{lat_abs:.1f}{hem}. Sun transits NORTH. Seasons inverted."

        city_meta[city_name] = {'lat': city['lat'], 'col': city['color'], 'desc': desc}

        print(f"    Day length: {dl_min:.0f} – {dl_max:.0f} min ({dl_min/60:.1f}h – {dl_max/60:.1f}h)")
        print(f"    Max rate of change: {max_rate:.1f} min/day")
        print(f"    Fajr range: {min(fajr_times):.2f}h – {max(fajr_times):.2f}h")
        print(f"    Isha range: {min(isha_times):.2f}h – {max(isha_times):.2f}h")
        print(f"    States: {len(set(result['circadian']['state']))} distinct states")
        print(f"    Samples: {list(result['circadian']['samples'].keys())}")

    output = {
        'cities': all_cities,
        'dates': dates,
        'N': N,
        'cityMeta': city_meta,
    }

    out_path = '/Users/mmsetubal/Documents/USLaP workplace/Reports/Sibaha_alshams_alqamar/sibaha_circadian_data.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    import os
    size = os.path.getsize(out_path)
    print(f"\n  Exported: {out_path}")
    print(f"  Size: {size:,} bytes ({size/1024:.0f} KB)")

    return output


if __name__ == '__main__':
    main()
