# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

from openpyxl import Workbook


class AutoscrapPipeline(object):
  def process_item(self, item, spider):
    return item


class WriteToJson(object):

  def open_spider(self, spider):
    filename = 'out/{}_{}.js'.format(spider.name, spider.city)
    self.file = open(filename, 'w')

  def close_spider(self, spider):
    self.file.close()

  def process_item(self, item, spider):
    line = json.dumps(dict(item)) + "\n"
    self.file.write(line)
    return item


class WriteToXlsx(object):
  def open_spider(self, spider):
    self.workbook = Workbook()
    self.worksheet = self.workbook.active
    self.worksheet.page_setup.fitToWidth = 1
    self.keys_initialized = False

  def close_spider(self, spider):
    filename = 'out/{}_{}.xlsx'.format(spider.name, spider.city)
    self.workbook.save(filename)

  def process_item(self, item, spider):
    if not self.keys_initialized:
      self.worksheet.append(list(item.keys()))
      self.keys_initialized = True
    vlaues = [str(value) for value in item.values()]
    self.worksheet.append(vlaues)
    return item
