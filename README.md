# Web Tracker Prevalence — Write-up

## Crawling Process

To collect tracker data, I used DuckDuckGo's open-source [Tracker Radar Collector](https://github.com/duckduckgo/tracker-radar-collector), a Puppeteer-based crawler that visits websites in a headless Chromium browser and records all network activity during page load. The list of sites to crawl was sourced from the [Tranco top-1000](https://tranco-list.eu), a research-grade ranking that aggregates multiple domain lists (Alexa, Majestic, Umbrella) to produce a stable, manipulation-resistant ordering.

Each site was given a 30-second load window, with 4 parallel browser instances running concurrently to keep total crawl time manageable. For every site, the collector captured all outgoing network requests, cookies, JavaScript API usage, and fingerprinting signals. The crawl completed in just over 2 hours with a 97.1% success rate (971/1000 sites). Failed sites were mostly due to SSL errors or bot-detection blocking the headless browser.

Third-party requests were identified by comparing each request's domain against the visited site's domain. Requests originating from a different registrable domain were flagged as third-party, then mapped to their parent company (e.g. `doubleclick.net`, `googletagmanager.com`, and `google-analytics.com` all mapped to Google).

## Findings

**Google has by far the largest tracking footprint**, appearing on 47.4% of the top-1000 sites when all its domains are combined — more than three times the reach of the next largest network. This is consistent with DuckDuckGo's published Tracker Radar findings.

**Facebook and LinkedIn follow at 14% and 13.5%** respectively, primarily through social widgets (Like buttons, Share buttons) and advertising pixels embedded across the web.

**The tracker landscape is highly concentrated.** The top 5 companies alone (Google, Facebook, LinkedIn, Microsoft, OneTrust) collectively have reach across the majority of the top-1000 sites. Blocking just these networks would substantially reduce tracking exposure for most users.

**Consent management platforms are now ubiquitous.** OneTrust appearing on 11.8% of sites reflects the growing adoption of cookie consent banners following GDPR and CCPA — though their presence does not necessarily mean tracking is reduced, only that consent is requested.

**Most sites contact a small number of third-party domains**, with a median of 3, but the distribution has a long tail — the top 10% of sites contact 40 or more distinct third-party domains, typically large media and e-commerce properties with extensive ad-tech stacks.

## Plot
