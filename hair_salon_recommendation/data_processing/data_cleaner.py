# 数据清洗与预处理模块
import re
import jieba
import pandas as pd
from typing import List, Dict, Any

class DataCleaner:
    """数据清洗与预处理类"""
    
    def __init__(self):
        # 初始化停用词列表
        self.stopwords = self._load_stopwords()
        # 初始化自定义词典（发型相关词汇）
        self._load_custom_dict()
    
    def _load_stopwords(self) -> List[str]:
        """加载停用词"""
        # 这里使用默认的停用词列表，实际项目中可以替换为更完整的列表
        return [
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '也', '但', '于',
            '在', '有', '为', '以', '我', '你', '他', '她', '它', '我们', '你们', '他们',
            '这', '那', '之', '来', '去', '要', '会', '能', '好', '很', '非常', '不',
            '没', '无', '人', '们', '到', '说', '着', '过', '做', '出', '得', '着',
            '地', '个', '本', '上', '下', '左', '右', '前', '后', '里', '外', '中',
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万'
        ]
    
    def _load_custom_dict(self):
        """加载自定义词典，用于发型相关词汇的分词"""
        # 自定义发型词典
        custom_words = [
            '辛芷蕾发型', '气垫烫', '姬发式', '羊毛卷', '法式烫', '离子烫',
            '空气刘海', '八字刘海', '齐刘海', '中分', '偏分', '波波头',
            '锁骨发', '及腰长发', '短发', '中长发', '烫发', '染发',
            '直发', '卷发', '剪发', '造型', '发色', '发质'
        ]
        # 添加到jieba词典
        for word in custom_words:
            jieba.add_word(word)
    
    def clean_text(self, text: str) -> str:
        """清洗文本数据"""
        if not text:
            return ''
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多余空格和换行符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符和乱码
        text = re.sub(r'[^一-龥a-zA-Z0-9，。！？；：、,.!?;:]', '', text)
        
        # 统一中文标点符号
        text = text.replace('，', '，').replace('。', '。')
        text = text.replace('！', '！').replace('？', '？')
        
        return text.strip()
    
    def segment_text(self, text: str) -> List[str]:
        """中文分词与停用词过滤"""
        if not text:
            return []
        
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词和单字
        filtered_words = [
            word for word in words 
            if word not in self.stopwords and len(word) > 1
        ]
        
        return filtered_words
    
    def process_post_data(self, posts: List[Dict[str, Any]]) -> pd.DataFrame:
        """处理帖子数据"""
        # 转换为DataFrame
        df = pd.DataFrame(posts)
        
        # 清洗文本字段
        if 'title' in df.columns:
            df['title_clean'] = df['title'].apply(self.clean_text)
        if 'content' in df.columns:
            df['content_clean'] = df['content'].apply(self.clean_text)
        
        # 分词
        if 'title_clean' in df.columns:
            df['title_seg'] = df['title_clean'].apply(self.segment_text)
        if 'content_clean' in df.columns:
            df['content_seg'] = df['content_clean'].apply(self.segment_text)
        
        # 合并标题和内容的分词结果
        df['full_seg'] = df.apply(
            lambda x: x['title_seg'] + x['content_seg'] 
            if 'title_seg' in x and 'content_seg' in x else [], axis=1
        )
        
        # 去重
        df = df.drop_duplicates(subset=['post_id'])
        
        return df
    
    def process_poi_data(self, pois: List[Dict[str, Any]]) -> pd.DataFrame:
        """处理POI数据"""
        df = pd.DataFrame(pois)
        
        # 清洗地址字段
        if 'address' in df.columns:
            df['address_clean'] = df['address'].apply(self.clean_text)
        
        # 转换经纬度为数值类型
        if 'latitude' in df.columns:
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        if 'longitude' in df.columns:
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # 转换评分为数值类型
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        # 去重
        df = df.drop_duplicates(subset=['salon_id'])
        
        return df
    
    def remove_duplicate_posts(self, df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
        """根据内容相似度去除重复帖子"""
        # 这里使用简单的去重方式，实际项目中可以使用更复杂的相似度算法
        # 例如：基于TF-IDF和余弦相似度的去重
        return df.drop_duplicates(subset=['content_clean'], keep='first')
    
    def convert_interaction_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换互动数据为数值类型"""
        interaction_cols = ['likes', 'collects', 'comments']
        for col in interaction_cols:
            if col in df.columns:
                # 处理带有单位的数据，如"1.2k" -> 1200
                df[col] = df[col].apply(lambda x: self._parse_number(x))
        
        return df
    
    def _parse_number(self, num_str: str) -> int:
        """解析带单位的数字字符串"""
        if not num_str or num_str == '0':
            return 0
        
        num_str = str(num_str).strip()
        
        # 处理千分位
        if 'k' in num_str.lower():
            return int(float(num_str.lower().replace('k', '')) * 1000)
        # 处理万分位
        elif 'w' in num_str.lower():
            return int(float(num_str.lower().replace('w', '')) * 10000)
        else:
            # 提取纯数字
            num = re.sub(r'[^\d]', '', num_str)
            return int(num) if num else 0
    
    def get_cleaned_data(self, raw_data: List[Dict[str, Any]], data_type: str) -> pd.DataFrame:
        """获取清洗后的数据"""
        if data_type == 'post':
            df = self.process_post_data(raw_data)
            df = self.convert_interaction_data(df)
            df = self.remove_duplicate_posts(df)
        elif data_type == 'poi':
            df = self.process_poi_data(raw_data)
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        return df
