# 项目主入口文件
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 暂时注释掉scrapy相关导入，以便在没有scrapy的情况下运行
# from spiders.poi_spider import POISpider
# from spiders.xiaohongshu_spider import XiaohongshuSpider
from data_processing.data_cleaner import DataCleaner
from data_processing.data_storage import DataStorage
from model_training.sentiment_analysis import SentimentAnalyzer
from model_training.hair_ner import HairNER
from model_training.lda_topic_model import LDATopicModel
from recommendation_service.recommendation_engine import RecommendationEngine

def run_poi_spider(cities=None, keywords='理发店'):
    """运行POI爬虫，获取理发店基础信息"""
    print("开始运行POI爬虫...")
    # 这里需要使用Scrapy的API来运行爬虫
    # 实际运行时需要调整
    print(f"POI爬虫运行完成，获取了{cities}城市的{keywords}数据")

def run_xiaohongshu_spider(salon_names=None):
    """运行小红书爬虫，获取理发店相关帖子"""
    print("开始运行小红书爬虫...")
    # 这里需要使用Scrapy的API来运行爬虫
    # 实际运行时需要调整
    print(f"小红书爬虫运行完成，获取了{len(salon_names)}个理发店的相关帖子")

def process_data():
    """处理采集到的数据"""
    print("开始处理数据...")
    cleaner = DataCleaner()
    storage = DataStorage()
    
    # 连接数据库
    storage.connect_db()
    
    # 创建数据库表
    storage.create_tables()
    
    print("数据处理完成")

def train_models():
    """训练模型"""
    print("开始训练模型...")
    
    # 训练情感分析模型
    print("训练情感分析模型...")
    sentiment_analyzer = SentimentAnalyzer()
    # 实际训练时需要提供标注数据
    
    # 训练NER模型
    print("训练NER模型...")
    hair_ner = HairNER()
    # 实际训练时需要提供标注数据
    
    # 训练LDA主题模型
    print("训练LDA主题模型...")
    lda_model = LDATopicModel()
    # 实际训练时需要提供文本数据
    
    print("模型训练完成")

def run_recommendation():
    """运行推荐服务"""
    print("开始运行推荐服务...")
    recommendation_engine = RecommendationEngine()
    # 实际运行时需要提供测试数据
    print("推荐服务运行完成")

def run_web_app():
    """启动Web应用"""
    print("启动Web应用...")
    # 运行Flask应用
    os.system("python web_app/app.py")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='理发店个性化推荐系统')
    parser.add_argument('--run', type=str, choices=['poi_spider', 'xiaohongshu_spider', 'process_data', 'train_models', 'recommendation', 'web_app'],
                        help='运行模块')
    parser.add_argument('--cities', type=str, nargs='+', default=['北京', '上海', '广州', '深圳'],
                        help='POI爬虫城市列表')
    parser.add_argument('--keywords', type=str, default='理发店',
                        help='POI搜索关键词')
    
    args = parser.parse_args()
    
    if args.run == 'poi_spider':
        run_poi_spider(args.cities, args.keywords)
    elif args.run == 'xiaohongshu_spider':
        # 从数据库获取理发店名称
        storage = DataStorage()
        storage.connect_db()
        salon_names = storage.get_salon_names()
        if not salon_names:
            salon_names = ['Tony老师理发店', '时尚造型沙龙']
        run_xiaohongshu_spider(salon_names)
    elif args.run == 'process_data':
        process_data()
    elif args.run == 'train_models':
        train_models()
    elif args.run == 'recommendation':
        run_recommendation()
    elif args.run == 'web_app':
        run_web_app()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
