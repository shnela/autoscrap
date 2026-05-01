# -*- coding: utf-8 -*-
import scrapy

from crawler.autoplac_parser import offer_to_car_offer_dict, parse_listing_page, parse_offer_page
from crawler.items import CarOfferItem
from crawler.offer_availability import mark_offer_expired

DEFAULT_LISTING_URL = "https://autoplac.pl/oferty/samochody-osobowe/volvo/v90-cross-country"


class AutoplacOffersSpider(scrapy.Spider):
    """
    Crawls an Autoplac listing, follows offer pages, and stores offers in CarOffer.
    """

    name = "autoplac_offers"
    allowed_domains = ["autoplac.pl"]

    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def __init__(self, listing_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing_url = (listing_url or DEFAULT_LISTING_URL).strip()

    def start_requests(self):
        yield scrapy.Request(self.listing_url, callback=self.parse_listing)

    def parse_listing(self, response):
        offer_urls, next_page_url = parse_listing_page(response.text, base_url=response.url)
        if not offer_urls:
            self.logger.warning("No offer URLs on listing %s", response.url)
        for url in offer_urls:
            yield scrapy.Request(url, callback=self.parse_offer)
        if next_page_url:
            yield scrapy.Request(next_page_url, callback=self.parse_listing)

    def parse_offer(self, response):
        if response.status in (404, 410):
            mark_offer_expired(source="autoplac", url=response.url)
            self.logger.info("Listing HTTP %s (expired) %s", response.status, response.url)
            return

        offer, body = parse_offer_page(response.text)
        if not offer:
            self.logger.warning("No embedded offer payload for %s", response.url)
            mark_offer_expired(source="autoplac", url=response.url)
            return

        payload = offer_to_car_offer_dict(offer, body or {}, response.url)
        if not payload.get("external_listing_id"):
            self.logger.warning("Skipping offer without id: %s", response.url)
            return

        yield CarOfferItem(**payload)
