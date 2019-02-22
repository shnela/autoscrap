from collections import namedtuple

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel

ITALY_CODE = 'I'
FRANCE_CODE = 'F'
GERMANY_CODE = 'D'
COUNTRY_CHOICES = (
  (ITALY_CODE, 'Italy'),
  (FRANCE_CODE, 'France'),
  (GERMANY_CODE, 'Germany'),
)

AutoscoutUrls = namedtuple('AutoscoutUrls',
                           'dealers_list_url dealer_url_template')
AUTOSCOUT_URLS = {
  ITALY_CODE: AutoscoutUrls(
    'https://concessionari.autoscout24.it/DealersSearch/Find',
    'https://www.autoscout24.it/concessionari/{}/veicoli'
  ),
  FRANCE_CODE: AutoscoutUrls(
    'https://garages.autoscout24.fr/DealersSearch/Find',
    'https://www.autoscout24.fr/garages/{}/vehicules'
  ),
  GERMANY_CODE: AutoscoutUrls(
    'https://haendler.autoscout24.de/DealersSearch/Find',
    'https://www.autoscout24.de/haendler/{}/fahrzeuge'
  ),
}


class DealerStats(TimeStampedModel):
  dealer = models.ForeignKey('dealers.Dealer', on_delete=models.CASCADE)
  cars_count = models.PositiveIntegerField()

  class Meta:
    ordering = ('-created',)


class Dealer(TimeStampedModel):
  id = models.PositiveIntegerField(primary_key=True)
  url_name = models.CharField(max_length=128)
  company_name = models.CharField(max_length=128)
  company_url = models.CharField(max_length=128, null=True, blank=True)
  # address
  street = models.CharField(max_length=64)
  zip = models.CharField(max_length=16)
  city = models.CharField(max_length=64)
  country = models.CharField(max_length=1, choices=COUNTRY_CHOICES)
  geo_long = models.DecimalField(max_digits=10, decimal_places=8)
  geo_lat = models.DecimalField(max_digits=10, decimal_places=8)
  # ratings
  average_ratings = models.DecimalField(max_digits=3, decimal_places=2)
  ratings_count = models.PositiveIntegerField()
  # denormalized field of last created DealerStats
  cars_count = models.PositiveIntegerField(null=True, blank=True)

  @property
  def vehicles_url(self):
    dealer_url_template = AUTOSCOUT_URLS[self.country].dealer_url_template
    return dealer_url_template.format(self.url_name)

  def __str__(self):
    return '{} ({})'.format(self.company_name, self.city)

  @staticmethod
  @receiver(post_save, sender=DealerStats)
  def update_cars_count(sender, **kwargs):
    if kwargs['created']:
      instance = kwargs['instance']
      instance.dealer.cars_count = instance.cars_count
      instance.dealer.save()
