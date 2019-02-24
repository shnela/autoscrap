from django.contrib import admin

from admintimestamps import TimestampedAdminMixin
from djqscsv import write_csv

from dealers.admin_filters import CarsCountFilter
from dealers.models import (
  Dealer,
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
  actions = (import_dealers,)

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
