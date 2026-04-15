 # 理发店个性化推荐系统

## 项目概述

基于位置与社交媒体文本分析的理发店个性化推荐系统，用于学术研究。该系统利用地理位置信息和小红书帖子文本数据，构建理发店服务质量与风格的量化指标，实现距离优先、好评优先及发型风格优先的分类推荐策略。

## 系统架构

系统采用四层架构：

1. **数据采集层**：使用Scrapy爬虫合规获取理发店POI数据和小红书帖子
2. **数据处理层**：清洗、预处理和存储数据
3. **模型训练层**：训练情感分析、NER和LDA主题模型
4. **推荐服务层**：实现多种推荐算法和API服务

## 核心功能

- **POI数据采集**：从高德地图API获取理发店基础信息
- **社交媒体数据采集**：合规爬取小红书理发店相关帖子
- **情感分析**：分析帖子情感倾向，计算好评分数
- **发型实体识别**：识别文本中的发型名称和技术名词
- **主题发现**：使用LDA发现潜在的发型风格主题
- **个性化推荐**：
  - 距离优先推荐
  - 好评优先推荐
  - 发型风格优先推荐（基于NER）
  - 发型主题优先推荐（基于LDA）

## 技术栈

- **地理服务**：高德地图API
- **数据采集**：Python Scrapy
- **数据存储**：PostgreSQL, Redis
- **数据处理**：Pandas, Jieba
- **NLP模型**：PyTorch, HuggingFace Transformers
- **主题模型**：Gensim LDA
- **后端服务**：Flask

## 项目结构

```
hair_salon_recommendation/
├── spiders/              # 爬虫模块
│   ├── poi_spider.py     # POI数据爬虫
│   ├── xiaohongshu_spider.py  # 小红书帖子爬虫
│   └── items.py          # 数据项定义
├── data_processing/      # 数据处理模块
│   ├── data_cleaner.py   # 数据清洗与预处理
│   └── data_storage.py   # 数据存储
├── model_training/       # 模型训练模块
│   ├── sentiment_analysis.py  # 情感分析模型
│   ├── hair_ner.py       # 发型NER模型
│   └── lda_topic_model.py     # LDA主题模型
├── recommendation_service/  # 推荐服务模块
│   └── recommendation_engine.py  # 推荐规则引擎
├── web_app/              # Web应用模块
│   └── app.py            # Flask后端服务
├── config/               # 配置模块
│   └── config.py         # 系统配置
├── main.py               # 项目主入口
└── README.md             # 项目说明文档
```

## 安装与运行

### 安装依赖

```bash
pip install scrapy flask pandas numpy torch transformers gensim scikit-learn jieba psycopg2-binary redis
```

### 配置文件

修改 `config/config.py` 中的配置信息，包括：
- 高德地图API密钥
- 数据库连接信息
- 模型配置

### 运行模块

使用 `main.py` 运行各个模块：

```bash
# 运行POI爬虫
python main.py --run poi_spider --cities 北京 上海 广州 深圳

# 运行小红书爬虫
python main.py --run xiaohongshu_spider

# 处理数据
python main.py --run process_data

# 训练模型
python main.py --run train_models

# 运行推荐服务
python main.py --run recommendation

# 启动Web应用
python main.py --run web_app
```

## API接口

### 推荐接口

```
POST /api/recommend
```

参数：
- `user_lat`：用户纬度
- `user_lon`：用户经度
- `recommendation_type`：推荐类型（distance, review, hair_style, topic）
- `style_entity`：发型实体（可选，用于hair_style推荐）
- `target_topic`：目标主题ID（可选，用于topic推荐）
- `top_n`：返回结果数量（默认10）

### 理发店列表接口

```
GET /api/salons
```

### 理发店详情接口

```
GET /api/salons/<salon_id>
```

### 主题列表接口

```
GET /api/topics
```

### 发型风格列表接口

```
GET /api/hair_styles
```

## 数据说明

- 数据采集严格遵守Robots协议，仅限学术研究使用
- 数据采用匿名化存储，不得用于商业目的
- 研究结果发布时，不对外公开原始数据或爬虫细节

## 学术伦理

- 本项目严格限制在学术研究范畴
- 数据采集采用最小数据集、非商业、匿名化原则
- 严禁绕过登录、加密等技术保护措施
- 不得用于任何商业目的

## 注意事项

1. 运行爬虫前请确保遵守相关网站的Robots协议
2. 模型训练需要大量标注数据，实际使用时需要准备
3. 本项目仅用于学术研究，请勿用于商业用途
4. 运行前请确保已正确配置数据库和API密钥

## 许可证

本项目仅供学术研究使用，版权归项目作者所有。
