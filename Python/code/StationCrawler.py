# -*- coding: UTF-8 -*-

import requests
from bs4 import BeautifulSoup
import os
import sys


class StationCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }
        self.page_url = 'http://detail.zol.com.cn/cell_phone_index/subcate57_0_list_1_0_1_2_0_'
        self.base_url = 'http://detail.zol.com.cn'
        self.result_path = '/home/xiaosi/qunar/company/data/crawler/station_degree_20171204.txt'
        self.two_degree_source_path = 'https://baike.baidu.com/item/%E4%BA%8C%E7%AD%89%E7%AB%99'
        self.one_degree_source_path = 'https://baike.baidu.com/item/%E4%B8%80%E7%AD%89%E7%AB%99'
        self.special_degree_source_path = 'https://baike.baidu.com/item/%E7%89%B9%E7%AD%89%E7%AB%99'
        self.base_path = os.path.dirname(__file__)

    def request(self, url):
        r = requests.get(url, headers=self.headers)
        return r

    # 清空文件内容
    @staticmethod
    def clear(path):
        f = open(path, 'w+')
        f.truncate()
        f.close()

    # 保存结果
    @staticmethod
    def save_result(result, path):
        f = open(path, 'a')
        f.write(result)
        f.close()

    # 特等车站
    @staticmethod
    def special_degree_station_crawl(self, path):
        r = self.request(path)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'lxml')
        box = soup.find('table', {"class": "table-view log-set-param"})
        trs = box.find_all('tr')
        s_degree = '特等站'
        self.special_one_degree_station_parse(self, trs, s_degree)

    # 一等车站
    @staticmethod
    def one_degree_station_crawl(self, path):
        r = self.request(path)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'lxml')
        box = soup.find('table', {"log-set-param": "table_view"})
        trs = box.find_all('tr')
        s_degree = '一等站'
        self.special_one_degree_station_parse(self, trs, s_degree)

    # 二等车站
    @staticmethod
    def two_degree_station_crawl(self, path):
        r = self.request(path)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'lxml')
        box = soup.find('table', {"log-set-param": "table_view"})
        trs = box.find_all('tr')
        s_degree = '二等站'
        self.two_degree_station_parse(self, trs, s_degree)

    # 特等一等车站解析
    @staticmethod
    def special_one_degree_station_parse(self, trs, s_degree):
        index = 0
        for tr in trs:
            if index == 0:
                index += 1
                continue

            tds = tr.find_all('td')
            length = len(tds)
            s_name = ''
            if length > 0:
                href = tds[0].find('a')
                s_name = href.string
            result = "{\"name\":\"" + s_name + "\",\"degree\":\"" + s_degree + "\"}"
            print 'index: %s result: %s' % (index, result)
            self.save_result(result+"\n", self.result_path)
            index += 1

    # 二等车站解析
    @staticmethod
    def two_degree_station_parse(self, trs, s_degree):
        index = 0
        for tr in trs:
            if index == 0:
                index += 1
                continue
            tds = tr.find_all('td')
            length = len(tds)
            if length < 1:
                continue
            hrefs = tds[0].find_all('a')
            for href in hrefs:
                s_name = href.string
                result = "{\"name\":\"" + s_name + "\",\"degree\":\"" + s_degree + "\"}"
                print 'index: %s result: %s' % (index, result)
                self.save_result(result+"\n", self.result_path)
                index += 1

    def run(self):
        # 特等车站
        self.special_degree_station_crawl(self, self.special_degree_source_path)
        # 一等
        self.one_degree_station_crawl(self, self.one_degree_source_path)
        # 二等
        self.two_degree_station_crawl(self, self.two_degree_source_path)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    stationCrawler = StationCrawler()
    stationCrawler.run()