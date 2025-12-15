#!/usr/bin/env python3
"""
配置管理器
用于管理环境变量配置,支持Web界面配置
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.backup_dir = Path("backups/config")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log = Path("logs/config_audit.log")
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置状态"""
        config = {
            "ai_models": self._get_ai_models_config(),
            "data_sources": self._get_data_sources_config(),
            "databases": self._get_databases_config(),
            "system": self._get_system_config()
        }
        return config
    
    def _get_ai_models_config(self) -> Dict[str, Any]:
        """获取AI模型配置"""
        models = {}
        
        # DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        models["deepseek"] = {
            "name": "DeepSeek V3",
            "configured": bool(deepseek_key),
            "masked_key": self._mask_key(deepseek_key),
            "priority": 5,
            "description": "性价比最高,推荐使用",
            "get_url": "https://platform.deepseek.com/"
        }
        
        # 通义千问
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        models["dashscope"] = {
            "name": "通义千问",
            "configured": bool(dashscope_key),
            "masked_key": self._mask_key(dashscope_key),
            "priority": 4,
            "description": "国产稳定,可作为备用",
            "get_url": "https://dashscope.aliyun.com/"
        }
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        models["openai"] = {
            "name": "OpenAI GPT",
            "configured": bool(openai_key),
            "masked_key": self._mask_key(openai_key),
            "priority": 3,
            "description": "功能强大,需要国外网络",
            "get_url": "https://platform.openai.com/"
        }
        
        return models
    
    def _get_data_sources_config(self) -> Dict[str, Any]:
        """获取数据源配置"""
        sources = {}
        
        # FinnHub
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        sources["finnhub"] = {
            "name": "FinnHub",
            "configured": bool(finnhub_key),
            "masked_key": self._mask_key(finnhub_key),
            "description": "美股/港股新闻,免费60次/分钟",
            "get_url": "https://finnhub.io/"
        }
        
        # Alpha Vantage
        alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        sources["alpha_vantage"] = {
            "name": "Alpha Vantage",
            "configured": bool(alpha_key),
            "masked_key": self._mask_key(alpha_key),
            "description": "美股数据,免费5次/分钟",
            "get_url": "https://www.alphavantage.co/"
        }
        
        return sources
    
    def _get_databases_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        databases = {}
        
        # MongoDB
        mongodb_enabled = os.getenv("USE_MONGODB_STORAGE", "false").lower() == "true"
        databases["mongodb"] = {
            "name": "MongoDB",
            "enabled": mongodb_enabled,
            "host": os.getenv("MONGODB_HOST", "mongodb"),
            "port": os.getenv("MONGODB_PORT", "27017"),
            "database": os.getenv("MONGODB_DATABASE", "tradingagents")
        }
        
        # Redis
        redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        databases["redis"] = {
            "name": "Redis",
            "enabled": redis_enabled,
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": os.getenv("REDIS_PORT", "6379")
        }
        
        return databases
    
    def _get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return {
            "timezone": os.getenv("TZ", "Asia/Shanghai"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "memory_enabled": os.getenv("MEMORY_ENABLED", "true").lower() == "true",
            "cache_strategy": os.getenv("TA_CACHE_STRATEGY", "integrated")
        }
    
    def update_config(self, key: str, value: str, user: str = "system") -> Dict[str, Any]:
        """更新配置"""
        try:
            # 备份当前配置
            self._backup_config()
            
            # 读取现有配置
            env_vars = self._read_env_file()
            
            # 更新变量
            env_vars[key] = value
            
            # 写入文件
            self._write_env_file(env_vars)
            
            # 重载环境变量
            self._reload_env()
            
            # 🔥 自动同步LLM配置到MongoDB（针对小白用户开箱即用）
            if key in ["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY"]:
                self._sync_llm_config_to_mongodb()
            
            # 记录审计日志
            self._log_config_change(user, "update", key)
            
            return {
                "success": True,
                "message": "配置已保存并同步到数据库",
                "backup_created": True
            }
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return {
                "success": False,
                "message": f"配置更新失败: {str(e)}"
            }
    
    def verify_api_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """验证API密钥"""
        if provider == "deepseek":
            return self._verify_deepseek(api_key)
        elif provider == "dashscope":
            return self._verify_dashscope(api_key)
        elif provider == "finnhub":
            return self._verify_finnhub(api_key)
        elif provider == "alpha_vantage":
            return self._verify_alpha_vantage(api_key)
        else:
            return {
                "verified": False,
                "message": "不支持的提供商"
            }
    
    def _verify_deepseek(self, api_key: str) -> Dict[str, Any]:
        """验证DeepSeek API密钥"""
        try:
            import requests
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "verified": True,
                    "message": "验证成功",
                    "details": {"model": "deepseek-chat", "available": True}
                }
            else:
                return {
                    "verified": False,
                    "message": f"验证失败: HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "verified": False,
                "message": f"验证失败: {str(e)}"
            }
    
    def _verify_dashscope(self, api_key: str) -> Dict[str, Any]:
        """验证通义千问API密钥"""
        try:
            import requests
            response = requests.get(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            
            # 通义千问即使密钥正确,GET请求也会返回405,但401表示密钥错误
            if response.status_code != 401:
                return {
                    "verified": True,
                    "message": "验证成功"
                }
            else:
                return {
                    "verified": False,
                    "message": "API密钥无效"
                }
        except Exception as e:
            return {
                "verified": False,
                "message": f"验证失败: {str(e)}"
            }
    
    def _verify_finnhub(self, api_key: str) -> Dict[str, Any]:
        """验证FinnHub API密钥"""
        try:
            import requests
            response = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "verified": True,
                    "message": "验证成功"
                }
            else:
                return {
                    "verified": False,
                    "message": f"验证失败: HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "verified": False,
                "message": f"验证失败: {str(e)}"
            }
    
    def _verify_alpha_vantage(self, api_key: str) -> Dict[str, Any]:
        """验证Alpha Vantage API密钥"""
        try:
            import requests
            response = requests.get(
                f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Error Message" not in data:
                    return {
                        "verified": True,
                        "message": "验证成功"
                    }
            
            return {
                "verified": False,
                "message": "API密钥无效"
            }
        except Exception as e:
            return {
                "verified": False,
                "message": f"验证失败: {str(e)}"
            }
    
    def _backup_config(self):
        """备份配置文件"""
        if self.env_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f".env.backup.{timestamp}"
            shutil.copy(self.env_file, backup_file)
            logger.info(f"配置已备份到: {backup_file}")
    
    def _read_env_file(self) -> Dict[str, str]:
        """读取.env文件"""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def _write_env_file(self, env_vars: Dict[str, str]):
        """写入.env文件"""
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write("# ============================================\n")
            f.write("# TradingAgents 配置文件\n")
            f.write(f"# 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ============================================\n\n")
            
            # 分组写入
            ai_models = {}
            data_sources = {}
            databases = {}
            system = {}
            others = {}
            
            for key, value in env_vars.items():
                if key in ["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"]:
                    ai_models[key] = value
                elif key in ["FINNHUB_API_KEY", "ALPHA_VANTAGE_API_KEY"]:
                    data_sources[key] = value
                elif key.startswith("MONGODB_") or key.startswith("REDIS_") or key == "USE_MONGODB_STORAGE":
                    databases[key] = value
                elif key in ["TZ", "LOG_LEVEL", "MEMORY_ENABLED", "TA_CACHE_STRATEGY"]:
                    system[key] = value
                else:
                    others[key] = value
            
            # AI模型
            if ai_models:
                f.write("# AI模型API密钥\n")
                for key, value in ai_models.items():
                    f.write(f"{key}={value}\n")
                f.write("\n")
            
            # 数据源
            if data_sources:
                f.write("# 数据源API密钥\n")
                for key, value in data_sources.items():
                    f.write(f"{key}={value}\n")
                f.write("\n")
            
            # 数据库
            if databases:
                f.write("# 数据库配置\n")
                for key, value in databases.items():
                    f.write(f"{key}={value}\n")
                f.write("\n")
            
            # 系统
            if system:
                f.write("# 系统配置\n")
                for key, value in system.items():
                    f.write(f"{key}={value}\n")
                f.write("\n")
            
            # 其他
            if others:
                f.write("# 其他配置\n")
                for key, value in others.items():
                    f.write(f"{key}={value}\n")
    
    def _reload_env(self):
        """重载环境变量"""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            logger.info("环境变量已重载")
        except Exception as e:
            logger.error(f"环境变量重载失败: {e}")
    
    def _mask_key(self, key: Optional[str]) -> str:
        """掩码密钥"""
        if not key:
            return ""
        if len(key) <= 8:
            return "****"
        return f"{key[:4]}****{key[-4:]}"
    
    def _log_config_change(self, user: str, action: str, key: str):
        """记录配置变更"""
        try:
            with open(self.audit_log, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} | {user} | {action} | {key}\n")
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")
    
    def _sync_llm_config_to_mongodb(self):
        """同步LLM配置到MongoDB数据库（开箱即用功能）"""
        try:
            from pymongo import MongoClient
            
            # 从环境变量读取MongoDB连接信息
            mongo_uri = os.getenv("MONGODB_CONNECTION_STRING") or \
                       f"mongodb://{os.getenv('MONGODB_USERNAME', 'admin')}:" \
                       f"{os.getenv('MONGODB_PASSWORD', 'tradingagents123')}@" \
                       f"{os.getenv('MONGODB_HOST', 'mongodb')}:" \
                       f"{os.getenv('MONGODB_PORT', '27017')}/" \
                       f"?authSource={os.getenv('MONGODB_AUTH_SOURCE', 'admin')}"
            
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db = client[os.getenv("MONGODB_DATABASE", "tradingagents")]
            
            # 读取当前环境变量中的API Key
            deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
            dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            
            # 构建LLM配置
            llm_configs = []
            
            # 通义千问（阿里百炼）
            if dashscope_key:
                llm_configs.append({
                    "provider": "zhipu",
                    "model_name": "glm-4",
                    "api_key": dashscope_key,
                    "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                    "enabled": True,
                    "priority": 1,
                    "max_tokens": 4000,
                    "temperature": 0.7
                })
            
            # DeepSeek
            if deepseek_key:
                llm_configs.append({
                    "provider": "deepseek",
                    "model_name": "deepseek-chat",
                    "api_key": deepseek_key,
                    "base_url": "https://api.deepseek.com",
                    "enabled": True,
                    "priority": 2,
                    "max_tokens": 4000,
                    "temperature": 0.7
                })
            
            # OpenAI
            if openai_key:
                llm_configs.append({
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "api_key": openai_key,
                    "base_url": "https://api.openai.com/v1",
                    "enabled": True,
                    "priority": 3,
                    "max_tokens": 4000,
                    "temperature": 0.7
                })
            
            # 保存到数据库
            if llm_configs:
                llm_config_doc = {
                    "config_type": "llm",
                    "version": 1,
                    "llm_configs": llm_configs,
                    "updated_at": datetime.now()
                }
                
                result = db.system_config.update_one(
                    {"config_type": "llm"},
                    {"$set": llm_config_doc},
                    upsert=True
                )
                
                logger.info(f"✅ LLM配置已自动同步到MongoDB (匹配:{result.matched_count}, 修改:{result.modified_count})")
            
            client.close()
            
        except Exception as e:
            logger.error(f"⚠️ LLM配置同步到MongoDB失败: {e}")
            # 不抛出异常，避免影响主流程


# 全局实例
config_manager = ConfigManager()
