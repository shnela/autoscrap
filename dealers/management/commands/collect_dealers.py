from django.core.management.base import BaseCommand
from crawler.spiders.autoscout import AutoscoutDealersSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


LOCALIZATIONS = {
  'I': ['Firenze', 'Bologna', 'Roma', 'Milano', 'Bergamo', 'Busto Arsizio',
         'Livorno', 'Lucca', 'Pistoia', 'Viareggio', 'Pisa'],
  'F': ['Lyon', 'Paris', 'Bourg en Bresse', 'Oyonax', 'Annegy', 'Chambery'],
  'D': ['Berlin', 'Mannheim'],
}

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

runner = CrawlerRunner(get_project_settings())


@defer.inlineCallbacks
def crawl():
  for localization, cities in LOCALIZATIONS.items():
    for city in cities:
      try:
        yield runner.crawl(AutoscoutDealersSpider,
                           localization=localization, city=city)
      except Exception as err:
        print(localization, city, err)
        runner.stop()
  reactor.stop()


class Command(BaseCommand):
  help = "Collect dealers from particular country and city"

  def add_arguments(self, parser):
    parser.add_argument('--localization', type=str,
                        help='Code of country from which Dealers will be downloaded.')
    parser.add_argument('--city', type=str,
                        help='City from which Dealers will be downloaded.')

  def handle(self, *args, **options):
    crawl()
    reactor.run()
