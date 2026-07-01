# Recursive JSON Parser — Algorithmic Task

The working directory contains a test file (`test_parser.py`) that tests a JSON parser.

Your task:
1. Read `test_parser.py` to understand the expected behaviour
2. Create a Python file called `parser.py` that implements:
   - A function `parse_json(text: str) -> Any` that parses a JSON string and returns the corresponding Python object
   - An exception class `ParseError` that is raised on invalid input
3. The parser must handle:
   - Primitives: integers, floats, booleans (true/false), null, strings
   - Strings with escapes: \\", \\\\, \\n, \\uXXXX
   - Arrays (including nested and empty)
   - Objects (including nested and empty)
   - Whitespace (leading, trailing, between tokens)
   - Deeply nested structures
4. The parser must raise `ParseError` on:
   - Unterminated strings, arrays, objects
   - Trailing commas
   - Empty input
   - Invalid tokens
   - Double commas
5. Run the tests to verify
6. Signal done when all tests pass

Do NOT modify `test_parser.py`.

HINT: A recursive descent parser is the cleanest approach. Write a class that tracks position in the input string and has methods for each JSON value type.
