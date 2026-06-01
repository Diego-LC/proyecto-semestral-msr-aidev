"""Minimal access helpers for the AIDev dataset on Hugging Face."""

from __future__ import annotations

import json
from typing import Dict, Iterable
from urllib.parse import urlencode
from urllib.request import urlopen


DATASET = "hao-li/AIDev"
DATASET_SERVER = "https://datasets-server.huggingface.co"
DEFAULT_SPLIT = "train"


def api_get(path: str, **params) -> Dict:
    query = urlencode(params)
    url = f"{DATASET_SERVER}/{path}?{query}"
    with urlopen(url) as response:
        return json.load(response)


def get_parquet_urls(
    configs: Iterable[str],
    dataset: str = DATASET,
    split: str = DEFAULT_SPLIT,
) -> Dict[str, str]:
    requested = set(configs)
    manifest = api_get("parquet", dataset=dataset)
    urls: Dict[str, str] = {}

    for entry in manifest.get("parquet_files", []):
        config = entry.get("config")
        if config in requested and entry.get("split") == split:
            urls[config] = entry["url"]

    return urls
