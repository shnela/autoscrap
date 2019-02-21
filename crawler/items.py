from scrapy_djangoitem import DjangoItem
from dealers.models import (
  Dealer,
  DealerStats,
)


class DealerItem(DjangoItem):
  django_model = Dealer
  map_fields = {
    'Id': 'id',
    'UrlName': 'url_name',
    'CompanyName': 'company_name',
    'City': 'city',
    'Country': 'country',
  }

  def __init__(self, *args, **kwargs):
    kwargs = {
      self.map_fields[k]: v
      for k, v in kwargs.items()
      if k in self.map_fields
    }
    super().__init__(*args, **kwargs)

  @property
  def instance(self):
    if self._instance is None:
      modelargs = dict((k, self.get(k)) for k in self._values
                       if k in self._model_fields)
      try:
        # if such Dealer exists, set created and updated fields
        dealer = Dealer.objects.get(id=self.get('id'))
        modelargs['created'] = dealer.created
        modelargs['modified'] = dealer.modified
      except Dealer.DoesNotExist:
        pass
      self._instance = self.django_model(**modelargs)
    return self._instance


class DealerStatsItem(DjangoItem):
  django_model = DealerStats
