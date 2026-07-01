from tokenizer import tokenize
from parser import parse, MarkdownError
from renderer import render


def convert(markdown: str) -> str:
    """Convert markdown text to HTML."""
    if markdown.strip() == '':
        return ''
    tokens = tokenize(markdown)
    ast = parse(tokens)
    return render(ast)


__all__ = ['convert', 'MarkdownError']
