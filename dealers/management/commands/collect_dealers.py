from django.core.management.base import BaseCommand
from crawler.spiders.autoscout import AutoscoutDealersSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class Command(BaseCommand):
  help = "Collect dealers from particular country and city"

  def add_arguments(self, parser):
    parser.add_argument('--localization', type=str,
                        help='Code of country from which Dealers will be downloaded.')
    parser.add_argument('--city', type=str,
                        help='City from which Dealers will be downloaded.')

  def handle(self, *args, **options):
    process = CrawlerProcess(get_project_settings())
    process.crawl(AutoscoutDealersSpider,
                  localization=options['localization'], city=options['city'])
    process.start()
