# 数据存储模块
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import redis
from typing import List, Dict, Any
from config.config import DATABASE_CONFIG, REDIS_CONFIG

class DataStorage:
    """数据存储类，负责与PostgreSQL和Redis交互"""
    
    def __init__(self):
        self.db_config = DATABASE_CONFIG
        self.redis_config = REDIS_CONFIG
        self.conn = None
        self.redis_client = None
    
    def connect_db(self):
        """连接到PostgreSQL数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            print("成功连接到PostgreSQL数据库")
        except Exception as e:
            print(f"连接数据库失败: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")
    
    def connect_redis(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db']
            )
            # 测试连接
            self.redis_client.ping()
            print("成功连接到Redis")
        except Exception as e:
            print(f"连接Redis失败: {e}")
            raise
    
    def close_redis(self):
        """关闭Redis连接"""
        if self.redis_client:
            self.redis_client.close()
            print("Redis连接已关闭")
    
    def create_tables(self):
        """创建数据库表"""
        if not self.conn:
            self.connect_db()
        
        with self.conn.cursor() as cursor:
            # 创建理发店表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS salons (
                    salon_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    address TEXT,
                    latitude NUMERIC,
                    longitude NUMERIC,
                    phone VARCHAR(50),
                    rating NUMERIC,
                    category VARCHAR(100),
                    city VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建帖子表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id VARCHAR(50) PRIMARY KEY,
                    salon_name VARCHAR(255) NOT NULL,
                    title TEXT,
                    content TEXT,
                    title_clean TEXT,
                    content_clean TEXT,
                    likes INTEGER DEFAULT 0,
                    collects INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    publish_time VARCHAR(50),
                    keywords VARCHAR(255),
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (salon_name) REFERENCES salons(name) ON DELETE CASCADE
                )
            """)
            
            # 创建帖子分词表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_segments (
                    segment_id SERIAL PRIMARY KEY,
                    post_id VARCHAR(50) NOT NULL,
                    title_seg TEXT[],
                    content_seg TEXT[],
                    full_seg TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)
            
            # 创建情感分析结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id SERIAL PRIMARY KEY,
                    post_id VARCHAR(50) NOT NULL,
                    positive_prob NUMERIC,
                    negative_prob NUMERIC,
                    neutral_prob NUMERIC,
                    sentiment_label VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)
            
            # 创建NER结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ner_results (
                    id SERIAL PRIMARY KEY,
                    post_id VARCHAR(50) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_text VARCHAR(100),
                    start_pos INTEGER,
                    end_pos INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)
            
            # 创建LDA主题结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lda_topics (
                    id SERIAL PRIMARY KEY,
                    salon_name VARCHAR(255) NOT NULL,
                    topic_id INTEGER NOT NULL,
                    topic_prob NUMERIC,
                    topic_keywords TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (salon_name) REFERENCES salons(name) ON DELETE CASCADE
                )
            """)
            
            # 创建推荐结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id SERIAL PRIMARY KEY,
                    user_location TEXT,
                    recommendation_type VARCHAR(50),
                    salon_id VARCHAR(50) NOT NULL,
                    salon_name VARCHAR(255) NOT NULL,
                    score NUMERIC,
                    rank INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (salon_id) REFERENCES salons(salon_id) ON DELETE CASCADE
                )
            """)
        
        self.conn.commit()
        print("数据库表创建完成")
    
    def insert_salons(self, salons_df: pd.DataFrame):
        """插入理发店数据"""
        if not self.conn:
            self.connect_db()
        
        # 准备插入数据
        insert_data = []
        for _, row in salons_df.iterrows():
            insert_data.append((
                row['salon_id'],
                row['name'],
                row.get('address', ''),
                row.get('latitude', None),
                row.get('longitude', None),
                row.get('phone', ''),
                row.get('rating', None),
                row.get('category', ''),
                row.get('city', '')
            ))
        
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO salons (
                    salon_id, name, address, latitude, longitude, 
                    phone, rating, category, city
                ) VALUES %s
                ON CONFLICT (salon_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    address = EXCLUDED.address,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    phone = EXCLUDED.phone,
                    rating = EXCLUDED.rating,
                    category = EXCLUDED.category,
                    city = EXCLUDED.city,
                    updated_at = CURRENT_TIMESTAMP
                """,
                insert_data
            )
        
        self.conn.commit()
        print(f"成功插入/更新 {len(insert_data)} 条理发店数据")
    
    def insert_posts(self, posts_df: pd.DataFrame):
        """插入帖子数据"""
        if not self.conn:
            self.connect_db()
        
        # 准备插入数据
        insert_data = []
        for _, row in posts_df.iterrows():
            insert_data.append((
                row['post_id'],
                row['salon_name'],
                row.get('title', ''),
                row.get('content', ''),
                row.get('title_clean', ''),
                row.get('content_clean', ''),
                row.get('likes', 0),
                row.get('collects', 0),
                row.get('comments', 0),
                row.get('publish_time', ''),
                row.get('keywords', ''),
                row.get('url', '')
            ))
        
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO posts (
                    post_id, salon_name, title, content, title_clean, content_clean,
                    likes, collects, comments, publish_time, keywords, url
                ) VALUES %s
                ON CONFLICT (post_id) DO UPDATE SET
                    salon_name = EXCLUDED.salon_name,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    title_clean = EXCLUDED.title_clean,
                    content_clean = EXCLUDED.content_clean,
                    likes = EXCLUDED.likes,
                    collects = EXCLUDED.collects,
                    comments = EXCLUDED.comments,
                    publish_time = EXCLUDED.publish_time,
                    keywords = EXCLUDED.keywords,
                    url = EXCLUDED.url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                insert_data
            )
        
        self.conn.commit()
        print(f"成功插入/更新 {len(insert_data)} 条帖子数据")
    
    def insert_post_segments(self, posts_df: pd.DataFrame):
        """插入帖子分词数据"""
        if not self.conn:
            self.connect_db()
        
        # 准备插入数据
        insert_data = []
        for _, row in posts_df.iterrows():
            insert_data.append((
                row['post_id'],
                row.get('title_seg', []),
                row.get('content_seg', []),
                row.get('full_seg', [])
            ))
        
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO post_segments (
                    post_id, title_seg, content_seg, full_seg
                ) VALUES %s
                ON CONFLICT (post_id) DO UPDATE SET
                    title_seg = EXCLUDED.title_seg,
                    content_seg = EXCLUDED.content_seg,
                    full_seg = EXCLUDED.full_seg,
                    updated_at = CURRENT_TIMESTAMP
                """,
                insert_data
            )
        
        self.conn.commit()
        print(f"成功插入/更新 {len(insert_data)} 条帖子分词数据")
    
    def get_salon_names(self) -> List[str]:
        """获取所有理发店名称"""
        if not self.conn:
            self.connect_db()
        
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT name FROM salons")
            return [row[0] for row in cursor.fetchall()]
    
    def cache_result(self, key: str, value: Any, expire: int = 3600):
        """缓存结果到Redis"""
        if not self.redis_client:
            self.connect_redis()
        
        self.redis_client.setex(key, expire, str(value))
    
    def get_cached_result(self, key: str) -> Any:
        """从Redis获取缓存结果"""
        if not self.redis_client:
            self.connect_redis()
        
        return self.redis_client.get(key)
    
    def batch_insert(self, table_name: str, data: List[Dict[str, Any]]):
        """批量插入数据到指定表"""
        if not self.conn or not data:
            return
        
        columns = list(data[0].keys())
        values = [tuple(row[col] for col in columns) for row in data]
        
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                values
            )
        
        self.conn.commit()
        print(f"成功批量插入 {len(values)} 条数据到 {table_name} 表")
