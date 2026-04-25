# -*- coding: utf-8 -*-
import json
import re
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from offers.feature_inference import infer_from_autoscout_listing_details
from offers.models import OfferListingAvailability

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(?P<json>.+?)</script>',
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_ENGINE_BADGE_RE = re.compile(r"\b([TDB][2-8])\b", re.I)


def extract_next_data(html):
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return None
    return json.loads(m["json"])


def html_to_text(html):
    if not html:
        return ""
    t = _TAG_RE.sub("\n", html)
    return "\n".join(line.strip() for line in t.splitlines() if line.strip())


def _int_or_none(val):
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _decimal_or_none(val):
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _clean_vin(raw):
    if not raw:
        return ""
    s = str(raw).strip().upper()
    if len(s) == 17 and re.match(r"^[A-HJ-NPR-Z0-9]{17}$", s):
        return s
    return ""


def _text_value(val):
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        for key in ("formatted", "label", "value", "name"):
            v = val.get(key)
            if v:
                return str(v)
    return str(val)


def _upholstery_color_from_vehicle(vehicle):
    for key in (
        "upholsteryColor",
        "upholsteryColour",
        "interiorColor",
        "interiorColour",
        "seatColor",
        "seatColour",
    ):
        txt = _text_value(vehicle.get(key)).strip()
        if txt:
            return txt[:64]
    return ""


def _engine_model_from_vehicle(vehicle):
    for key in (
        "engineModel",
        "engineCode",
        "engineType",
        "engineVariant",
        "motorCode",
    ):
        txt = _text_value(vehicle.get(key)).strip()
        if txt:
            return txt[:128]
    return ""


def _extract_engine_badge(*texts):
    for text in texts:
        if not text:
            continue
        m = _ENGINE_BADGE_RE.search(str(text).upper())
        if m:
            return m.group(1).upper()
    return ""


def _wheel_size_from_vehicle(vehicle):
    def _normalize_wheel_size(raw):
        if not raw:
            return ""
        s = str(raw).strip()
        m = re.search(r"\b(1[4-9]|2[0-4])\b", s)
        if not m:
            m = re.search(r"\b(\d{2})[\"′”]?\b", s)
        if m:
            return '{}"'.format(int(m.group(1)))
        return ""

    for key in (
        "wheelSize",
        "rimSize",
        "wheelRimSize",
        "tyreSize",
    ):
        txt = _text_value(vehicle.get(key)).strip()
        if txt:
            normalized = _normalize_wheel_size(txt)
            if normalized:
                return normalized
    return ""


def _listing_location_text(location):
    if not isinstance(location, dict):
        return ""
    parts = []
    for key in ("city", "zip", "state", "countryCode"):
        value = location.get(key)
        if value:
            parts.append(str(value).strip())
    if not parts:
        for key in ("addressLine1", "address"):
            value = location.get(key)
            if value:
                parts.append(str(value).strip())
                break
    return ", ".join(p for p in parts if p)[:256]


def parse_listing_page(html):
    """Return (listings, number_of_pages, current_page) from a /lst/ page."""
    data = extract_next_data(html)
    if not data:
        return None, 0, 1
    pp = data.get("props", {}).get("pageProps", {})
    listings = pp.get("listings") or []
    pages = int(pp.get("numberOfPages") or 0)
    q = data.get("query") or {}
    cur = int(q.get("page") or 1)
    return listings, pages, cur


def listing_details_to_offer_dict(listing_details, marketplace_domain="autoscout24.com"):
    """Map `listingDetails` from offer page __NEXT_DATA__ to unified CarOffer fields."""
    if not listing_details:
        return {}

    lid = listing_details.get("id") or ""
    rel = listing_details.get("webPage") or listing_details.get("url") or ""
    if rel.startswith("http"):
        url = rel
    else:
        url = "https://www.{}{}".format(
            marketplace_domain,
            rel if rel.startswith("/") else "/{}".format(rel),
        )

    vehicle = listing_details.get("vehicle") or {}
    prices = listing_details.get("prices") or {}
    pub = prices.get("public") or {}

    price_raw = pub.get("priceRaw")
    price_amount = _decimal_or_none(price_raw)

    mileage_raw = vehicle.get("mileageInKmRaw")
    mileage_km = _int_or_none(mileage_raw)

    fr_raw = vehicle.get("firstRegistrationDateRaw") or ""
    first_registration_date = None
    if fr_raw:
        first_registration_date = parse_date(str(fr_raw)[:10])

    fuel_cat = vehicle.get("fuelCategory") or {}
    fuel_type = (fuel_cat.get("formatted") or "")[:64]

    fc = vehicle.get("fuelConsumptionCombined") or {}
    fuel_l100 = _decimal_or_none(fc.get("raw"))

    co2 = vehicle.get("co2emissionInGramPerKmWithFallback") or {}
    co2_g = _int_or_none(co2.get("raw"))

    ident = vehicle.get("identifier") or {}
    vin = _clean_vin(ident.get("vin"))[:17]

    gears_n = _int_or_none(vehicle.get("gears"))

    seller = listing_details.get("seller") or {}
    seller_links = seller.get("links")

    loc = listing_details.get("location")

    images = listing_details.get("images") or []
    image_urls = [u for u in images if isinstance(u, str)]

    mv = (
        vehicle.get("modelVersionInput")
        or vehicle.get("variant")
        or ""
    )
    title = " ".join(
        p
        for p in (
            vehicle.get("make"),
            vehicle.get("model"),
            mv,
        )
        if p
    ).strip()[:512]

    prev_owners = vehicle.get("noOfPreviousOwners")
    if prev_owners is not None and prev_owners != "":
        prev_owners = _int_or_none(prev_owners)
    else:
        prev_owners = None

    listing_created_at = parse_datetime(listing_details.get("createdTimestampWithOffset") or "")

    base = {
        "source": "autoscout24",
        "external_listing_id": str(lid)[:64],
        "url": url[:1024],
        "title": title or (listing_details.get("id") or "AutoScout24")[:512],
        "description": html_to_text(listing_details.get("description") or ""),
        "price_amount": price_amount,
        "price_currency": "EUR",
        "price_display": (pub.get("price") or "")[:64],
        "price_tax_deductible": pub.get("taxDeductible"),
        "mileage_km": mileage_km,
        "first_registration_raw": (vehicle.get("firstRegistrationDate") or "")[:32],
        "first_registration_date": first_registration_date,
        "year": _int_or_none(vehicle.get("productionYear")),
        "fuel_type": fuel_type,
        "wheel_size": _wheel_size_from_vehicle(vehicle),
        "engine_model": (
            _engine_model_from_vehicle(vehicle)
            or _extract_engine_badge(
                title,
                vehicle.get("modelVersionInput"),
                vehicle.get("variant"),
                listing_details.get("description"),
                listing_details.get("url"),
                listing_details.get("webPage"),
            )
        ),
        "transmission": (vehicle.get("transmissionType") or "")[:64],
        "drive_train": (vehicle.get("driveTrain") or "")[:64],
        "body_type": (vehicle.get("bodyType") or "")[:64],
        "color": (vehicle.get("bodyColor") or "")[:64],
        "upholstery_color": _upholstery_color_from_vehicle(vehicle),
        "paint_type": (vehicle.get("paintType") or "")[:64],
        "doors": _int_or_none(vehicle.get("numberOfDoors")),
        "seats": _int_or_none(vehicle.get("numberOfSeats")),
        "engine_cc": _int_or_none(vehicle.get("rawDisplacementInCCM")),
        "engine_power_hp": _int_or_none(vehicle.get("rawPowerInHp")),
        "engine_power_kw": _int_or_none(vehicle.get("rawPowerInKw")),
        "gears": gears_n,
        "co2_g_km": co2_g,
        "fuel_consumption_l100km_combined": fuel_l100,
        "make": (vehicle.get("make") or "")[:128],
        "model": (vehicle.get("model") or "")[:128],
        "model_version": (vehicle.get("modelVersionInput") or "")[:256],
        "variant": (vehicle.get("variant") or "")[:128],
        "vin": vin,
        "had_accident": vehicle.get("hadAccident"),
        "has_full_service_history": vehicle.get("hasFullServiceHistory"),
        "non_smoking": vehicle.get("nonSmoking"),
        "previous_owners": prev_owners,
        "next_inspection_raw": (vehicle.get("nextVehicleSafetyInspection") or "")[:32],
        "seller_type": (seller.get("type") or "")[:32],
        "seller_name": (seller.get("companyName") or "")[:256],
        "seller_contact": (seller.get("contactName") or "")[:256],
        "seller_as24_id": str(seller.get("id") or "")[:32],
        "seller_sell_id": str(seller.get("sellId") or "")[:32],
        "seller_is_dealer": seller.get("isDealer"),
        "seller_links": seller_links,
        "listing_location": _listing_location_text(loc),
        "seller_location": loc,
        "image_urls": image_urls[:60],
        "listing_created_at": listing_created_at,
        "raw_payload": listing_details,
    }
    base.update(infer_from_autoscout_listing_details(listing_details))
    base["listing_availability"] = OfferListingAvailability.ACTIVE
    base["listing_checked_at"] = timezone.now()
    return base
