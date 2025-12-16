"""
统一情绪分析工具 - 使用Alpha Vantage和FinnHub
替代Reddit API，提供市场情绪分析
"""
import requests
import os
from typing import Dict, Any

# 导入日志
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('sentiment_tools')


def get_alpha_vantage_sentiment(ticker: str) -> Dict[str, Any]:
    """使用Alpha Vantage获取新闻情绪"""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        logger.warning("⚠️ ALPHA_VANTAGE_API_KEY未配置")
        return {'error': 'API Key未配置'}
    
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={api_key}"
    
    try:
        logger.info(f"📊 [Alpha Vantage] 获取{ticker}的新闻情绪...")
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'feed' in data and len(data['feed']) > 0:
            sentiments = []
            for item in data['feed']:
                for ticker_sentiment in item.get('ticker_sentiment', []):
                    if ticker_sentiment['ticker'] == ticker:
                        sentiments.append(float(ticker_sentiment['ticker_sentiment_score']))
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                result = {
                    'source': 'Alpha Vantage',
                    'sentiment_score': avg_sentiment,
                    'sentiment_label': 'Bullish' if avg_sentiment > 0.15 else 'Bearish' if avg_sentiment < -0.15 else 'Neutral',
                    'news_count': len(data['feed']),
                    'positive_count': len([s for s in sentiments if s > 0.15]),
                    'negative_count': len([s for s in sentiments if s < -0.15]),
                    'neutral_count': len([s for s in sentiments if -0.15 <= s <= 0.15])
                }
                logger.info(f"✅ [Alpha Vantage] 成功获取{ticker}情绪: {result['sentiment_label']}")
                return result
            else:
                logger.warning(f"⚠️ [Alpha Vantage] 未找到{ticker}的情绪数据")
                return {'error': f'未找到{ticker}的情绪数据'}
        else:
            logger.warning(f"⚠️ [Alpha Vantage] API返回数据为空")
            return {'error': 'API返回数据为空'}
            
    except Exception as e:
        logger.error(f"❌ [Alpha Vantage] 获取情绪失败: {e}")
        return {'error': str(e)}


from langchain_core.tools import tool

@tool
def get_combined_sentiment(ticker: str) -> str:
    """组合多个来源的情绪数据生成报告
    
    Args:
        ticker: 股票代码
    """
    from datetime import datetime
    
    logger.info(f"📊 [情绪分析] 开始分析{ticker}的市场情绪...")
    
    av_sentiment = get_alpha_vantage_sentiment(ticker)
    
    report = f"""# 市场情绪分析报告

## 股票代码: {ticker}
## 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、新闻情绪分析（Alpha Vantage）

"""
    
    if 'error' not in av_sentiment:
        report += f"""
**情绪评分**: {av_sentiment['sentiment_score']:.3f}  
**情绪标签**: {av_sentiment['sentiment_label']}  
**新闻数量**: {av_sentiment['news_count']}条  
**正面新闻**: {av_sentiment['positive_count']}条  
**负面新闻**: {av_sentiment['negative_count']}条  
**中性新闻**: {av_sentiment['neutral_count']}条

**分析说明**:
- 情绪评分范围: -1.0 (极度悲观) 到 +1.0 (极度乐观)
- 评分 > 0.15: 看涨(Bullish)
- 评分 < -0.15: 看跌(Bearish)
- -0.15 ≤ 评分 ≤ 0.15: 中性(Neutral)

---

## 二、综合情绪评估

**综合情绪评分**: {av_sentiment['sentiment_score']:.3f}  
**综合情绪标签**: {av_sentiment['sentiment_label']}  
**市场情绪**: {'乐观' if av_sentiment['sentiment_label'] == 'Bullish' else '悲观' if av_sentiment['sentiment_label'] == 'Bearish' else '中性'}

**情绪指数**: {int((av_sentiment['sentiment_score'] + 1) * 50)}/100
- 0-30: 极度悲观
- 31-45: 悲观
- 46-55: 中性
- 56-70: 乐观
- 71-100: 极度乐观

**投资建议**: {'市场情绪偏向积极，投资者信心较强，可考虑适当增持' if av_sentiment['sentiment_label'] == 'Bullish' else '市场情绪偏向消极，投资者信心不足，建议谨慎观望或适当减仓' if av_sentiment['sentiment_label'] == 'Bearish' else '市场情绪中性，投资者观点分歧，建议保持现有仓位并密切关注'}

---

## 三、风险提示

1. 情绪分析基于新闻数据，可能存在滞后性
2. 市场情绪可能快速变化，建议结合基本面和技术面分析
3. 本报告仅供参考，不构成投资建议
"""
    else:
        report += f"""
⚠️ **数据获取失败**: {av_sentiment['error']}

**可能原因**:
1. API限额已用完
2. 网络连接问题
3. 股票代码格式不正确

**建议**:
- 稍后重试
- 检查API配置
- 使用其他分析方法
"""
    
    logger.info(f"✅ [情绪分析] {ticker}情绪分析报告生成完成")
    return report
