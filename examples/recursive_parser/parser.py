"""A recursive descent JSON parser."""
from typing import Any


class ParseError(Exception):
    """Raised when the JSON input is invalid."""
    pass


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def error(self, msg: str = "invalid JSON") -> None:
        raise ParseError(f"{msg} at position {self.pos}")

    def skip_whitespace(self) -> None:
        while self.pos < self.length and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    def peek(self) -> str:
        if self.pos >= self.length:
            self.error("unexpected end of input")
        return self.text[self.pos]

    def parse_value(self) -> Any:
        self.skip_whitespace()
        ch = self.peek()
        if ch == '"':
            return self.parse_string()
        if ch == '[':
            return self.parse_array()
        if ch == '{':
            return self.parse_object()
        if ch == '-' or ch.isdigit():
            return self.parse_number()
        if ch == 't':
            return self.parse_literal("true", True)
        if ch == 'f':
            return self.parse_literal("false", False)
        if ch == 'n':
            return self.parse_literal("null", None)
        self.error("invalid token")

    def parse_literal(self, literal: str, value: Any) -> Any:
        end = self.pos + len(literal)
        if self.text[self.pos:end] == literal:
            self.pos = end
            return value
        self.error("invalid token")

    def parse_number(self) -> Any:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < self.length and self.text[self.pos].isdigit():
            self.pos += 1
        is_float = False
        if self.pos < self.length and self.text[self.pos] == '.':
            is_float = True
            self.pos += 1
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                self.error("invalid number")
            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
        # optional exponent
        if self.pos < self.length and self.text[self.pos] in 'eE':
            is_float = True
            self.pos += 1
            if self.pos < self.length and self.text[self.pos] in '+-':
                self.pos += 1
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                self.error("invalid number")
            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
        num_str = self.text[start:self.pos]
        if is_float:
            return float(num_str)
        return int(num_str)

    def parse_string(self) -> str:
        # assumes current char is '"'
        self.pos += 1
        chars = []
        while True:
            if self.pos >= self.length:
                self.error("unterminated string")
            ch = self.text[self.pos]
            if ch == '"':
                self.pos += 1
                return "".join(chars)
            if ch == '\\':
                self.pos += 1
                if self.pos >= self.length:
                    self.error("unterminated string")
                esc = self.text[self.pos]
                if esc == '"':
                    chars.append('"')
                elif esc == '\\':
                    chars.append('\\')
                elif esc == 'n':
                    chars.append('\n')
                elif esc == 't':
                    chars.append('\t')
                elif esc == 'r':
                    chars.append('\r')
                elif esc == '/':
                    chars.append('/')
                elif esc == 'b':
                    chars.append('\b')
                elif esc == 'f':
                    chars.append('\f')
                elif esc == 'u':
                    hex_digits = self.text[self.pos + 1:self.pos + 5]
                    if len(hex_digits) != 4:
                        self.error("invalid unicode escape")
                    try:
                        code = int(hex_digits, 16)
                    except ValueError:
                        self.error("invalid unicode escape")
                    chars.append(chr(code))
                    self.pos += 4
                else:
                    self.error("invalid escape character")
                self.pos += 1
            else:
                chars.append(ch)
                self.pos += 1

    def parse_array(self) -> list:
        self.pos += 1  # consume '['
        result = []
        self.skip_whitespace()
        if self.pos < self.length and self.text[self.pos] == ']':
            self.pos += 1
            return result
        while True:
            self.skip_whitespace()
            if self.pos >= self.length:
                self.error("unterminated array")
            if self.text[self.pos] == ']':
                # trailing comma or empty
                if result:
                    self.error("trailing comma in array")
                self.pos += 1
                return result
            if self.text[self.pos] == ',':
                self.error("double comma in array")
            result.append(self.parse_value())
            self.skip_whitespace()
            if self.pos >= self.length:
                self.error("unterminated array")
            ch = self.text[self.pos]
            if ch == ',':
                self.pos += 1
                continue
            elif ch == ']':
                self.pos += 1
                return result
            else:
                self.error("expected ',' or ']' in array")

    def parse_object(self) -> dict:
        self.pos += 1  # consume '{'
        result = {}
        self.skip_whitespace()
        if self.pos < self.length and self.text[self.pos] == '}':
            self.pos += 1
            return result
        while True:
            self.skip_whitespace()
            if self.pos >= self.length:
                self.error("unterminated object")
            if self.text[self.pos] == '}':
                if result:
                    self.error("trailing comma in object")
                self.pos += 1
                return result
            if self.text[self.pos] != '"':
                self.error("expected string key in object")
            key = self.parse_string()
            self.skip_whitespace()
            if self.pos >= self.length or self.text[self.pos] != ':':
                self.error("expected ':' in object")
            self.pos += 1
            value = self.parse_value()
            result[key] = value
            self.skip_whitespace()
            if self.pos >= self.length:
                self.error("unterminated object")
            ch = self.text[self.pos]
            if ch == ',':
                self.pos += 1
                continue
            elif ch == '}':
                self.pos += 1
                return result
            else:
                self.error("expected ',' or '}' in object")


def parse_json(text: str) -> Any:
    """Parse a JSON string and return the corresponding Python object."""
    if text is None or len(text) == 0:
        raise ParseError("empty input")
    parser = _Parser(text)
    parser.skip_whitespace()
    if parser.pos >= parser.length:
        raise ParseError("empty input")
    value = parser.parse_value()
    parser.skip_whitespace()
    if parser.pos != parser.length:
        parser.error("trailing characters")
    return value
