#!/usr/bin/env python3
"""
Fetch publications from NASA ADS API and generate a YAML file for Jekyll.

This script queries the ADS API for publications associated with a given ORCID,
prioritizes peer-reviewed versions over arXiv preprints, and outputs a structured
YAML file that Jekyll can use to generate publication cards.

Requirements:
    - requests library
    - pyyaml library
    - ADS_API_KEY environment variable set

Usage:
    export ADS_API_KEY="your-api-key-here"
    python fetch_publications.py
"""

import os
import sys
from typing import Any, Dict, List

import requests
import yaml

# Configuration
ORCID = "0000-0003-3356-880X"
ADS_API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
OUTPUT_FILE = "_data/publications.yml"


def get_ads_api_key() -> str:
    """Retrieve ADS API key from environment variable."""
    api_key = os.environ.get("ADS_API_KEY")
    if not api_key:
        print(
            "Error: ADS_API_KEY environment variable not set.", file=sys.stderr
        )
        print(
            "Get your API key from: https://ui.adsabs.harvard.edu/user/settings/token",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def fetch_publications(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch publications from ADS API using ORCID.

    Returns a list of publications sorted by date (most recent first).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Query parameters
    # fl = fields to return
    params = {
        "q": f"orcid:{ORCID}",
        "fl": "title,author,year,pubdate,bibcode,doi,pub,abstract,doctype,identifier,property",
        "sort": "date desc",
        "rows": 100,  # Adjust if you have more than 100 publications
    }

    try:
        response = requests.get(ADS_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if "response" in data and "docs" in data["response"]:
            return data["response"]["docs"]
        else:
            print("Warning: Unexpected API response format", file=sys.stderr)
            return []

    except requests.exceptions.RequestException as e:
        print(f"Error fetching publications from ADS: {e}", file=sys.stderr)
        sys.exit(1)


def get_publication_url(pub: Dict[str, Any]) -> str:
    """
    Determine the best URL for a publication.
    Priority: DOI > published journal > arXiv
    """
    # Check if it's a peer-reviewed article
    properties = pub.get("property", [])
    is_refereed = "REFEREED" in properties

    # If DOI exists and it's refereed, use DOI link
    if is_refereed and pub.get("doi"):
        doi = pub["doi"][0]  # DOI is usually a list
        return f"https://doi.org/{doi}"

    # Check for direct journal links in identifiers
    identifiers = pub.get("identifier", [])

    # Look for arXiv identifier
    arxiv_id = None
    for identifier in identifiers:
        if "arXiv:" in identifier:
            arxiv_id = identifier.replace("arXiv:", "")
            break

    # If it's published (has DOI), prefer DOI even if not marked as refereed
    if pub.get("doi"):
        doi = pub["doi"][0]
        return f"https://doi.org/{doi}"

    # Try to construct URL from bibcode for journal articles
    bibcode = pub.get("bibcode", "")
    if bibcode and not bibcode.startswith("arXiv"):
        # Use ADS abstract page which will have links to journal
        return f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"

    # Fall back to arXiv if available
    if arxiv_id:
        return f"https://arxiv.org/abs/{arxiv_id}"

    # Last resort: ADS abstract page
    if bibcode:
        return f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"

    return ""


def format_authors(authors: List[str]) -> str:
    """
    Format author list for display.
    Abbreviates to first author et al. if more than 3 authors.
    """
    if not authors:
        return ""

    # Format: Last, First -> F.Last
    formatted = []
    for author in authors[:3]:
        parts = author.split(", ")
        if len(parts) == 2:
            last_name = parts[0]
            first_name = parts[1]
            # Get first initial
            initial = first_name[0] + "." if first_name else ""
            formatted.append(f"{initial}{last_name}")
        else:
            formatted.append(author)

    if len(authors) > 3:
        return ", ".join(formatted) + " et al."
    else:
        return ", ".join(formatted)


def create_short_title(title: str, max_length: int = 60) -> str:
    """Create a shortened version of the title for display."""
    if len(title) <= max_length:
        return title

    # Try to cut at a word boundary
    truncated = title[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7:  # Only cut at space if it's not too early
        truncated = truncated[:last_space]

    return truncated + "..."


def is_preprint(pub: Dict[str, Any]) -> bool:
    """Check if publication is a preprint (arXiv)."""
    bibcode = pub.get("bibcode", "")
    properties = pub.get("property", [])

    # Check if it's marked as refereed (peer-reviewed)
    is_refereed = "REFEREED" in properties

    # Check if bibcode starts with arXiv
    is_arxiv = bibcode.startswith("arXiv")

    # It's a preprint if it's arXiv and not refereed, or if it has no DOI
    return (is_arxiv or not pub.get("doi")) and not is_refereed


def process_publications(pubs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw ADS publications into formatted data for Jekyll.
    Handles deduplication (preprint vs published version).
    """
    processed = []
    seen_titles = {}  # Track publications by normalized title

    for pub in pubs:
        # Skip if no title
        if not pub.get("title"):
            continue

        title = (
            pub["title"][0] if isinstance(pub["title"], list) else pub["title"]
        )

        # Normalize title for comparison (remove spaces, lowercase)
        normalized_title = "".join(title.lower().split())

        # Check if we've seen this paper before
        if normalized_title in seen_titles:
            # If current version is published and previous was preprint, replace it
            existing_idx = seen_titles[normalized_title]
            if not is_preprint(pub) and is_preprint(processed[existing_idx]):
                # Replace preprint with published version
                processed[existing_idx] = format_publication(pub, title)
            # Otherwise, keep the first one we found (should be most recent)
            continue

        # Format and add the publication
        formatted = format_publication(pub, title)
        processed.append(formatted)
        seen_titles[normalized_title] = len(processed) - 1

    return processed


def format_publication(pub: Dict[str, Any], title: str) -> Dict[str, Any]:
    """Format a single publication for YAML output."""
    authors = pub.get("author", [])
    year = pub.get("year", "N/A")
    url = get_publication_url(pub)

    # Determine publication status
    properties = pub.get("property", [])
    is_refereed = "REFEREED" in properties
    pub_status = "published" if is_refereed else "preprint"

    # Get venue (journal or arXiv)
    venue = pub.get("pub", "arXiv")
    if isinstance(venue, list):
        venue = venue[0] if venue else "arXiv"

    return {
        "title": title,
        "short_title": create_short_title(title),
        "authors": format_authors(authors),
        "year": year,
        "url": url,
        "venue": venue,
        "status": pub_status,
        "bibcode": pub.get("bibcode", ""),
    }


def save_publications_yaml(
    publications: List[Dict[str, Any]], output_file: str
):
    """Save publications to YAML file."""
    try:
        with open(output_file, "w") as f:
            yaml.dump(
                publications,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        print(
            f"Successfully saved {len(publications)} publications to {output_file}"
        )
    except Exception as e:
        print(f"Error saving YAML file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to fetch and process publications."""
    print("Fetching publications from ADS...")

    api_key = get_ads_api_key()
    raw_publications = fetch_publications(api_key)

    print(f"Found {len(raw_publications)} total entries from ADS")

    publications = process_publications(raw_publications)

    print(f"Processed {len(publications)} unique publications (deduplicated)")

    save_publications_yaml(publications, OUTPUT_FILE)

    # Print summary
    published_count = sum(1 for p in publications if p["status"] == "published")
    preprint_count = sum(1 for p in publications if p["status"] == "preprint")

    print("\nSummary:")
    print(f"  Published papers: {published_count}")
    print(f"  Preprints: {preprint_count}")
    print(f"  Total: {len(publications)}")


if __name__ == "__main__":
    main()
