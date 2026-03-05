"""
增强版自主研究智能体 - 集成真实搜索引擎
支持 Tavily API 和 DuckDuckGo 搜索
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  Tavily 未安装，将使用模拟搜索")

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class RealSearchProvider:
    """真实搜索引擎提供者"""
    
    def __init__(self):
        self.tavily_client = None
        if TAVILY_AVAILABLE:
            api_key = os.getenv("TAVILY_API_KEY")
            if api_key:
                self.tavily_client = TavilyClient(api_key=api_key)
                print("✅ Tavily 搜索已启用")
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """
        执行真实网络搜索
        
        优先级: Tavily > DuckDuckGo > 模拟搜索
        """
        # 方法1: Tavily (最佳选择 - 专为 AI 优化)
        if self.tavily_client:
            try:
                response = self.tavily_client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="advanced",
                    include_answer=True
                )
                
                results = []
                for item in response.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "source_type": "web",
                        "date": "2025-02",
                        "relevance_score": item.get("score", 0.5)
                    })
                
                # 如果 Tavily 提供了直接答案
                if "answer" in response and response["answer"]:
                    results.insert(0, {
                        "title": "AI 生成摘要",
                        "url": query,
                        "snippet": response["answer"],
                        "source_type": "ai_summary",
                        "date": "2025-02",
                        "relevance_score": 1.0
                    })
                
                return results
            except Exception as e:
                print(f"⚠️  Tavily 搜索失败: {e}")
        
        # 方法2: DuckDuckGo (免费替代)
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(
                        query,
                        max_results=max_results
                    ))
                    
                    return [{
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "source_type": "web",
                        "date": "recent"
                    } for r in search_results]
            except Exception as e:
                print(f"⚠️  DuckDuckGo 搜索失败: {e}")
        
        # 方法3: 模拟搜索（后备方案）
        print("⚠️  使用模拟搜索结果")
        return self._mock_search(query, max_results)
    
    def _mock_search(self, query: str, max_results: int) -> List[dict]:
        """模拟搜索结果（用于开发和测试）"""
        return [
            {
                "title": f"关于 {query} 的权威指南",
                "url": f"https://example.com/guide-{i}",
                "snippet": f"深入探讨 {query} 的各个方面，包括定义、应用场景和最佳实践...",
                "source_type": "article",
                "date": "2025-02"
            }
            for i in range(max_results)
        ]


# 修改原始的 web_search_tool 以使用真实搜索
def create_real_search_tool():
    """创建真实搜索工具"""
    from langchain_core.tools import tool
    import json
    
    search_provider = RealSearchProvider()
    
    @tool
    def web_search_tool(query: str, num_results: int = 5) -> str:
        """
        执行网络搜索并返回结果
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果的 JSON 字符串
        """
        results = search_provider.search(query, num_results)
        return json.dumps(results, ensure_ascii=False, indent=2)
    
    return web_search_tool


# 网页内容提取工具
def create_content_extractor():
    """创建网页内容提取工具"""
    from langchain_core.tools import tool
    
    @tool
    def extract_webpage_content(url: str) -> str:
        """
        提取网页的主要内容
        
        Args:
            url: 网页URL
            
        Returns:
            提取的文本内容
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Research Agent)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 限制长度
            return text[:3000] + "..." if len(text) > 3000 else text
            
        except Exception as e:
            return f"无法提取内容: {str(e)}"
    
    return extract_webpage_content


# 使用示例
if __name__ == "__main__":
    # 测试搜索功能
    provider = RealSearchProvider()
    results = provider.search("LangGraph tutorial", max_results=3)
    
    print("\n🔍 搜索测试结果:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   摘要: {result['snippet'][:100]}...")
        print()
