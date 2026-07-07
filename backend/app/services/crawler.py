"""
爬虫服务
作用：从指定URL出发，按设定深度递归爬取页面，提取文本内容和内部链接
做法：
1. 发送HTTP GET请求获取页面
2. 解析HTML，提取正文文本和所有内部链接
3. 对每个内部链接，如果深度未达到上限则继续爬取
4. 遵守爬取频率限制，避免对目标站点造成压力
"""

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import asyncio


class SiteCrawler:
    def __init__(self, timeout: int = 30, delay: float = 1.0):
        self.timeout = timeout
        self.delay = delay  # 请求间隔（秒），避免对目标站点造成压力
        self.visited = set()
        self.domains = set()

    async def crawl(self, start_url: str, max_depth: int = 2, max_pages: int = 100) -> list[dict]:
        """
        主爬取方法

        参数：
            start_url: 起始URL
            max_depth: 最大爬取深度
            max_pages: 最大爬取页数

        返回：
            list[dict]: 每个元素包含 {'url', 'title', 'text', 'links'}
        """
        parsed = urlparse(start_url)
        self.domains.add(parsed.netloc)
        self.visited = set()

        results = []
        queue = [(start_url, 0)]  # (url, current_depth)

        while queue and len(results) < max_pages:
            url, depth = queue.pop(0)

            if url in self.visited:
                continue
            self.visited.add(url)

            # 只爬取同域名的链接
            parsed_url = urlparse(url)
            if parsed_url.netloc not in self.domains:
                continue

            page_data = await self._fetch_page(url)
            if page_data:
                results.append(page_data)

                # 深度未到上限则加入子链接
                if depth < max_depth:
                    for link in page_data.get("links", []):
                        if link not in self.visited:
                            queue.append((link, depth + 1))

            await asyncio.sleep(self.delay)

        return results

    async def _fetch_page(self, url: str) -> Optional[dict]:
        """
        获取单个页面的内容

        做法：
        1. 设置 User-Agent 模拟浏览器
        2. 使用 httpx 异步发送请求
        3. 用 BeautifulSoup 解析 HTML
        4. 移除 script/style 等标签后提取文本
        5. 收集同域名的 a 标签 href 作为内部链接
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # 移除干扰标签
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # 移除图片标签中的 base64 src 数据，防止图片编码被当作文本检测
            for img_tag in soup.find_all("img", src=True):
                if "base64" in img_tag.get("src", "").lower():
                    img_tag.decompose()

            # 提取标题
            title = soup.title.string.strip() if soup.title else ""

            # 提取正文文本
            body = soup.find("body")
            text = body.get_text(separator="\n", strip=True) if body else ""

            # 提取同域内部链接
            links = []
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"])
                parsed_full = urlparse(full_url)
                if parsed_full.netloc in self.domains and parsed_full.scheme in ("http", "https"):
                    links.append(full_url)

            return {
                "url": url,
                "title": title,
                "text": text,
                "links": links[:50],  # 每页最多50个链接，防止队列膨胀
            }

        except Exception as e:
            print(f"[Crawler] Error fetching {url}: {e}")
            return None
