# 系统配置文件

# 高德地图API配置
AMAP_CONFIG = {
    'key': 'f130f5b16fac19d43ba45a666043de7f',  # 新高德地图API密钥
    'poi_search_url': 'https://restapi.amap.com/v3/place/text',
    'distance_url': 'https://restapi.amap.com/v3/distance'
}

# 小红书爬虫配置
XIAOHONGSHU_CONFIG = {
    'search_url': 'https://www.xiaohongshu.com/api/sns/v6/search',
    'max_pages': 1,  # 减少最大爬取页数，提高速度
    'sleep_time': (1, 3),  # 减少随机休眠时间，提高速度
    'user_agents': [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1'
    ]
}

# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'hair_salon_db',
    'user': 'postgres',
    'password': 'password'
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

# 模型配置
MODEL_CONFIG = {
    'bert_model': 'bert-base-chinese',
    'max_seq_length': 512,
    'batch_size': 16,
    'num_epochs': 5,
    'learning_rate': 2e-5,
    'lda_topics': 20,  # LDA主题数量
    'ner_model_path': './model_training/models/ner_model.pth'
}

# 推荐权重配置
RECOMMENDATION_WEIGHTS = {
    'like_weight': 0.3,
    'collect_weight': 0.3,
    'sentiment_weight': 0.4
}
