"""
Re-run Otomoto text inference (audio, headlights, feature flags) from stored raw_payload.

Use when you improved feature_inference.py and re-crawling hit HTTP cache or you do not want
to re-download listings. Does not touch price, mileage, etc. Uses QuerySet.update() (no CarOffer.save()).
"""

from django.core.management.base import BaseCommand

from offers.feature_inference import empty_feature_defaults, infer_from_otomoto_advert
from offers.models import CarOffer


def _infer_field_names():
    return list(empty_feature_defaults().keys())


class Command(BaseCommand):
    help = (
        "Re-apply infer_from_otomoto_advert() to CarOffer rows (source=otomoto) using raw_payload. "
        "No HTTP; optional --public-slug / --limit; --dry-run to print only."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--public-slug",
            default="",
            help="Only rows with this public_slug (e.g. ID6HPXLy).",
        )
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print would-change rows without writing.",
        )

    def handle(self, *args, **options):
        field_names = _infer_field_names()
        qs = CarOffer.objects.filter(source="otomoto").exclude(raw_payload__isnull=True)
        slug = (options.get("public_slug") or "").strip()
        if slug:
            qs = qs.filter(public_slug=slug)
        if options.get("limit") is not None:
            qs = qs[: int(options["limit"])]

        checked = 0
        updated = 0
        for offer in qs.iterator():
            checked += 1
            adv = offer.raw_payload
            if not isinstance(adv, dict) or not adv.get("id"):
                continue
            merged = infer_from_otomoto_advert(adv)
            patch = {k: merged[k] for k in field_names if k in merged}
            before = {k: getattr(offer, k) for k in field_names}
            if before == patch:
                continue
            updated += 1
            if options["dry_run"]:
                changed = [k for k in field_names if before.get(k) != patch.get(k)]
                parts = [f"{k}: {before.get(k)!r} -> {patch.get(k)!r}" for k in changed]
                self.stdout.write(
                    f"[dry-run] pk={offer.pk} slug={offer.public_slug!r} | " + " | ".join(parts)
                )
                continue
            CarOffer.objects.filter(pk=offer.pk).update(**patch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {checked}, updated {updated}" + (" (dry-run)" if options["dry_run"] else "")
            )
        )
