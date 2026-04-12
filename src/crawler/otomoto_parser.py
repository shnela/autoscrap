# -*- coding: utf-8 -*-
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.utils.dateparse import parse_datetime

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(?P<json>.+?)</script>',
    re.DOTALL,
)
_PUBLIC_SLUG_RE = re.compile(r"-(ID[a-zA-Z0-9]+)\.html")


def extract_next_data(html):
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return None
    return json.loads(m["json"])


def find_advert_search(next_data):
    if not next_data:
        return None
    urql = next_data.get("props", {}).get("pageProps", {}).get("urqlState") or {}
    for entry in urql.values():
        raw = entry.get("data")
        if not raw or "advertSearch" not in raw:
            continue
        payload = json.loads(raw)
        return payload.get("advertSearch")
    return None


def normalized_listing_url(url):
    """Strip `page` so pagination always starts from a consistent base query."""
    parts = urlparse(url)
    q = parse_qs(parts.query, keep_blank_values=True)
    q.pop("page", None)
    query = urlencode(sorted((k, v) for k, vals in q.items() for v in vals), doseq=True)
    return urlunparse(parts._replace(query=query))


def listing_url_for_page(base_url, page):
    parts = urlparse(base_url)
    q = parse_qs(parts.query, keep_blank_values=True)
    if page and page > 1:
        q["page"] = [str(page)]
    else:
        q.pop("page", None)
    query = urlencode(sorted((k, v) for k, vals in q.items() for v in vals), doseq=True)
    return urlunparse(parts._replace(query=query))


def public_slug_from_url(url):
    m = _PUBLIC_SLUG_RE.search(url or "")
    return m.group(1) if m else ""


def _param_raw(parameters_dict, key):
    if not parameters_dict:
        return None, None
    entry = parameters_dict.get(key)
    if not entry:
        return None, None
    values = entry.get("values") or []
    if not values:
        return None, None
    first = values[0]
    return first.get("value"), first.get("label")


def _int_from_value(raw):
    if raw is None or raw == "":
        return None
    try:
        return int(str(raw).replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _bool_from_otomoto(raw):
    if raw is None:
        return None
    s = str(raw).lower()
    if s in ("1", "true"):
        return True
    if s in ("0", "false"):
        return False
    return None


def _parse_dt(value):
    if not value:
        return None
    return parse_datetime(str(value))


def _clean_vin(raw):
    if not raw:
        return ""
    s = str(raw).strip().upper()
    if len(s) == 17 and re.match(r"^[A-HJ-NPR-Z0-9]{17}$", s):
        return s
    return ""


def advert_to_car_offer_dict(advert):
    """Map Otomoto `advert` object from __NEXT_DATA__ to unified CarOffer field names."""
    pd = advert.get("parametersDict") or {}

    def p(key):
        return _param_raw(pd, key)

    make_val, make_label = p("make")
    model_val, model_label = p("model")
    mileage_raw, _ = p("mileage")
    year_raw, _ = p("year")
    engine_cc_raw, _ = p("engine_capacity")
    power_raw, _ = p("engine_power")
    doors_raw, _ = p("door_count")
    seats_raw, _ = p("nr_seats")
    vin_raw, _ = p("vin")
    _, reg_label = p("date_registration")

    price = advert.get("price") or {}
    price_value = price.get("value")
    try:
        price_amount = Decimal(str(price_value)) if price_value not in (None, "") else None
    except (InvalidOperation, TypeError, ValueError):
        price_amount = None

    seller = advert.get("seller") or {}
    location = seller.get("location")

    images = advert.get("images") or {}
    photos = images.get("photos") or []
    image_urls = []
    for ph in photos[:50]:
        u = ph.get("url") or ph.get("id")
        if u:
            image_urls.append(u)

    url = advert.get("url") or ""

    return {
        "source": "otomoto",
        "external_listing_id": str(advert.get("id") or "")[:64],
        "public_slug": public_slug_from_url(url),
        "url": url,
        "title": (advert.get("title") or "")[:512],
        "description": advert.get("description") or "",
        "price_amount": price_amount,
        "price_currency": (price.get("currency") or "PLN")[:8],
        "price_labels": list(price.get("labels") or []),
        "price_drop": advert.get("priceDrop"),
        "year": _int_from_value(year_raw),
        "mileage_km": _int_from_value(mileage_raw),
        "engine_cc": _int_from_value(engine_cc_raw),
        "engine_power_hp": _int_from_value(power_raw),
        "fuel_type": (p("fuel_type")[1] or "")[:64],
        "gearbox": (p("gearbox")[1] or "")[:64],
        "transmission": (p("transmission")[1] or "")[:128],
        "body_type": (p("body_type")[1] or "")[:64],
        "color": (p("color")[1] or "")[:64],
        "doors": _int_from_value(doors_raw),
        "seats": _int_from_value(seats_raw),
        "make": (make_label or "")[:128],
        "make_slug": (make_val or "")[:128],
        "model": (model_label or "")[:128],
        "model_slug": (model_val or "")[:128],
        "vin": _clean_vin(vin_raw)[:17],
        "country_origin": (p("country_origin")[1] or "")[:128],
        "date_registration": (reg_label or "")[:128],
        "damaged": _bool_from_otomoto(p("damaged")[0]),
        "no_accident": _bool_from_otomoto(p("no_accident")[0]),
        "registered": _bool_from_otomoto(p("registered")[0]),
        "service_record": _bool_from_otomoto(p("service_record")[0]),
        "vat": (p("vat")[1] or "")[:64],
        "new_used": (p("new_used")[1] or "")[:32],
        "seller_type": (seller.get("type") or "")[:32],
        "seller_name": (seller.get("name") or "")[:256],
        "seller_otomoto_id": str(seller.get("id") or "")[:32],
        "seller_uuid": str(seller.get("uuid") or "")[:64],
        "seller_url": (seller.get("sellerUrl") or "")[:1024],
        "seller_website": (seller.get("website") or "")[:1024],
        "seller_location": location,
        "image_urls": image_urls,
        "main_features": list(advert.get("mainFeatures") or []),
        "listing_created_at": _parse_dt(advert.get("createdAt")),
        "listing_updated_at": _parse_dt(advert.get("updatedAt")),
        "raw_payload": advert,
    }
