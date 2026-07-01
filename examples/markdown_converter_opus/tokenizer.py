"""Tokenizer: converts raw markdown into a list of block-level tokens.

Each token is a dict with a 'type' and type-specific fields.
Inline content is left as raw strings for the parser to handle.
"""


def tokenize(markdown):
    lines = markdown.split("\n")
    tokens = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            content_lines = []
            i += 1
            closed = False
            while i < n:
                if lines[i].strip().startswith("```"):
                    closed = True
                    i += 1
                    break
                content_lines.append(lines[i])
                i += 1
            tokens.append({
                "type": "code_block",
                "lang": lang,
                "content": "\n".join(content_lines),
                "closed": closed,
            })
            continue

        # Blank line
        if stripped == "":
            tokens.append({"type": "blank"})
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            tokens.append({"type": "hr"})
            i += 1
            continue

        # Header
        if stripped.startswith("#"):
            j = 0
            while j < len(stripped) and stripped[j] == "#":
                j += 1
            if 1 <= j <= 6 and j < len(stripped) and stripped[j] == " ":
                content = stripped[j:].strip()
                tokens.append({"type": "header", "level": j, "content": content})
                i += 1
                continue

        # Blockquote
        if stripped.startswith(">"):
            tokens.append({"type": "blockquote_line", "content": _strip_quote(line)})
            i += 1
            continue

        # Unordered list item (preserve indentation)
        ul = _match_ul(line)
        if ul is not None:
            indent, content = ul
            tokens.append({"type": "ul_item", "indent": indent, "content": content})
            i += 1
            continue

        # Ordered list item
        ol = _match_ol(line)
        if ol is not None:
            indent, content = ol
            tokens.append({"type": "ol_item", "indent": indent, "content": content})
            i += 1
            continue

        # Paragraph line
        tokens.append({"type": "text", "content": line})
        i += 1

    return tokens


def _strip_quote(line):
    s = line.lstrip()
    s = s[1:]  # remove '>'
    if s.startswith(" "):
        s = s[1:]
    return s


def _leading_spaces(line):
    count = 0
    for ch in line:
        if ch == " ":
            count += 1
        else:
            break
    return count


def _match_ul(line):
    indent = _leading_spaces(line)
    rest = line[indent:]
    if rest.startswith("- "):
        return indent, rest[2:]
    return None


def _match_ol(line):
    indent = _leading_spaces(line)
    rest = line[indent:]
    j = 0
    while j < len(rest) and rest[j].isdigit():
        j += 1
    if j > 0 and j + 1 < len(rest) and rest[j] == "." and rest[j + 1] == " ":
        return indent, rest[j + 2:]
    return None
