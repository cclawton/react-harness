from typing import Any


class ParseError(Exception):
    pass


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.n = len(text)

    def error(self, msg: str):
        raise ParseError(f"{msg} at position {self.pos}")

    def skip_ws(self):
        while self.pos < self.n and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    def peek(self):
        if self.pos < self.n:
            return self.text[self.pos]
        return None

    def parse(self) -> Any:
        self.skip_ws()
        if self.pos >= self.n:
            self.error("Empty input")
        value = self.parse_value()
        self.skip_ws()
        if self.pos != self.n:
            self.error("Trailing characters")
        return value

    def parse_value(self) -> Any:
        self.skip_ws()
        c = self.peek()
        if c is None:
            self.error("Unexpected end of input")
        if c == '"':
            return self.parse_string()
        if c == '[':
            return self.parse_array()
        if c == '{':
            return self.parse_object()
        if c == '-' or c.isdigit():
            return self.parse_number()
        if self.text.startswith("true", self.pos):
            self.pos += 4
            return True
        if self.text.startswith("false", self.pos):
            self.pos += 5
            return False
        if self.text.startswith("null", self.pos):
            self.pos += 4
            return None
        self.error(f"Invalid token '{c}'")

    def parse_string(self) -> str:
        # assumes current char is '"'
        self.pos += 1
        chars = []
        while True:
            if self.pos >= self.n:
                self.error("Unterminated string")
            c = self.text[self.pos]
            if c == '"':
                self.pos += 1
                return "".join(chars)
            if c == '\\':
                self.pos += 1
                if self.pos >= self.n:
                    self.error("Unterminated string")
                esc = self.text[self.pos]
                if esc == '"':
                    chars.append('"')
                elif esc == '\\':
                    chars.append('\\')
                elif esc == '/':
                    chars.append('/')
                elif esc == 'n':
                    chars.append('\n')
                elif esc == 't':
                    chars.append('\t')
                elif esc == 'r':
                    chars.append('\r')
                elif esc == 'b':
                    chars.append('\b')
                elif esc == 'f':
                    chars.append('\f')
                elif esc == 'u':
                    hexdigits = self.text[self.pos + 1:self.pos + 5]
                    if len(hexdigits) < 4:
                        self.error("Invalid unicode escape")
                    try:
                        code = int(hexdigits, 16)
                    except ValueError:
                        self.error("Invalid unicode escape")
                    chars.append(chr(code))
                    self.pos += 4
                else:
                    self.error(f"Invalid escape '\\{esc}'")
                self.pos += 1
            elif c == '\n':
                self.error("Unterminated string")
            else:
                chars.append(c)
                self.pos += 1

    def parse_number(self):
        start = self.pos
        if self.peek() == '-':
            self.pos += 1
        while self.pos < self.n and self.text[self.pos].isdigit():
            self.pos += 1
        is_float = False
        if self.peek() == '.':
            is_float = True
            self.pos += 1
            while self.pos < self.n and self.text[self.pos].isdigit():
                self.pos += 1
        if self.peek() in ('e', 'E'):
            is_float = True
            self.pos += 1
            if self.peek() in ('+', '-'):
                self.pos += 1
            while self.pos < self.n and self.text[self.pos].isdigit():
                self.pos += 1
        num_str = self.text[start:self.pos]
        if num_str in ('', '-'):
            self.error("Invalid number")
        try:
            if is_float:
                return float(num_str)
            return int(num_str)
        except ValueError:
            self.error("Invalid number")

    def parse_array(self):
        self.pos += 1  # skip [
        result = []
        self.skip_ws()
        if self.peek() == ']':
            self.pos += 1
            return result
        while True:
            value = self.parse_value()
            result.append(value)
            self.skip_ws()
            c = self.peek()
            if c == ',':
                self.pos += 1
                self.skip_ws()
                if self.peek() == ']':
                    self.error("Trailing comma in array")
                continue
            if c == ']':
                self.pos += 1
                return result
            if c is None:
                self.error("Unterminated array")
            self.error(f"Expected ',' or ']', got '{c}'")

    def parse_object(self):
        self.pos += 1  # skip {
        result = {}
        self.skip_ws()
        if self.peek() == '}':
            self.pos += 1
            return result
        while True:
            self.skip_ws()
            if self.peek() != '"':
                if self.peek() is None:
                    self.error("Unterminated object")
                self.error("Expected string key")
            key = self.parse_string()
            self.skip_ws()
            if self.peek() != ':':
                self.error("Expected ':'")
            self.pos += 1
            value = self.parse_value()
            result[key] = value
            self.skip_ws()
            c = self.peek()
            if c == ',':
                self.pos += 1
                self.skip_ws()
                if self.peek() == '}':
                    self.error("Trailing comma in object")
                continue
            if c == '}':
                self.pos += 1
                return result
            if c is None:
                self.error("Unterminated object")
            self.error(f"Expected ',' or '}}', got '{c}'")


def parse_json(text: str) -> Any:
    return _Parser(text).parse()
