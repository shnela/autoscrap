from django.core.management.base import BaseCommand
from crawler.spiders.autoscout import AutoscoutDealerCarsSpider

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from dealers.models import Dealer

runner = CrawlerRunner(get_project_settings())


@defer.inlineCallbacks
def crawl():
  for dealer in Dealer.objects.filter(cars_count__isnull=False):
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
