"""
Multi-Framework Documentation Crawler for Archon V6

Crawls documentation for Pydantic AI, LangGraph, CrewAI, and AutoGen.
Stores all documentation in the same Supabase table with framework metadata.
"""

import asyncio
import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client, create_client
from bs4 import BeautifulSoup
import aiohttp
import xml.etree.ElementTree as ET

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archon.framework_config import FRAMEWORKS, get_framework  # noqa: E402
from archon.constants import EMBEDDING_MODEL, EMBEDDING_DIM  # noqa: E402

load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


class MultiFrameworkCrawler:
    """Crawls documentation for multiple AI frameworks"""

    def __init__(self, openai_client: AsyncOpenAI, supabase: Client):
        self.openai_client = openai_client
        self.supabase = supabase
        self.session: aiohttp.ClientSession = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        try:
            response = await self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text[:8000]  # Limit to avoid token limits
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0] * EMBEDDING_DIM

    async def fetch_url(self, url: str) -> str:
        """Fetch URL content"""
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error fetching {url}: Status {response.status}")
                    return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    async def get_sitemap_urls(self, sitemap_url: str) -> List[str]:
        """Extract URLs from sitemap"""
        try:
            content = await self.fetch_url(sitemap_url)
            if not content:
                return []

            root = ET.fromstring(content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = [elem.text for elem in root.findall('.//ns:loc', namespace)]
            print(f"Found {len(urls)} URLs in sitemap")
            return urls
        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")
            return []

    async def extract_content(self, html: str, url: str) -> Dict[str, str]:
        """Extract content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url.split('/')[-1]

            # Get main content (try different selectors)
            main_content = None
            for selector in ['main', 'article', '.content', '#content', '.documentation']:
                main_content = soup.find(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.find('body')

            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)

            return {
                'title': title_text,
                'content': cleaned_text,
                'url': url
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return {'title': url, 'content': '', 'url': url}

    def chunk_content(self, content: str, chunk_size: int = 1500) -> List[str]:
        """Split content into chunks"""
        words = content.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks

    async def crawl_framework(self, framework_name: str) -> int:
        """
        Crawl documentation for a specific framework

        Args:
            framework_name: Name of the framework to crawl

        Returns:
            Number of pages processed
        """
        framework = get_framework(framework_name)
        if not framework:
            print(f"Unknown framework: {framework_name}")
            return 0

        print(f"\n{'='*60}")
        print(f"Crawling {framework.display_name} Documentation")
        print(f"{'='*60}")

        # Get URLs from sitemap
        if not framework.sitemap_url:
            print(f"No sitemap URL configured for {framework_name}")
            return 0

        urls = await self.get_sitemap_urls(framework.sitemap_url)
        if not urls:
            print(f"No URLs found for {framework_name}")
            return 0

        print(f"Processing {len(urls)} pages...")

        pages_processed = 0
        for i, url in enumerate(urls):
            try:
                print(f"[{i+1}/{len(urls)}] Processing: {url}")

                # Fetch page content
                html = await self.fetch_url(url)
                if not html:
                    continue

                # Extract content
                page_data = await self.extract_content(html, url)
                if not page_data['content']:
                    continue

                # Chunk content
                chunks = self.chunk_content(page_data['content'])
                print(f"  Created {len(chunks)} chunks")

                # Process each chunk
                for chunk_num, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = await self.get_embedding(chunk)

                    # Prepare data for insertion
                    data = {
                        'url': url,
                        'chunk_number': chunk_num,
                        'title': f"{page_data['title']} - Part {chunk_num + 1}",
                        'content': chunk,
                        'metadata': {
                            'source': f'{framework_name}_docs',
                            'framework': framework_name,
                            'framework_display': framework.display_name,
                            'total_chunks': len(chunks)
                        },
                        'embedding': embedding
                    }

                    # Insert into Supabase
                    try:
                        self.supabase.table('site_pages').insert(data).execute()
                    except Exception as e:
                        print(f"  Error inserting chunk: {e}")

                pages_processed += 1

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  Error processing {url}: {e}")
                continue

        print(f"\n✅ Completed {framework.display_name}: {pages_processed} pages processed")
        return pages_processed

    async def crawl_all_frameworks(self, frameworks: List[str] = None) -> Dict[str, int]:
        """
        Crawl documentation for all or specified frameworks

        Args:
            frameworks: List of framework names to crawl (None = all)

        Returns:
            Dictionary of framework_name -> pages_processed
        """
        if frameworks is None:
            frameworks = list(FRAMEWORKS.keys())

        results = {}

        for framework_name in frameworks:
            count = await self.crawl_framework(framework_name)
            results[framework_name] = count

        return results


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Crawl AI framework documentation')
    parser.add_argument(
        '--frameworks',
        nargs='+',
        choices=list(FRAMEWORKS.keys()),
        help='Frameworks to crawl (default: all)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available frameworks'
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable frameworks:")
        for name, info in FRAMEWORKS.items():
            print(f"  - {name}: {info.display_name}")
        return

    print("\n" + "="*60)
    print("Archon V6 - Multi-Framework Documentation Crawler")
    print("="*60)

    async with MultiFrameworkCrawler(openai_client, supabase) as crawler:
        results = await crawler.crawl_all_frameworks(args.frameworks)

    print("\n" + "="*60)
    print("Crawling Summary")
    print("="*60)
    total = 0
    for framework, count in results.items():
        framework_info = get_framework(framework)
        print(f"{framework_info.display_name}: {count} pages")
        total += count
    print(f"\nTotal: {total} pages processed across {len(results)} frameworks")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
