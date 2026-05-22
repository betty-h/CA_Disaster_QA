"""
scrape_disaster_info.py

Scrapes California disaster recovery information from authoritative public sources.
Saves structured content to scraped_content.json for use by generate_qa_pairs.py.

Sources cover the full topic distribution:
  - FEMA (registration, housing, individual assistance)
  - CalOES / disaster.ca.gov
  - CA Insurance Commissioner
  - SBA disaster loans
  - EDD disaster unemployment
  - 211 LA / 211 SF (local coordination)
  - CA Franchise Tax Board (tax relief)
  - CAL FIRE / debris removal
  - Red Cross CA
  - Legal Aid (renters, undocumented)
"""

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
import requests
import trafilatura
from trafilatura.settings import use_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── trafilatura config: be a polite scraper ──────────────────────────────────
traf_config = use_config()
traf_config.set("DEFAULT", "SLEEP_TIME", "2")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; disaster-recovery-research-bot/1.0; "
        "+https://example.org/research)"
    )
}

# ── Sources ──────────────────────────────────────────────────────────────────
# Each entry: (topic_category, url, short_label)
SOURCES = [
    # FEMA — highest volume queries
    ("fema_registration",    "https://www.disasterassistance.gov/", "FEMA: DisasterAssistance.gov Registration"),
    ("fema_individual_assist","https://www.fema.gov/assistance/individual", "FEMA: Individual Assistance Overview"),
    ("fema_housing",         "https://www.fema.gov/assistance/individual/housing", "FEMA: Temporary Housing"),
    ("fema_appeals",         "https://www.fema.gov/assistance/individual/after-applying/appeals", "FEMA: Appeals Process"),
    ("fema_after_applying",  "https://www.fema.gov/assistance/individual/after-applying", "FEMA: After Applying"),
    ("fema_disaster_map",    "https://www.fema.gov/disasters/disaster-declarations", "FEMA: Disaster Declarations"),

    # CA state
    ("caloes_overview",      "https://www.caloes.ca.gov/individuals-families", "CalOES: Individuals & Families"),
    ("ca_disaster_portal",   "https://www.ca.gov/topics/disaster-recovery/", "CA Disaster Recovery"),
    ("ca_wildfire_recovery", "https://www.wildfirerecovery.caloes.ca.gov/", "CalOES: Wildfire Recovery"),

    # Insurance
    ("ca_insurance",         "https://www.insurance.ca.gov/01-consumers/140-catastrophes/", "CA DOI: Catastrophe Resources"),
    ("ca_insurance_claims",  "https://www.insurance.ca.gov/01-consumers/105-type/95-guides/03-res/disaster-claims.cfm", "CA DOI: Filing Disaster Claims"),

    # SBA disaster loans
    ("sba_disaster_loans",   "https://www.sba.gov/funding-programs/disaster-assistance", "SBA: Disaster Loans Overview"),
    ("sba_home_loans",       "https://www.sba.gov/funding-programs/disaster-assistance/physical-damage-loans", "SBA: Home Disaster Loans"),
    ("sba_business_loans",   "https://www.sba.gov/funding-programs/disaster-assistance/economic-injury-disaster-loans", "SBA: Business Disaster Loans"),

    # EDD — disaster unemployment
    ("edd_dua",              "https://edd.ca.gov/en/Unemployment/Disaster_Unemployment_Assistance/", "EDD: Disaster Unemployment Assistance"),

    # Tax relief
    ("ftb_tax_relief",       "https://www.ftb.ca.gov/file/when-to-file/help-with-disaster-relief.html", "FTB: Disaster Tax Relief"),
    ("irs_disaster_relief",  "https://www.irs.gov/newsroom/tax-relief-in-disaster-situations", "IRS: Disaster Tax Relief"),

    # Red Cross (blocks scrapers — use public-facing alternatives)
    ("redcross_recovery",    "https://www.redcross.org/about-us/our-work/disaster-relief.html", "Red Cross: Disaster Relief"),

    # CAL FIRE / debris
    ("ca_debris_removal",    "https://calrecycle.ca.gov/disaster/", "CalRecycle: Disaster Debris"),
    ("calfire_ready",        "https://www.readyforwildfire.org/post-wildfire/", "Ready for Wildfire: Post-Wildfire"),

    # Utility restoration
    ("cpuc_outages",         "https://www.cpuc.ca.gov/consumer-support", "CPUC: Consumer Support"),

    # Food assistance
    ("cdss_food",            "https://www.cdss.ca.gov/inforesources/cdss-programs/CalFresh", "CDSS: CalFresh / Food Assistance"),

    # Mental health
    ("samhsa_crisis",        "https://www.samhsa.gov/find-help/disaster-distress-helpline", "SAMHSA: Disaster Distress Helpline"),

    # Legal aid / special populations
    ("doj_undocumented",     "https://oag.ca.gov/immigrant", "CA DOJ: Immigrant Rights"),
    ("legal_aid_ca",         "https://www.lawhelpca.org/disaster-relief-information", "LawHelpCA: Disaster Relief"),

    # 211
    ("211_la",               "https://211la.org/articles/inside-look-disaster-resources", "211 LA: Disaster Resources"),
    ("211_housing",          "https://www.211.org/get-help/housing-expenses", "211: Housing Help"),

    # Contractor fraud
    ("cslb_fraud",           "https://www.cslb.ca.gov/Media_Room/Disaster_Help_Center/", "CSLB: Disaster Fraud Prevention"),

    # Specific disaster types
    ("earthquake_prep",      "https://www.earthquakeauthority.com/", "CEA: Earthquake Authority"),
    ("flood_recovery",       "https://www.floodsmart.gov/recover", "FloodSmart: After a Flood"),

    # Document replacement
    ("dmv_records",          "https://www.dmv.ca.gov/portal/driver-licenses-identification-cards/replace-your-driver-license-or-identification-dl-id-card/", "DMV: Replace License"),

    # Housing / renter rights
    ("hcd_renter",           "https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/tenants-factsheet.pdf", "HCD: Renter Protections"),
    ("recover_hcd",          "https://recover.hcd.ca.gov/", "ReCoverCA: Housing Program"),
]

# ── Scraper ──────────────────────────────────────────────────────────────────

@dataclass
class PageResult:
    category: str
    label: str
    url: str
    text: str = ""
    error: Optional[str] = None
    char_count: int = 0


def fetch_text(url: str, timeout: int = 15) -> tuple[str, Optional[str]]:
    """Fetch a URL and extract main-body text via trafilatura."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            config=traf_config,
        )
        if not text:
            # Fallback: strip tags with BS4
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # trim runs of blank lines
            import re
            text = re.sub(r"\n{3,}", "\n\n", text)
        return (text or "").strip(), None
    except Exception as exc:
        return "", str(exc)


def scrape_all(sources: list, delay: float = 1.5) -> list[PageResult]:
    results = []
    for i, (category, url, label) in enumerate(sources, 1):
        log.info(f"[{i}/{len(sources)}] {label}  →  {url}")
        text, err = fetch_text(url)
        result = PageResult(
            category=category,
            label=label,
            url=url,
            text=text[:12_000],          # cap at 12 k chars per page
            error=err,
            char_count=len(text),
        )
        if err:
            log.warning(f"  ERROR: {err}")
        else:
            log.info(f"  OK  ({result.char_count:,} chars)")
        results.append(result)
        if i < len(sources):
            time.sleep(delay)
    return results


# ── Topic taxonomy (used by the QA generator) ────────────────────────────────
TOPIC_DISTRIBUTION = {
    "tier_1_critical": [
        "FEMA registration and individual assistance",
        "Temporary housing and shelters",
        "How to apply for disaster aid (eligibility, deadlines)",
        "Filing insurance claims after a disaster",
        "Disaster unemployment assistance (DUA)",
    ],
    "tier_2_high_volume": [
        "SBA disaster loans for homeowners and businesses",
        "Food and water assistance (CalFresh, food banks)",
        "Power/utility restoration and outage reporting",
        "Debris and hazardous material removal",
        "Document replacement (ID, birth certificate, DMV)",
        "Tax filing extensions and disaster tax relief",
        "Wildfire-specific recovery steps",
        "Earthquake-specific recovery steps",
    ],
    "tier_3_moderate": [
        "Mental health and emotional support after a disaster",
        "Renter rights and protections after disaster damage",
        "School closures and re-opening",
        "FEMA appeals process",
        "Contractor licensing and avoiding post-disaster fraud",
        "Flood insurance and NFIP claims",
        "Medical needs, prescriptions, and hospital access",
        "Small business recovery",
    ],
    "tier_4_long_tail": [
        "Resources for undocumented / mixed-status families",
        "Livestock and large animal evacuation and recovery",
        "Pet-friendly shelters and veterinary assistance",
        "Seniors and people with disabilities — special assistance",
        "Replacing a car or vehicle damaged in disaster",
        "Internet, phone, and communications outages",
        "Workers' comp and job protection during evacuation",
        "Agricultural disaster relief for farmers",
        "Emotional support for children after a disaster",
        "Long-term recovery: rebuilding permits and zoning",
        "Donated goods and volunteer coordination",
        "Water quality testing after flooding",
        "Mold remediation guidance",
    ],
}


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting scrape …")
    pages = scrape_all(SOURCES)

    ok = [p for p in pages if not p.error]
    failed = [p for p in pages if p.error]
    log.info(f"\nScrape complete: {len(ok)} OK, {len(failed)} failed")

    if failed:
        log.warning("Failed URLs:")
        for p in failed:
            log.warning(f"  {p.url}  →  {p.error}")

    output = {
        "topic_distribution": TOPIC_DISTRIBUTION,
        "pages": [asdict(p) for p in pages],
        "stats": {
            "total": len(pages),
            "successful": len(ok),
            "failed": len(failed),
            "total_chars": sum(p.char_count for p in ok),
        },
    }

    out_path = "scraped_content.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log.info(f"Saved → {out_path}  ({output['stats']['total_chars']:,} total chars)")
