"""
BGE嵌入模型封装
"""
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from backend.utils.logger import get_logger

class BGEEmbedding:
    """BGE嵌入模型封装"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 模型配置
        self.model_name = config["bge"]["model_name"]
        model_path = config["bge"].get("model_path")
        self.model_path = Path(model_path) if model_path else None
        self.dimension = config["bge"]["dimension"]
        
        # 初始化模型
        self._load_model()
    
    def _load_model(self):
        """加载BGE模型"""
        try:
            # 如果有本地路径，优先使用本地模型
            if self.model_path and self.model_path.exists():
                self.logger.info(f"加载本地BGE模型: {self.model_path}")
                self.model = SentenceTransformer(str(self.model_path))
            else:
                self.logger.info(f"下载BGE模型: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                
                # 保存到本地（如果指定了路径）
                if self.model_path:
                    self.model_path.parent.mkdir(parents=True, exist_ok=True)
                    self.model.save(str(self.model_path))
                    self.logger.info(f"模型已保存到: {self.model_path}")
            
            # 设备配置
            if torch.cuda.is_available():
                self.device = "cuda"
                self.model = self.model.to("cuda")
                self.logger.info("使用GPU加速")
            else:
                self.device = "cpu"
                self.logger.info("使用CPU计算")
                
        except Exception as e:
            self.logger.error(f"BGE模型加载失败: {e}")
            raise
    
    def embed_text(self, text: str, normalize: bool = True) -> List[float]:
        """单个文本嵌入"""
        try:
            # 预处理文本
            text = self._preprocess_text(text)
            
            # 生成嵌入
            embedding = self.model.encode(
                text,
                normalize_embeddings=normalize,
                convert_to_tensor=False
            )
            
            return embedding.tolist()
            
        except Exception as e:
            self.logger.error(f"文本嵌入失败: {e}")
            raise
    
    def embed_batch(self, 
                   texts: List[str], 
                   batch_size: int = 32,
                   normalize: bool = True) -> List[List[float]]:
        """批量文本嵌入"""
        try:
            # 预处理文本
            texts = [self._preprocess_text(text) for text in texts]
            
            # 批量生成嵌入
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                convert_to_tensor=False,
                show_progress_bar=len(texts) > 10
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            self.logger.error(f"批量嵌入失败: {e}")
            raise
    
    def similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        try:
            embeddings = self.embed_batch([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def find_most_similar(self, 
                         query: str, 
                         candidates: List[str],
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """找到最相似的文本"""
        try:
            # 生成查询嵌入
            query_embedding = self.embed_text(query)
            
            # 生成候选嵌入
            candidate_embeddings = self.embed_batch(candidates)
            
            # 计算相似度
            similarities = cosine_similarity(
                [query_embedding], 
                candidate_embeddings
            )[0]
            
            # 排序并返回top_k结果
            results = []
            for i, similarity in enumerate(similarities):
                results.append({
                    "text": candidates[i],
                    "similarity": float(similarity),
                    "index": i
                })
            
            # 按相似度降序排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"相似度搜索失败: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not isinstance(text, str):
            text = str(text)
        
        # 去除多余空白
        text = ' '.join(text.split())
        
        # 长度限制（BGE模型通常有输入长度限制）
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]
            self.logger.warning(f"文本被截断到{max_length}字符")
        
        return text
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path) if self.model_path else None,
            "dimension": self.dimension,
            "device": self.device,
            "max_seq_length": getattr(self.model, 'max_seq_length', 512)
        }
    
    def validate_model(self) -> bool:
        """验证模型是否正常工作"""
        try:
            test_text = "这是一个测试文本"
            embedding = self.embed_text(test_text)
            
            # 检查嵌入维度
            if len(embedding) != self.dimension:
                self.logger.error(f"嵌入维度不匹配: 期望{self.dimension}, 实际{len(embedding)}")
                return False
            
            # 检查嵌入值范围
            if not all(isinstance(x, (int, float)) for x in embedding):
                self.logger.error("嵌入包含非数值")
                return False
            
            self.logger.info("BGE模型验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"模型验证失败: {e}")
            return False

class BGEReranker:
    """BGE重排序模型（可选）"""
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.logger = get_logger(__name__)
        
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.logger.info(f"重排序模型加载成功: {model_name}")
        except Exception as e:
            self.logger.warning(f"重排序模型加载失败: {e}")
            self.model = None
    
    def rerank(self, 
              query: str, 
              documents: List[str], 
              top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """重排序文档"""
        if not self.model:
            self.logger.warning("重排序模型不可用，跳过重排序")
            return [{"text": doc, "score": 0.0, "index": i} 
                   for i, doc in enumerate(documents)]
        
        try:
            # 构建查询-文档对
            pairs = [(query, doc) for doc in documents]
            
            # 计算重排序分数
            scores = self.model.predict(pairs)
            
            # 构建结果
            results = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                results.append({
                    "text": doc,
                    "score": float(score),
                    "index": i
                })
            
            # 按分数降序排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            if top_k:
                results = results[:top_k]
            
            return results
            
        except Exception as e:
            self.logger.error(f"重排序失败: {e}")
            return [{"text": doc, "score": 0.0, "index": i} 
                   for i, doc in enumerate(documents)]
