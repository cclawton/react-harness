import re
from tokenizer import (
    tokenize, HeaderToken, CodeBlockToken, ListItemToken,
    BlockquoteToken, HorizontalRuleToken, ParagraphToken,
)


class MarkdownError(Exception):
    pass


# AST Node classes
class Node:
    pass


class HeaderNode(Node):
    def __init__(self, level, children):
        self.level = level
        self.children = children


class CodeBlockNode(Node):
    def __init__(self, language, content):
        self.language = language
        self.content = content


class ListNode(Node):
    def __init__(self, ordered, items):
        self.ordered = ordered
        self.items = items  # list of (children, sublist)


class BlockquoteNode(Node):
    def __init__(self, children):
        self.children = children


class HorizontalRuleNode(Node):
    pass


class ParagraphNode(Node):
    def __init__(self, children):
        self.children = children


# Inline nodes
class TextNode(Node):
    def __init__(self, text):
        self.text = text


class BoldNode(Node):
    def __init__(self, children):
        self.children = children


class ItalicNode(Node):
    def __init__(self, children):
        self.children = children


class CodeNode(Node):
    def __init__(self, text):
        self.text = text


class LinkNode(Node):
    def __init__(self, children, url):
        self.children = children
        self.url = url


# Inline parsing

def find_italic_close(text, start):
    """Find closing * for italic, skipping over ** bold markers."""
    i = start
    n = len(text)
    while i < n:
        if text[i:i+2] == '**':
            i += 2
            continue
        if text[i] == '*':
            return i
        i += 1
    return -1


def parse_inline(text):
    """Parse inline formatting into a list of nodes."""
    nodes = []
    i = 0
    n = len(text)

    while i < n:
        # Inline code
        if text[i] == '`':
            end = text.find('`', i + 1)
            if end == -1:
                raise MarkdownError("Unclosed inline code")
            nodes.append(CodeNode(text[i+1:end]))
            i = end + 1
            continue

        # Link [text](url)
        if text[i] == '[':
            close = text.find(']', i + 1)
            if close != -1 and close + 1 < n and text[close + 1] == '(':
                url_close = text.find(')', close + 2)
                if url_close != -1:
                    link_text = text[i+1:close]
                    url = text[close+2:url_close]
                    nodes.append(LinkNode(parse_inline(link_text), url))
                    i = url_close + 1
                    continue
            raise MarkdownError("Unclosed link")

        # Bold **
        if text[i:i+2] == '**':
            end = text.find('**', i + 2)
            if end == -1:
                raise MarkdownError("Unclosed bold")
            inner = text[i+2:end]
            nodes.append(BoldNode(parse_inline(inner)))
            i = end + 2
            continue

        # Italic *
        if text[i] == '*':
            end = find_italic_close(text, i + 1)
            if end == -1:
                raise MarkdownError("Unclosed italic")
            inner = text[i+1:end]
            nodes.append(ItalicNode(parse_inline(inner)))
            i = end + 1
            continue

        # Plain text - accumulate until next special char
        j = i
        while j < n and text[j] not in '`[*':
            j += 1
        nodes.append(TextNode(text[i:j]))
        i = j

    return nodes


# Block parsing

def parse(tokens):
    """Convert tokens into AST nodes."""
    nodes = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if isinstance(tok, HeaderToken):
            nodes.append(HeaderNode(tok.level, parse_inline(tok.text)))
            i += 1

        elif isinstance(tok, CodeBlockToken):
            nodes.append(CodeBlockNode(tok.language, tok.content))
            i += 1

        elif isinstance(tok, HorizontalRuleToken):
            nodes.append(HorizontalRuleNode())
            i += 1

        elif isinstance(tok, BlockquoteToken):
            inner_text = '\n'.join(tok.lines)
            inner_tokens = tokenize(inner_text)
            nodes.append(BlockquoteNode(parse(inner_tokens)))
            i += 1

        elif isinstance(tok, ListItemToken):
            items, i = build_list(tokens, i)
            nodes.append(ListNode(tok.ordered, items))

        elif isinstance(tok, ParagraphToken):
            nodes.append(ParagraphNode(parse_inline(tok.text)))
            i += 1

        else:
            i += 1

    return nodes


def build_list(tokens, i):
    """Build a list (possibly nested) starting at index i.
    Returns (items, next_index).
    items is a list of (inline_children, sublist_or_None).
    """
    base_indent = tokens[i].indent
    ordered = tokens[i].ordered
    items = []

    while i < len(tokens) and isinstance(tokens[i], ListItemToken):
        tok = tokens[i]
        if tok.indent < base_indent:
            break
        if tok.indent == base_indent:
            if tok.ordered != ordered:
                break
            children = parse_inline(tok.text)
            sublist = None
            if i + 1 < len(tokens) and isinstance(tokens[i+1], ListItemToken) and tokens[i+1].indent > base_indent:
                sub_items, new_i = build_list(tokens, i + 1)
                sublist = ListNode(tokens[i+1].ordered, sub_items)
                i = new_i
            else:
                i += 1
            items.append((children, sublist))
        else:
            break

    return items, i
