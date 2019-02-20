# -*- coding: utf-8 -*-
from collections import namedtuple
import humps
import json
import re

from geopy import distance
from geopy.geocoders import Nominatim
import scrapy
from scrapy.utils.project import get_project_settings

AutoscoutUrls = namedtuple('AutoscoutUrls',
                           'dealers_list_url dealer_url_template')
AUTOSCOUT_URLS = {
  'it': AutoscoutUrls(
    'https://concessionari.autoscout24.it/DealersSearch/Find',
    'https://www.autoscout24.it/concessionari/{}/veicoli'
  ),
  'fr': AutoscoutUrls(
    'https://garages.autoscout24.fr/DealersSearch/Find',
    'https://www.autoscout24.fr/garages/{}/vehicules'
  ),
  'de': AutoscoutUrls(
    'https://haendler.autoscout24.de/DealersSearch/Find',
    'https://www.autoscout24.de/haendler/{}/fahrzeuge'
  ),
}


class AutoscoutDealersSpider(scrapy.Spider):
  name = 'autoscout_dealers'
  # custom_settings = {
  #   'CLOSESPIDER_PAGECOUNT': 10,
  # }
  allowed_domains = ['autoscout24.it', 'autoscout24.fr', 'autoscout24.de']

  def __init__(self, localization, city, km_to=2500, register_from=2018,
               max_distance_km=30):
    super().__init__()
    self.city = city
    self.max_distance_km = max_distance_km

    try:
      autoscout_urls = AUTOSCOUT_URLS[localization]
    except KeyError:
      raise ValueError('Unknown localization: {}'.format(localization))

    self.dealers_list_url = autoscout_urls.dealers_list_url
    dealer_url_template = '{}/?atype=C&kmto={}&fregfrom={}'.format(
      autoscout_urls.dealer_url_template, km_to, register_from)
    self.dealer_url_template = dealer_url_template
    self.geolocation = self.get_geolocation(city)

  def start_requests(self, page=1):
    results_per_page = 100
    data = {
      'CurrentPage': page, 'ResultsPerPage': results_per_page,
      'Distance': self.max_distance_km, 'Sorting': 'location',
    }
    as_geo = self.geopy2autoscout_geo(self.geolocation)
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
      url = self.dealer_url_template.format(dealer['UrlName'])
      yield scrapy.Request(url=url, callback=self.parse_dealer,
                           meta=dealer)

    if dealer_data:
      page = int(response.meta['page'])
      self.logger.info("Page {}".format(page))
      yield from self.start_requests(page + 1)

  @staticmethod
  def get_geolocation(city):
    user_agent = get_project_settings()['USER_AGENT']
    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    return geolocator.geocode(city)

  @staticmethod
  def autoscout_geo2geopy(as_geo):
    return as_geo['Longitude'], as_geo['Latitude']

  @staticmethod
  def geopy2autoscout_geo(geopy_geo):
    return {
      'Longitude': geopy_geo.longitude,
      'Latitude': geopy_geo.latitude,
    }

  def get_distance_from_location(self, dealer):
    """
    Returns distance between self.location and dealer location
    """
    city_geo = self.geolocation.longitude, self.geolocation.latitude
    dealer_geo = self.autoscout_geo2geopy(dealer['GeoLocation'])
    return int(distance.distance(city_geo, dealer_geo).km)

  @classmethod
  def get_phone_numbers(cls, dealer):
    for phone_data in dealer['PhoneNumbers']:
      phone_number = '{}: ({}) {} {}'.format(
        phone_data['Type'],
        phone_data['AreaCode'],
        phone_data['CountryCode'],
        phone_data['Number'],
      )
      yield phone_number

  def important_dealer_data(self, dealer):
    required_fields = [
      'CompanyName',
      'CompanyUrl',
      'Country',
      'City',
      'Zip',
      'AverageRatings',
      'RatingsCount',
    ]
    dealer_important_data = {
      'phones': list(self.get_phone_numbers(dealer)),
      'distance': self.get_distance_from_location(dealer),
    }
    for field in required_fields:
      key = humps.decamelize(field)
      dealer_important_data[key] = dealer[field]
    return dealer_important_data

  @classmethod
  def get_dealer_url(cls, response):
    """
    Returns dealer url without parameters.
    It prevents autoscout24 from discovering client's IP when employees uses
    url from excel file.
    """
    url = response.url
    return url
    # TODO: is this neccesary?
    get_index = url.find('?')
    if get_index > -1:
      url = url[:get_index]
    return url

  def parse_dealer(self, response):
    cars_count_str = response.xpath(
      '//h1[contains(@class, "dp-list__title__count")]/text()').extract_first()
    cars_count = int(re.match(r'\d+', cars_count_str).group())
    if cars_count:
      result = {
        'company_name': response.meta['CompanyName'],
        'cars_count': cars_count,
        'url': self.get_dealer_url(response),
        # 'company_info': response.meta,
      }
      result.update(self.important_dealer_data(response.meta))
      yield result
