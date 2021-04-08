# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SciAbsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
        # define the fields for your item here like:
        # name = scrapy.Field()
    journal = scrapy.Field()
    volume = scrapy.Field()
    issue = scrapy.Field()
    pages = scrapy.Field()
    article_type = scrapy.Field()
    pdf_link = scrapy.Field()
    author_aff_address = scrapy.Field()
    article_title = scrapy.Field()
    article_link = scrapy.Field()
    authors = scrapy.Field()
    doi = scrapy.Field()
    abstracts = scrapy.Field()
    keywords = scrapy.Field()
    issue_date = scrapy.Field()

