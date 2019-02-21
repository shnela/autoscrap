# -*- coding: utf-8 -*-
import humps
import json
import re

from geopy import distance
import scrapy

from crawler.items import (
  DealerItem,
  DealerStatsItem,
)
from dealers.models import AUTOSCOUT_URLS
from utils.geo import (
  get_geolocation,
  geopy2autoscout_geo,
)

ALLOWED_DOMAINS = ['autoscout24.it', 'autoscout24.fr', 'autoscout24.de']


class AutoscoutDealersSpider(scrapy.Spider):
  name = 'autoscout_dealers'
  allowed_domains = ALLOWED_DOMAINS

  def __init__(self, localization, city, max_distance_km=30):
    super().__init__()
    self.city = city
    self.max_distance_km = max_distance_km

    try:
      autoscout_urls = AUTOSCOUT_URLS[localization]
    except KeyError:
      raise ValueError('Unknown localization: {}'.format(localization))

    self.dealers_list_url = autoscout_urls.dealers_list_url
    self.geolocation = get_geolocation(city)

  def start_requests(self, page=1):
    results_per_page = 100
    data = {
      'CurrentPage': page, 'ResultsPerPage': results_per_page,
      'Distance': self.max_distance_km, 'Sorting': 'location',
    }
    as_geo = geopy2autoscout_geo(self.geolocation)
    data.update(as_geo)
    yield scrapy.Request(
      url=self.dealers_list_url, method='POST',
      headers={'Content-Type': 'application/json; charset=UTF-8'},
      body=json.dumps(data),
      meta={'page': page},
      callback=self.parse_dealers_list
    )

  def parse_dealers_list(self, response):
    json_data = json.loads(response.body_as_unicode())
    dealer_data = json_data['dealers']
    for dealer in dealer_data:
      yield DealerItem(**dealer)

    if dealer_data:
      page = int(response.meta['page'])
      self.logger.info("Page {}".format(page))
      yield from self.start_requests(page + 1)

  # def get_distance_from_location(self, dealer):
  #   """
  #   Returns distance between self.location and dealer location
  #   """
  #   city_geo = self.geolocation.longitude, self.geolocation.latitude
  #   dealer_geo = autoscout_geo2geopy(dealer['GeoLocation'])
  #   return int(distance.distance(city_geo, dealer_geo).km)

  # @classmethod
  # def get_phone_numbers(cls, dealer):
  #   for phone_data in dealer['PhoneNumbers']:
  #     phone_number = '{}: ({}) {} {}'.format(
  #       phone_data['Type'],
  #       phone_data['AreaCode'],
  #       phone_data['CountryCode'],
  #       phone_data['Number'],
  #     )
  #     yield phone_number
  #
  # def important_dealer_data(self, dealer):
  #   required_fields = [
  #     'Id',
  #     'CompanyName',
  #     'CompanyUrl',
  #     'Country',
  #     'City',
  #     'Zip',
  #     'AverageRatings',
  #     'RatingsCount',
  #   ]
  #   dealer_important_data = {
  #     'phones': list(self.get_phone_numbers(dealer)),
  #     'distance': self.get_distance_from_location(dealer),
  #   }
  #   for field in required_fields:
  #     key = humps.decamelize(field)
  #     dealer_important_data[key] = dealer[field]
  #   return dealer_important_data


class AutoscoutDealerStatsSpider(scrapy.Spider):
  name = 'autoscout_dealer_stats'
  allowed_domains = ALLOWED_DOMAINS

  def __init__(self, dealers, km_to=2500, register_from=2018):
    super().__init__()
    # try:
    #   autoscout_urls = AUTOSCOUT_URLS[localization]
    # except KeyError:
    #   # TODO: move to model
    #   raise ValueError('Unknown localization: {}'.format(localization))

    self.dealers = dealers
    self.dealer_url_args = '?atype=C&kmto={}&fregfrom={}'.format(km_to,
                                                            register_from)

  def start_requests(self):
    for dealer in self.dealers:
      url = '{}/{}'.format(dealer.vehicles_url, self.dealer_url_args)
      yield scrapy.Request(
        url=url,
        meta={'dealer': dealer},
      )

  def parse(self, response):
    # parse dealer
    cars_count_str = response.xpath(
      '//h1[contains(@class, "dp-list__title__count")]/text()').extract_first()
    cars_count = int(re.match(r'\d+', cars_count_str).group())
    if cars_count:
      yield DealerStatsItem(
        dealer=response.meta['dealer'],
        cars_count=cars_count,
      )
