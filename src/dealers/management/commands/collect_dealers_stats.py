from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from crawler.spiders.autoscout import AutoscoutDealerStatsSpider
from dealers.models import Dealer


class Command(BaseCommand):
  help = "Collect stats about dealers cars"

  def handle(self, *args, **options):
    process = CrawlerProcess(get_project_settings())
    dealers = Dealer.objects.all()
    process.crawl(AutoscoutDealerStatsSpider, dealers=dealers)
    process.start()
 