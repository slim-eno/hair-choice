# 理发店POI数据爬虫
import scrapy
import json
from .items import SalonPOIItem
from config.config import AMAP_CONFIG

class POISpider(scrapy.Spider):
    name = 'poi_spider'
    allowed_domains = ['restapi.amap.com']
    start_urls = []
    
    def __init__(self, cities=None, keywords='理发店', **kwargs):
        super().__init__(**kwargs)
        self.cities = cities or ['北京', '上海', '广州', '深圳']
        self.keywords = keywords
        self.api_key = AMAP_CONFIG['key']
        self.poi_url = AMAP_CONFIG['poi_search_url']
        
    def start_requests(self):
        """生成初始请求，获取各城市的理发店POI数据"""
        for city in self.cities:
            for page in range(1, 21):  # 最多获取20页数据
                params = {
                    'key': self.api_key,
                    'keywords': self.keywords,
                    'city': city,
                    'citylimit': 'true',
                    'offset': 20,
                    'page': page,
                    'extensions': 'all'
                }
                yield scrapy.FormRequest(
                    url=self.poi_url,
                    method='GET',
                    formdata=params,
                    meta={'city': city, 'page': page},
                    callback=self.parse_poi
                )
    
    def parse_poi(self, response):
        """解析POI数据"""
        try:
            data = json.loads(response.text)
            if data['status'] == '1' and data['pois']:
                for poi in data['pois']:
                    item = SalonPOIItem()
                    item['salon_id'] = poi['id']
                    item['name'] = poi['name']
                    item['address'] = poi['address']
                    item['latitude'] = poi['location'].split(',')[1] if poi['location'] else ''
                    item['longitude'] = poi['location'].split(',')[0] if poi['location'] else ''
                    item['phone'] = poi['tel'] if 'tel' in poi else ''
                    item['rating'] = poi['biz_ext']['rating'] if 'biz_ext' in poi and 'rating' in poi['biz_ext'] else ''
                    item['category'] = poi['type']
                    item['city'] = response.meta['city']
                    
                    yield item
        except Exception as e:
            self.logger.error(f"解析POI数据失败: {e}, 响应: {response.text}")
