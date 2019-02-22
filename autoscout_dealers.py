from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from crawler.spiders.autoscout import AutoscoutDealersSpider

LOCALIZATIONS = {
  'I': ['Firenze', 'Bologna', 'Roma', 'Milano', 'Bergamo', 'Busto Arsizio',
         'Livorno', 'Lucca', 'Pistoia', 'Viareggio', 'Pisa'],
  'F': ['Lyon', 'Paris', 'Bourg en Bresse', 'Oyonax', 'Annegy', 'Chambery'],
  'D': ['Berlin', 'Mannheim'],
}


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


if __name__ == '__main__':
  configure_logging()
  runner = CrawlerRunner(get_project_settings())
  crawl()
  reactor.run()
