from django.test import TestCase

from crawler.otomoto_parser import advert_to_car_offer_dict


class OtomotoPreviousOwnersInferenceTests(TestCase):
    def _build_advert(self, *, title="", description="", main_features=None, parameters_dict=None):
        return {
            "id": "123",
            "url": "https://www.otomoto.pl/osobowe/oferta/volvo-v90-cross-country-ID6TEST1.html",
            "title": title,
            "description": description,
            "price": {"value": "100000", "currency": "PLN"},
            "parametersDict": parameters_dict or {},
            "seller": {"type": "private", "name": "Jan Kowalski", "location": {"city": "Warszawa"}},
            "images": {"photos": []},
            "mainFeatures": list(main_features or []),
        }

    def test_sets_previous_owners_to_zero_for_od_nowosci_phrase(self):
        advert = self._build_advert(description="Auto od nowości w jednych rękach.")

        result = advert_to_car_offer_dict(advert)

        self.assertEqual(result["previous_owners"], 0)

    def test_sets_previous_owners_to_zero_for_pierwszy_wlasciciel_phrase(self):
        advert = self._build_advert(title="Volvo V90 CC, pierwszy właściciel")

        result = advert_to_car_offer_dict(advert)

        self.assertEqual(result["previous_owners"], 0)

    def test_uses_numeric_previous_owners_from_parameters_dict(self):
        advert = self._build_advert(
            parameters_dict={
                "no_of_previous_owners": {
                    "label": "Liczba poprzednich właścicieli",
                    "values": [{"value": "2", "label": "2"}],
                }
            }
        )

        result = advert_to_car_offer_dict(advert)

        self.assertEqual(result["previous_owners"], 2)
