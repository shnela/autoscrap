from collections import namedtuple

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel

ITALY_CODE = 'IT'
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


class DealerCar(TimeStampedModel):
  dealer = models.ForeignKey('dealers.Dealer', on_delete=models.CASCADE)
  info = models.CharField(max_length=64)
  url = models.CharField(max_length=256)

  class Meta:
    ordering = ('-created',)


class Dealer(TimeStampedModel):
  id = models.PositiveIntegerField(primary_key=True)
  company_name = models.CharField(max_length=128)
  zip = models.CharField(max_length=16)
  city = models.CharField(max_length=64)
  country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
  # autoscout json data
  autoscout_data = models.JSONField()
  # denormalized field of last created DealerStats
  cars_count = models.PositiveIntegerField(null=True, blank=True)

  @property
  def address(self):
    return '{}\n {} {}\n {}'.format(
      self.autoscout_data['Street'],
      self.zip,
      self.city,
      self.get_country_display(),
    )

  @property
  def phone_numbers(self):
    phones = list()
    for phone_obj in self.autoscout_data['PhoneNumbers']:
      phone_str = '{}: +{} ({}) {}'.format(
        phone_obj['Type'],
        phone_obj['AreaCode'],
        phone_obj['CountryCode'],
        phone_obj['Number'],
      )
      phones.append(phone_str)
    phones.sort()
    return '\n'.join(phones)

  @property
  def url_name(self):
    return self.autoscout_data['UrlName']

  @property
  def company_url(self):
    return self.autoscout_data['CompanyUrl']

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
