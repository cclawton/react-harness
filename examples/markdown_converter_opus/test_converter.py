"""Tests for the markdown-to-HTML converter — do not modify this file."""
import pytest
from converter import convert, MarkdownError


class TestHeaders:
    def test_h1(self):
        assert convert("# Title") == "<h1>Title</h1>"

    def test_h2(self):
        assert convert("## Section") == "<h2>Section</h2>"

    def test_h3(self):
        assert convert("### Subsection") == "<h3>Subsection</h3>"

    def test_h4(self):
        assert convert("#### Deep") == "<h4>Deep</h4>"

    def test_h5(self):
        assert convert("##### Deeper") == "<h5>Deeper</h5>"

    def test_h6(self):
        assert convert("###### Deepest") == "<h6>Deepest</h6>"

    def test_header_with_formatting(self):
        assert convert("# **Bold** Title") == "<h1><strong>Bold</strong> Title</h1>"

    def test_header_with_whitespace_after_hash(self):
        assert convert("#  Spaced") == "<h1>Spaced</h1>"


class TestBold:
    def test_simple_bold(self):
        assert convert("**text**") == "<p><strong>text</strong></p>"

    def test_bold_in_sentence(self):
        assert convert("This is **bold** text") == "<p>This is <strong>bold</strong> text</p>"

    def test_multiple_bold(self):
        assert convert("**one** and **two**") == "<p><strong>one</strong> and <strong>two</strong></p>"

    def test_unclosed_bold(self):
        with pytest.raises(MarkdownError):
            convert("This is **unclosed bold")


class TestItalic:
    def test_simple_italic(self):
        assert convert("*text*") == "<p><em>text</em></p>"

    def test_italic_in_sentence(self):
        assert convert("This is *italic* text") == "<p>This is <em>italic</em> text</p>"

    def test_unclosed_italic(self):
        with pytest.raises(MarkdownError):
            convert("This is *unclosed italic")


class TestNestedFormatting:
    def test_bold_inside_italic(self):
        assert convert("*italic **bold** italic*") == "<p><em>italic <strong>bold</strong> italic</em></p>"

    def test_italic_inside_bold(self):
        assert convert("**bold *italic* bold**") == "<p><strong>bold <em>italic</em> bold</strong></p>"

    def test_code_inside_bold(self):
        assert convert("**bold `code` bold**") == "<p><strong>bold <code>code</code> bold</strong></p>"

    def test_link_inside_bold(self):
        result = convert("**[text](http://example.com)**")
        assert result == "<p><strong><a href=\"http://example.com\">text</a></strong></p>"


class TestInlineCode:
    def test_simple_code(self):
        assert convert("`code`") == "<p><code>code</code></p>"

    def test_code_in_sentence(self):
        assert convert("Use `printf` function") == "<p>Use <code>printf</code> function</p>"

    def test_code_with_special_chars(self):
        assert convert("Type `**not bold**`") == "<p>Type <code>**not bold**</code></p>"

    def test_unclosed_code(self):
        with pytest.raises(MarkdownError):
            convert("This has `unclosed code")


class TestCodeBlocks:
    def test_simple_code_block(self):
        md = "```\nprint('hello')\n```"
        assert convert(md) == "<pre><code>print('hello')\n</code></pre>"

    def test_code_block_with_language(self):
        md = "```python\nprint('hello')\n```"
        assert convert(md) == '<pre><code class="language-python">print(\'hello\')\n</code></pre>'

    def test_code_block_preserves_markdown(self):
        """Markdown inside code blocks should NOT be converted."""
        md = "```\n# Not a header\n**Not bold**\n```"
        assert convert(md) == "<pre><code># Not a header\n**Not bold**\n</code></pre>"

    def test_code_block_multiline(self):
        md = "```\nline 1\nline 2\nline 3\n```"
        assert convert(md) == "<pre><code>line 1\nline 2\nline 3\n</code></pre>"

    def test_code_block_empty(self):
        md = "```\n```"
        assert convert(md) == "<pre><code></code></pre>"


class TestLinks:
    def test_simple_link(self):
        assert convert("[text](http://example.com)") == '<p><a href="http://example.com">text</a></p>'

    def test_link_in_sentence(self):
        result = convert("See [this site](http://example.com) for more")
        assert result == '<p>See <a href="http://example.com">this site</a> for more</p>'

    def test_link_with_query_params(self):
        result = convert("[search](https://example.com?q=1&v=2)")
        assert result == '<p><a href="https://example.com?q=1&v=2">search</a></p>'


class TestUnorderedLists:
    def test_simple_list(self):
        md = "- one\n- two\n- three"
        assert convert(md) == "<ul>\n<li>one</li>\n<li>two</li>\n<li>three</li>\n</ul>"

    def test_list_with_formatting(self):
        md = "- **bold** item\n- *italic* item"
        assert convert(md) == "<ul>\n<li><strong>bold</strong> item</li>\n<li><em>italic</em> item</li>\n</ul>"

    def test_nested_list(self):
        md = "- top\n  - nested\n- back"
        assert convert(md) == "<ul>\n<li>top\n<ul>\n<li>nested</li>\n</ul>\n</li>\n<li>back</li>\n</ul>"

    def test_list_with_code(self):
        md = "- item with `code`"
        assert convert(md) == "<ul>\n<li>item with <code>code</code></li>\n</ul>"


class TestOrderedLists:
    def test_simple_ordered_list(self):
        md = "1. first\n2. second\n3. third"
        assert convert(md) == "<ol>\n<li>first</li>\n<li>second</li>\n<li>third</li>\n</ol>"

    def test_ordered_list_with_formatting(self):
        md = "1. **bold** item"
        assert convert(md) == "<ol>\n<li><strong>bold</strong> item</li>\n</ol>"


class TestBlockquotes:
    def test_simple_blockquote(self):
        assert convert("> quoted text") == "<blockquote>\n<p>quoted text</p>\n</blockquote>"

    def test_blockquote_with_formatting(self):
        result = convert("> **bold** quote")
        assert result == "<blockquote>\n<p><strong>bold</strong> quote</p>\n</blockquote>"

    def test_multiline_blockquote(self):
        md = "> line 1\n> line 2"
        assert convert(md) == "<blockquote>\n<p>line 1\nline 2</p>\n</blockquote>"


class TestHorizontalRule:
    def test_simple_hr(self):
        assert convert("---") == "<hr>"

    def test_hr_with_surrounding_content(self):
        md = "above\n\n---\n\nbelow"
        result = convert(md)
        assert "<hr>" in result
        assert "above" in result
        assert "below" in result


class TestParagraphs:
    def test_simple_paragraph(self):
        assert convert("Hello world") == "<p>Hello world</p>"

    def test_multi_line_paragraph(self):
        md = "line 1\nline 2"
        assert convert(md) == "<p>line 1\nline 2</p>"

    def test_separate_paragraphs(self):
        md = "para 1\n\npara 2"
        result = convert(md)
        assert "<p>para 1</p>" in result
        assert "<p>para 2</p>" in result

    def test_empty_input(self):
        assert convert("") == ""

    def test_whitespace_only(self):
        assert convert("   \n  \n  ") == ""


class TestMixedContent:
    def test_header_then_paragraph(self):
        md = "# Title\n\nSome text"
        result = convert(md)
        assert "<h1>Title</h1>" in result
        assert "<p>Some text</p>" in result

    def test_list_then_paragraph(self):
        md = "- item 1\n- item 2\n\nA paragraph"
        result = convert(md)
        assert "<ul>" in result
        assert "<li>item 1</li>" in result
        assert "<p>A paragraph</p>" in result

    def test_code_block_then_paragraph(self):
        md = "```\ncode\n```\n\nAfter code"
        result = convert(md)
        assert "<pre><code>" in result
        assert "<p>After code</p>" in result

    def test_header_with_link(self):
        result = convert("# [Home](https://example.com)")
        assert result == '<h1><a href="https://example.com">Home</a></h1>'

    def test_blockquote_containing_list(self):
        md = "> - item 1\n> - item 2"
        result = convert(md)
        assert "<blockquote>" in result
        assert "<ul>" in result
        assert "<li>item 1</li>" in result
