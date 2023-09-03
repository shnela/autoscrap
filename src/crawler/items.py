from scrapy_djangoitem import DjangoItem
from dealers.models import (
  Dealer,
  DealerCar,
  DealerStats,
)


class DealerItem(DjangoItem):
  django_model = Dealer

  def __init__(self, dealer):
    kwargs = {
      'id': dealer['Id'],
      'company_name': dealer['CompanyName'],
      'zip': dealer['Zip'],
      'city': dealer['City'],
      'country': dealer['Country'],
      'autoscout_data': dealer,
    }
    super().__init__(**kwargs)

  @property
  def instance(self):
    if self._instance is None:
      modelargs = {k: self.get(k) for k in self._values
                   if k in self._model_fields}
      try:
        # if such Dealer exists, set cars_count and created
        dealer = Dealer.objects.get(id=self.get('id'))
        modelargs['created'] = dealer.created
        modelargs['cars_count'] = dealer.cars_count
      except Dealer.DoesNotExist:
        pass
      self._instance = self.django_model(**modelargs)
    return self._instance


class DealerStatsItem(DjangoItem):
  django_model = DealerStats


class DealerCarItem(DjangoItem):
  django_model = DealerCar
