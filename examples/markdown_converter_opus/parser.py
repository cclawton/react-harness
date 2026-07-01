"""Parser: converts block tokens into an AST of nodes.

AST node types (dicts):
  {"type": "header", "level": int, "children": [inline nodes]}
  {"type": "paragraph", "children": [inline nodes]}
  {"type": "code_block", "lang": str, "content": str}
  {"type": "hr"}
  {"type": "list", "ordered": bool, "items": [list_item...]}
  {"type": "list_item", "children": [inline nodes], "sublist": node or None}
  {"type": "blockquote", "children": [block nodes]}

Inline node types:
  {"type": "text", "value": str}
  {"type": "strong", "children": [...]}
  {"type": "em", "children": [...]}
  {"type": "code", "value": str}
  {"type": "link", "href": str, "children": [...]}
"""

from tokenizer import tokenize


class MarkdownError(Exception):
    pass


def parse(markdown):
    tokens = tokenize(markdown)
    return parse_blocks(tokens)


def parse_blocks(tokens):
    nodes = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        t = tok["type"]

        if t == "blank":
            i += 1
            continue

        if t == "header":
            nodes.append({
                "type": "header",
                "level": tok["level"],
                "children": parse_inline(tok["content"]),
            })
            i += 1
            continue

        if t == "hr":
            nodes.append({"type": "hr"})
            i += 1
            continue

        if t == "code_block":
            if not tok["closed"]:
                raise MarkdownError("Unclosed code block")
            nodes.append({
                "type": "code_block",
                "lang": tok["lang"],
                "content": tok["content"],
            })
            i += 1
            continue

        if t == "blockquote_line":
            # collect consecutive blockquote lines
            quote_lines = []
            while i < n and tokens[i]["type"] == "blockquote_line":
                quote_lines.append(tokens[i]["content"])
                i += 1
            inner_md = "\n".join(quote_lines)
            inner_nodes = parse_blocks(tokenize(inner_md))
            nodes.append({"type": "blockquote", "children": inner_nodes})
            continue

        if t in ("ul_item", "ol_item"):
            list_node, i = parse_list(tokens, i)
            nodes.append(list_node)
            continue

        if t == "text":
            # collect consecutive text lines into a paragraph
            para_lines = []
            while i < n and tokens[i]["type"] == "text":
                para_lines.append(tokens[i]["content"])
                i += 1
            content = "\n".join(para_lines)
            nodes.append({
                "type": "paragraph",
                "children": parse_inline(content),
            })
            continue

        i += 1

    return nodes


def parse_list(tokens, i, base_indent=0):
    """Parse a list starting at index i. Returns (list_node, next_index)."""
    n = len(tokens)
    ordered = tokens[i]["type"] == "ol_item"
    item_type = tokens[i]["type"]
    base_indent = tokens[i]["indent"]
    items = []

    while i < n and tokens[i]["type"] in ("ul_item", "ol_item"):
        tok = tokens[i]
        if tok["indent"] < base_indent:
            break
        if tok["indent"] > base_indent:
            # nested list belongs to previous item
            sublist, i = parse_list(tokens, i)
            if items:
                items[-1]["sublist"] = sublist
            continue
        # same level; but must match ordered-ness of this list
        if tok["type"] != item_type:
            break
        item = {
            "type": "list_item",
            "children": parse_inline(tok["content"]),
            "sublist": None,
        }
        items.append(item)
        i += 1

    return {"type": "list", "ordered": ordered, "items": items}, i


# ---------------- Inline parsing ----------------

def parse_inline(text):
    """Parse inline markdown into a list of inline nodes."""
    nodes, pos = _parse_inline_until(text, 0, None)
    return nodes


def _parse_inline_until(text, pos, stop):
    """Parse inline content starting at pos.

    stop: a marker string ('**', '*', '`') that ends this context, or None.
    Returns (nodes, new_pos). new_pos points just after the stop marker if
    the stop was found; if stop is None it parses to the end.
    If stop is given but not found, raises MarkdownError.
    """
    nodes = []
    buf = []
    n = len(text)

    def flush():
        if buf:
            nodes.append({"type": "text", "value": "".join(buf)})
            buf.clear()

    while pos < n:
        # check stop marker
        if stop is not None and text.startswith(stop, pos):
            # if stop is single '*' but we're at '**', treat as bold, not close
            if not (stop == "*" and text.startswith("**", pos)):
                flush()
                return nodes, pos + len(stop)

        ch = text[pos]

        # inline code
        if ch == "`":
            end = text.find("`", pos + 1)
            if end == -1:
                raise MarkdownError("Unclosed inline code")
            flush()
            nodes.append({"type": "code", "value": text[pos + 1:end]})
            pos = end + 1
            continue

        # bold
        if text.startswith("**", pos):
            flush()
            children, pos = _parse_inline_until(text, pos + 2, "**")
            nodes.append({"type": "strong", "children": children})
            continue

        # italic
        if ch == "*":
            flush()
            children, pos = _parse_inline_until(text, pos + 1, "*")
            nodes.append({"type": "em", "children": children})
            continue

        # link
        if ch == "[":
            link = _try_parse_link(text, pos)
            if link is not None:
                node, pos = link
                flush()
                nodes.append(node)
                continue

        buf.append(ch)
        pos += 1

    if stop is not None:
        raise MarkdownError("Unclosed formatting marker: " + stop)

    flush()
    return nodes, pos


def _try_parse_link(text, pos):
    # text[pos] == '['
    close_bracket = text.find("]", pos + 1)
    if close_bracket == -1:
        return None
    if close_bracket + 1 >= len(text) or text[close_bracket + 1] != "(":
        return None
    close_paren = text.find(")", close_bracket + 2)
    if close_paren == -1:
        return None
    label = text[pos + 1:close_bracket]
    href = text[close_bracket + 2:close_paren]
    children = parse_inline(label)
    node = {"type": "link", "href": href, "children": children}
    return node, close_paren + 1
