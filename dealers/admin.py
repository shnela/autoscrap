from django.contrib import admin

from admintimestamps import TimestampedAdminMixin
from djqscsv import write_csv

from dealers.admin_filters import CarsCountFilter, CarPrefixFilter
from dealers.models import (
  Dealer,
  DealerCar,
  DealerStats,
)


def import_dealers(modeladmin, request, queryset):
  queryset = queryset.values(
    'company_name',
    'cars_count',
    'city',
    'country',
  )
  with open('out/dealers.csv', 'wb') as csv_file:
    write_csv(queryset, csv_file)


import_dealers.short_description = "Export dealers to csv file"


class DealerStatsInline(admin.TabularInline):
  model = DealerStats
  readonly_fields = ('dealer', 'cars_count', 'created',)
  can_delete = False
  extra = 0


class DealerCarInline(admin.TabularInline):
  model = DealerCar
  readonly_fields = ('dealer', 'info', 'url', 'modified',)
  can_delete = False
  extra = 0


class DealerStatsAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('dealer', 'cars_count',)
  list_filter = ('dealer__country',)


class DealerCarsAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('dealer', 'info', 'url')
  list_filter = ('dealer__country', 'info')


class DealerAdmin(admin.ModelAdmin):
  list_display = (
    'company_name', 'cars_count', 'country', 'city', 'zip', 'created',
    'modified',
  )
  search_fields = ('company_name', 'city', 'zip',)
  list_filter = (
    'country',
    'created',
    CarsCountFilter,
    CarPrefixFilter,
  )
  fieldsets = [
    ('Company', {
      'fields': [
        'company_name',
        'phone_numbers',
        'address',
        'company_url',
      ]
    }),
    ('Cars', {
      'fields': [
        'vehicles_url',
        'cars_count',
      ]
    }),
    ('Other', {
      'fields': [
        'autoscout_data',
        'created',
        'modified',
      ]
    }),
  ]

  def get_readonly_fields(self, request, obj=None):
    # all fields are read-only
    return [e for fieldset in self.fieldsets for e in fieldset[1]['fields']]

  inlines = (DealerStatsInline, DealerCarInline,)
  actions = (import_dealers,)


admin.site.register(Dealer, DealerAdmin)
admin.site.register(DealerCar, DealerCarsAdmin)
admin.site.register(DealerStats, DealerStatsAdmin)
