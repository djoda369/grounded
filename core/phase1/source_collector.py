from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from core.phase1.ingestion import normalize_text

SOURCE_TYPE_KEYS = (
    "website",
    "manual_links",
    "search",
    "reddit",
    "youtube",
    "reviews",
    "social_links",
)

PRIORITY_PATH_TERMS = (
    "about",
    "purpose",
    "mission",
    "impact",
    "sustainability",
    "esg",
    "responsibility",
    "products",
    "brand",
    "values",
)

SITEMAP_PATHS = (
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
)

COMMON_PRIORITY_PATHS = (
    "/about",
    "/about-us",
    "/purpose",
    "/mission",
    "/impact",
    "/sustainability",
    "/esg",
    "/responsibility",
    "/products",
    "/brands",
    "/our-story",
    "/values",
)

LOW_QUALITY_TITLE_TERMS = (
    "access denied",
    "captcha",
    "checking your browser",
    "hang tight",
    "just a moment",
    "one more step",
    "routing to checkout",
    "temporarily unavailable",
)

LOW_QUALITY_TEXT_TERMS = (
    "enable javascript",
    "checking your browser",
    "please verify you are human",
    "routing to checkout",
    "temporarily unavailable",
    "we should be up and moving shortly",
)

SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
}


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content_type: str
    body: str


class ExtractingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._tag_stack: list[str] = []
        self._current_link: str | None = None
        self._current_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("href"):
            self._current_link = attrs_dict["href"]
            self._current_link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link:
            self.links.append((self._current_link, normalize_text(" ".join(self._current_link_text))))
            self._current_link = None
            self._current_link_text = []
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index] == tag:
                del self._tag_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        active = self._tag_stack[-1] if self._tag_stack else ""
        if active in {"script", "style", "noscript", "svg"}:
            return
        if "title" in self._tag_stack:
            self.title_parts.append(data.strip())
        else:
            self.text_parts.append(data.strip())
        if self._current_link is not None:
            self._current_link_text.append(data.strip())


def parse_source_settings(settings: Any) -> dict[str, Any]:
    raw = settings if isinstance(settings, dict) else {}
    max_sources = raw.get("maxSources", 5)
    if max_sources not in (3, 5, 10):
        max_sources = 5
    enabled_raw = raw.get("enabledSourceTypes")
    enabled = {
        key: bool(enabled_raw.get(key, key in {"website", "manual_links"}))
        if isinstance(enabled_raw, dict)
        else key in {"website", "manual_links"}
        for key in SOURCE_TYPE_KEYS
    }
    return {"maxSources": max_sources, "enabledSourceTypes": enabled}


def validate_public_website_url(url: str) -> str:
    normalized = normalize_input_url(url)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("website_url must use http or https.")
    if not parsed.netloc or not parsed.hostname:
        raise ValueError("website_url must include a valid host.")
    if parsed.username or parsed.password:
        raise ValueError("website_url must not include credentials.")
    host = parsed.hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("website_url must be a public website URL.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return normalized
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        raise ValueError("website_url must be a public website URL.")
    return normalized


def normalize_input_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        raise ValueError("website_url is required.")
    if re.match(r"^[a-z][a-z0-9+.-]*://", value, flags=re.IGNORECASE) and not re.match(
        r"^https?://",
        value,
        flags=re.IGNORECASE,
    ):
        return value
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        value = f"https://{value}"
    value, _ = urldefrag(value)
    return value


def extract_html(html: str) -> dict[str, Any]:
    parser = ExtractingHTMLParser()
    parser.feed(html)
    title = normalize_text(" ".join(parser.title_parts))
    text = normalize_text("\n".join(parser.text_parts))
    return {"title": title, "text": text, "links": parser.links}


def default_fetcher(url: str, timeout: float = 8.0) -> FetchResult:
    request = Request(
        url,
        headers={
            "User-Agent": "Grounded-Gaia-Onboarding/1.0 (+https://grounded.world)",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(1_500_000)
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="ignore")
            return FetchResult(
                url=response.geturl(),
                status=int(response.status),
                content_type=content_type,
                body=body,
            )
    except HTTPError as exc:
        body = exc.read(200_000).decode("utf-8", errors="ignore")
        return FetchResult(url=url, status=int(exc.code), content_type=exc.headers.get("Content-Type", ""), body=body)
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def collect_sources(
    website_url: str,
    source_settings: Any = None,
    manual_links: Any = None,
    fetcher: Callable[[str], FetchResult] | None = None,
    now: Callable[[], datetime] | None = None,
) -> list[dict[str, Any]]:
    settings = parse_source_settings(source_settings)
    enabled = settings["enabledSourceTypes"]
    max_sources = int(settings["maxSources"])
    fetch = fetcher or default_fetcher
    clock = now or (lambda: datetime.now(timezone.utc))
    root_url = validate_public_website_url(website_url)
    root_host = urlparse(root_url).hostname or ""
    ledger: list[dict[str, Any]] = []
    seen: set[str] = set()

    def timestamp() -> str:
        return clock().isoformat()

    def add_skipped(url: str, source_type: str, reason: str) -> None:
        canonical = canonicalize_url(url)
        if canonical in seen:
            return
        seen.add(canonical)
        ledger.append(
            {
                "url": canonical,
                "type": source_type,
                "title": "",
                "fetched_at": timestamp(),
                "status": "skipped",
                "excerpt": "",
                "error": reason,
            }
        )

    def fetch_entry(url: str, source_type: str) -> dict[str, Any] | None:
        canonical = canonicalize_url(url)
        if canonical in seen:
            return None
        seen.add(canonical)
        try:
            result = fetch(canonical)
        except Exception as exc:
            return {
                "url": canonical,
                "type": source_type,
                "title": "",
                "fetched_at": timestamp(),
                "status": "error",
                "excerpt": "",
                "error": str(exc),
            }
        content_type = result.content_type.lower()
        if result.status >= 400:
            return {
                "url": canonical,
                "type": source_type,
                "title": "",
                "fetched_at": timestamp(),
                "status": "skipped",
                "excerpt": "",
                "error": f"HTTP {result.status}",
            }
        if "html" not in content_type and "text/plain" not in content_type and content_type:
            return {
                "url": canonical,
                "type": source_type,
                "title": "",
                "fetched_at": timestamp(),
                "status": "skipped",
                "excerpt": "",
                "error": f"Unsupported content type: {result.content_type}",
            }
        extracted = extract_html(result.body)
        title = extracted["title"]
        text = extracted["text"]
        if len(text) < 80:
            return {
                "url": canonical,
                "type": source_type,
                "title": title,
                "fetched_at": timestamp(),
                "status": "skipped",
                "excerpt": text,
                "error": "No usable page text found.",
            }
        quality_issue = low_quality_reason(title, text)
        if quality_issue:
            return {
                "url": canonical,
                "type": source_type,
                "title": title,
                "fetched_at": timestamp(),
                "status": "skipped",
                "excerpt": text[:500],
                "error": quality_issue,
            }
        return {
            "url": canonical,
            "type": source_type,
            "title": title or canonical,
            "fetched_at": timestamp(),
            "status": "ok",
            "excerpt": text[:5000],
            "error": "",
            "links": extracted["links"],
        }

    def add_link_candidates(
        entry: dict[str, Any] | None,
        base_url: str,
        crawl_candidates: list[tuple[int, str]],
        social_candidates: list[str],
    ) -> None:
        if not entry or entry.get("status") != "ok":
            return
        for href, label in entry.get("links", []):
            absolute = canonicalize_url(urljoin(base_url, href))
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            host = parsed.hostname or ""
            if same_domain(host, root_host):
                crawl_candidates.append((priority_score(absolute, label), absolute))
            elif is_social_or_media(host):
                social_candidates.append(absolute)

    def sitemap_candidates() -> list[str]:
        candidates: list[str] = []
        parsed_root = urlparse(root_url)
        origin = f"{parsed_root.scheme}://{parsed_root.netloc}"
        for path in SITEMAP_PATHS:
            sitemap_url = canonicalize_url(urljoin(origin, path))
            try:
                result = fetch(sitemap_url)
            except Exception:
                continue
            if result.status >= 400:
                continue
            candidates.extend(extract_sitemap_urls(result.body, root_host))
        return candidates

    if enabled["website"]:
        root_entry = fetch_entry(root_url, "website")
        if root_entry:
            ledger.append(public_entry(root_entry))
        crawl_candidates: list[tuple[int, str]] = []
        social_candidates: list[str] = []
        add_link_candidates(root_entry, root_url, crawl_candidates, social_candidates)
        for url in sitemap_candidates():
            crawl_candidates.append((priority_score(url, ""), url))
        for path in COMMON_PRIORITY_PATHS:
            crawl_candidates.append((priority_score(path, ""), urljoin(root_url, path)))

        attempts = 0
        queue = sorted((score, canonicalize_url(url)) for score, url in crawl_candidates)
        queued: set[str] = set()
        while queue and ok_source_count(ledger) < max_sources and attempts < max_sources * 8:
            _, url = queue.pop(0)
            canonical = canonicalize_url(url)
            if canonical in queued:
                continue
            queued.add(canonical)
            attempts += 1
            if ok_source_count(ledger) >= max_sources:
                break
            entry = fetch_entry(canonical, "website")
            if entry:
                ledger.append(public_entry(entry))
                nested_candidates: list[tuple[int, str]] = []
                add_link_candidates(entry, canonical, nested_candidates, social_candidates)
                for item in nested_candidates:
                    queue.append(item)
                queue.sort(key=lambda item: item[0])

        if enabled["social_links"]:
            for url in dedupe_urls(social_candidates)[: max_sources]:
                if ok_source_count(ledger) >= max_sources:
                    break
                entry = fetch_entry(url, infer_external_type(url))
                if entry:
                    ledger.append(public_entry(entry))
        elif social_candidates:
            add_skipped("social-links:detected", "social_links", "Social links detected but disabled in source settings.")
    else:
        add_skipped(root_url, "website", "Website sources disabled in source settings.")

    if enabled["manual_links"]:
        for link in normalize_manual_links(manual_links):
            if ok_source_count(ledger) >= max_sources:
                break
            try:
                normalized = validate_public_website_url(link)
            except ValueError as exc:
                add_skipped(str(link), "manual_links", str(exc))
                continue
            entry = fetch_entry(normalized, "manual_links")
            if entry:
                ledger.append(public_entry(entry))

    for source_type in ("search", "reviews"):
        if enabled[source_type]:
            add_skipped(f"{source_type}:{root_host}", source_type, "Public API integration is not configured in this MVP.")

    for source_type, domain_label in (("reddit", "reddit.com"), ("youtube", "youtube.com")):
        if enabled[source_type] and not any(entry["type"] == source_type for entry in ledger):
            add_skipped(f"{source_type}:{root_host}", source_type, f"No public {domain_label} link was discovered from the submitted website.")

    return dedupe_ledger(ledger)


def public_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in entry.items() if key != "links"}


def canonicalize_url(url: str) -> str:
    value, _ = urldefrag(str(url or "").strip())
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower(), path=path).geturl()
    return value


def same_domain(host: str, root_host: str) -> bool:
    host = host.lower().removeprefix("www.")
    root = root_host.lower().removeprefix("www.")
    return host == root


def is_social_or_media(host: str) -> bool:
    normalized = host.lower().removeprefix("www.")
    return normalized in SOCIAL_DOMAINS or normalized.endswith(".youtube.com") or normalized == "youtube.com" or normalized.endswith(".reddit.com") or normalized == "reddit.com"


def infer_external_type(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "reddit.com" in host:
        return "reddit"
    return "social_links"


def low_quality_reason(title: str, text: str) -> str:
    combined_title = title.lower()
    combined_text = text.lower()[:1500]
    if any(term in combined_title for term in LOW_QUALITY_TITLE_TERMS):
        return "Low-quality blocker, queue, or splash page detected."
    if any(term in combined_text for term in LOW_QUALITY_TEXT_TERMS):
        return "Low-quality blocker, queue, or splash page detected."
    return ""


def extract_sitemap_urls(xml: str, root_host: str) -> list[str]:
    urls = re.findall(r"<loc>\s*([^<]+)\s*</loc>", xml, flags=re.IGNORECASE)
    output: list[str] = []
    for url in urls:
        canonical = canonicalize_url(url)
        parsed = urlparse(canonical)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if same_domain(parsed.hostname, root_host):
            output.append(canonical)
    return dedupe_urls(output)


def priority_score(url: str, label: str) -> int:
    haystack = f"{url} {label}".lower()
    for index, term in enumerate(PRIORITY_PATH_TERMS):
        if term in haystack:
            return index
    return 100


def normalize_manual_links(manual_links: Any) -> list[str]:
    if manual_links is None:
        return []
    if isinstance(manual_links, str):
        return [line.strip() for line in manual_links.splitlines() if line.strip()]
    if isinstance(manual_links, list):
        return [str(item).strip() for item in manual_links if str(item).strip()]
    return []


def ok_source_count(ledger: list[dict[str, Any]]) -> int:
    return sum(1 for entry in ledger if entry.get("status") == "ok")


def dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for url in urls:
        canonical = canonicalize_url(url)
        if canonical in seen:
            continue
        seen.add(canonical)
        output.append(canonical)
    return output


def dedupe_ledger(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for entry in ledger:
        key = (str(entry.get("url", "")), str(entry.get("type", "")))
        if key in seen:
            continue
        seen.add(key)
        output.append(entry)
    return output


def ledger_to_documents(ledger: list[dict[str, Any]]) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for entry in ledger:
        if entry.get("status") != "ok" or not str(entry.get("excerpt", "")).strip():
            continue
        documents.append(
            {
                "source": str(entry.get("url") or entry.get("title") or "web source"),
                "kind": str(entry.get("type") or "website"),
                "text": "\n".join(
                    part
                    for part in (
                        str(entry.get("title") or ""),
                        str(entry.get("excerpt") or ""),
                    )
                    if part
                ),
            }
        )
    return documents


def infer_company_name(website_url: str, ledger: list[dict[str, Any]]) -> str:
    for entry in ledger:
        title = str(entry.get("title") or "").strip()
        if title and not low_quality_reason(title, str(entry.get("excerpt") or "")):
            return re.split(r"\s+[|-]\s+|:", title, maxsplit=1)[0].strip()[:80] or title[:80]
    host = (urlparse(website_url).hostname or "Company").removeprefix("www.")
    return host.split(".")[0].replace("-", " ").title()


def suggest_competitors(company_profile: dict[str, Any], website_url: str, source_ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    company_name = str(company_profile.get("market") or company_profile.get("brand") or infer_company_name(website_url, source_ledger))
    brand = str(company_profile.get("brand") or company_name).lower()
    source_text = "\n".join(str(entry.get("excerpt") or "") for entry in source_ledger if entry.get("status") == "ok")
    names = extract_competitor_names(source_text, {brand, company_name.lower()})
    if not names:
        names = category_fallback_names(source_text, company_name)
    suggestions: list[dict[str, Any]] = []
    ok_links = [str(entry.get("url")) for entry in source_ledger if entry.get("status") == "ok" and entry.get("url")]
    for index, name in enumerate(names[:6], start=1):
        confidence = max(45, 82 - index * 7)
        suggestions.append(
            {
                "name": name,
                "selected": False,
                "confidence": confidence,
                "rationale": f"{name} appears relevant to benchmark against {company_name} based on category, positioning, or adjacent public-source language.",
                "source_links": ok_links[:3],
            }
        )
    return suggestions


def extract_competitor_names(text: str, exclusions: set[str]) -> list[str]:
    candidates: list[str] = []
    patterns = (
        r"(?:competitors?|alternatives?|rivals?|alongside|including)\s+([^.\n]{5,180})",
        r"(?:brands such as|brands like)\s+([^.\n]{5,180})",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidates.extend(split_candidate_names(match.group(1)))
    output: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        normalized = re.sub(r"\s+", " ", name).strip(" ,;:()")
        key = normalized.lower()
        if len(normalized) < 3 or key in exclusions or key in seen:
            continue
        if len(normalized.split()) > 5:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def split_candidate_names(value: str) -> list[str]:
    cleaned = re.sub(r"\band\b", ",", value, flags=re.IGNORECASE)
    parts = re.split(r",|/|;|\|", cleaned)
    names: list[str] = []
    for part in parts:
        matches = re.findall(r"\b[A-Z][A-Za-z0-9&'.-]*(?:\s+[A-Z][A-Za-z0-9&'.-]*){0,3}", part.strip())
        names.extend(matches or [part.strip()])
    return names


def category_fallback_names(text: str, company_name: str) -> list[str]:
    lower = text.lower()
    if any(term in lower for term in ("yogurt", "yoghurt", "dairy", "milk")):
        return ["Danone", "Muller", "Arla Foods", "Yeo Valley"]
    if any(term in lower for term in ("fashion", "apparel", "clothing")):
        return ["Patagonia", "Everlane", "Levi Strauss", "Nike"]
    if any(term in lower for term in ("coffee", "beverage", "drink")):
        return ["Nestle", "Starbucks", "PepsiCo", "Coca-Cola"]
    host = (urlparse(company_name).hostname or "").replace("www.", "")
    return [name for name in ("Category Leader", "Purpose-Led Challenger", "Mainstream Incumbent") if name.lower() not in host]
