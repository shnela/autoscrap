from scrapy_djangoitem import (
    DjangoItem,
)

from dealers.models import (
    Dealer,
    DealerCar,
    DealerStats,
)
from offers.models import (
    AutoScout24Offer,
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
        oid = self.get("otomoto_ad_id")
        if not oid:
            raise ValueError("CarOfferItem requires otomoto_ad_id")

        skip = {"id", "created", "modified", "otomoto_ad_id"}
        defaults = {}
        for f in CarOffer._meta.fields:
            name = f.name
            if name in skip:
                continue
            if name in self:
                defaults[name] = self[name]

        obj, _ = CarOffer.objects.update_or_create(otomoto_ad_id=oid, defaults=defaults)
        self._instance = obj
        return obj


class AutoScout24OfferItem(DjangoItem):
    django_model = AutoScout24Offer

    def save(self, *args, **kwargs):
        guid = self.get("listing_guid")
        if not guid:
            raise ValueError("AutoScout24OfferItem requires listing_guid")

        skip = {"id", "created", "modified", "listing_guid"}
        defaults = {}
        for f in AutoScout24Offer._meta.fields:
            name = f.name
            if name in skip:
                continue
            if name in self:
                defaults[name] = self[name]

        obj, _ = AutoScout24Offer.objects.update_or_create(listing_guid=guid, defaults=defaults)
        self._instance = obj
        return obj
