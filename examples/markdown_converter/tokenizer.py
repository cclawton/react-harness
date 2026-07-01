import re


class Token:
    pass


class HeaderToken(Token):
    def __init__(self, level, text):
        self.level = level
        self.text = text


class CodeBlockToken(Token):
    def __init__(self, language, content):
        self.language = language
        self.content = content


class ListItemToken(Token):
    def __init__(self, ordered, indent, text):
        self.ordered = ordered
        self.indent = indent
        self.text = text


class BlockquoteToken(Token):
    def __init__(self, lines):
        self.lines = lines


class HorizontalRuleToken(Token):
    pass


class ParagraphToken(Token):
    def __init__(self, text):
        self.text = text


def tokenize(text):
    """Convert raw markdown text into a list of block-level tokens."""
    tokens = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines
        if stripped == '':
            i += 1
            continue

        # Code block
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            content_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                content_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            content = '\n'.join(content_lines) + '\n' if content_lines else ''
            tokens.append(CodeBlockToken(lang, content))
            continue

        # Header
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            tokens.append(HeaderToken(len(m.group(1)), m.group(2)))
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^-{3,}$', stripped):
            tokens.append(HorizontalRuleToken())
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                content = lines[i].strip()[1:].lstrip()
                bq_lines.append(content)
                i += 1
            tokens.append(BlockquoteToken(bq_lines))
            continue

        # List item
        m = re.match(r'^(\s*)(-|\d+\.)\s+(.*)', line)
        if m:
            indent = len(m.group(1))
            ordered = m.group(2).endswith('.')
            tokens.append(ListItemToken(ordered, indent, m.group(3)))
            i += 1
            continue

        # Paragraph - collect consecutive non-special lines
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            next_stripped = next_line.strip()
            if next_stripped == '':
                break
            if next_stripped.startswith('```'):
                break
            if re.match(r'^#{1,6}\s+', next_line):
                break
            if re.match(r'^-{3,}$', next_stripped):
                break
            if next_stripped.startswith('>'):
                break
            if re.match(r'^\s*(-|\d+\.)\s+', next_line):
                break
            para_lines.append(next_line)
            i += 1
        tokens.append(ParagraphToken('\n'.join(para_lines)))

    return tokens
