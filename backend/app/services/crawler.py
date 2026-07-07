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
from urllib.parse import urljoin, urlparse, unquote
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

# 需要跳过的 URL 模式（锚点、空链接等）
_SKIP_URL_PATTERNS = (
    re.compile(r'#$', re.IGNORECASE),             # 锚点链接如 "url/"
    re.compile(r'^javascript:', re.IGNORECASE),   # JS 伪协议
    re.compile(r'^mailto:', re.IGNORECASE),       # 邮件协议
    re.compile(r'^tel:', re.IGNORECASE),          # 电话协议
    re.compile(r'^\?'),                           # 只有查询参数的 URL
)


class SiteCrawler:
    """
    网站爬虫

    优化：
    - 共享 httpx 客户端连接池，避免每次请求重建 TCP 连接
    - 默认延迟降至 0.3s，在保证礼貌爬取的前提下提升速度
    - 使用并发请求 + 信号量控制，避免串行等待
    - 过滤锚点、空链接等无效 URL，减少无用爬取
    """

    def __init__(
        self,
        timeout: int = 30,
        delay: float = 0.3,
        max_concurrent: int = 5,
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
        - BFS 层级遍历，按深度分组并发
        - 标准化 URL（去锚点、去尾部斜杠），避免重复爬取
        - 使用 set 去重 visited，避免同一页面被多次请求
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
                    return await self._fetch_page(url, depth)

            results = []
            # BFS: 当前层待爬取的 URL 列表
            current_level = [(start_url, 0)]

            while current_level and len(results) < max_pages:
                # 过滤无效 URL，收集有效 URL
                valid_urls = []
                for url, depth in current_level:
                    normalized = self._normalize_url(url)
                    if not normalized:
                        continue
                    if normalized in self.visited:
                        continue
                    parsed_url = urlparse(normalized)
                    if parsed_url.netloc not in self.domains:
                        continue
                    valid_urls.append((normalized, depth))

                if not valid_urls:
                    break

                # 限制数量（不超过剩余容量）
                remaining = max_pages - len(results)
                valid_urls = valid_urls[:remaining]
                self.visited.update(u for u, _ in valid_urls)

                # 并发请求当前层
                tasks = [_fetch_with_semaphore(url, depth) for url, depth in valid_urls]
                batch_results = await asyncio.gather(*tasks)

                # 收集结果并提取子链接
                next_level = []
                for page_data in batch_results:
                    if page_data is None:
                        continue
                    results.append(page_data)
                    # 提取子链接加入下一层
                    if page_data["_depth"] < max_depth:
                        for link in page_data.get("links", []):
                            normalized = self._normalize_url(link)
                            if normalized and normalized not in self.visited:
                                parsed_link = urlparse(normalized)
                                if parsed_link.netloc in self.domains:
                                    next_level.append((normalized, page_data["_depth"] + 1))

                # 批次间短暂延迟
                if next_level and len(results) < max_pages:
                    await asyncio.sleep(self.delay)

                current_level = next_level

            return results
        finally:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _normalize_url(url: str) -> Optional[str]:
        """
        标准化 URL：解码百分号编码、去除锚点、去除尾部斜杠

        返回 None 表示应跳过该 URL
        """
        if not url:
            return None

        # 跳过伪协议
        lower = url.lower().strip()
        for pattern in _SKIP_URL_PATTERNS:
            if pattern.search(lower):
                return None

        # 解码百分号编码，去除 fragment（#xxx）
        decoded = unquote(url)
        parsed = urlparse(decoded)
        # 去掉 fragment
        clean = parsed._replace(fragment="").geturl()

        # 标准化尾部斜杠（去掉末尾多余的 /，但保留根路径 /）
        if clean != "/" and clean.endswith("/"):
            clean = clean.rstrip("/")

        return clean if clean else None

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

    async def _fetch_page(self, url: str, depth: int) -> Optional[dict]:
        """
        获取单个页面的内容

        优化：
        - 使用共享客户端发送请求（复用 TCP 连接）
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
                links.append(full_url)

            return {
                "url": url,
                "title": title,
                "text": text,
                "links": links[:50],
                "_depth": depth,
            }

        except Exception as e:
            print(f"[Crawler] Error fetching {url}: {e}")
            return None
