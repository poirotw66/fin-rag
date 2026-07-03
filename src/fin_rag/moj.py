from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from bs4.element import Tag


TITLE_SUFFIX_RE = re.compile(r"\s*（[^）]*）$")
MINGUO_DATE_RE = re.compile(r"民國\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日")


@dataclass(frozen=True)
class MojLawDocument:
    title: str
    revision_date: str
    text: str


def parse_moj_law_html(html: str) -> MojLawDocument:
    soup = BeautifulSoup(html, "html.parser")
    return MojLawDocument(
        title=_extract_title(soup),
        revision_date=_extract_revision_date(soup),
        text=_extract_article_text(soup),
    )


def _extract_title(soup: BeautifulSoup) -> str:
    title_node = soup.select_one("#hlLawName")
    title = _normalize_line(title_node.get_text(" ", strip=True) if title_node else "")
    return TITLE_SUFFIX_RE.sub("", title)


def _extract_revision_date(soup: BeautifulSoup) -> str:
    revision_node = soup.select_one("#trLNNDate td")
    revision_text = _normalize_line(revision_node.get_text(" ", strip=True) if revision_node else "")
    match = MINGUO_DATE_RE.search(revision_text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _extract_article_text(soup: BeautifulSoup) -> str:
    articles: list[str] = []
    for row in soup.select("#pnLawFla .row"):
        article_node = row.select_one(".col-no a")
        article = _normalize_line(article_node.get_text(" ", strip=True) if article_node else "")
        if not article.startswith("第 ") or "條" not in article:
            continue
        article_body = row.select_one(".law-article")
        body_lines = _extract_body_lines(article_body)
        if not body_lines:
            continue
        articles.append("\n".join([article, *body_lines]))
    return "\n\n".join(articles)


def _extract_body_lines(article_body: Tag | None) -> list[str]:
    if article_body is None:
        return []
    line_nodes = article_body.find_all("div", recursive=False)
    if not line_nodes:
        line_nodes = [article_body]
    return [
        text
        for text in (_normalize_line(node.get_text(" ", strip=True)) for node in line_nodes)
        if text
    ]


def _normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
