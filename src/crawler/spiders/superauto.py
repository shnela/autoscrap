# -*- coding: utf-8 -*-
import json

import scrapy

from crawler.items import CarOfferItem
from crawler.offer_availability import mark_offer_expired
from crawler.superauto_parser import (
    get_offers_api_url,
    is_offer_detail_url,
    normalized_listing_url,
    offer_page_to_car_offer_dict,
    parse_get_offers_payload,
    parse_listing_page,
)

DEFAULT_LISTING_URL = "https://www.superauto.pl/oferty?brand=volvo&model=volvo.v90&utm_place=konfigurator-sapl-hero"
_GET_OFFERS_HEADERS = {
    "X-Auth-Token": "aUyW8Gwj9YbgkhkajPVkPT72eSwLZHAx",
    "Content-Type": "text/html+xml; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}


class SuperautoOffersSpider(scrapy.Spider):
    """
    Crawl Superauto listing URL and save offer details to CarOffer.
    """

    name = "superauto_offers"
    allowed_domains = ["superauto.pl"]

    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def __init__(self, listing_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing_url = normalized_listing_url((listing_url or DEFAULT_LISTING_URL).strip())
        self._seen_offer_urls = set()

    def start_requests(self):
        yield scrapy.Request(self.listing_url, callback=self.parse_listing)

    def parse_listing(self, response):
        local_urls = parse_listing_page(response.text, base_url=response.url)
        for url in local_urls:
            if url in self._seen_offer_urls:
                continue
            self._seen_offer_urls.add(url)
            yield scrapy.Request(url, callback=self.parse_offer)

        api_url = get_offers_api_url(response.url)
        yield scrapy.Request(api_url, callback=self.parse_listing_api, headers=_GET_OFFERS_HEADERS)

    def parse_listing_api(self, response):
        try:
            payload = json.loads(response.text)
        except (TypeError, ValueError, json.JSONDecodeError):
            self.logger.warning("Invalid /get-offers response: %s", response.url)
            return

        offer_urls, _offer_ids = parse_get_offers_payload(payload, base_url=response.url)
        if not offer_urls:
            self.logger.warning("No offer URLs from /get-offers %s", response.url)
            return

        for url in offer_urls:
            if url in self._seen_offer_urls:
                continue
            self._seen_offer_urls.add(url)
            yield scrapy.Request(url, callback=self.parse_offer)

    def parse_offer(self, response):
        if not is_offer_detail_url(response.url):
            return

        if response.status in (404, 410):
            mark_offer_expired(source="superauto", url=response.url.split("?")[0])
            self.logger.info("Listing HTTP %s (expired) %s", response.status, response.url)
            return

        payload = offer_page_to_car_offer_dict(response.text, response.url)
        if not payload.get("external_listing_id"):
            self.logger.warning("Skipping offer without id: %s", response.url)
            return
        yield CarOfferItem(**payload)
