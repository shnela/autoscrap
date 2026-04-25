# -*- coding: utf-8 -*-
import scrapy

from crawler.items import CarOfferItem
from crawler.offer_availability import mark_offer_expired
from crawler.otomoto_parser import (
    advert_to_car_offer_dict,
    extract_next_data,
    find_advert_search,
    listing_url_for_page,
    normalized_listing_url,
    public_slug_from_url,
)

DEFAULT_LISTING_URL = (
    "https://www.otomoto.pl/osobowe/volvo/v60--v60-cross-country--v90--v90-cross-country"
    "?min_id=6146687692"
    "&search%5Bfilter_enum_no_accident%5D=1"
    "&search%5Bfilter_enum_registered%5D=1"
    "&search%5Bfilter_enum_service_record%5D=1"
    "&search%5Bmake_model_generation%5D%5B0%5D=volvo%7Cv60"
    "&search%5Bmake_model_generation%5D%5B1%5D=volvo%7Cv60-cross-country"
    "&search%5Bmake_model_generation%5D%5B2%5D=volvo%7Cv90"
    "&search%5Bmake_model_generation%5D%5B3%5D=volvo%7Cv90-cross-country"
)


class OtomotoOffersSpider(scrapy.Spider):
    """
    Crawls an Otomoto search results URL, follows each offer, and saves CarOffer rows
    from the `__NEXT_DATA__.props.pageProps.advert` payload on detail pages.
    """

    name = "otomoto_offers"
    allowed_domains = ["otomoto.pl"]

    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def __init__(self, listing_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing_url = normalized_listing_url((listing_url or DEFAULT_LISTING_URL).strip())

    def start_requests(self):
        yield scrapy.Request(
            listing_url_for_page(self.listing_url, 1),
            callback=self.parse_listing,
            meta={"listing_base": self.listing_url},
        )

    def parse_listing(self, response):
        data = extract_next_data(response.text)
        advert_search = find_advert_search(data)
        if not advert_search:
            self.logger.warning("No advertSearch in listing %s", response.url)
            return

        edges = advert_search.get("edges") or []
        page_info = advert_search.get("pageInfo") or {}
        total = int(advert_search.get("totalCount") or 0)
        page_size = int(page_info.get("pageSize") or 0)
        current_offset = int(page_info.get("currentOffset") or 0)

        for edge in edges:
            node = edge.get("node") or {}
            url = node.get("url")
            if url:
                nid = node.get("id")
                meta = {"external_listing_id": str(nid)} if nid else {}
                yield scrapy.Request(url, callback=self.parse_offer, meta=meta)

        fetched = len(edges)
        next_offset = current_offset + fetched
        if fetched > 0 and next_offset < total:
            next_page = next_offset // page_size + 1 if page_size else 2
            listing_base = response.meta.get("listing_base") or self.listing_url
            yield scrapy.Request(
                listing_url_for_page(listing_base, next_page),
                callback=self.parse_listing,
                meta={"listing_base": listing_base},
            )

    def parse_offer(self, response):
        meta = response.meta or {}
        eid = meta.get("external_listing_id")

        if response.status in (404, 410):
            n = mark_offer_expired(
                source="otomoto",
                external_listing_id=eid,
                public_slug=public_slug_from_url(response.url) if not eid else None,
            )
            if not n:
                mark_offer_expired(source="otomoto", url=response.url)
            self.logger.info("Listing HTTP %s (expired) %s", response.status, response.url)
            return

        data = extract_next_data(response.text)
        if not data:
            self.logger.warning("No __NEXT_DATA__ on %s", response.url)
            n = mark_offer_expired(
                source="otomoto",
                external_listing_id=eid,
                public_slug=public_slug_from_url(response.url) if not eid else None,
            )
            if not n:
                mark_offer_expired(source="otomoto", url=response.url)
            return

        advert = data.get("props", {}).get("pageProps", {}).get("advert")
        if not advert:
            self.logger.warning("No advert in pageProps for %s", response.url)
            n = mark_offer_expired(
                source="otomoto",
                external_listing_id=eid,
                public_slug=public_slug_from_url(response.url) if not eid else None,
            )
            if not n:
                mark_offer_expired(source="otomoto", url=response.url)
            return

        payload = advert_to_car_offer_dict(advert)
        if not payload.get("external_listing_id"):
            self.logger.warning("Skipping offer without id: %s", response.url)
            return

        yield CarOfferItem(**payload)
