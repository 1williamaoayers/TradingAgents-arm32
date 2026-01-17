"""
AI 关键词生成工具
利用 LLM 生成股票的关联关键词（公司名、负责人、主打产品等），用于增强新闻搜索的精准度。
"""
import os
import logging
from typing import List, Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class KeywordGenerator:
    """AI 关键词生成器"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.enabled = OpenAI is not None and self.api_key is not None
        
        if not self.enabled:
            if OpenAI is None:
                logger.warning("⚠️ openai 库未安装，AI 关键词生成功能已禁用")
            if self.api_key is None:
                logger.warning("⚠️ DEEPSEEK_API_KEY 未设置，AI 关键词生成功能已禁用")

    async def generate_keywords(self, symbol: str, company_name: Optional[str] = None) -> List[str]:
        """
        生成股票关联关键词
        """
        if not self.enabled:
            return [symbol] + ([company_name] if company_name else [])

        # 智能识别市场以调整提示词
        is_hk = symbol.isdigit() and len(symbol) <= 5 or ".HK" in symbol.upper()
        
        market_suffix = " (Focus on HK stock market terms like '南向资金', '港股通' if applicable)" if is_hk else ""
        
        system_prompt = f"""
        You are a financial expert. Return 4-6 ESSENTIAL keywords for this stock to help search news/notices/reports.
        Rules:
        1. Include the FULL company name AND its common SHORT name (e.g., '小米' for '小米集团').
        2. Include KEY persons (CEO/Founder).
        3. Include KEY brands/products.
        4. {market_suffix}
        5. Output format: Comma separated string ONLY. No explanations.
        """
        
        user_input = f"Stock Code: {symbol}"
        if company_name:
            user_input += f", Company Name: {company_name}"

        try:
            import asyncio
            
            def _fetch_from_ai():
                client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    stream=False,
                    timeout=10
                )
                return response.choices[0].message.content.strip()

            content = await asyncio.to_thread(_fetch_from_ai)
            
            # 清理和分割结果
            keywords = [k.strip() for k in content.split(',') if k.strip()]
            
            # 基础保障：代码、公司名、简名
            if company_name and len(company_name) > 2:
                short_name = company_name.replace("集团", "").replace("股份", "").replace("有限责任", "").replace("公司", "")
                if short_name and short_name not in keywords:
                    keywords.append(short_name)

            if company_name and company_name not in keywords:
                keywords.insert(0, company_name)
            if symbol not in keywords:
                keywords.insert(0, symbol)
                
            logger.info(f"✨ AI 生成增強關鍵詞 ({symbol}): {keywords}")
            return keywords
            
        except Exception as e:
            logger.warning(f"⚠️ AI 关键词生成失败 ({symbol}): {e}. 退回到基础模式。")
            return [symbol] + ([company_name] if company_name else [])

    def is_relevant(self, title: str, content: str, keywords: List[str]) -> bool:
        """
        判断新闻是否相关
        
        Args:
            title: 新闻标题
            content: 新闻内容或摘要
            keywords: 关键词列表
            
        Returns:
            是否相关
        """
        if not keywords:
            return True
            
        t = (title + " " + (content or "")).lower()
        # 只要包含任何一个关键词即认为相关
        return any(k.lower() in t for k in keywords)

# 单例
_generator = None

def get_keyword_generator():
    global _generator
    if _generator is None:
        _generator = KeywordGenerator()
    return _generator
