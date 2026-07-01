from parser import (
    HeaderNode, CodeBlockNode, ListNode, BlockquoteNode,
    HorizontalRuleNode, ParagraphNode,
    TextNode, BoldNode, ItalicNode, CodeNode, LinkNode,
)


def render_inline(nodes):
    parts = []
    for node in nodes:
        if isinstance(node, TextNode):
            parts.append(node.text)
        elif isinstance(node, BoldNode):
            parts.append('<strong>' + render_inline(node.children) + '</strong>')
        elif isinstance(node, ItalicNode):
            parts.append('<em>' + render_inline(node.children) + '</em>')
        elif isinstance(node, CodeNode):
            parts.append('<code>' + node.text + '</code>')
        elif isinstance(node, LinkNode):
            parts.append('<a href="' + node.url + '">' + render_inline(node.children) + '</a>')
    return ''.join(parts)


def render_list(node):
    tag = 'ol' if node.ordered else 'ul'
    lines = ['<' + tag + '>']
    for children, sublist in node.items:
        content = render_inline(children)
        if sublist:
            lines.append('<li>' + content)
            lines.append(render_list(sublist))
            lines.append('</li>')
        else:
            lines.append('<li>' + content + '</li>')
    lines.append('</' + tag + '>')
    return '\n'.join(lines)


def render(nodes):
    parts = []
    for node in nodes:
        if isinstance(node, HeaderNode):
            parts.append('<h' + str(node.level) + '>' + render_inline(node.children) + '</h' + str(node.level) + '>')
        elif isinstance(node, CodeBlockNode):
            if node.language:
                parts.append('<pre><code class="language-' + node.language + '">' + node.content + '</code></pre>')
            else:
                parts.append('<pre><code>' + node.content + '</code></pre>')
        elif isinstance(node, ListNode):
            parts.append(render_list(node))
        elif isinstance(node, BlockquoteNode):
            inner = render(node.children)
            parts.append('<blockquote>\n' + inner + '\n</blockquote>')
        elif isinstance(node, HorizontalRuleNode):
            parts.append('<hr>')
        elif isinstance(node, ParagraphNode):
            parts.append('<p>' + render_inline(node.children) + '</p>')
    return '\n'.join(parts)
