from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q

from dealers.models import (
  Dealer,
  DealerStats,
)
from admintimestamps import TimestampedAdminMixin


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


class DealerStatsInline(admin.TabularInline):
  model = DealerStats
  readonly_fields = ('dealer', 'cars_count', 'created',)
  can_delete = False
  extra = 0


class DealerStatsAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('dealer', 'cars_count')
  list_filter = ('dealer__country',)


class DealerAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('company_name', 'cars_count', 'country', 'city', 'zip',)
  search_fields = ('company_name', 'city', 'zip',)
  list_filter = (
    'country',
    CarsCountFilter,
  )
  inlines = (DealerStatsInline,)
  readonly_fields = ['vehicles_url']

  def get_readonly_fields(self, request, obj=None):
    # if request.user.is_superuser:
    #   return self.readonly_fields

    return list(set(
      [field.name for field in self.opts.local_fields] +
      [field.name for field in self.opts.local_many_to_many] +
      self.readonly_fields
    ))


admin.site.register(Dealer, DealerAdmin)
admin.site.register(DealerStats, DealerStatsAdmin)
