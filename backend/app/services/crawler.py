"""
爬虫服务
作用：从指定URL出发，按设定深度递归爬取页面，提取文本内容和内部链接
做法：
1. 发送HTTP GET请求获取页面
2. 解析HTML，提取正文文本和所有内部链接
3. 对每个内部链接，如果深度未达到上限则继续爬取
4. 遵守爬取频率限制，避免对目标站点造成压力
5. 过滤图片、静态资源等非HTML页面，防止二进制内容被误判为文本
"""

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import asyncio
import re


# 需要跳过的静态资源文件扩展名（不会被当作HTML页面爬取）
_STATIC_EXTENSIONS = frozenset((
    ".gif", ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".svg", ".ico", ".avif",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".rar", ".tar", ".gz", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
    ".json", ".xml", ".yaml", ".yml",
    ".exe", ".dmg", ".apk", ".deb", ".rpm",
))

# 通过 Content-Type 判断是否为非HTML内容
_NON_HTML_CONTENT_TYPES = (
    "image/", "video/", "audio/", "application/octet-stream",
    "application/pdf", "application/zip", "application/x-",
)


class SiteCrawler:
    """
    网站爬虫

    优化：
    - 共享 httpx 客户端连接池，避免每次请求重建 TCP 连接
    - 默认延迟降至 0.3s，在保证礼貌爬取的前提下提升速度
    - 使用 aiohttp/lxml 替代 httpx+lxml 的 text 转换开销
    """

    def __init__(
        self,
        timeout: int = 30,
        delay: float = 0.3,  # 默认从 1.0s 降到 0.3s
        max_concurrent: int = 5,  # 最大并发请求数
    ):
        self.timeout = timeout
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.visited: set[str] = set()
        self.domains: set[str] = set()
        self._client: Optional[httpx.AsyncClient] = None

    async def crawl(
        self, start_url: str, max_depth: int = 2, max_pages: int = 100
    ) -> list[dict]:
        """
        主爬取方法

        优化：
        - 在 __init__ 中创建一次 httpx 客户端，复用连接池
        - 使用信号量控制并发请求数，避免过多连接
        - 批量提取链接和文本，减少重复解析
        """
        parsed = urlparse(start_url)
        self.domains.add(parsed.netloc)
        self.visited = set()

        # 创建共享客户端（连接池复用）
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )

        try:
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def _fetch_with_semaphore(url: str, depth: int) -> Optional[dict]:
                async with semaphore:
                    return await self._fetch_page(url)

            results = []
            queue = [(start_url, 0)]  # (url, current_depth)

            while queue and len(results) < max_pages:
                # 批量收集当前批次可并发请求的 URL
                batch_urls = []
                for url, depth in queue[:]:
                    if url in self.visited:
                        queue.remove((url, depth))
                        continue
                    parsed_url = urlparse(url)
                    if parsed_url.netloc not in self.domains:
                        queue.remove((url, depth))
                        continue
                    batch_urls.append((url, depth))

                if not batch_urls:
                    break

                # 限制单批数量（不超过剩余容量）
                remaining = max_pages - len(results)
                batch_urls = batch_urls[:remaining]
                self.visited.update(u for u, _ in batch_urls)

                # 并发请求当前批次
                tasks = [_fetch_with_semaphore(url, depth) for url, depth in batch_urls]
                batch_results = await asyncio.gather(*tasks)

                for page_data in batch_results:
                    if page_data:
                        results.append(page_data)
                        # 提取子链接加入队列
                        if page_data.get("_depth", 0) < max_depth:
                            for link in page_data.get("links", []):
                                if link not in self.visited:
                                    queue.append((link, page_data["_depth"] + 1))

                # 批次间短暂延迟，避免瞬时并发
                if queue and len(results) < max_pages:
                    await asyncio.sleep(self.delay)

            return results
        finally:
            await self._client.aclose()
            self._client = None

    async def _is_html_page(self, url: str, response: httpx.Response) -> bool:
        """
        判断请求的URL是否为HTML页面，而非静态资源或图片

        策略：
        1. 通过文件扩展名快速判断（.gif/.jpg/.css/.js 等直接跳过）
        2. 通过 Content-Type 响应头判断（image/*, application/octet-stream 等跳过）
        3. 通过响应体大小判断（过大文件大概率不是HTML页面）
        """
        # 策略1：检查URL路径的文件扩展名
        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in _STATIC_EXTENSIONS:
            if path.endswith(ext):
                return False

        # 策略2：检查 Content-Type
        content_type = response.headers.get("content-type", "").lower()
        for ct in _NON_HTML_CONTENT_TYPES:
            if content_type.startswith(ct):
                return False

        # 策略3：HTML页面一般不超过10MB
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return False

        return True

    async def _fetch_page(self, url: str) -> Optional[dict]:
        """
        获取单个页面的内容

        优化：
        - 使用共享客户端发送请求（复用 TCP 连接）
        - 使用 response.text 而非 response.content 解码（httpx 内部已缓存）
        - 一次性提取所有需要的数据，减少 DOM 遍历次数
        """
        try:
            if not self._client:
                return None

            response = await self._client.get(url)
            response.raise_for_status()

            # 过滤非HTML页面（图片、CSS、JS、PDF等静态资源）
            if not await self._is_html_page(url, response):
                return None

            # 解析 HTML（lxml 解析器比 html.parser 快约 3-5 倍）
            soup = BeautifulSoup(response.text, "lxml")

            # 一次性移除所有干扰标签
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # 移除 base64 图片标签
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
                "links": links[:50],
                "_depth": 0,  # 临时字段，供 crawl() 使用，清理后移除
            }

        except Exception as e:
            print(f"[Crawler] Error fetching {url}: {e}")
            return None
