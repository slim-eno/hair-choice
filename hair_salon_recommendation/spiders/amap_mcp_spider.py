# 基于高德地图API的理发店POI爬虫
import json
import requests
from config.config import AMAP_CONFIG

class AmapMCPSpider:
    """
    基于高德地图API的理发店POI爬虫，用于根据用户位置获取附近的理发店
    """
    
    def __init__(self, keywords='理发店'):
        self.keywords = keywords
        self.api_key = AMAP_CONFIG['key']
        self.poi_search_url = AMAP_CONFIG['poi_search_url']
        self.geo_url = 'https://restapi.amap.com/v3/geocode/geo'
        self.distance_url = 'https://restapi.amap.com/v3/distance'
    
    def search_nearby_salons(self, user_lat, user_lon, radius=5000, page=1, offset=20):
        """
        根据用户位置搜索附近的理发店
        
        Args:
            user_lat: 用户纬度
            user_lon: 用户经度
            radius: 搜索半径（米），默认5000米
            page: 页码，默认1
            offset: 每页结果数，默认20
            
        Returns:
            list: 理发店POI列表
        """
        try:
            # 构建请求参数
            params = {
                'keywords': self.keywords,
                'location': f'{user_lon},{user_lat}',  # 注意：高德地图API要求经纬度顺序为 经度,纬度
                'radius': str(radius),
                'page': str(page),
                'offset': str(offset),
                'key': self.api_key,
                'extensions': 'all'  # 使用all获取完整信息，包括照片等
            }
            
            # 发送请求
            response = requests.get(self.poi_search_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析结果
            result = response.json()
            
            if result.get('status') == '1' and 'pois' in result:
                salons = []
                for poi in result['pois']:
                    # 解析位置信息
                    location = poi.get('location', '')
                    lat = ''
                    lon = ''
                    if location:
                        lon, lat = location.split(',')
                    
                    # 解析评分信息
                    rating = ''
                    if 'biz_ext' in poi and isinstance(poi['biz_ext'], dict):
                        rating = poi['biz_ext'].get('rating', '')
                    
                    # 提取照片信息
                    photos = []
                    if 'photos' in poi and isinstance(poi['photos'], list):
                        for photo in poi['photos']:
                            if isinstance(photo, dict) and 'url' in photo:
                                photos.append(photo['url'])
                    
                    salon = {
                        'id': poi.get('id', ''),
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'latitude': lat,
                        'longitude': lon,
                        'phone': poi.get('tel', ''),
                        'rating': rating,
                        'category': poi.get('type', ''),
                        'city': poi.get('cityname', ''),
                        'photos': photos  # 添加照片列表
                    }
                    salons.append(salon)
                print(f"成功获取到 {len(salons)} 家附近的理发店")
                return salons
            else:
                print(f"获取附近理发店失败: {result}")
                return []
        except Exception as e:
            print(f"搜索附近理发店失败: {e}")
            return []
    
    def geocode_address(self, address, city=''):
        """
        将地址转换为经纬度
        
        Args:
            address: 地址字符串
            city: 城市名称，可选
            
        Returns:
            tuple: (经度, 纬度)，如果转换失败返回 (None, None)
        """
        try:
            # 构建请求参数
            params = {
                'address': address,
                'key': self.api_key
            }
            
            if city:
                params['city'] = city
            
            # 发送请求
            response = requests.get(self.geo_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析结果
            result = response.json()
            
            if result.get('status') == '1' and 'geocodes' in result and result['geocodes']:
                geocode = result['geocodes'][0]
                location = geocode['location'].split(',')
                return float(location[0]), float(location[1])  # 经度, 纬度
            else:
                print(f"地理编码失败: {result}")
                return None, None
        except Exception as e:
            print(f"地理编码失败: {e}")
            return None, None
    
    def get_distance(self, origins, destination):
        """
        计算多个起点到一个终点的距离
        
        Args:
            origins: 起点列表，格式为 ['经度1,纬度1', '经度2,纬度2', ...]
            destination: 终点，格式为 '经度,纬度'
            
        Returns:
            list: 距离列表，单位为米
        """
        try:
            # 构建请求参数
            params = {
                'origins': '|'.join(origins),
                'destination': destination,
                'type': '1',  # 驾车距离
                'key': self.api_key
            }
            
            # 发送请求
            response = requests.get(self.distance_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析结果
            result = response.json()
            
            if result.get('status') == '1' and 'results' in result:
                distances = []
                for res in result['results']:
                    distances.append(int(res['distance']))
                return distances
            else:
                print(f"计算距离失败: {result}")
                return []
        except Exception as e:
            print(f"计算距离失败: {e}")
            return []
