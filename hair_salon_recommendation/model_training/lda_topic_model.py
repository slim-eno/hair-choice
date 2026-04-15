# LDA主题模型，用于发现发型风格主题
from typing import List, Dict, Any, Tuple
from config.config import MODEL_CONFIG

# 尝试导入gensim，如果失败则使用简单实现
try:
    import gensim
    from gensim import corpora
    import pandas as pd
    import numpy as np
    
    # 标记是否成功导入gensim
    GENSIM_AVAILABLE = True
except Exception as e:
    print(f"无法导入gensim或其依赖，将使用简单实现: {e}")
    GENSIM_AVAILABLE = False

if GENSIM_AVAILABLE:
    class LDATopicModel:
        """LDA主题模型类"""
        
        def __init__(self):
            self.num_topics = MODEL_CONFIG['lda_topics']
            self.lda_model = None
            self.dictionary = None
            self.corpus = None
        
        def train(self, texts: List[List[str]]):
            """训练LDA模型"""
            # 创建词典
            self.dictionary = corpora.Dictionary(texts)
            
            # 过滤极端词（出现频率过低或过高的词）
            self.dictionary.filter_extremes(no_below=5, no_above=0.5)
            
            # 创建语料库
            self.corpus = [self.dictionary.doc2bow(text) for text in texts]
            
            # 训练LDA模型
            self.lda_model = gensim.models.LdaModel(
                corpus=self.corpus,
                id2word=self.dictionary,
                num_topics=self.num_topics,
                random_state=42,
                passes=10,
                alpha='auto',
                per_word_topics=True
            )
            
            print(f"LDA模型训练完成，共发现 {self.num_topics} 个主题")
            
            # 打印主题
            self.print_topics()
        
        def print_topics(self, num_words: int = 10):
            """打印主题"""
            for idx, topic in self.lda_model.print_topics(num_words=num_words):
                print(f"主题 {idx}: {topic}")
        
        def get_document_topics(self, text: List[str]) -> List[Tuple[int, float]]:
            """获取文档的主题分布"""
            if not self.lda_model or not self.dictionary:
                raise ValueError("模型未训练，请先调用train方法")
            
            bow = self.dictionary.doc2bow(text)
            return self.lda_model.get_document_topics(bow)
        
        def get_topic_keywords(self, topic_id: int, num_words: int = 10) -> List[Tuple[str, float]]:
            """获取主题的关键词"""
            if not self.lda_model:
                raise ValueError("模型未训练，请先调用train方法")
            
            return self.lda_model.show_topic(topic_id, num_words=num_words)
        
        def predict_batch(self, texts: List[List[str]]) -> List[List[Tuple[int, float]]]:
            """批量预测文本的主题分布"""
            results = []
            for text in texts:
                results.append(self.get_document_topics(text))
            return results
        
        def get_salon_topic_distribution(self, salon_posts: Dict[str, List[List[str]]]) -> Dict[str, List[float]]:
            """获取每个理发店的主题分布"""
            salon_topics = {}
            
            for salon_name, posts in salon_posts.items():
                # 计算每个帖子的主题分布
                post_topics = self.predict_batch(posts)
                
                # 初始化主题分布向量
                topic_dist = np.zeros(self.num_topics)
                
                # 聚合所有帖子的主题分布
                for post_topic in post_topics:
                    for topic_id, prob in post_topic:
                        topic_dist[topic_id] += prob
                
                # 归一化
                if np.sum(topic_dist) > 0:
                    topic_dist = topic_dist / np.sum(topic_dist)
                
                salon_topics[salon_name] = topic_dist.tolist()
            
            return salon_topics
        
        def save_model(self, model_path: str = './model_training/models/lda_model'):
            """保存模型"""
            if not self.lda_model:
                raise ValueError("模型未训练，请先调用train方法")
            
            self.lda_model.save(model_path)
            self.dictionary.save(f"{model_path}.dict")
            print(f"模型保存成功: {model_path}")
        
        def load_model(self, model_path: str = './model_training/models/lda_model'):
            """加载模型"""
            self.lda_model = gensim.models.LdaModel.load(model_path)
            self.dictionary = corpora.Dictionary.load(f"{model_path}.dict")
            print(f"模型加载成功: {model_path}")
        
        def visualize_topics(self, output_path: str = './model_training/visualizations/lda_topics.html'):
            """可视化主题"""
            try:
                import pyLDAvis
                import pyLDAvis.gensim_models as gensimvis
                
                vis = gensimvis.prepare(self.lda_model, self.corpus, self.dictionary)
                pyLDAvis.save_html(vis, output_path)
                print(f"主题可视化结果已保存到: {output_path}")
            except ImportError:
                print("请安装pyLDAvis库以使用可视化功能: pip install pyLDAvis")
        
        def process_posts(self, posts_df: pd.DataFrame) -> List[List[str]]:
            """处理帖子数据，准备LDA训练"""
            # 从DataFrame中提取分词后的文本
            texts = posts_df['full_seg'].tolist()
            
            # 过滤空文本
            texts = [text for text in texts if text and len(text) > 5]
            
            return texts
        
        def get_dominant_topic(self, text: List[str]) -> Tuple[int, float]:
            """获取文本的主导主题"""
            topics = self.get_document_topics(text)
            if not topics:
                return (-1, 0.0)
            
            # 找到概率最高的主题
            dominant_topic = max(topics, key=lambda x: x[1])
            return dominant_topic
        
        def get_topics(self, text: str, num_topics: int = 3, num_words: int = 5) -> List[str]:
            """获取文本的主题
            
            Args:
                text: 文本字符串
                num_topics: 返回的主题数量
                num_words: 每个主题的关键词数量
                
            Returns:
                List[str]: 主题关键词列表
            """
            try:
                # 简单的分词实现，使用jieba或其他分词库
                try:
                    import jieba
                    tokens = list(jieba.cut(text))
                except ImportError:
                    # 如果没有安装jieba，使用简单的字符分词
                    tokens = list(text)
                
                # 获取文档的主题分布
                if self.lda_model and self.dictionary:
                    # 如果模型已训练，使用模型预测
                    bow = self.dictionary.doc2bow(tokens)
                    document_topics = self.lda_model.get_document_topics(bow)
                    
                    # 排序主题，取概率最高的前num_topics个
                    document_topics.sort(key=lambda x: x[1], reverse=True)
                    top_topics = document_topics[:num_topics]
                    
                    # 获取每个主题的关键词
                    topics = []
                    for topic_id, _ in top_topics:
                        topic_keywords = self.lda_model.show_topic(topic_id, num_words=num_words)
                        keywords = [word for word, _ in topic_keywords]
                        topics.extend(keywords)
                    
                    return topics[:num_words * num_topics]
                else:
                    # 如果模型未训练，返回固定主题
                    return ['发型设计', '服务质量', '环境设施', '价格性价比']
            except Exception as e:
                print(f"获取主题失败: {e}")
                return ['发型设计', '服务质量', '环境设施', '价格性价比']
else:
    class LDATopicModel:
        """简单的LDA主题模型实现"""
        
        def __init__(self):
            self.num_topics = MODEL_CONFIG['lda_topics']
        
        def get_topics(self, text: str, num_topics: int = 3, num_words: int = 5) -> List[str]:
            """简单的主题提取，返回固定主题"""
            return ['发型设计', '服务质量', '环境设施', '价格性价比']
        
        # 其他方法的简单实现
        def train(self, texts: List[List[str]]):
            pass
        
        def print_topics(self, num_words: int = 10):
            pass
        
        def get_document_topics(self, text: List[str]) -> List[Tuple[int, float]]:
            return []
        
        def get_topic_keywords(self, topic_id: int, num_words: int = 10) -> List[Tuple[str, float]]:
            return []
        
        def predict_batch(self, texts: List[List[str]]) -> List[List[Tuple[int, float]]]:
            return []
        
        def get_salon_topic_distribution(self, salon_posts: Dict[str, List[List[str]]]) -> Dict[str, List[float]]:
            return {}
        
        def save_model(self, model_path: str = './model_training/models/lda_model'):
            pass
        
        def load_model(self, model_path: str = './model_training/models/lda_model'):
            pass
        
        def visualize_topics(self, output_path: str = './model_training/visualizations/lda_topics.html'):
            pass
        
        def process_posts(self, posts_df) -> List[List[str]]:
            return []
        
        def get_dominant_topic(self, text: List[str]) -> Tuple[int, float]:
            return (-1, 0.0)
