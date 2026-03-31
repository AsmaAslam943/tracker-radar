#!/usr/bin/env python3
"""
Parse the raw JSON output from Tracker Radar Collector, identify third-party
tracker domains, and produce the summary CSV files used by the plotting script.
"""

import os, json, re, argparse, collections
from pathlib import Path
import pandas as pd
from tqdm import tqdm

OWNER_CATEGORY = {
    # Advertising
    "Google":               "Advertising",
    "DoubleClick":          "Advertising",
    "Facebook":             "Advertising",
    "Trade Desk":           "Advertising",
    "AppNexus":             "Advertising",
    "Criteo":               "Advertising",
    "Taboola":              "Advertising",
    "Outbrain":             "Advertising",
    "Index Exchange":       "Advertising",
    "OpenX":                "Advertising",
    "Rubicon Project":      "Advertising",
    "PubMatic":             "Advertising",
    "Amazon":               "Advertising",
    "Quantcast":            "Advertising",
    "Bidswitch":            "Advertising",
    "Verizon Media":        "Advertising",
    "MediaMath":            "Advertising",
    "Sovrn":                "Advertising",
    "TripleLift":           "Advertising",
    "33Across":             "Advertising",
    # Analytics
    "Adobe":                "Analytics",
    "Hotjar":               "Analytics",
    "Mixpanel":             "Analytics",
    "Segment":              "Analytics",
    "Heap":                 "Analytics",
    "Amplitude":            "Analytics",
    "Chartbeat":            "Analytics",
    "Nielsen":              "Analytics",
    "Comscore":             "Analytics",
    "AT Internet":          "Analytics",
    "New Relic":            "Analytics",
    "Dynatrace":            "Analytics",
    "Datadog":              "Analytics",
    # Social
    "Twitter":              "Social",
    "LinkedIn":             "Social",
    "Pinterest":            "Social",
    "Snap":                 "Social",
    "TikTok":               "Social",
    # CDN / Infrastructure (first-party-ish but still third-party requests)
    "Cloudflare":           "CDN / Infrastructure",
    "Akamai":               "CDN / Infrastructure",
    "Fastly":               "CDN / Infrastructure",
    "Edgecast":             "CDN / Infrastructure",
    # Tag Management
    "Tealium":              "Tag Management",
    "Ensighten":            "Tag Management",
    "Signal":               "Tag Management",
}

# Domain suffix 
DOMAIN_OWNER_HINTS = {
    "google-analytics.com":     ("Google Analytics", "Analytics"),
    "googletagmanager.com":     ("Google Tag Manager", "Tag Management"),
    "googlesyndication.com":    ("Google", "Advertising"),
    "doubleclick.net":          ("Google/DoubleClick", "Advertising"),
    "googleadservices.com":     ("Google", "Advertising"),
    "facebook.net":             ("Facebook", "Advertising"),
    "facebook.com":             ("Facebook", "Social"),
    "connect.facebook.net":     ("Facebook", "Social"),
    "criteo.com":               ("Criteo", "Advertising"),
    "criteo.net":               ("Criteo", "Advertising"),
    "taboola.com":              ("Taboola", "Advertising"),
    "outbrain.com":             ("Outbrain", "Advertising"),
    "amazon-adsystem.com":      ("Amazon", "Advertising"),
    "scorecardresearch.com":    ("Comscore", "Analytics"),
    "hotjar.com":               ("Hotjar", "Analytics"),
    "mixpanel.com":             ("Mixpanel", "Analytics"),
    "segment.com":              ("Segment", "Analytics"),
    "segment.io":               ("Segment", "Analytics"),
    "amplitude.com":            ("Amplitude", "Analytics"),
    "chartbeat.com":            ("Chartbeat", "Analytics"),
    "chartbeat.net":            ("Chartbeat", "Analytics"),
    "twitter.com":              ("Twitter", "Social"),
    "t.co":                     ("Twitter", "Social"),
    "linkedin.com":             ("LinkedIn", "Social"),
    "licdn.com":                ("LinkedIn", "Social"),
    "pinterest.com":            ("Pinterest", "Social"),
    "pinimg.com":               ("Pinterest", "Social"),
    "tiktok.com":               ("TikTok", "Social"),
    "snapchat.com":             ("Snap", "Social"),
    "adnxs.com":                ("AppNexus", "Advertising"),
    "indexexchange.com":        ("Index Exchange", "Advertising"),
    "openx.net":                ("OpenX", "Advertising"),
    "rubiconproject.com":       ("Rubicon Project", "Advertising"),
    "pubmatic.com":             ("PubMatic", "Advertising"),
    "quantserve.com":           ("Quantcast", "Advertising"),
    "bidswitch.net":            ("Bidswitch", "Advertising"),
    "33across.com":             ("33Across", "Advertising"),
    "omtrdc.net":               ("Adobe", "Analytics"),
    "2o7.net":                  ("Adobe", "Analytics"),
    "demdex.net":               ("Adobe", "Analytics"),
    "newrelic.com":             ("New Relic", "Analytics"),
    "nr-data.net":              ("New Relic", "Analytics"),
    "cloudflare.com":           ("Cloudflare", "CDN / Infrastructure"),
    "cloudflare.net":           ("Cloudflare", "CDN / Infrastructure"),
    "tealiumiq.com":            ("Tealium", "Tag Management"),
    "tiqcdn.com":               ("Tealium", "Tag Management"),
    "tradedesk.com":            ("Trade Desk", "Advertising"),
    "adsrvr.org":               ("Trade Desk", "Advertising"),
    "id5-sync.com":             ("ID5", "Advertising"),
    "casalemedia.com":          ("Index Exchange", "Advertising"),
    "mediamath.com":            ("MediaMath", "Advertising"),
    "sovrn.com":                ("Sovrn", "Advertising"),
    "triplelift.com":           ("TripleLift", "Advertising"),
}


def extract_registrable_domain(hostname: str) -> str:
  
    parts = hostname.lstrip(".").split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname


def classify_domain(domain: str):
    """Return (owner_label, category) for a third-party domain."""
    # Exact match first
    if domain in DOMAIN_OWNER_HINTS:
        return DOMAIN_OWNER_HINTS[domain]
    # Suffix match
    for suffix, info in DOMAIN_OWNER_HINTS.items():
        if domain.endswith("." + suffix) or domain == suffix:
            return info
    return (domain, "Other / Unknown")


def is_third_party(request_domain: str, site_domain: str) -> bool:
    rd = extract_registrable_domain(request_domain)
    sd = extract_registrable_domain(site_domain)
    return rd != sd


def parse_results(raw_dir: Path):
    tracker_sites: dict[str, set] = collections.defaultdict(set)
    site_tracker_count: dict[str, int] = {}
    sites_visited = []

    json_files = sorted(raw_dir.glob("*.json"))
    if not json_files:
        print(f"ERROR: no JSON files found in {raw_dir}")
        print("  → Run ./scripts/02_crawl.sh first, or check the path.")
        return [], {}, {}

    print(f"Parsing {len(json_files)} result files...")
    for jf in tqdm(json_files):
        try:
            data = json.loads(jf.read_text())
        except Exception:
            continue

        site_url = data.get("initialUrl", "")
        site_domain = re.sub(r"https?://(www\.)?", "", site_url).rstrip("/")
        if not site_domain:
            site_domain = jf.stem
        sites_visited.append(site_domain)

        requests_data = data.get("data", {}).get("requests", [])
        trackers_on_site = set()

        for req in requests_data:
            url = req.get("url", "")
            try:
                from urllib.parse import urlparse
                req_hostname = urlparse(url).hostname or ""
            except Exception:
                continue
            if not req_hostname:
                continue
            if not is_third_party(req_hostname, site_domain):
                continue

            req_domain = extract_registrable_domain(req_hostname)
            _, category = classify_domain(req_domain)
            # Only count domains with a known tracker signature OR any 3rd-party
            trackers_on_site.add(req_domain)
            tracker_sites[req_domain].add(site_domain)

        site_tracker_count[site_domain] = len(trackers_on_site)

    return sites_visited, tracker_sites, site_tracker_count


def build_dataframes(sites_visited, tracker_sites, site_tracker_count):
    total_sites = len(sites_visited)

    #Tracks all domains and sites in dataframes 
    rows = []
    for domain, sites in tracker_sites.items():
        owner, category = classify_domain(domain)
        rows.append({
            "tracker_domain": domain,
            "owner":          owner,
            "category":       category,
            "sites_seen":     len(sites),
            "site_pct":       round(len(sites) / total_sites * 100, 2),
        })
    prevalence_df = (
        pd.DataFrame(rows)
        .sort_values("sites_seen", ascending=False)
        .reset_index(drop=True)
    )

    # ── Category-level aggregation ────────────────────────────────────────────
    # For each category: how many sites have ≥1 tracker from that category?
    cat_sites: dict[str, set] = collections.defaultdict(set)
    for domain, sites in tracker_sites.items():
        _, cat = classify_domain(domain)
        cat_sites[cat].update(sites)
    category_df = pd.DataFrame([
        {"category": cat, "sites_with_tracker": len(s),
         "site_pct": round(len(s) / total_sites * 100, 2)}
        for cat, s in cat_sites.items()
    ]).sort_values("sites_with_tracker", ascending=False).reset_index(drop=True)

    # Counts site per tracker distribution  
    dist_df = (
        pd.DataFrame(list(site_tracker_count.items()),
                     columns=["site", "tracker_count"])
        .sort_values("tracker_count", ascending=False)
        .reset_index(drop=True)
    )

    return prevalence_df, category_df, dist_df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="results/raw",  help="Dir with raw JSON files")
    ap.add_argument("--out", default="results",       help="Output dir for CSVs")
    args = ap.parse_args()

    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    sites, tracker_sites, site_tracker_count = parse_results(raw_dir)
    if not sites:
        return

    print(f"\n✓ Sites visited:          {len(sites)}")
    print(f"✓ Unique 3rd-party domains: {len(tracker_sites)}")
    avg = sum(site_tracker_count.values()) / max(len(site_tracker_count), 1)
    print(f"✓ Avg trackers / site:    {avg:.1f}")

    prev_df, cat_df, dist_df = build_dataframes(sites, tracker_sites, site_tracker_count)

    prev_df.to_csv(out_dir / "tracker_prevalence.csv", index=False)
    cat_df.to_csv(out_dir  / "tracker_by_category.csv", index=False)
    dist_df.to_csv(out_dir / "site_tracker_counts.csv", index=False)
    prev_df.head(20).to_csv(out_dir / "top_trackers.csv", index=False)

    print(f"\nTop 10 trackers by prevalence:")
    print(prev_df.head(10)[["tracker_domain","owner","category","site_pct"]].to_string(index=False))
    print(f"\n✓ CSVs written to {out_dir}/")
    print("Next step: python3 analysis/04_plot.py")


if __name__ == "__main__":
    main()
