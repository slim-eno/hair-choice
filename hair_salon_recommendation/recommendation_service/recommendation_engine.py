# 推荐规则引擎
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from config.config import RECOMMENDATION_WEIGHTS
from spiders.amap_mcp_spider import AmapMCPSpider

# 尝试导入XiaohongshuAnalyzer，如果失败则不使用小红书帖子爬取分析功能
try:
    from spiders.xiaohongshu_analyzer import XiaohongshuAnalyzer
    XIAOHONGSHU_AVAILABLE = True
except ImportError as e:
    print(f"无法导入小红书分析器，将不使用小红书帖子爬取分析功能: {e}")
    XIAOHONGSHU_AVAILABLE = False

# 导入大模型工具类
try:
    from llm.qwen_llm import QwenLLM
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"无法导入大模型工具类，将不使用大模型功能: {e}")
    LLM_AVAILABLE = False

class RecommendationEngine:
    """推荐规则引擎，实现不同类型的推荐算法"""
    
    def __init__(self):
        self.weights = RECOMMENDATION_WEIGHTS
        # 初始化高德地图MCP爬虫
        self.amap_spider = AmapMCPSpider()
        # 初始化小红书帖子分析器（如果可用）
        self.xiaohongshu_analyzer = XiaohongshuAnalyzer() if XIAOHONGSHU_AVAILABLE else None
        # 初始化大模型工具类（如果可用）
        self.llm = None
        if LLM_AVAILABLE:
            try:
                self.llm = QwenLLM(api_key="sk-3c49c69726bc46e2885f6f0c47be4e11")
                print("大模型工具类初始化成功")
            except Exception as e:
                print(f"大模型工具类初始化失败: {e}")
                self.llm = None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两个经纬度之间的距离（单位：公里）"""
        # 使用Haversine公式计算距离
        R = 6371  # 地球半径（公里）
        
        # 转换为弧度
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def z_score_normalize(self, series: pd.Series) -> pd.Series:
        """Z-Score归一化"""
        return (series - series.mean()) / series.std()
    
    def calculate_review_score(self, posts_df: pd.DataFrame) -> pd.DataFrame:
        """计算理发店的好评分数"""
        # 按理发店分组
        salon_groups = posts_df.groupby('salon_name')
        
        # 确定情感分数列名
        sentiment_col = 'positive_prob' if 'positive_prob' in posts_df.columns else 'sentiment'
        
        # 计算每个理发店的平均互动数据和情感分数
        salon_stats = salon_groups.agg({
            'likes': 'mean',
            'collects': 'mean',
            'comments': 'mean',
            sentiment_col: 'mean'
        }).reset_index()
        
        # 归一化各项指标
        salon_stats['likes_norm'] = self.z_score_normalize(salon_stats['likes'])
        salon_stats['collects_norm'] = self.z_score_normalize(salon_stats['collects'])
        salon_stats['positive_norm'] = self.z_score_normalize(salon_stats[sentiment_col])
        
        # 计算综合好评分数
        salon_stats['review_score'] = (
            self.weights['like_weight'] * salon_stats['likes_norm'] +
            self.weights['collect_weight'] * salon_stats['collects_norm'] +
            self.weights['sentiment_weight'] * salon_stats['positive_norm']
        )
        
        return salon_stats[['salon_name', 'review_score']]
    
    def recommend_by_distance(self, salons_df: pd.DataFrame, user_lat: float, user_lon: float, top_n: int = 10) -> pd.DataFrame:
        """距离优先推荐"""
        # 确保salons_df有正确的列名
        if 'salon_id' not in salons_df.columns and 'id' in salons_df.columns:
            salons_df = salons_df.rename(columns={'id': 'salon_id'})
        
        if 'salon_name' not in salons_df.columns and 'name' in salons_df.columns:
            salons_df = salons_df.rename(columns={'name': 'salon_name'})
        
        # 计算每个理发店到用户的距离
        salons_df['distance'] = salons_df.apply(
            lambda row: self.calculate_distance(
                user_lat, user_lon, float(row['latitude']), float(row['longitude'])
            ), axis=1
        )
        
        # 按距离升序排序
        recommended = salons_df.sort_values(by='distance', ascending=True).head(top_n)
        
        # 添加排名
        recommended['rank'] = range(1, len(recommended) + 1)
        
        return recommended
    
    def recommend_by_review(self, salons_df: pd.DataFrame, posts_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """好评优先推荐"""
        # 计算每个理发店的好评分数
        salon_review_scores = self.calculate_review_score(posts_df)
        
        # 合并理发店信息和好评分数
        merged = pd.merge(
            salons_df,
            salon_review_scores,
            on='salon_name',
            how='left'
        )
        
        # 按好评分数降序排序
        recommended = merged.sort_values(by='review_score', ascending=False).head(top_n)
        
        # 添加排名
        recommended['rank'] = range(1, len(recommended) + 1)
        
        return recommended
    
    def recommend_by_hair_style(self, salons_df: pd.DataFrame, posts_df: pd.DataFrame, 
                               style_entity: str, top_n: int = 10) -> pd.DataFrame:
        """发型风格优先推荐（基于NER结果）"""
        # 确定内容列名
        content_col = 'content_clean' if 'content_clean' in posts_df.columns else 'cleaned_content' if 'cleaned_content' in posts_df.columns else 'content'
        
        # 筛选包含指定发型实体的帖子
        style_posts = posts_df[posts_df[content_col].str.contains(style_entity, na=False)]
        
        # 计算每个理发店的好评分数
        salon_review_scores = self.calculate_review_score(style_posts)
        
        # 计算每个理发店的发型频次
        style_freq = style_posts.groupby('salon_name').size().reset_index(name='style_freq')
        
        # 合并数据
        merged = pd.merge(
            salons_df,
            salon_review_scores,
            on='salon_name',
            how='left'
        )
        
        merged = pd.merge(
            merged,
            style_freq,
            on='salon_name',
            how='left'
        )
        
        # 填充缺失值
        merged['review_score'] = merged['review_score'].fillna(0)
        merged['style_freq'] = merged['style_freq'].fillna(0)
        
        # 计算发型风格推荐分数
        merged['style_score'] = merged['review_score'] * merged['style_freq']
        
        # 按发型风格分数降序排序
        recommended = merged.sort_values(by='style_score', ascending=False).head(top_n)
        
        # 添加排名
        recommended['rank'] = range(1, len(recommended) + 1)
        
        return recommended
    
    def recommend_by_topic(self, salons_df: pd.DataFrame, topic_distributions: Dict[str, List[float]], 
                          target_topic: int, top_n: int = 10) -> pd.DataFrame:
        """发型风格优先推荐（基于LDA主题）"""
        # 转换主题分布为DataFrame
        topic_df = pd.DataFrame.from_dict(
            topic_distributions,
            orient='index',
            columns=[f'topic_{i}' for i in range(len(next(iter(topic_distributions.values()))))]
        ).reset_index().rename(columns={'index': 'salon_name'})
        
        # 提取目标主题的概率
        topic_df['target_topic_prob'] = topic_df[f'topic_{target_topic}']
        
        # 合并理发店信息和主题概率
        merged = pd.merge(
            salons_df,
            topic_df[['salon_name', 'target_topic_prob']],
            on='salon_name',
            how='left'
        )
        
        # 填充缺失值
        merged['target_topic_prob'] = merged['target_topic_prob'].fillna(0)
        
        # 按目标主题概率降序排序
        recommended = merged.sort_values(by='target_topic_prob', ascending=False).head(top_n)
        
        # 添加排名
        recommended['rank'] = range(1, len(recommended) + 1)
        
        return recommended
    
    def get_recommendations(self, salons_df: pd.DataFrame = None, posts_df: pd.DataFrame = None, 
                           user_lat: float = None, user_lon: float = None, 
                           recommendation_type: str = 'distance', 
                           style_entity: str = None, 
                           target_topic: str = None, 
                           top_n: int = 10, 
                           radius: int = 5000) -> Dict[str, Any]:
        """根据推荐类型获取推荐结果"""
        # 如果没有提供理发店数据，使用高德地图MCP获取附近的理发店
        if salons_df is None or salons_df.empty:
            if user_lat is None or user_lon is None:
                raise ValueError("当没有提供理发店数据时，必须提供用户位置")
            
            # 使用高德地图MCP获取附近的理发店
            nearby_salons = self.amap_spider.search_nearby_salons(user_lat, user_lon, radius=radius, page=1, offset=50)
            
            if not nearby_salons:
                # 如果无法获取到附近的理发店，抛出异常
                raise ValueError("未能获取到附近的理发店")
            
            # 转换为DataFrame
            salons_df = pd.DataFrame(nearby_salons)
            
            # 确保salons_df有正确的列名
            if 'salon_id' not in salons_df.columns and 'id' in salons_df.columns:
                salons_df = salons_df.rename(columns={'id': 'salon_id'})
            
            if 'salon_name' not in salons_df.columns and 'name' in salons_df.columns:
                salons_df = salons_df.rename(columns={'name': 'salon_name'})
            
            # 为每个理发店添加默认照片
            if 'photos' not in salons_df.columns:
                salons_df['photos'] = salons_df.apply(lambda x: ['https://picsum.photos/400/200?random=' + str(hash(x['salon_name']))], axis=1)
        
        # 获取推荐结果
        recommended = None
        
        # 爬取小红书帖子（所有推荐类型都爬取，用于生成报告）
        all_posts = []
        if (posts_df is None or posts_df.empty) and self.xiaohongshu_analyzer:
            # 获取理发店名称列表
            salon_names = salons_df['salon_name'].tolist()
            
            # 扩大爬取的理发店数量到10家
            xhs_posts = self.xiaohongshu_analyzer.crawl_and_analyze(salon_names[:10])
            
            if xhs_posts:
                # 转换为DataFrame
                posts_df = pd.DataFrame(xhs_posts)
                all_posts = xhs_posts
        
        # 根据推荐类型获取推荐结果
        if recommendation_type == 'distance':
            recommended = self.recommend_by_distance(salons_df, user_lat, user_lon, top_n)
        elif recommendation_type == 'review' and posts_df is not None and not posts_df.empty:
            recommended = self.recommend_by_review(salons_df, posts_df, top_n)
        elif recommendation_type == 'hair_style' and style_entity and posts_df is not None and not posts_df.empty:
            recommended = self.recommend_by_hair_style(salons_df, posts_df, style_entity, top_n)
        elif recommendation_type == 'topic' and target_topic is not None and posts_df is not None and not posts_df.empty:
            # 从帖子数据中获取主题分布
            topic_distributions = self._get_topic_distributions(posts_df)
            if topic_distributions:
                recommended = self.recommend_by_topic(salons_df, topic_distributions, target_topic, top_n)
            else:
                # 如果无法获取主题分布，使用距离优先推荐
                recommended = self.recommend_by_distance(salons_df, user_lat, user_lon, top_n)
        else:
            # 如果帖子数据不可用，默认使用距离优先推荐
            recommended = self.recommend_by_distance(salons_df, user_lat, user_lon, top_n)
        
        # 生成推荐语和推荐报告
        recommendation_phrase = ""
        recommendation_report = ""
        salon_reviews = {}
        
        if self.llm:
            # 生成推荐语
            recommendation_phrase = self.llm.generate_recommendation_phrase(recommended.to_dict('records'))
            
            # 生成推荐报告
            similar_posts = []
            if posts_df is not None and not posts_df.empty:
                # 获取相似度最高的帖子
                similar_posts = posts_df.sort_values(by='likes', ascending=False).head(5).to_dict('records')
            
            recommendation_report = self.llm.generate_recommendation_report(recommended.to_dict('records'), similar_posts)
            
            # 为每个理发店生成毒舌辣评
            for salon_name in recommended['salon_name'].tolist():
                # 筛选该理发店的帖子
                salon_posts = [post for post in all_posts if post['salon_name'] == salon_name]
                # 即使没有小红书帖子，也调用大模型生成毒舌辣评
                review = self.llm.generate_salon_review(salon_name, salon_posts)
                salon_reviews[salon_name] = review
        
        # 返回包含推荐结果、推荐语、推荐报告和毒舌辣评的字典
        return {
            'recommendations': recommended,
            'recommendation_phrase': recommendation_phrase,
            'recommendation_report': recommendation_report,
            'salon_reviews': salon_reviews
        }
    
    def _get_topic_distributions(self, posts_df: pd.DataFrame) -> Dict[str, List[float]]:
        """从帖子数据中获取主题分布"""
        # 实际应用中，主题分布应该预先计算并存储在数据库中
        # 目前返回空字典，后续可以替换为真实的主题分布计算逻辑
        return {}
    
    def calculate_salon_metrics(self, salons_df: pd.DataFrame, posts_df: pd.DataFrame) -> pd.DataFrame:
        """计算理发店的各项指标"""
        # 计算好评分数
        review_scores = self.calculate_review_score(posts_df)
        
        # 计算发型实体频次
        from data_processing.data_cleaner import DataCleaner
        cleaner = DataCleaner()
        
        # 提取所有发型实体（这里使用简化实现）
        hair_entities = [
            '辛芷蕾发型', '气垫烫', '姬发式', '羊毛卷', '法式烫', '离子烫',
            '空气刘海', '八字刘海', '齐刘海', '中分', '偏分', '波波头',
            '锁骨发', '短发', '中长发', '烫发', '染发', '直发', '卷发'
        ]
        
        # 计算每个理发店的发型实体频次
        salon_entities = {}
        for salon in posts_df['salon_name'].unique():
            salon_posts = posts_df[posts_df['salon_name'] == salon]['content_clean']
            entity_counts = {}
            for entity in hair_entities:
                count = salon_posts.str.contains(entity, na=False).sum()
                if count > 0:
                    entity_counts[entity] = count
            salon_entities[salon] = entity_counts
        
        # 合并数据
        merged = pd.merge(
            salons_df,
            review_scores,
            on='salon_name',
            how='left'
        )
        
        # 添加发型实体频次
        merged['hair_entities'] = merged['salon_name'].map(salon_entities)
        
        return merged
