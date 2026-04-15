# Flask后端服务
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import os
from recommendation_service.recommendation_engine import RecommendationEngine

app = Flask(__name__, static_url_path='/static', static_folder='static')

# 初始化推荐引擎
recommendation_engine = RecommendationEngine()

# 检查小红书分析器是否可用
XIAOHONGSHU_AVAILABLE = hasattr(recommendation_engine, 'xiaohongshu_analyzer') and recommendation_engine.xiaohongshu_analyzer is not None



# 静态文件服务 - 支持src目录下的图片
@app.route('/static/<path:filename>')
def static_files(filename):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, filename)

# 支持直接访问src目录下的图片
@app.route('/src/<path:filename>')
def src_files(filename):
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'src')
    return send_from_directory(src_dir, filename)

# 根路径返回HTML页面
@app.route('/')
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'index.html')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取HTML文件失败: {e}")
        return f"读取HTML文件失败: {e}", 500

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """推荐API接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        
        # 验证必要参数
        if not all(key in data for key in ['user_lat', 'user_lon', 'recommendation_type']):
            return jsonify({'error': '缺少必要参数'}), 400
        
        user_lat = float(data['user_lat'])
        user_lon = float(data['user_lon'])
        recommendation_type = data['recommendation_type']
        style_entity = data.get('style_entity')
        target_topic = data.get('target_topic')
        top_n = int(data.get('top_n', 10))
        radius = int(data.get('radius', 5000))
        
        # 从数据库获取数据
        salons_df = get_salons_data()
        posts_df = get_posts_data()
        
        # 获取推荐结果
        recommendation_result = recommendation_engine.get_recommendations(
            salons_df=salons_df,
            posts_df=posts_df,
            user_lat=user_lat,
            user_lon=user_lon,
            recommendation_type=recommendation_type,
            style_entity=style_entity,
            target_topic=target_topic,
            top_n=top_n,
            radius=radius
        )
        
        # 提取推荐结果
        recommended = recommendation_result['recommendations']
        recommendation_phrase = recommendation_result['recommendation_phrase']
        recommendation_report = recommendation_result['recommendation_report']
        salon_reviews = recommendation_result['salon_reviews']
        
        # 转换为JSON格式
        result = recommended.to_dict('records')
        
        # 获取相似度最高的帖子链接
        similar_posts = []
        if XIAOHONGSHU_AVAILABLE and posts_df is not None and not posts_df.empty:
            # 这里可以添加获取相似度最高的帖子链接的逻辑
            similar_posts = posts_df.sort_values(by='positive_prob', ascending=False).head(3)[['title', 'url']].to_dict('records')
        
        return jsonify({
            'status': 'success',
            'recommendation_type': recommendation_type,
            'count': len(result),
            'results': result,
            'similar_posts': similar_posts,
            'recommendation_phrase': recommendation_phrase,
            'recommendation_report': recommendation_report,
            'salon_reviews': salon_reviews
        })
    
    except Exception as e:
        print(f"API推荐错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/salons', methods=['GET'])
def get_salons():
    """获取理发店列表"""
    try:
        # 获取请求参数
        user_lat = float(request.args.get('user_lat', 39.9087))  # 默认北京坐标
        user_lon = float(request.args.get('user_lon', 116.3975))  # 默认北京坐标
        
        # 使用推荐引擎获取附近的理发店
        recommendation_result = recommendation_engine.get_recommendations(
            salons_df=pd.DataFrame(),
            posts_df=pd.DataFrame(),
            user_lat=user_lat,
            user_lon=user_lon,
            recommendation_type='distance',
            top_n=20
        )
        
        # 提取推荐结果
        recommended = recommendation_result['recommendations']
        
        return jsonify({
            'status': 'success',
            'count': len(recommended),
            'results': recommended.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/salons/<salon_id>', methods=['GET'])
def get_salon_detail(salon_id):
    """获取理发店详情"""
    try:
        # 获取请求参数
        user_lat = float(request.args.get('user_lat', 39.9087))  # 默认北京坐标
        user_lon = float(request.args.get('user_lon', 116.3975))  # 默认北京坐标
        
        # 首先获取所有理发店数据
        recommendation_result = recommendation_engine.get_recommendations(
            salons_df=pd.DataFrame(),
            posts_df=pd.DataFrame(),
            user_lat=user_lat,
            user_lon=user_lon,
            recommendation_type='distance',
            top_n=50
        )
        
        # 提取推荐结果
        recommended = recommendation_result['recommendations']
        
        # 根据salon_id查找对应的理发店
        salon = recommended[recommended['salon_id'] == salon_id]
        
        if salon.empty:
            return jsonify({'error': '理发店不存在'}), 404
        
        # 获取理发店名称
        salon_name = salon.iloc[0]['salon_name']
        
        # 获取帖子数据
        posts_df = pd.DataFrame()
        if XIAOHONGSHU_AVAILABLE:
            # 爬取并分析小红书帖子
            xhs_posts = recommendation_engine.xiaohongshu_analyzer.crawl_and_analyze([salon_name])
            if xhs_posts:
                posts_df = pd.DataFrame(xhs_posts)
        
        # 构建响应
        salon_detail = {
            'salon_id': salon.iloc[0]['salon_id'],
            'name': salon.iloc[0]['salon_name'],
            'address': salon.iloc[0].get('address', '暂无'),
            'latitude': salon.iloc[0].get('latitude', 0),
            'longitude': salon.iloc[0].get('longitude', 0),
            'phone': salon.iloc[0].get('phone', '暂无'),
            'rating': salon.iloc[0].get('rating', '暂无'),
            'category': salon.iloc[0].get('category', '暂无'),
            'city': salon.iloc[0].get('city', '暂无'),
            'posts': []
        }
        
        # 添加帖子数据
        if not posts_df.empty:
            salon_posts = posts_df[posts_df['salon_name'] == salon_name].head(10)
            for _, post in salon_posts.iterrows():
                salon_detail['posts'].append({
                    'post_id': post['post_id'],
                    'title': post['title'],
                    'content': post['content'],
                    'likes': post['likes'],
                    'collects': post['collects'],
                    'comments': post['comments'],
                    'publish_time': post['publish_time'],
                    'url': post['url'],
                    'positive_prob': post['positive_prob'] if 'positive_prob' in post else 0
                })
        
        return jsonify({
            'status': 'success',
            'result': salon_detail
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """获取LDA主题列表"""
    try:
        # 模拟主题数据
        topics = [
            {'topic_id': 0, 'keywords': ['气垫烫', '发型', '效果', '满意', '老师']},
            {'topic_id': 1, 'keywords': ['辛芷蕾发型', '技术', '专业', '好看', '朋友']},
            {'topic_id': 2, 'keywords': ['法式烫', '环境', '服务', '周到', '满意']},
            {'topic_id': 3, 'keywords': ['染发', '颜色', '喜欢', '性价比', '高']},
            {'topic_id': 4, 'keywords': ['发型设计', '脸型', '适合', '专业', '时尚']}
        ]
        
        return jsonify({
            'status': 'success',
            'count': len(topics),
            'results': topics
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hair_styles', methods=['GET'])
def get_hair_styles():
    """获取发型风格列表"""
    try:
        # 这里返回预定义的发型风格列表
        hair_styles = [
            '辛芷蕾发型', '气垫烫', '姬发式', '羊毛卷', '法式烫', '离子烫',
            '空气刘海', '八字刘海', '齐刘海', '中分', '偏分', '波波头',
            '锁骨发', '短发', '中长发', '烫发', '染发', '直发', '卷发'
        ]
        
        return jsonify({
            'status': 'success',
            'count': len(hair_styles),
            'results': hair_styles
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_salons_data() -> pd.DataFrame:
    """获取理发店数据"""
    # 这里返回空DataFrame，让推荐引擎自动调用高德地图API获取数据
    return pd.DataFrame()

def get_posts_data() -> pd.DataFrame:
    """获取帖子数据"""
    # 这里返回空DataFrame，让推荐引擎自动调用小红书爬虫获取数据
    return pd.DataFrame()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
