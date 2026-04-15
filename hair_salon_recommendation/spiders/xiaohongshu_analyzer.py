# 小红书帖子爬取分析模块
import time
import random
import requests
import json
from config.config import XIAOHONGSHU_CONFIG

# 尝试导入模型和工具，如果失败则使用简单实现
try:
    # 先尝试导入data_cleaner，因为它依赖较少
    from data_processing.data_cleaner import DataCleaner
    
    # 尝试导入sentiment_analysis，它可能依赖transformers
    try:
        from model_training.sentiment_analysis import SentimentAnalyzer
        SENTIMENT_AVAILABLE = True
    except ImportError as e:
        print(f"无法导入情感分析模型，将使用简单实现: {e}")
        SENTIMENT_AVAILABLE = False
    
    # 尝试导入hair_ner，它可能依赖torch
    try:
        from model_training.hair_ner import HairNER
        HAIR_NER_AVAILABLE = True
    except ImportError as e:
        print(f"无法导入发型NER模型，将使用简单实现: {e}")
        HAIR_NER_AVAILABLE = False
    
    # 尝试导入lda_topic_model，它可能依赖gensim
    try:
        from model_training.lda_topic_model import LDATopicModel
        LDA_AVAILABLE = True
    except ImportError as e:
        print(f"无法导入LDA主题模型，将使用简单实现: {e}")
        LDA_AVAILABLE = False
    
    # 标记是否有任何模型可用
    MODELS_AVAILABLE = SENTIMENT_AVAILABLE or HAIR_NER_AVAILABLE or LDA_AVAILABLE
except ImportError as e:
    print(f"无法导入任何模型，将使用简单实现: {e}")
    MODELS_AVAILABLE = False
    SENTIMENT_AVAILABLE = False
    HAIR_NER_AVAILABLE = False
    LDA_AVAILABLE = False

class SimpleSentimentAnalyzer:
    """简单的情感分析器实现"""
    
    def analyze_sentiment(self, text):
        """简单的情感分析，基于关键词"""
        positive_words = ['好', '棒', '赞', '满意', '喜欢', '推荐', '不错', '优秀', '完美', '出色']
        negative_words = ['差', '糟糕', '不满意', '不喜欢', '不推荐', '失望', '垃圾', '差', '差', '差']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 0.8
        elif negative_count > positive_count:
            return 0.2
        else:
            return 0.5

class SimpleHairNER:
    """简单的发型实体提取器"""
    
    def extract_hair_styles(self, text):
        """简单的发型实体提取，基于关键词"""
        hair_styles = [
            '辛芷蕾发型', '气垫烫', '姬发式', '羊毛卷', '法式烫', '离子烫',
            '空气刘海', '八字刘海', '齐刘海', '中分', '偏分', '波波头',
            '锁骨发', '短发', '中长发', '烫发', '染发', '直发', '卷发'
        ]
        
        extracted = []
        for style in hair_styles:
            if style in text:
                extracted.append(style)
        
        return extracted

class SimpleLDAModel:
    """简单的主题模型"""
    
    def get_topics(self, text):
        """简单的主题提取，返回固定主题"""
        return ['发型设计', '服务质量', '环境设施', '价格性价比']

class SimpleDataCleaner:
    """简单的数据清洗器"""
    
    def clean_text(self, text):
        """简单的文本清洗"""
        if not isinstance(text, str):
            return ''
        
        # 移除特殊字符
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 移除多余的空格
        text = ' '.join(text.split())
        
        return text

class XiaohongshuAnalyzer:
    """
    小红书帖子爬取分析模块，用于爬取指定理发店的小红书帖子并进行分析
    """
    
    def __init__(self):
        self.max_pages = XIAOHONGSHU_CONFIG['max_pages']
        self.sleep_range = XIAOHONGSHU_CONFIG['sleep_time']
        self.user_agents = XIAOHONGSHU_CONFIG['user_agents']
        self.search_url = XIAOHONGSHU_CONFIG['search_url']
        
        # 初始化data_cleaner
        try:
            self.data_cleaner = DataCleaner()
        except:
            self.data_cleaner = SimpleDataCleaner()
        
        # 初始化sentiment_analyzer
        if SENTIMENT_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentAnalyzer()
            except:
                self.sentiment_analyzer = SimpleSentimentAnalyzer()
        else:
            self.sentiment_analyzer = SimpleSentimentAnalyzer()
        
        # 初始化hair_ner
        if HAIR_NER_AVAILABLE:
            try:
                self.hair_ner = HairNER()
            except:
                self.hair_ner = SimpleHairNER()
        else:
            self.hair_ner = SimpleHairNER()
        
        # 初始化lda_model
        if LDA_AVAILABLE:
            try:
                self.lda_model = LDATopicModel()
            except:
                self.lda_model = SimpleLDAModel()
        else:
            self.lda_model = SimpleLDAModel()
    
    def get_random_headers(self):
        """生成随机请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.xiaohongshu.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.xiaohongshu.com',
            'Content-Type': 'application/json',
            'Cookie': 'xhsTrackerId=xxx; xhsTracker=xxx; xhs_sig=xxx;',  # 添加Cookie
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
    
    def search_salon_posts(self, salon_name, page=1):
        """
        搜索指定理发店的小红书帖子
        
        Args:
            salon_name: 理发店名称
            page: 页码
            
        Returns:
            list: 帖子列表
        """
        try:
            # 构建搜索URL和参数
            import urllib.parse
            url = self.search_url
            headers = self.get_random_headers()
            
            # 小红书搜索API通常需要POST请求和特定的参数格式
            payload = {
                'keyword': salon_name,
                'page': page,
                'sort': 'general',
                'search_id': f'search_{int(time.time() * 1000)}'
            }
            
            print(f"正在搜索 {salon_name} 的小红书帖子，URL: {url}")
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            # 检查响应内容
            response_text = response.text.strip()
            if not response_text:
                print(f"搜索帖子失败: 响应内容为空")
                return []
            
            # 解析响应
            try:
                data = response.json()
                
                # 小红书API响应格式可能不同，需要根据实际情况调整
                if 'items' in data:
                    # 提取帖子列表
                    posts = []
                    for item in data['items']:
                        if 'note_card' in item:
                            note = item['note_card']
                            post = {
                                'post_id': note.get('note_id', ''),
                                'title': note.get('title', ''),
                                'content': note.get('desc', ''),
                                'likes': note.get('likes', 0),
                                'collects': note.get('collects', 0),
                                'comments': note.get('comments', 0),
                                'url': f"https://www.xiaohongshu.com/note/{note.get('note_id', '')}"
                            }
                            posts.append(post)
                    
                    print(f"成功获取到 {len(posts)} 篇关于 {salon_name} 的帖子")
                    return posts
                elif data.get('success') and 'data' in data:
                    # 另一种可能的响应格式
                    print(f"成功获取到 {len(data['data'])} 篇关于 {salon_name} 的帖子")
                    return data['data']
                else:
                    print(f"搜索帖子失败: 响应格式不正确，状态: {data.get('success', '未知')}")
                    print(f"响应内容: {json.dumps(data, ensure_ascii=False)[:100]}...")
                    return []
            except json.JSONDecodeError as e:
                print(f"搜索帖子失败: 无法解析JSON响应，错误: {e}")
                print(f"响应内容前50个字符: {response_text[:50]}...")
                return []
        except requests.exceptions.RequestException as e:
            print(f"搜索帖子失败: 请求异常，错误: {e}")
            return []
        except Exception as e:
            print(f"搜索帖子失败: 未知异常，错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_post_detail(self, post_id):
        """
        获取帖子详情
        
        Args:
            post_id: 帖子ID
            
        Returns:
            dict: 帖子详情
        """
        try:
            # 构建帖子详情URL
            url = f"https://www.xiaohongshu.com/note/{post_id}"
            headers = self.get_random_headers()
            
            # 发送请求
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 这里需要根据小红书实际的页面结构进行解析
            # 由于小红书可能使用动态加载，这里使用简化的解析方式
            # 实际应用中需要使用更复杂的解析方法，如使用Selenium或Pyppeteer
            
            # 提取帖子标题和内容
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('h1', class_='note-title')
            title = title.text.strip() if title else ''
            
            content = soup.find('div', class_='note-content')
            content = ' '.join(content.stripped_strings) if content else ''
            
            # 提取互动数据
            likes = soup.find('span', class_='like-count')
            likes = likes.text.strip() if likes else '0'
            
            collects = soup.find('span', class_='collect-count')
            collects = collects.text.strip() if collects else '0'
            
            comments = soup.find('span', class_='comment-count')
            comments = comments.text.strip() if comments else '0'
            
            return {
                'post_id': post_id,
                'title': title,
                'content': content,
                'likes': likes,
                'collects': collects,
                'comments': comments,
                'url': url
            }
        except Exception as e:
            print(f"获取帖子详情失败: {e}")
            return None
    
    def analyze_post(self, post):
        """
        分析帖子内容
        
        Args:
            post: 帖子字典
            
        Returns:
            dict: 分析结果
        """
        try:
            # 清洗文本
            cleaned_content = self.data_cleaner.clean_text(post['content'])
            
            # 情感分析
            sentiment = self.sentiment_analyzer.analyze_sentiment(cleaned_content)
            
            # 发型实体提取
            hair_styles = self.hair_ner.extract_hair_styles(cleaned_content)
            
            # 主题建模
            topics = self.lda_model.get_topics(cleaned_content)
            
            return {
                'sentiment': sentiment,
                'hair_styles': hair_styles,
                'topics': topics,
                'cleaned_content': cleaned_content
            }
        except Exception as e:
            print(f"分析帖子失败: {e}")
            return {
                'sentiment': 0.5,  # 默认中性
                'hair_styles': [],
                'topics': [],
                'cleaned_content': ''
            }
    
    def crawl_and_analyze(self, salon_names):
        """
        爬取并分析指定理发店的小红书帖子
        
        Args:
            salon_names: 理发店名称列表
            
        Returns:
            list: 包含分析结果的帖子列表
        """
        all_posts = []
        
        for salon_name in salon_names:
            print(f"开始爬取 {salon_name} 的小红书帖子...")
            
            for page in range(1, self.max_pages + 1):
                # 随机休眠
                time.sleep(random.uniform(*self.sleep_range))
                
                # 搜索帖子
                posts = self.search_salon_posts(salon_name, page)
                
                if not posts:
                    break
                
                # 分析每个帖子
                for post in posts:
                    # 分析帖子
                    analysis_result = self.analyze_post(post)
                    
                    # 合并结果
                    full_post = {
                        **post,
                        **analysis_result,
                        'salon_name': salon_name,
                        'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    all_posts.append(full_post)
                    print(f"爬取并分析成功: {salon_name} - {post.get('title', '无标题')}")
        
        return all_posts
    
    def batch_analyze_salons(self, salons):
        """
        批量分析理发店的小红书帖子
        
        Args:
            salons: 理发店列表，每个元素包含name字段
            
        Returns:
            dict: 分析结果，key为理发店名称，value为分析结果
        """
        results = {}
        
        for salon in salons:
            salon_name = salon.get('name')
            if not salon_name:
                continue
            
            # 爬取并分析帖子
            posts = self.crawl_and_analyze([salon_name])
            
            if posts:
                # 计算理发店的综合评分
                total_sentiment = sum(post['sentiment'] for post in posts)
                avg_sentiment = total_sentiment / len(posts)
                
                # 统计发型风格
                hair_style_counts = {}
                for post in posts:
                    for style in post['hair_styles']:
                        hair_style_counts[style] = hair_style_counts.get(style, 0) + 1
                
                # 统计主题
                topic_counts = {}
                for post in posts:
                    for topic in post['topics']:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
                results[salon_name] = {
                    'posts': posts,
                    'avg_sentiment': avg_sentiment,
                    'hair_style_counts': hair_style_counts,
                    'topic_counts': topic_counts,
                    'total_posts': len(posts)
                }
        
        return results
