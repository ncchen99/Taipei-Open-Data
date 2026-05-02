#!/usr/bin/env python3
"""Fetch dataset usage metadata from Taipei, New Taipei, and gov open data platforms.

Outputs markdown files:
- taipei_open_data_usage.md
- ntpc_open_data_usage.md
- gov_open_data_usage.md
- topics_gov/ (per-topic files)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
import http.cookiejar


TAIPEI_SEARCH_URL = "https://data.taipei/api/v2/frontstage/tpeod/dataset.search"
NTPC_DATASETS_PAGE = "https://data.ntpc.gov.tw/datasets"
NTPC_SEARCH_URL = "https://data.ntpc.gov.tw/api/v1/dataset.search"
GOV_SEARCH_URL = "https://data.gov.tw/api/front/dataset/list"
GOV_DATASETS_PAGE = "https://data.gov.tw/datasets/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


class HttpClient:
    def __init__(self, headers: dict[str, str]) -> None:
        self._headers = headers
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = build_opener(HTTPCookieProcessor(self._cookie_jar))

    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        request_url = url
        if params:
            request_url = f"{url}?{urlencode(params)}"

        body_bytes: bytes | None = None
        headers = dict(self._headers)
        if json_body is not None:
            body_bytes = json.dumps(
                json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = Request(request_url, data=body_bytes,
                      headers=headers, method=method)
        with self._opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
        return json.loads(raw.decode("utf-8"))

    def get_text(self, url: str, timeout: int = 60) -> str:
        req = Request(url, headers=self._headers, method="GET")
        with self._opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace")


@dataclass
class DatasetRow:
    name: str
    usage_count: int
    updated_at: str
    topic: str


def _to_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def fetch_taipei_datasets(client: HttpClient, page_limit: int = 200) -> list[DatasetRow]:
    rows: list[DatasetRow] = []
    page_num = 1

    while True:
        payload = {
            "page_num": page_num,
            "page_limit": page_limit,
            "qs": "",
            "sort": "metadata_changed.date_desc",
        }

        data = client.request_json(
            "POST", TAIPEI_SEARCH_URL, json_body=payload)
        result = data.get("payload", {}).get("search_result", [])

        if not result:
            break

        for item in result:
            rows.append(
                DatasetRow(
                    name=_normalize_text(
                        item.get("title") or item.get("name")),
                    usage_count=_to_int(item.get("use_count")),
                    updated_at=_normalize_text(
                        item.get("metadata_changed")
                        or item.get("changed")
                        or item.get("publish_date")
                    ),
                    topic=_normalize_text(item.get("topic_name")),
                )
            )

        if len(result) < page_limit:
            break
        page_num += 1

    rows.sort(key=lambda row: row.usage_count, reverse=True)
    return rows


def fetch_ntpc_datasets(client: HttpClient, page_limit: int = 200) -> list[DatasetRow]:
    rows: list[DatasetRow] = []

    # Keep same web session as browser to avoid anti-bot behavior.
    client.get_text(NTPC_DATASETS_PAGE)

    page_num = 1
    while True:
        params = {
            "page_num": page_num,
            "page_limit": page_limit,
            "sort": "view_count_desc",
        }
        data = client.request_json("GET", NTPC_SEARCH_URL, params=params)
        result = data.get("payload", {}).get("records", [])

        if not result:
            break

        for item in result:
            usage = item.get("use_count")
            if usage is None:
                usage = item.get("view_count")

            rows.append(
                DatasetRow(
                    name=_normalize_text(
                        item.get("title") or item.get("name")),
                    usage_count=_to_int(usage),
                    updated_at=_normalize_text(
                        item.get("resource_last_modified")
                        or item.get("metadata_changed")
                        or item.get("changed")
                        or item.get("publish_date")
                    ),
                    topic=_normalize_text(item.get("topic_name")),
                )
            )

        if len(result) < page_limit:
            break
        page_num += 1

    rows.sort(key=lambda row: row.usage_count, reverse=True)
    return rows


def _request_with_retry(
    client: HttpClient,
    method: str,
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    retries: int = 3,
    timeout: int = 90,
) -> dict[str, Any]:
    """Call client.request_json with retry on timeout/connection errors."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return client.request_json(method, url, json_body=json_body, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s …
    raise RuntimeError(f"All {retries} attempts failed for {url}") from last_exc


def fetch_gov_datasets(page_limit: int = 200) -> list[DatasetRow]:
    """Fetch all datasets from data.gov.tw using a dedicated fresh client."""
    rows: list[DatasetRow] = []
    client = HttpClient(headers=HEADERS)

    page_num = 1
    while True:
        payload = {
            "page_num": page_num,
            "page_limit": page_limit,
            "sort": "dataset_view_times_desc",
        }
        data = _request_with_retry(client, "POST", GOV_SEARCH_URL, json_body=payload)
        result = data.get("payload", {}).get("search_result", [])

        if not result:
            break

        for item in result:
            # metadata_changed is a dict {"date": "YYYY-MM-DD HH:MM:SS.ffffff", ...}
            changed_raw = item.get("metadata_changed") or {}
            if isinstance(changed_raw, dict):
                updated_at = changed_raw.get("date", "")[:19]
            else:
                updated_at = _normalize_text(changed_raw)

            topic = _normalize_text(item.get("topic_name")) or "未分類"

            rows.append(
                DatasetRow(
                    name=_normalize_text(item.get("title") or item.get("name")),
                    usage_count=_to_int(item.get("dataset_view_times")),
                    updated_at=updated_at,
                    topic=topic,
                )
            )

        if len(result) < page_limit:
            break
        page_num += 1

    rows.sort(key=lambda row: row.usage_count, reverse=True)
    return rows


def markdown_table(rows: list[DatasetRow], source: str, usage_note: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# {source} 開放資料集使用次數整理",
        "",
        f"- 產生時間: {now}",
        f"- 資料筆數: {len(rows)}",
        f"- 使用次數欄位說明: {usage_note}",
        "",
        "| 排名 | 資料集名稱 | 使用次數 | 更新時間 | 主題分類 |",
        "|---:|---|---:|---|---|",
    ]

    for idx, row in enumerate(rows, start=1):
        name = row.name.replace("|", "\\|")
        updated_at = row.updated_at.replace("|", "\\|")
        topic = row.topic.replace("|", "\\|")
        lines.append(
            f"| {idx} | {name} | {row.usage_count:,} | {updated_at} | {topic} |"
        )

    lines.append("")
    return "\n".join(lines)


def markdown_by_topic(rows: list[DatasetRow], source: str, usage_note: str) -> str:
    """Generate markdown with datasets grouped and ranked within each topic."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Group by topic, preserving overall view-count order within each group.
    by_topic: dict[str, list[DatasetRow]] = defaultdict(list)
    for row in rows:
        by_topic[row.topic].append(row)

    # Sort topics by total dataset count descending.
    sorted_topics = sorted(by_topic.items(), key=lambda kv: len(kv[1]), reverse=True)

    lines = [
        f"# {source} 開放資料集使用次數整理",
        "",
        f"- 產生時間: {now}",
        f"- 資料筆數: {len(rows)}",
        f"- 使用次數欄位說明: {usage_note}",
        "",
    ]

    for topic, topic_rows in sorted_topics:
        lines.append(f"## 類別：{topic}（{len(topic_rows)} 筆）")
        lines.append("")
        lines.append("| 類別內排名 | 資料集名稱 | 使用次數 | 更新時間 |")
        lines.append("|---:|---|---:|---|")
        for idx, row in enumerate(topic_rows, start=1):
            name = row.name.replace("|", "\\|")
            updated_at = row.updated_at.replace("|", "\\|")
            lines.append(f"| {idx} | {name} | {row.usage_count:,} | {updated_at} |")
        lines.append("")

    return "\n".join(lines)


def write_topic_files(rows: list[DatasetRow], source: str, usage_note: str, topic_dir: Path) -> None:
    """Write one markdown file per topic into topic_dir, plus a README index."""
    topic_dir.mkdir(exist_ok=True)

    by_topic: dict[str, list[DatasetRow]] = defaultdict(list)
    for row in rows:
        by_topic[row.topic].append(row)

    sorted_topics = sorted(by_topic.items(), key=lambda kv: len(kv[1]), reverse=True)

    # Write individual topic files.
    for topic, topic_rows in sorted_topics:
        safe_name = topic.replace("/", "_").replace("\\", "_").replace(" ", "_")
        file_path = topic_dir / f"{safe_name}.md"
        lines = [
            f"# {source} 開放資料集使用次數整理",
            "",
            f"## 類別：{topic}（{len(topic_rows)} 筆）",
            "",
            f"- 使用次數欄位說明: {usage_note}",
            "",
            "| 類別內排名 | 資料集名稱 | 使用次數 | 更新時間 |",
            "|---:|---|---:|---|",
        ]
        for idx, row in enumerate(topic_rows, start=1):
            name = row.name.replace("|", "\\|")
            updated_at = row.updated_at.replace("|", "\\|")
            lines.append(f"| {idx} | {name} | {row.usage_count:,} | {updated_at} |")
        lines.append("")
        file_path.write_text("\n".join(lines), encoding="utf-8")

    # Write README index.
    readme_lines = [
        f"# {source} 各主題拆分檔案索引",
        "",
        f"- 主題數: {len(sorted_topics)}",
        "",
        "| 主題 | 檔案 |",
        "|---|---|",
    ]
    for topic, _ in sorted_topics:
        safe_name = topic.replace("/", "_").replace("\\", "_").replace(" ", "_")
        readme_lines.append(f"| {topic} | [{topic}.md]({safe_name}.md) |")
    readme_lines.append("")
    (topic_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> None:
    output_dir = Path.cwd()
    client = HttpClient(headers=HEADERS)

    taipei_rows = fetch_taipei_datasets(client)
    ntpc_rows = fetch_ntpc_datasets(client)
    gov_rows = fetch_gov_datasets()

    taipei_md = markdown_table(
        taipei_rows,
        source="臺北市",
        usage_note="使用 API 回傳的 use_count 欄位",
    )
    ntpc_md = markdown_table(
        ntpc_rows,
        source="新北市",
        usage_note="若 use_count 不存在，使用 view_count 作為使用次數",
    )
    gov_md = markdown_by_topic(
        gov_rows,
        source="政府資料開放平臺",
        usage_note="使用 API 回傳的 dataset_view_times 欄位（瀏覽次數）",
    )

    write_markdown(output_dir / "taipei_open_data_usage.md", taipei_md)
    write_markdown(output_dir / "ntpc_open_data_usage.md", ntpc_md)
    write_markdown(output_dir / "gov_open_data_usage.md", gov_md)

    write_topic_files(
        gov_rows,
        source="政府資料開放平臺",
        usage_note="使用 API 回傳的 dataset_view_times 欄位（瀏覽次數）",
        topic_dir=output_dir / "topics_gov",
    )

    print("Done. Generated files:")
    print("- taipei_open_data_usage.md")
    print("- ntpc_open_data_usage.md")
    print("- gov_open_data_usage.md")
    print("- topics_gov/ (per-topic files)")


if __name__ == "__main__":
    main()
