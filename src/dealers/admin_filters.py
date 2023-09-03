from django.contrib.admin import (
    SimpleListFilter,
)
from django.db.models import (
    Q,
)

from dealers.models import (
    DealerCar,
)


class CarsCountFilter(SimpleListFilter):
    title = "cars_count"
    parameter_name = "cars_count"

    def lookups(self, request, model_admin):
        return (
            ("0", "None"),
            ("1", "0"),
            ("2", "Less than 10"),
            ("3", "Less than 100"),
            ("4", "100 and more"),
        )

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.filter(cars_count__isnull=True)
        elif self.value() == "1":
            return queryset.filter(cars_count=0)
        elif self.value() == "2":
            return queryset.filter(cars_count__gte=1, cars_count__lt=10)
        elif self.value() == "3":
            return queryset.filter(cars_count__gte=11, cars_count__lt=100)
        elif self.value() == "4":
            return queryset.filter(cars_count__gte=100)


class CarPrefixFilter(SimpleListFilter):
    title = "different_cars"
    parameter_name = "cars"

    def lookups(self, request, model_admin):
        car_info_prefixes = set((d.info.split()[0], d.info.split()[0]) for d in DealerCar.objects.all())
        return sorted(car_info_prefixes)

    def queryset(self, request, queryset):
        car_info_prefix = request.GET.get("cars")
        if car_info_prefix is not None:
            matched_cars = DealerCar.objects.filter(info__istartswith=car_info_prefix).select_related("dealer")
            queryset = queryset.filter(id__in=(dc.dealer.id for dc in matched_cars))
        return queryset.all()
