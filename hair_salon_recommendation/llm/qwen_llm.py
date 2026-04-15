# 大模型调用工具类
import requests
import json

class QwenLLM:
    """调用qwen3-max大模型进行文本生成"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_text(self, prompt, temperature=0.7, max_tokens=2000):
        """调用大模型生成文本"""
        try:
            payload = {
                "model": "qwen3-max",
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
            response = requests.post(self.base_url, headers=self.headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "output" in result and "choices" in result["output"] and len(result["output"]["choices"]) > 0:
                return result["output"]["choices"][0]["message"]["content"]
            else:
                print(f"大模型调用失败: {result}")
                return ""
        except Exception as e:
            print(f"大模型调用异常: {e}")
            return ""
    
    def generate_salon_review(self, salon_name, posts):
        """生成理发店的毒舌辣评"""
        # 提取帖子内容
        post_contents = [post["content"] for post in posts if "content" in post]
        if not post_contents:
            return f"{salon_name}: 暂无评价，可能是太普通了吧~"
        
        # 构建prompt
        prompt = f"""你现在是一个毒舌辣评家，请对理发店{salon_name}进行毒舌评价，要求：
1. 基于以下用户评价：
{"\n".join(post_contents[:5])}  # 最多使用5篇帖子
2. 语言风格：毒舌、犀利、幽默，带有吐槽感
3. 评价要具体，不能太笼统
4. 字数控制在100-200字之间
5. 开头直接点名理发店，不要铺垫
6. 结尾可以加一句总结性的吐槽
"""
       
        return self.generate_text(prompt, temperature=0.8, max_tokens=500)
    
    def generate_recommendation_report(self, recommended_salons, similar_posts):
        """生成推荐报告"""
        # 构建prompt
        salon_list = []
        for salon in recommended_salons:
            salon_list.append(f"- {salon['salon_name']} (评分: {salon.get('rating', '暂无')}, 距离: {salon['distance']:.2f}km)\n  地址: {salon.get('address', '暂无')}")
        
        post_list = []
        for post in similar_posts[:3]:
            post_list.append(f"- {post['title']}")
        
        prompt = f"""你现在是一个专业的理发店推荐顾问，请基于以下推荐结果生成一份推荐报告：
1. 推荐的理发店列表：
{"\n".join(salon_list)}

2. 相似度最高的帖子：
{"\n".join(post_list)}

3. 报告要求：
- 语言风格：专业、友好、有说服力
- 结构清晰，包含：推荐理由、各理发店特色、总结建议
- 字数控制在500-800字之间
- 突出每个理发店的优势和适合的人群
- 结尾给出个性化的推荐建议
        """
        
        return self.generate_text(prompt, temperature=0.7, max_tokens=1000)
    
    def generate_recommendation_phrase(self, recommended_salons):
        """生成推荐语"""
        # 构建prompt
        salon_list = []
        for salon in recommended_salons[:3]:
            salon_list.append(f"- {salon['salon_name']} (评分: {salon.get('rating', '暂无')}, 距离: {salon['distance']:.2f}km)\n  地址: {salon.get('address', '暂无')}")
        
        prompt = f"""请为以下推荐的理发店生成一句吸引人的推荐语：
{"\n".join(salon_list)}

要求：
1. 语言简洁、有力，有吸引力
2. 突出推荐的核心优势
3. 字数控制在50-100字之间
4. 适合作为推荐结果的标题或引导语
        """
        
        return self.generate_text(prompt, temperature=0.8, max_tokens=200)