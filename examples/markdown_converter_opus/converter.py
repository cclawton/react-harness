"""Converter: orchestrates tokenize -> parse -> render."""
from parser import parse, MarkdownError
from renderer import render

__all__ = ["convert", "MarkdownError"]


def convert(markdown):
    if markdown is None:
        return ""
    if markdown.strip() == "":
        return ""
    nodes = parse(markdown)
    return render(nodes)
