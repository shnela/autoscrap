# -*- coding: utf-8 -*-
import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from django.utils import timezone
from django.utils.dateparse import parse_date
from parsel import Selector

from offers.feature_inference import infer_features_from_text
from offers.models import OfferListingAvailability

_SUPERAUTO_BASE_URL = "https://www.superauto.pl"
_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_DETAIL_OFFER_PATH_RE = re.compile(r"^/samochody-[^/]+/osobowe/.+-\d+$", re.I)


def normalized_listing_url(url):
    parts = urlparse(url)
    q = parse_qs(parts.query, keep_blank_values=True)
    q.pop("page", None)
    query = urlencode(sorted((k, v) for k, vals in q.items() for v in vals), doseq=True)
    return urlunparse(parts._replace(query=query))


def get_offers_api_url(listing_url):
    parts = urlparse(listing_url)
    base = urlunparse((parts.scheme, parts.netloc, "", "", "", ""))
    query = urlencode(parse_qs(parts.query, keep_blank_values=True), doseq=True)
    return "{}{}{}".format(base, "/get-offers", "?{}".format(query) if query else "")


def _clean_text(value):
    return str(value or "").strip()


def _int_from_text(value):
    if value is None:
        return None
    digits = re.sub(r"[^\d]", "", str(value))
    if not digits:
        return None
    try:
        return int(digits)
    except (TypeError, ValueError):
        return None


def _decimal_from_text(value):
    if value is None:
        return None
    raw = str(value).replace("\xa0", " ").replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", re.sub(r"[^\d.,]", " ", raw))
    if not m:
        return None
    try:
        return Decimal(m.group(0))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _kw_from_hp(hp):
    if hp is None:
        return None
    return int((Decimal(hp) * Decimal("0.7355")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _clean_vin(vin):
    s = _clean_text(vin).upper()
    return s if _VIN_RE.match(s) else ""


def _extract_first(pattern, text, flags=re.I | re.S):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else ""


def is_offer_detail_url(url):
    """
    True only for real offer detail pages, e.g.
    /samochody-uzywane/osobowe/volvo-v90-...-278740
    """
    path = urlparse(_clean_text(url)).path.rstrip("/")
    return bool(_DETAIL_OFFER_PATH_RE.match(path))


def _extract_ldjson_vehicle(html):
    sel = Selector(text=html)
    for raw in sel.css('script[type="application/ld+json"]::text').getall():
        raw = _clean_text(raw)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and str(item.get("@type", "")).lower() == "vehicle":
                    return item
            continue
        if isinstance(payload, dict) and str(payload.get("@type", "")).lower() == "vehicle":
            return payload
    return {}


def parse_listing_page(html, base_url=_SUPERAUTO_BASE_URL):
    sel = Selector(text=html)
    urls = []
    seen = set()
    for href in sel.css('a.offerItem::attr(href), a[href*="/samochody-"]::attr(href)').getall():
        abs_url = urljoin(base_url, href)
        if not is_offer_detail_url(abs_url):
            continue
        clean = abs_url.split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        urls.append(clean)
    return urls


def parse_get_offers_payload(payload, base_url=_SUPERAUTO_BASE_URL):
    if not isinstance(payload, dict):
        return [], []
    offers_list_html = payload.get("offersList") or ""
    urls = parse_listing_page(offers_list_html, base_url=base_url)
    offer_ids = [str(x) for x in (payload.get("offersIds") or []) if str(x).strip()]
    return urls, offer_ids


def offer_page_to_car_offer_dict(html, page_url):
    sel = Selector(text=html)
    ld = _extract_ldjson_vehicle(html)

    canonical = _clean_text(sel.css('link[rel="canonical"]::attr(href)').get()) or page_url.split("?")[0]
    title = (
        _clean_text(ld.get("name"))
        or _clean_text(sel.css("h1::text").get())
        or _clean_text(sel.css("title::text").get().replace("| Samochody używane - Superauto.pl", ""))
    )[:512]

    description = _clean_text(sel.css('meta[name="description"]::attr(content)').get()) or _clean_text(ld.get("description"))
    vin = _clean_vin(sel.css(".vin-number::text").get())
    offer_no = _clean_text(sel.css(".offer-id span::text").get())
    external_id = (
        _extract_first(r"const\s+offerId\s*=\s*`?(\d+)`?\s*;", html)
        or _clean_text(ld.get("sku"))
        or _extract_first(r"-(\d+)(?:\?|$)", canonical)
    )[:64]

    spec_map = {}
    for node in sel.css(".data-used .data-desc"):
        label = _clean_text(" ".join(node.xpath("./text()").getall())).rstrip(":")
        value = " ".join(t.strip() for t in node.css("span *::text, span::text").getall() if _clean_text(t))
        if label and value and label not in spec_map:
            spec_map[label] = value

    plain_text = "\n".join(t.strip() for t in sel.xpath("//text()").getall() if _clean_text(t))

    country_origin = _extract_first(r"Kraj pochodzenia pojazdu:\s*([^\n<]+)", plain_text)
    first_registration_raw = _extract_first(r"Pierwsza rejestracja:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", plain_text)
    first_registration_date = parse_date(first_registration_raw) if first_registration_raw else None
    owner_more_than_one = _extract_first(r"Więcej niż 1 właściciel:\s*([^\n<]+)", plain_text).lower()
    history_damage = _extract_first(r"Historia uszkodzeń:\s*([^\n<]+)", plain_text).lower()
    insurance_active = _extract_first(r"Aktywne ubezpieczenie:\s*([^\n<]+)", plain_text).lower()

    equipment = []
    for item in sel.css("#car-equipment li"):
        text = " ".join(t.strip() for t in item.css("*::text, ::text").getall() if _clean_text(t))
        if text:
            equipment.append(text)
    equipment = list(dict.fromkeys(equipment))

    image_urls = []
    og_image = _clean_text(sel.css('meta[property="og:image"]::attr(content)').get()) or _clean_text(ld.get("image"))
    if og_image:
        image_urls.append(og_image)

    price_amount = _decimal_from_text(((ld.get("offers") or {}).get("price")))
    if price_amount is None:
        price_amount = _decimal_from_text(_extract_first(r"Nasza cena brutto:\s*([0-9\s]+zł)", plain_text))
    price_display = _extract_first(r"Nasza cena brutto:\s*([0-9\s]+zł)", plain_text)

    year = _int_from_text(spec_map.get("Rok produkcji"))
    mileage_km = _int_from_text(spec_map.get("Przebieg"))
    engine_cc = _int_from_text(spec_map.get("Pojemność silnika"))
    engine_power_hp = _int_from_text(spec_map.get("Moc"))
    engine_power_kw = _kw_from_hp(engine_power_hp)

    make = _clean_text((ld.get("brand") or {}).get("name"))[:128]
    model_heading = _clean_text(sel.css("#car-data .eq-title span::text").get())
    model = (model_heading.replace(make, "", 1).strip() if model_heading.lower().startswith(make.lower()) else model_heading)[:128]
    variant = _clean_text(sel.css("#car-data .eq-subtitle::text").get())[:128]

    fuel_type = spec_map.get("Rodzaj paliwa", "")
    transmission = spec_map.get("Skrzynia biegów", "")
    drive_train = spec_map.get("Napęd", "")

    inferred = infer_features_from_text(
        title=title,
        description=description,
        equipment_text=" ".join(equipment),
        main_features_text=" ".join(equipment),
        drive_train=drive_train,
        transmission=transmission,
        model_line="{} {} {}".format(make, model, variant).strip(),
    )

    base = {
        "source": "superauto",
        "external_listing_id": external_id,
        "url": canonical[:1024],
        "title": title or "Superauto offer",
        "description": description,
        "price_amount": price_amount,
        "price_currency": _clean_text(((ld.get("offers") or {}).get("priceCurrency")) or "PLN")[:8] or "PLN",
        "price_display": price_display[:64],
        "price_tax_deductible": "vat" in plain_text.lower(),
        "year": year,
        "mileage_km": mileage_km,
        "engine_cc": engine_cc,
        "engine_power_hp": engine_power_hp,
        "engine_power_kw": engine_power_kw,
        "fuel_type": _clean_text(fuel_type)[:64],
        "gearbox": _clean_text(transmission)[:64],
        "transmission": _clean_text(transmission)[:128],
        "drive_train": _clean_text(drive_train)[:64],
        "body_type": _clean_text(spec_map.get("Typ nadwozia") or ld.get("bodyType"))[:64],
        "color": _clean_text(spec_map.get("Kolor") or ld.get("color"))[:64],
        "doors": _int_from_text(spec_map.get("Liczba drzwi") or ld.get("numberOfDoors")),
        "seats": _int_from_text(spec_map.get("Liczba miejsc") or ld.get("seatingCapacity")),
        "make": make,
        "model": model,
        "variant": variant,
        "vin": vin[:17],
        "first_registration_raw": first_registration_raw[:32],
        "first_registration_date": first_registration_date,
        "registered": True if insurance_active == "tak" else None if not insurance_active else False,
        "previous_owners": 0 if owner_more_than_one == "nie" else None,
        "country_origin": _clean_text(country_origin)[:128],
        "seller_type": "dealer",
        "seller_name": "Superauto.pl",
        "seller_sell_id": offer_no[:32],
        "seller_is_dealer": True,
        "listing_location": "",
        "seller_location": None,
        "image_urls": image_urls[:60],
        "main_features": equipment[:200],
        "had_accident": True if "odnotowano" in history_damage else None,
        "no_accident": False if "odnotowano" in history_damage else None,
        "raw_payload": {"ldjson": ld, "spec_map": spec_map},
        "listing_availability": OfferListingAvailability.ACTIVE,
        "listing_checked_at": timezone.now(),
    }
    base.update(inferred)
    return base
