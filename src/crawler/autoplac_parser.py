# -*- coding: utf-8 -*-
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from parsel import Selector

from offers.feature_inference import infer_features_from_text
from offers.models import OfferListingAvailability

_AUTOPLAC_BASE_URL = "https://autoplac.pl"
_TAG_RE = re.compile(r"<[^>]+>")
_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def _text(val):
    return str(val or "").strip()


def _html_to_text(html):
    if not html:
        return ""
    t = _TAG_RE.sub("\n", str(html))
    return "\n".join(line.strip() for line in t.splitlines() if line.strip())


def _int_or_none(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _decimal_or_none(val):
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _clean_vin(v):
    s = _text(v).upper()
    return s if _VIN_RE.match(s) else ""


def _map_seller_type(source_type_display):
    s = _text(source_type_display).lower()
    if not s:
        return ""
    if "prywat" in s:
        return "private"
    if "dealer" in s or "komis" in s or "integrator" in s or "firma" in s:
        return "dealer"
    return s[:32]


def _extract_embedded_cache(html):
    sel = Selector(text=html)
    raw = sel.css('script[type="application/json"]::text').get()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def parse_listing_page(html, base_url=_AUTOPLAC_BASE_URL):
    """
    Return (offer_urls, next_page_url) from listing HTML.
    """
    offer_urls = []
    seen = set()

    cache = _extract_embedded_cache(html) or {}
    for entry in cache.values():
        if not isinstance(entry, dict):
            continue
        body = entry.get("body") or {}
        if not isinstance(body, dict):
            continue
        offer_list = body.get("offerList") or []
        for item in offer_list:
            if not isinstance(item, dict):
                continue
            offer = item.get("offer") or {}
            rel = offer.get("webUrl")
            if not rel:
                continue
            abs_url = urljoin(base_url, rel)
            if abs_url in seen:
                continue
            seen.add(abs_url)
            offer_urls.append(abs_url)

    sel = Selector(text=html)
    for rel in sel.css('a[href*="/oferta/"]::attr(href)').getall():
        abs_url = urljoin(base_url, rel)
        if "/oferta/" not in abs_url or abs_url in seen:
            continue
        seen.add(abs_url)
        offer_urls.append(abs_url)

    next_rel = sel.css('a[rel="next"]::attr(href)').get()
    next_page_url = urljoin(base_url, next_rel) if next_rel else None
    return offer_urls, next_page_url


def parse_offer_page(html):
    """
    Return offer payload from embedded app JSON cache (`body.offer`).
    """
    cache = _extract_embedded_cache(html) or {}
    for key, entry in cache.items():
        if not str(key).startswith("https://api.autoplac.pl/offer/"):
            continue
        if not isinstance(entry, dict):
            continue
        body = entry.get("body") or {}
        offer = body.get("offer")
        if isinstance(offer, dict):
            return offer, body
    return None, None


def offer_to_car_offer_dict(offer, body, page_url):
    if not offer:
        return {}

    price_info = offer.get("priceInfo") or {}
    primary_price = price_info.get("primary") or {}
    location = offer.get("locationInfo") or {}

    listing_url = _text(offer.get("webUrl"))
    if listing_url and not listing_url.startswith("http"):
        listing_url = urljoin(_AUTOPLAC_BASE_URL, listing_url)
    if not listing_url:
        listing_url = page_url

    photos = body.get("photoList") or []
    image_urls = []
    for p in photos:
        if not isinstance(p, dict):
            continue
        u = p.get("url") or p.get("webpUrl") or p.get("miniatureUrl")
        if u:
            image_urls.append(str(u))

    equipment = offer.get("equipment") or []
    equipment_text = " ".join(_text(x) for x in equipment if _text(x))

    title = _text(offer.get("title"))[:512]
    description = _html_to_text(offer.get("description"))
    drive_train = _text(offer.get("driveTypeText"))
    transmission = _text(offer.get("transmissionTypeText"))
    model_line = " ".join(
        p
        for p in (
            _text(offer.get("brand")),
            _text(offer.get("model")),
            _text(offer.get("version")),
        )
        if p
    )
    inferred = infer_features_from_text(
        title=title,
        description=description,
        equipment_text=equipment_text,
        main_features_text="",
        drive_train=drive_train,
        transmission=transmission,
        model_line=model_line,
    )

    first_registration_raw = _text(offer.get("firstRegistrationDate"))[:32]
    first_registration_date = parse_date(first_registration_raw[:10]) if first_registration_raw else None
    listing_updated_at = parse_datetime(_text(offer.get("updateTime")))

    city = _text(location.get("city"))
    district = _text(location.get("districtName"))
    voivodeship = _text(location.get("voivodeshipDisplay") or location.get("voivodeshipName"))
    country = _text(location.get("locationCountryName"))
    location_parts = [p for p in (city, district, voivodeship, country) if p]

    base = {
        "source": "autoplac",
        "external_listing_id": str(offer.get("id") or offer.get("hashedId") or "")[:64],
        "url": listing_url[:1024],
        "title": title or "Autoplac offer",
        "description": description,
        "price_amount": _decimal_or_none(primary_price.get("price") or primary_price.get("valueWithoutCurrency")),
        "price_currency": _text(price_info.get("currency") or "PLN")[:8] or "PLN",
        "price_display": _text(primary_price.get("value"))[:64],
        "price_tax_deductible": bool(price_info.get("invoiceType") and _text(price_info.get("invoiceType")) != "NONE"),
        "year": _int_or_none(offer.get("productionYear")),
        "mileage_km": _int_or_none(offer.get("mileage")),
        "engine_cc": _int_or_none(offer.get("engineCapacity")),
        "engine_power_kw": _int_or_none(offer.get("enginePowerKW")),
        "fuel_type": _text(offer.get("fuelTypeText"))[:64],
        "gearbox": transmission[:64],
        "transmission": transmission[:128],
        "drive_train": drive_train[:64],
        "body_type": _text(offer.get("bodyTypeText"))[:64],
        "color": _text(offer.get("colorText"))[:64],
        "doors": _int_or_none(offer.get("doors")),
        "seats": _int_or_none(offer.get("seats")),
        "make": _text(offer.get("brand"))[:128],
        "model": _text(offer.get("model"))[:128],
        "variant": _text(offer.get("version"))[:128],
        "vin": _clean_vin(offer.get("vin") if offer.get("vinAvailable") else "")[:17],
        "first_registration_raw": first_registration_raw,
        "first_registration_date": first_registration_date,
        "registered": offer.get("registered"),
        "previous_owners": 0 if offer.get("firstOwner") else None,
        "country_origin": _text(location.get("locationCountryName"))[:128],
        "seller_type": _map_seller_type(offer.get("sourceTypeDisplay")),
        "seller_contact": _text(offer.get("phoneNumber"))[:256],
        "seller_sell_id": str(offer.get("userId") or "")[:32],
        "seller_is_dealer": _map_seller_type(offer.get("sourceTypeDisplay")) == "dealer",
        "listing_location": ", ".join(location_parts)[:256],
        "seller_location": location,
        "image_urls": image_urls[:60],
        "main_features": list(equipment)[:200],
        "listing_updated_at": listing_updated_at,
        "raw_payload": {"offer": offer, "body": body},
        "listing_availability": OfferListingAvailability.ACTIVE,
        "listing_checked_at": timezone.now(),
    }
    base.update(inferred)
    return base
