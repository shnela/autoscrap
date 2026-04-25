# -*- coding: utf-8 -*-
"""Mark CarOffer rows expired when detail pages return 404/410 (used by spiders)."""

from __future__ import annotations

from django.utils import timezone


def mark_offer_expired(
    *,
    source: str,
    external_listing_id: str | None = None,
    url: str | None = None,
    public_slug: str | None = None,
) -> int:
    """
    Set listing_availability=expired and listing_checked_at=now for matching row(s).
    Prefer external_listing_id; else public_slug (Otomoto); else exact url.
    Returns number of rows updated (0 or 1 for normal use).
    """
    from offers.models import CarOffer, OfferListingAvailability

    qs = CarOffer.objects.filter(source=source)
    if external_listing_id:
        qs = qs.filter(external_listing_id=str(external_listing_id))
    elif public_slug:
        qs = qs.filter(public_slug=public_slug)
    elif url:
        qs = qs.filter(url=url)
    else:
        return 0
    return qs.update(
        listing_availability=OfferListingAvailability.EXPIRED,
        listing_checked_at=timezone.now(),
    )
