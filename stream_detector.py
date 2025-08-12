import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Optional


class AudioStream:
    def __init__(self, url: str, quality_score: int = 0, format: str = ""):
        self.url = url
        self.quality_score = quality_score
        self.format = format

    def __repr__(self):
        return f"AudioStream(url='{self.url}', format='{self.format}', quality={self.quality_score})"


class StreamDetector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        self.audio_formats = {
            ".flac": 100,
            ".wav": 100,
            ".aiff": 100,
            ".opus": 90,
            ".aac": 85,
            ".m4a": 85,
            ".ogg": 80,
            ".mp3": 75,
            ".wma": 65,
        }

        self.content_type_formats = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/aac": "aac",
            "audio/mp4": "aac",
            "audio/x-m4a": "m4a",
            "audio/flac": "flac",
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/x-wav": "wav",
            "audio/ogg": "ogg",
            "audio/opus": "opus",
            "audio/x-ms-wma": "wma",
            "audio/aiff": "aiff",
            "audio/x-aiff": "aiff",
        }

        self.audio_patterns = [
            r'https?://[^\s"\'<>]+\.(?:mp3|flac|wav|aac|ogg|m4a|wma|opus|aiff)(?:\?[^\s"\'<>]*)?',
            r'https?://[^\s"\'<>]*(?:audio|stream|sound)[^\s"\'<>]*\.(?:mp3|flac|wav|aac|ogg|m4a|wma|opus|aiff)',
            r'https?://[^\s"\'<>]*\.m3u8[^\s"\'<>]*',
            r'https?://[^\s"\'<>]*\.pls[^\s"\'<>]*',
        ]

    def fetch_page_content(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return None

    def extract_audio_urls_from_html(
        self, html_content: str, base_url: str
    ) -> List[str]:
        audio_urls = set()

        soup = BeautifulSoup(html_content, "html.parser")

        for audio_tag in soup.find_all("audio"):
            if audio_tag.get("src"):
                audio_urls.add(urljoin(base_url, audio_tag["src"]))
            for source in audio_tag.find_all("source"):
                if source.get("src"):
                    audio_urls.add(urljoin(base_url, source["src"]))

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(href.lower().endswith(ext) for ext in self.audio_formats.keys()):
                audio_urls.add(urljoin(base_url, href))

        for pattern in self.audio_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if self._is_valid_audio_url(match):
                    audio_urls.add(match)

        return list(audio_urls)

    def extract_audio_urls_from_javascript(self, html_content: str) -> List[str]:
        audio_urls = set()

        soup = BeautifulSoup(html_content, "html.parser")
        scripts = soup.find_all("script")

        for script in scripts:
            if script.string:
                for pattern in self.audio_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if self._is_valid_audio_url(match):
                            audio_urls.add(match)

        return list(audio_urls)

    def _is_valid_audio_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

    def get_content_type(self, url: str) -> Optional[str]:
        try:
            response = self.session.head(url, timeout=3, allow_redirects=True)
            if response.status_code == 200:
                return response.headers.get("content-type", "").lower().split(";")[0]
        except:
            pass

        try:
            response = self.session.get(
                url, timeout=3, allow_redirects=True, stream=True
            )
            if response.status_code == 200:
                response.close()
                return response.headers.get("content-type", "").lower().split(";")[0]
        except:
            pass

        return None

    def analyze_stream_quality(self, url: str) -> AudioStream:
        quality_score = 0
        format_detected = ""
        url_lower = url.lower()

        for ext, score in self.audio_formats.items():
            if ext in url_lower:
                quality_score += score
                format_detected = ext[1:]
                break

        if not format_detected:
            content_type = self.get_content_type(url)
            if content_type and content_type in self.content_type_formats:
                format_detected = self.content_type_formats[content_type]
                ext_key = f".{format_detected}"
                if ext_key in self.audio_formats:
                    quality_score += self.audio_formats[ext_key]

        nominal_bitrate = 128
        bitrate_match = re.search(r"(\d+)k(?:bps)?", url_lower)

        if bitrate_match:
            bitrate = int(bitrate_match.group(1))
        else:
            bitrate = nominal_bitrate

        if bitrate >= 320:
            quality_score += 30
        elif bitrate >= 256:
            quality_score += 25
        elif bitrate >= 192:
            quality_score += 20
        elif bitrate >= 128:
            quality_score += 15
        elif bitrate >= 64:
            quality_score += 10
        else:
            quality_score += 5

        if any(indicator in url_lower for indicator in ["hq", "high", "lossless"]):
            quality_score += 20
        if any(indicator in url_lower for indicator in ["hd", "1080", "720"]):
            quality_score += 15

        return AudioStream(url, quality_score, format_detected)

    def parse_playlist_file(self, playlist_url: str) -> List[str]:
        try:
            response = self.session.get(playlist_url, timeout=10)
            response.raise_for_status()
            content = response.text

            urls = []

            if playlist_url.lower().endswith(".pls"):
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("File") and "=" in line:
                        url = line.split("=", 1)[1].strip()
                        if self._is_valid_audio_url(url):
                            urls.append(url)

            elif (
                playlist_url.lower().endswith(".m3u8") or "m3u8" in playlist_url.lower()
            ):
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if self._is_valid_audio_url(line):
                            if line.startswith("http"):
                                urls.append(line)
                            else:
                                urls.append(urljoin(playlist_url, line))

            logging.info(f"Parsed playlist {playlist_url}, found {len(urls)} streams")
            return urls

        except Exception as e:
            logging.error(f"Failed to parse playlist {playlist_url}: {e}")
            return []

    def find_audio_streams(self, url: str) -> List[AudioStream]:
        logging.info(f"Analyzing URL: {url}")

        html_content = self.fetch_page_content(url)
        if not html_content:
            return []

        html_audio_urls = self.extract_audio_urls_from_html(html_content, url)

        js_audio_urls = self.extract_audio_urls_from_javascript(html_content)

        all_urls = list(set(html_audio_urls + js_audio_urls))

        final_urls = []
        for audio_url in all_urls:
            if (
                audio_url.lower().endswith((".pls", ".m3u8"))
                or "m3u8" in audio_url.lower()
            ):
                playlist_streams = self.parse_playlist_file(audio_url)
                final_urls.extend(playlist_streams)
            else:
                final_urls.append(audio_url)

        final_urls = list(set(final_urls))

        streams = []
        for audio_url in final_urls:
            stream = self.analyze_stream_quality(audio_url)
            streams.append(stream)
            logging.info(f"Found stream: {stream}")

        streams.sort(key=lambda x: x.quality_score, reverse=True)

        return streams

    def get_best_stream(self, url: str) -> Optional[AudioStream]:
        streams = self.find_audio_streams(url)
        return streams[0] if streams else None
