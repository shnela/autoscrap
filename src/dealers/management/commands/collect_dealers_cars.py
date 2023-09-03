from django.core.management.base import (
    BaseCommand,
)
from django.db.models import (
    Q,
)
from scrapy.crawler import (
    CrawlerRunner,
)
from scrapy.utils.project import (
    get_project_settings,
)
from twisted.internet import (
    defer,
    reactor,
)

from crawler.spiders.autoscout import (
    AutoscoutDealerCarsSpider,
)
from dealers.models import (
    Dealer,
)

runner = CrawlerRunner(get_project_settings())


@defer.inlineCallbacks
def crawl():
    for dealer in Dealer.objects.filter(Q(cars_count__isnull=False) & Q(cars_count__gt=0)):
        try:
            yield runner.crawl(AutoscoutDealerCarsSpider, dealer=dealer)
        except Exception as err:
            print(dealer)
            runner.stop()
    reactor.stop()


class Command(BaseCommand):
    help = "Collect dealers from particular country and city"

    def handle(self, *args, **options):
        crawl()
        reactor.run()
