from __future__ import annotations

import json
import re
from pathlib import Path

from .types import Chunk, ManifestEntry


ARTICLE_RE = re.compile(
    r"^\s*(第\s*[一二三四五六七八九十百千\d]+(?:\s*-\s*\d+|\s*之\s*[一二三四五六七八九十百千\d]+)?\s*條)\s*$",
    re.MULTILINE,
)


def load_manifest(path: str | Path) -> dict[str, ManifestEntry]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["doc_id"]: ManifestEntry(**item) for item in data}


def chunk_text_by_article(
    *,
    doc_id: str,
    title: str,
    track: str,
    source_url: str,
    revision_date: str,
    text: str,
) -> list[Chunk]:
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        normalized = _normalize_text(text)
        return [
            Chunk(
                doc_id=doc_id,
                title=title,
                article="paragraph-1",
                text=normalized,
                track=track,
                source_url=source_url,
                revision_date=revision_date,
            )
        ] if normalized else []

    chunks: list[Chunk] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        article = _normalize_text(match.group(1))
        body = _normalize_text(text[start:end])
        if body:
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    title=title,
                    article=article,
                    text=body,
                    track=track,
                    source_url=source_url,
                    revision_date=revision_date,
                )
            )
    return chunks


def write_chunks_jsonl(chunks: list[Chunk], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_json(), ensure_ascii=False) + "\n")


def read_chunks_jsonl(path: str | Path) -> list[Chunk]:
    source = Path(path)
    if not source.exists():
        return []
    return [Chunk.from_json(json.loads(line)) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _canonical_article(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def extract_articles(text: str, wanted: list[str]) -> str:
    wanted_set = {_canonical_article(article) for article in wanted}
    matches = list(ARTICLE_RE.finditer(text))
    blocks: list[str] = []
    for index, match in enumerate(matches):
        article = _normalize_text(match.group(1))
        if _canonical_article(article) not in wanted_set:
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())
    return "\n\n".join(blocks) + ("\n" if blocks else "")

