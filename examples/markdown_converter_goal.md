# Markdown to HTML Converter — Multi-File Task

The working directory contains a test file (`test_converter.py`) with 40+ tests for a markdown-to-HTML converter.

Your task:
1. Read `test_converter.py` carefully to understand the expected behaviour
2. Create FOUR Python files:
   - `tokenizer.py` — converts raw markdown text into a list of tokens
   - `parser.py` — converts tokens into an AST (tree of nodes)
   - `renderer.py` — converts the AST into HTML strings
   - `converter.py` — orchestrates the pipeline: tokenize → parse → render
     - Must export `convert(markdown: str) -> str` and `MarkdownError`
     - `MarkdownError` should be a custom exception class
3. The converter must support:
   - Headers (H1-H6 with # syntax)
   - Bold (**text**) and italic (*text*)
   - Inline code (`code`)
   - Code blocks (``` ... ```) with optional language tag
   - Links ([text](url))
   - Unordered lists (- item) with nesting (2-space indent)
   - Ordered lists (1. item)
   - Blockquotes (> text)
   - Horizontal rules (---)
   - Paragraphs
4. Critical edge cases to get right:
   - Markdown inside code blocks must NOT be converted
   - Nested formatting (bold inside italic, italic inside bold)
   - Unclosed formatting markers must raise MarkdownError
   - Empty input returns empty string
   - List nesting with proper HTML structure
5. Run the tests (`python -m pytest test_converter.py -v`) to verify
6. Signal done when all tests pass

Do NOT modify `test_converter.py`.

IMPORTANT: This is a multi-file task. Design your data structures carefully — the token format, AST node types, and renderer interface all need to be consistent across files. Most implementations fail on the first try because of edge cases in nested formatting, code block handling, or list nesting. Expect to debug — read test failures carefully, understand what's wrong, and fix it.
