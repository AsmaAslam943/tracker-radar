#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
Path("results").mkdir(exist_ok=True)

# ── Tracker prevalence: drawn from known real-world DDG Tracker Radar data ──
TRACKERS = [
    # (domain, owner, category, approx_site_pct)
    ("google-analytics.com",    "Google Analytics",    "Analytics",            76),
    ("googletagmanager.com",    "Google Tag Manager",  "Tag Management",       71),
    ("doubleclick.net",         "Google/DoubleClick",  "Advertising",          63),
    ("googlesyndication.com",   "Google",              "Advertising",          59),
    ("googleadservices.com",    "Google",              "Advertising",          48),
    ("connect.facebook.net",    "Facebook",            "Social",               42),
    ("facebook.com",            "Facebook",            "Social",               38),
    ("criteo.com",              "Criteo",              "Advertising",          24),
    ("amazon-adsystem.com",     "Amazon",              "Advertising",          22),
    ("scorecardresearch.com",   "Comscore",            "Analytics",            21),
    ("taboola.com",             "Taboola",             "Advertising",          19),
    ("hotjar.com",              "Hotjar",              "Analytics",            17),
    ("adnxs.com",               "AppNexus",            "Advertising",          16),
    ("outbrain.com",            "Outbrain",            "Advertising",          15),
    ("pubmatic.com",            "PubMatic",            "Advertising",          14),
    ("rubiconproject.com",      "Rubicon Project",     "Advertising",          13),
    ("twitter.com",             "Twitter",             "Social",               12),
    ("linkedin.com",            "LinkedIn",            "Social",               11),
    ("segment.com",             "Segment",             "Analytics",            10),
    ("tealiumiq.com",           "Tealium",             "Tag Management",        9),
    ("openx.net",               "OpenX",               "Advertising",           8),
    ("indexexchange.com",       "Index Exchange",      "Advertising",           8),
    ("cloudflare.com",          "Cloudflare",          "CDN / Infrastructure",  7),
    ("newrelic.com",            "New Relic",           "Analytics",             7),
    ("mixpanel.com",            "Mixpanel",            "Analytics",             6),
    ("amplitude.com",           "Amplitude",           "Analytics",             5),
    ("pinterest.com",           "Pinterest",           "Social",                5),
    ("33across.com",            "33Across",            "Advertising",           4),
    ("adsrvr.org",              "Trade Desk",          "Advertising",           4),
    ("tiktok.com",              "TikTok",              "Social",                3),
]

N = 1000  # simulated sites

rows = []
for domain, owner, cat, pct in TRACKERS:
    sites_seen = int(round(pct / 100 * N + np.random.randint(-5, 6)))
    sites_seen = max(1, min(sites_seen, N))
    rows.append({
        "tracker_domain": domain,
        "owner":          owner,
        "category":       cat,
        "sites_seen":     sites_seen,
        "site_pct":       round(sites_seen / N * 100, 2),
    })

prev_df = pd.DataFrame(rows).sort_values("sites_seen", ascending=False).reset_index(drop=True)
prev_df.to_csv("results/tracker_prevalence.csv", index=False)
prev_df.head(20).to_csv("results/top_trackers.csv", index=False)

# ── Category aggregation ────────────────────────────────────────────────────
# Use rough independent-coverage estimates for each category
CAT_COVERAGE = {
    "Advertising":          87,
    "Analytics":            81,
    "Tag Management":       73,
    "Social":               58,
    "CDN / Infrastructure": 32,
    "Other / Unknown":      45,
}
cat_rows = [
    {"category": cat, "sites_with_tracker": int(round(pct / 100 * N)),
     "site_pct": round(pct, 2)}
    for cat, pct in CAT_COVERAGE.items()
]
pd.DataFrame(cat_rows).sort_values("site_pct", ascending=False).reset_index(drop=True) \
  .to_csv("results/tracker_by_category.csv", index=False)

# Log-normal distribution centred around 10 trackers/site, matching real data
tracker_counts = np.random.lognormal(mean=2.5, sigma=0.8, size=N).astype(int)
tracker_counts = np.clip(tracker_counts, 0, 80)
pd.DataFrame({"site": [f"site_{i}" for i in range(N)],
              "tracker_count": tracker_counts}) \
  .to_csv("results/site_tracker_counts.csv", index=False)

print("✓ Demo CSVs written to results/")
print(f"  Median tracker count: {int(np.median(tracker_counts))}")
print(f"  Top tracker: {prev_df.iloc[0]['tracker_domain']} ({prev_df.iloc[0]['site_pct']}% of sites)")
