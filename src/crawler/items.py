from scrapy_djangoitem import (
    DjangoItem,
)

from dealers.models import (
    Dealer,
    DealerCar,
    DealerStats,
)
from offers.models import (
    CarOffer,
)


class DealerItem(DjangoItem):
    django_model = Dealer

    def __init__(self, dealer):
        kwargs = {
            "id": dealer["Id"],
            "company_name": dealer["CompanyName"],
            "zip": dealer["Zip"],
            "city": dealer["City"],
            "country": dealer["Country"],
            "autoscout_data": dealer,
        }
        super().__init__(**kwargs)

    @property
    def instance(self):
        if self._instance is None:
            modelargs = {k: self.get(k) for k in self._values if k in self._model_fields}
            try:
                # if such Dealer exists, set cars_count and created
                dealer = Dealer.objects.get(id=self.get("id"))
                modelargs["created"] = dealer.created
                modelargs["cars_count"] = dealer.cars_count
            except Dealer.DoesNotExist:
                pass
            self._instance = self.django_model(**modelargs)
        return self._instance


class DealerStatsItem(DjangoItem):
    django_model = DealerStats


class DealerCarItem(DjangoItem):
    django_model = DealerCar


class CarOfferItem(DjangoItem):
    django_model = CarOffer

    def save(self, *args, **kwargs):
        src = self.get("source")
        eid = self.get("external_listing_id")
        if not src or not eid:
            raise ValueError("CarOfferItem requires source and external_listing_id")

        skip = {"id", "created", "modified", "source", "external_listing_id"}
        defaults = {}
        for f in CarOffer._meta.fields:
            name = f.name
            if name in skip:
                continue
            if name in self:
                defaults[name] = self[name]

        obj, _ = CarOffer.objects.update_or_create(
            source=src,
            external_listing_id=eid,
            defaults=defaults,
        )
        self._instance = obj
        return obj
