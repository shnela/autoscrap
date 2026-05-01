"""
GET each CarOffer.url (Otomoto / AutoScout24): 404/410 → expired; otherwise only listing_checked_at.

Run periodically (cron) with --limit and --sleep to stay polite. Does not use Scrapy cache.
"""

import time
from datetime import timedelta

import requests
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from offers.models import CarOffer, OfferListingAvailability

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class Command(BaseCommand):
    help = (
        "HTTP GET offer URLs; mark listing_availability=expired on 404/410; "
        "always refresh listing_checked_at. Skips already expired unless --include-expired."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source", default="", help="Filter: otomoto | autoscout24 | autoplac (empty = all)")
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--sleep", type=float, default=1.5, help="Pause between requests (seconds)")
        parser.add_argument(
            "--staleness-days",
            type=int,
            default=7,
            help="Only rows with listing_checked_at NULL or older than this many days.",
        )
        parser.add_argument(
            "--include-expired",
            action="store_true",
            help="Also process rows already marked expired (re-verify).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.now()
        stale_before = now - timedelta(days=int(options["staleness_days"]))

        qs = CarOffer.objects.exclude(url="").filter(
            models.Q(listing_checked_at__isnull=True) | models.Q(listing_checked_at__lt=stale_before),
        )
        src = (options.get("source") or "").strip()
        if src:
            qs = qs.filter(source=src)
        if not options["include_expired"]:
            qs = qs.exclude(listing_availability=OfferListingAvailability.EXPIRED)

        qs = qs.order_by("listing_checked_at")[: int(options["limit"])]

        headers = {"User-Agent": _DEFAULT_UA, "Accept-Language": "pl,en;q=0.9"}
        checked = 0
        expired = 0
        would_expire = 0
        errors = 0

        for offer in qs.iterator():
            checked += 1
            url = (offer.url or "").strip()
            if not url:
                continue
            try:
                r = requests.get(
                    url,
                    timeout=25,
                    stream=True,
                    headers=headers,
                    allow_redirects=True,
                )
                try:
                    status = r.status_code
                finally:
                    r.close()
            except requests.RequestException as e:
                errors += 1
                self.stderr.write(f"pk={offer.pk} request error: {e}")
                time.sleep(float(options["sleep"]))
                continue

            if options["dry_run"]:
                if status in (404, 410):
                    would_expire += 1
                self.stdout.write(f"[dry-run] pk={offer.pk} status={status} url={url[:80]}...")
            elif status in (404, 410):
                CarOffer.objects.filter(pk=offer.pk).update(
                    listing_availability=OfferListingAvailability.EXPIRED,
                    listing_checked_at=now,
                )
                expired += 1
            else:
                CarOffer.objects.filter(pk=offer.pk).update(listing_checked_at=now)

            time.sleep(float(options["sleep"]))

        msg = f"Checked {checked}, marked_expired={expired}, request_errors={errors}"
        if options["dry_run"]:
            msg += f", would_expire={would_expire} (dry-run, no DB writes)"
        self.stdout.write(self.style.SUCCESS(msg))
