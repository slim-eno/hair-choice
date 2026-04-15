# 小红书帖子爬虫
import scrapy
import random
import time
from .items import XiaohongshuPostItem
from config.config import XIAOHONGSHU_CONFIG

class XiaohongshuSpider(scrapy.Spider):
    name = 'xiaohongshu_spider'
    allowed_domains = ['xiaohongshu.com']
    start_urls = []
    
    def __init__(self, salon_names=None, **kwargs):
        super().__init__(**kwargs)
        # 从外部获取理发店名称列表，或使用默认测试名称
        self.salon_names = salon_names or ['Tony老师理发店', '时尚造型沙龙']
        self.max_pages = XIAOHONGSHU_CONFIG['max_pages']
        self.sleep_range = XIAOHONGSHU_CONFIG['sleep_time']
        self.user_agents = XIAOHONGSHU_CONFIG['user_agents']
        self.search_url = XIAOHONGSHU_CONFIG['search_url']
    
    def start_requests(self):
        """生成初始请求，搜索理发店相关帖子"""
        for salon_name in self.salon_names:
            for page in range(1, self.max_pages + 1):
                # 随机休眠，避免触发反爬
                time.sleep(random.uniform(*self.sleep_range))
                
                params = {
                    'keyword': salon_name,
                    'page': page
                }
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://www.xiaohongshu.com/',
                }
                
                yield scrapy.FormRequest(
                    url=self.search_url,
                    method='GET',
                    formdata=params,
                    headers=headers,
                    meta={'salon_name': salon_name, 'page': page},
                    callback=self.parse_search_results
                )
    
    def parse_search_results(self, response):
        """解析搜索结果，获取帖子列表"""
        try:
            # 这里需要根据小红书实际的页面结构进行解析
            # 注意：小红书可能使用动态加载或加密，实际爬取时需要调整
            posts = response.xpath('//div[@class="note-item"]')
            
            for post in posts:
                # 提取帖子基本信息
                post_url = post.xpath('.//a[@class="note-link"]/@href').get()
                if post_url:
                    # 随机休眠
                    time.sleep(random.uniform(*self.sleep_range))
                    
                    headers = {
                        'User-Agent': random.choice(self.user_agents),
                        'Accept': 'application/json, text/plain, */*',
                    }
                    
                    yield scrapy.Request(
                        url=response.urljoin(post_url),
                        headers=headers,
                        meta={'salon_name': response.meta['salon_name']},
                        callback=self.parse_post_detail
                    )
        except Exception as e:
            self.logger.error(f"解析搜索结果失败: {e}, 响应: {response.text[:500]}...")
    
    def parse_post_detail(self, response):
        """解析帖子详情"""
        try:
            item = XiaohongshuPostItem()
            
            # 提取帖子ID
            item['post_id'] = response.url.split('/')[-1].split('?')[0]
            
            # 提取标题和内容
            item['title'] = response.xpath('//h1[@class="note-title"]/text()').get(default='').strip()
            item['content'] = ' '.join(response.xpath('//div[@class="note-content"]//text()').getall()).strip()
            
            # 提取互动数据
            item['likes'] = response.xpath('//span[@class="like-count"]/text()').get(default='0').strip()
            item['collects'] = response.xpath('//span[@class="collect-count"]/text()').get(default='0').strip()
            item['comments'] = response.xpath('//span[@class="comment-count"]/text()').get(default='0').strip()
            
            # 提取发布时间
            item['publish_time'] = response.xpath('//span[@class="publish-time"]/text()').get(default='').strip()
            
            # 关联信息
            item['salon_name'] = response.meta['salon_name']
            item['keywords'] = response.meta['salon_name']
            item['url'] = response.url
            
            yield item
        except Exception as e:
            self.logger.error(f"解析帖子详情失败: {e}, URL: {response.url}")
