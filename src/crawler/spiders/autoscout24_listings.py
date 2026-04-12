# -*- coding: utf-8 -*-
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import scrapy

from crawler.autoscout24_parser import (
    extract_next_data,
    listing_details_to_offer_dict,
    parse_listing_page,
)
from crawler.items import AutoScout24OfferItem

DEFAULT_LISTING_URL = (
    "https://www.autoscout24.com/lst/volvo/v90-cross-country"
    "?sort=standard&desc=0&ustate=N%2CU&atype=C"
    "&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&cat=&damaged_listing=exclude&source=homepage_search-mask"
)


def normalized_listing_url(url):
    parts = urlparse(url)
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    return urlunparse(parts._replace(query=urlencode(pairs)))


def listing_url_with_page(base_url, page):
    parts = urlparse(base_url)
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    if page > 1:
        pairs.append(("page", str(page)))
    return urlunparse(parts._replace(query=urlencode(pairs)))


class Autoscout24OffersSpider(scrapy.Spider):
    """
    Crawls an AutoScout24 /lst/ search URL, follows /offers/... links, and stores
    rows from `__NEXT_DATA__.props.pageProps.listingDetails` on each offer page.
    """

    name = "autoscout24_offers"
    allowed_domains = ["autoscout24.com"]

    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def __init__(self, listing_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing_url = normalized_listing_url((listing_url or DEFAULT_LISTING_URL).strip())

    def start_requests(self):
        yield scrapy.Request(
            listing_url_with_page(self.listing_url, 1),
            callback=self.parse_listing,
            meta={"listing_base": self.listing_url},
        )

    def parse_listing(self, response):
        listings, num_pages, cur_page = parse_listing_page(response.text)
        if listings is None:
            self.logger.warning("No __NEXT_DATA__ listings on %s", response.url)
            return

        for item in listings:
            path = item.get("url")
            if not path:
                continue
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_offer,
            )

        listing_base = response.meta.get("listing_base") or self.listing_url
        if cur_page < num_pages:
            yield scrapy.Request(
                listing_url_with_page(listing_base, cur_page + 1),
                callback=self.parse_listing,
                meta={"listing_base": listing_base},
            )

    def parse_offer(self, response):
        data = extract_next_data(response.text)
        if not data:
            self.logger.warning("No __NEXT_DATA__ on %s", response.url)
            return

        ld = data.get("props", {}).get("pageProps", {}).get("listingDetails")
        if not ld:
            self.logger.warning("No listingDetails for %s", response.url)
            return

        host = urlparse(response.url).netloc or "www.autoscout24.com"
        marketplace_domain = host.split(":")[0]

        payload = listing_details_to_offer_dict(ld, marketplace_domain=marketplace_domain)
        if not payload.get("listing_guid"):
            self.logger.warning("Skipping offer without id: %s", response.url)
            return

        yield AutoScout24OfferItem(**payload)
