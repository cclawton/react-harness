"""Renderer: converts an AST into HTML strings."""


def render(nodes):
    parts = [render_block(node) for node in nodes]
    return "\n\n".join(p for p in parts if p != "")


def render_block(node):
    t = node["type"]

    if t == "header":
        level = node["level"]
        inner = render_inline(node["children"])
        return "<h{0}>{1}</h{0}>".format(level, inner)

    if t == "paragraph":
        inner = render_inline(node["children"])
        return "<p>{0}</p>".format(inner)

    if t == "hr":
        return "<hr>"

    if t == "code_block":
        lang = node["lang"]
        content = node["content"]
        if content:
            content = content + "\n"
        if lang:
            return '<pre><code class="language-{0}">{1}</code></pre>'.format(lang, content)
        return "<pre><code>{0}</code></pre>".format(content)

    if t == "list":
        return render_list(node)

    if t == "blockquote":
        inner = "\n".join(render_block(c) for c in node["children"])
        return "<blockquote>\n{0}\n</blockquote>".format(inner)

    return ""


def render_list(node):
    tag = "ol" if node["ordered"] else "ul"
    lines = ["<{0}>".format(tag)]
    for item in node["items"]:
        inner = render_inline(item["children"])
        if item["sublist"] is not None:
            sublist_html = render_list(item["sublist"])
            lines.append("<li>{0}\n{1}\n</li>".format(inner, sublist_html))
        else:
            lines.append("<li>{0}</li>".format(inner))
    lines.append("</{0}>".format(tag))
    return "\n".join(lines)


def render_inline(nodes):
    return "".join(render_inline_node(n) for n in nodes)


def render_inline_node(node):
    t = node["type"]
    if t == "text":
        return node["value"]
    if t == "strong":
        return "<strong>{0}</strong>".format(render_inline(node["children"]))
    if t == "em":
        return "<em>{0}</em>".format(render_inline(node["children"]))
    if t == "code":
        return "<code>{0}</code>".format(node["value"])
    if t == "link":
        return '<a href="{0}">{1}</a>'.format(node["href"], render_inline(node["children"]))
    return ""
