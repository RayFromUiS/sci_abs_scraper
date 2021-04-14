import scrapy
from scrapy.http import HtmlResponse
from scrapy.utils.project import get_project_settings
import re
import pymongo
import time
from datetime import datetime
from sci_abs.items import SciAbsItem
from sci_abs.helpers import read_urls
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


class ExampleSpider(scrapy.Spider):
    name = 'example'
    # allowed_domains = ['example.com']
    jour_urls = read_urls()
    jour_names = list(jour_urls.keys())

    def __init__(self):
        self.mongo_uri = get_project_settings().get('MONGO_URI')
        self.mongo_db = get_project_settings().get('MONGO_DATABASE')
        self.collection = 'sci_abs'
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def start_requests(self):
        '''
        make request from returned url of jour_urls
        '''

        for journal, url in self.jour_urls.items():
            yield scrapy.Request(url=url,
                                 callback=self.parse_jour,
                                 cb_kwargs={'journal': journal}
                                 )

    def parse_jour(self, response, journal):
        '''
        parse the journl links and maybe other item related info
        '''
        base_url = 'https://www.sciencedirect.com'
        articles = response.css('div.js-article-item')
        for article in articles:
            article_link = article.css('a.js-article__item__title__link') \
                .attrib.get('href')
            article_title = article.css('h3.text-m') \
                .css('span.anchor-text span::text').get()
            issue_date = article.css('dd.js-article-item-date::text').get()
            pdf_downloading_link = base_url + article.css('a.pdf-download').attrib.get('href') \
                if response.css('a.pdf-download').attrib.get('href') else None

            if not self.db[self.collection].find_one({'article_link': article_link}):
                # yield SeleniumRequest(
                yield scrapy.Request(
                    url=base_url + article_link,
                    callback=self.parse,
                    cb_kwargs={
                        'journal': journal,
                        'article_title': article_title,
                        'pdf_downloading_link': pdf_downloading_link,
                        'issue_date': issue_date},
                    # wait_until=EC.presence_of_element_located((By.ID, 'abstacts')),
                    # wait_time=10
                )
        # more articles links
        time.sleep(3)
        more_articles = response.css('a.button-alternative.js-listing-link.button-alternative-primary') \
            .attrib.get('href')
        if more_articles:
            yield response.follow(url=more_articles,
                                  callback=self.parse_previous,
                                  cb_kwargs={'journal': journal})

    def parse_previous(self, response, journal):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        base_url = 'https://www.sciencedirect.com'
        articles = response.css('li.js-article-list-item')
        for article in articles:
            article_title = article.css('dl.js-article.article-content').css('span.js-article-title::text').get()
            article_link = article.css('dl.js-article.article-content').css('dt a').attrib.get('href')
            pdf_downloading_link = base_url + article.css('a.pdf-download').attrib.get('href') \
                if response.css('a.pdf-download').attrib.get('href') else None
            if not self.db[self.collection].find_one({'article_link': article_link}):
                # yield SeleniumRequest(
                yield scrapy.Request(
                    url=base_url + article_link,
                    callback=self.parse,
                    cb_kwargs={
                        'journal': journal,
                        'article_title': article_title,
                        'pdf_downloading_link': pdf_downloading_link,
                        'issue_date': None},
                    # wait_until=EC.presence_of_element_located((By.ID, 'abstacts')),
                    # wait_time=10
                )

        next_issue = response.css('div.navigation-pre a').attrib.get('href')
        if next_issue:
            yield response.follow(url=next_issue,
                                  callback=self.parse_previous,
                                  cb_kwargs={'journal':journal}
                                  )


    def parse(self, response, journal, pdf_downloading_link, issue_date,article_title):
        '''
        parse html and store inside item accordingly
        '''

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        item = SciAbsItem()
        # driver = response.meta.get('driver')

        # try:
        #     driver.find_element_by_xpath("//*[@id='show-more-btn']").click()
        #     # time.sleep(5)
        #     WebDriverWait(driver, 20).until(lambda d: d.find_element_by_id("author-group"))
        #     # res = HtmlResponse(url=driver.current_url, body=driver.page_source, encoding='utf-8')
        #     # aff = res.xpath('//*[@id="author-group"]/dl[1]/dd/text()').get()
        #     aff = driver.find_element_by_xpath('//*[@id="author-group"]/dl[1]/dd/').text
        # except:
        #     aff = None
        # finally:
        item['author_aff_address'] = None
        item['journal'] = journal
        volume_issue = response.xpath("//div[contains(@class,'publication-volume')]/div/a/text()").get()
        if isinstance(volume_issue, str) and re.search(r',', volume_issue):
            item['issue'] = volume_issue.split(',')[-1]
            item['volume'] = volume_issue.split(',')
        else:
            item['volume'] = volume_issue
            item['issue'] = None

        item['article_type'] = response.xpath("//div[@class='article-dochead']/span/text()").get()
        item['pages'] = response.xpath("//div[contains(@class,'publication-volume')]/div/text()")[-1] \
            .get().split(' ')[-1]
        # item['article_title'] = response.xpath('//*[@id="screen-reader-main-title"]/span//text()').getall()
        item['article_title'] = article_title
        item['article_link'] = response.url
        authors = []
        authors_sel = response.css('div#banner').css('div.AuthorGroups').css('a.author span.content')
        for author in authors_sel:
            author_list = author.css('span::text').getall()
            authors.append(' '.join(author_list))
        item['authors'] = authors
        item['doi'] = response.css('a.doi').attrib.get('href')
        item['abstracts'] = response.xpath("//div[contains(@class,'author') \
                                and contains(@class,'abstract')]/div/p//text()").getall()
        item['keywords'] = response.css('div.Keywords span::text').getall()
        dates = response.xpath("//div[contains(@class,'publication-volume')]/div/text()").getall()
        issue_date_detail = None
        for date in dates:
            try:
                issue_date = datetime.strptime(date, '%B %Y').strftime('%Y-%m')
            except:
                continue
        item['issue_date'] = issue_date if issue_date else issue_date_detail
        item['pdf_link'] = pdf_downloading_link
        yield item
