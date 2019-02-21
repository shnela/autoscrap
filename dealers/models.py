from collections import namedtuple

from django.db import models

from django_extensions.db.models import TimeStampedModel

AutoscoutUrls = namedtuple('AutoscoutUrls',
                           'dealers_list_url dealer_url_template')
AUTOSCOUT_URLS = {
  'I': AutoscoutUrls(
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


class Dealer(TimeStampedModel):
  id = models.PositiveIntegerField(primary_key=True)
  url_name = models.CharField(max_length=128)
  company_name = models.CharField(max_length=128)
  url = models.CharField(max_length=128)
  city = models.CharField(max_length=64)
  country = models.CharField(max_length=8)

  @property
  def vehicles_url(self):
    return AUTOSCOUT_URLS[self.country].dealer_url_template.format(self.url_name)

  def __str__(self):
    return '{} ({})'.format(self.company_name, self.city)


class DealerStats(TimeStampedModel):
  dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
  cars_count = models.PositiveIntegerField()
