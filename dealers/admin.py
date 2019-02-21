from django.contrib import admin

from dealers.models import (
  Dealer,
  DealerStats,
)
from admintimestamps import TimestampedAdminMixin


class DealerStatsInline(admin.TabularInline):
    model = DealerStats
    readonly_fields = ('created',)


class DealerStatsAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('dealer', 'cars_count')


class DealerAdmin(TimestampedAdminMixin, admin.ModelAdmin):
  list_display = ('company_name', 'city')
  search_fields = ('company_name',)
  inlines = (DealerStatsInline,)


admin.site.register(Dealer, DealerAdmin)
admin.site.register(DealerStats, DealerStatsAdmin)
