# 数据采集项定义
import scrapy

class XiaohongshuPostItem(scrapy.Item):
    """小红书帖子数据项"""
    post_id = scrapy.Field()  # 帖子ID
    title = scrapy.Field()  # 帖子标题
    content = scrapy.Field()  # 帖子正文
    likes = scrapy.Field()  # 点赞数
    collects = scrapy.Field()  # 收藏数
    comments = scrapy.Field()  # 评论数
    publish_time = scrapy.Field()  # 发布时间
    salon_name = scrapy.Field()  # 关联的理发店名称
    keywords = scrapy.Field()  # 搜索关键词
    url = scrapy.Field()  # 帖子URL

class SalonPOIItem(scrapy.Item):
    """理发店POI数据项"""
    salon_id = scrapy.Field()  # 理发店唯一标识
    name = scrapy.Field()  # 理发店名称
    address = scrapy.Field()  # 地址
    latitude = scrapy.Field()  # 纬度
    longitude = scrapy.Field()  # 经度
    phone = scrapy.Field()  # 电话
    rating = scrapy.Field()  # 评分
    category = scrapy.Field()  # 分类
    city = scrapy.Field()  # 城市
