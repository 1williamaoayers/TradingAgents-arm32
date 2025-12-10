"""
节点输出存储模块
每个 LangGraph 节点的输出立即保存到 MongoDB，确保数据不丢失
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient
import os

from tradingagents.utils.logging_manager import get_logger

logger = get_logger(__name__)


class NodeStorage:
    """节点输出存储管理器"""
    
    def __init__(self):
        """初始化 MongoDB 连接"""
        self.enabled = os.getenv("USE_MONGODB_STORAGE", "false").lower() == "true"
        
        if not self.enabled:
            logger.warning("⚠️ [NodeStorage] MongoDB 存储未启用，节点输出将不会保存")
            self.collection = None
            return
        
        try:
            connection_string = os.getenv("MONGODB_CONNECTION_STRING")
            if not connection_string:
                logger.error("❌ [NodeStorage] MONGODB_CONNECTION_STRING 未设置")
                self.enabled = False
                return
            
            database_name = os.getenv("MONGODB_DATABASE", "tradingagents")
            
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.collection = self.db['analysis_nodes']
            
            # 创建索引
            self.collection.create_index([("session_id", 1), ("timestamp", 1)])
            self.collection.create_index([("session_id", 1), ("node_name", 1)])
            
            logger.info(f"✅ [NodeStorage] MongoDB 连接成功: {database_name}.analysis_nodes")
            
        except Exception as e:
            logger.error(f"❌ [NodeStorage] MongoDB 连接失败: {e}")
            self.enabled = False
            self.collection = None
    
    def save_node_output(
        self,
        session_id: str,
        node_name: str,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存节点输出到 MongoDB
        
        Args:
            session_id: 分析会话 ID
            node_name: 节点名称（如 "market_analyst", "bull_researcher"）
            output: 节点输出内容（可以是字符串或字典）
            metadata: 可选的元数据（如耗时、token 使用等）
        
        Returns:
            是否保存成功
        """
        if not self.enabled or not self.collection:
            return False
        
        try:
            document = {
                'session_id': session_id,
                'node_name': node_name,
                'output': output,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            
            result = self.collection.insert_one(document)
            
            # 计算输出大小
            output_size = len(str(output))
            logger.info(
                f"✅ [NodeStorage] 保存节点输出: {node_name} "
                f"(session={session_id[:8]}..., size={output_size} 字符)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ [NodeStorage] 保存节点输出失败: {node_name}, 错误: {e}")
            return False
    
    def get_node_output(
        self,
        session_id: str,
        node_name: str
    ) -> Optional[Any]:
        """
        获取指定节点的输出
        
        Args:
            session_id: 分析会话 ID
            node_name: 节点名称
        
        Returns:
            节点输出内容，如果不存在返回 None
        """
        if not self.enabled or not self.collection:
            return None
        
        try:
            document = self.collection.find_one({
                'session_id': session_id,
                'node_name': node_name
            })
            
            if document:
                return document.get('output')
            return None
            
        except Exception as e:
            logger.error(f"❌ [NodeStorage] 获取节点输出失败: {node_name}, 错误: {e}")
            return None
    
    def get_all_nodes(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的所有节点输出
        
        Args:
            session_id: 分析会话 ID
        
        Returns:
            字典，键为节点名称，值为输出内容
        """
        if not self.enabled or not self.collection:
            return {}
        
        try:
            documents = self.collection.find({
                'session_id': session_id
            }).sort('timestamp', 1)
            
            nodes = {}
            for doc in documents:
                node_name = doc.get('node_name')
                output = doc.get('output')
                nodes[node_name] = output
            
            logger.info(f"📊 [NodeStorage] 获取会话节点: {session_id[:8]}..., 共 {len(nodes)} 个节点")
            return nodes
            
        except Exception as e:
            logger.error(f"❌ [NodeStorage] 获取会话节点失败: {e}")
            return {}


# 全局单例
_node_storage = None

def get_node_storage() -> NodeStorage:
    """获取全局 NodeStorage 实例"""
    global _node_storage
    if _node_storage is None:
        _node_storage = NodeStorage()
    return _node_storage
