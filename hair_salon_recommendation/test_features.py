#!/usr/bin/env python3
# 测试核心功能

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spiders.amap_mcp_spider import AmapMCPSpider
from spiders.xiaohongshu_analyzer import XiaohongshuAnalyzer

def test_amap_spider():
    """测试高德地图爬虫功能"""
    print("=== 测试高德地图爬虫功能 ===")
    
    try:
        # 初始化爬虫
        spider = AmapMCPSpider()
        
        # 使用北京的经纬度作为测试
        user_lat = 39.9087
        user_lon = 116.3975
        
        # 搜索附近的理发店
        nearby_salons = spider.search_nearby_salons(user_lat, user_lon, radius=5000, page=1, offset=10)
        
        if nearby_salons:
            print(f"成功获取到 {len(nearby_salons)} 家附近的理发店")
            print("前3家理发店信息:")
            for i, salon in enumerate(nearby_salons[:3]):
                print(f"{i+1}. {salon['name']} - {salon['address']} - 距离: {salon.get('distance', '未知')} km")
            return True
        else:
            print("未能获取到附近的理发店")
            return False
    except Exception as e:
        print(f"测试高德地图爬虫失败: {e}")
        return False

def test_xiaohongshu_analyzer():
    """测试小红书帖子爬取分析功能"""
    print("\n=== 测试小红书帖子爬取分析功能 ===")
    
    try:
        # 初始化分析器
        analyzer = XiaohongshuAnalyzer()
        
        # 测试简单的理发店名称
        salon_names = ['Tony老师理发店', '时尚造型沙龙']
        
        # 爬取并分析帖子
        print(f"开始爬取 {salon_names} 的小红书帖子...")
        posts = analyzer.crawl_and_analyze(salon_names[:1])  # 只爬取一家理发店，避免爬取过多
        
        if posts:
            print(f"成功爬取并分析了 {len(posts)} 篇帖子")
            print("第一篇帖子的分析结果:")
            post = posts[0]
            print(f"标题: {post['title']}")
            print(f"情感分数: {post['sentiment']:.2f}")
            print(f"提取的发型: {', '.join(post['hair_styles'])}")
            print(f"主题: {', '.join(post['topics'])}")
            return True
        else:
            print("未能爬取到帖子")
            return False
    except Exception as e:
        print(f"测试小红书帖子爬取分析失败: {e}")
        return False

def test_recommendation_engine():
    """测试推荐引擎功能"""
    print("\n=== 测试推荐引擎功能 ===")
    
    try:
        from recommendation_service.recommendation_engine import RecommendationEngine
        
        # 初始化推荐引擎
        engine = RecommendationEngine()
        
        # 使用北京的经纬度作为测试
        user_lat = 39.9087
        user_lon = 116.3975
        
        # 测试距离优先推荐
        print("测试距离优先推荐...")
        recommendations = engine.get_recommendations(
            user_lat=user_lat,
            user_lon=user_lon,
            recommendation_type='distance',
            top_n=5
        )
        
        if not recommendations.empty:
            print(f"成功获取到 {len(recommendations)} 条推荐结果")
            print("推荐结果:")
            for i, (_, salon) in enumerate(recommendations.iterrows()):
                print(f"{i+1}. {salon['salon_name']} - 距离: {salon['distance']:.2f} km")
            return True
        else:
            print("未能获取到推荐结果")
            return False
    except Exception as e:
        print(f"测试推荐引擎失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试核心功能...")
    
    # 测试高德地图爬虫
    amap_result = test_amap_spider()
    
    # 测试小红书帖子爬取分析
    xhs_result = test_xiaohongshu_analyzer()
    
    # 测试推荐引擎
    # recommendation_result = test_recommendation_engine()
    
    print("\n=== 测试结果 ===")
    print(f"高德地图爬虫: {'通过' if amap_result else '失败'}")
    print(f"小红书帖子爬取分析: {'通过' if xhs_result else '失败'}")
    # print(f"推荐引擎: {'通过' if recommendation_result else '失败'}")
    
    print("\n测试完成！")
