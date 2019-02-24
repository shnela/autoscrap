from django.contrib.admin import SimpleListFilter
from django.db.models import Q


class CarsCountFilter(SimpleListFilter):
  title = 'cars_count'
  parameter_name = 'cars_count'

  def lookups(self, request, model_admin):
    return (
      ('0', 'None'),
      ('1', 'Less than 10'),
      ('2', 'Less than 100'),
      ('3', '100 and more'),
    )

  def queryset(self, request, queryset):
    if self.value() == '0':
      return queryset.filter(Q(cars_count=0) | Q(cars_count__isnull=True))
    elif self.value() == '1':
      return queryset.filter(cars_count__gte=1, cars_count__lt=10)
    elif self.value() == '2':
      return queryset.filter(cars_count__gte=11, cars_count__lt=100)
    elif self.value() == '3':
      return queryset.filter(cars_count__gte=100)
