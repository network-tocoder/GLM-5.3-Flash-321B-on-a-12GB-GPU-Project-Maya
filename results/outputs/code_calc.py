def evaluate(expr: str) -> float:
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]
        if c == ' ':
            i += 1
            continue
        if c in '+-*/^()':
            tokens.append(c)
            i += 1
        elif c == '.' or c.isdigit():
            j = i
            dot = 0
            while j < n and (expr[j].isdigit() or expr[j] == '.'):
                if expr[j] == '.':
                    dot += 1
                j += 1
            if dot > 1 or not (j > i and (expr[i].isdigit() or expr[i] == '.')):
                raise ValueError("invalid number")
            if expr[i] == '.' and j == i + 1:
                raise ValueError("invalid number")
            num = expr[i:j]
            if num == '.':
                raise ValueError("invalid number")
            tokens.append(float(num))
            i = j
        else:
            raise ValueError("invalid character")

    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def next_tok():
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def expect(tok):
        if pos >= len(tokens) or tokens[pos] != tok:
            raise ValueError("expected " + tok)
        nonlocal pos
        pos += 1

    def parse_expr():
        v = parse_term()
        while True:
            t = peek()
            if t == '+':
                next_tok()
                v = v + parse_term()
            elif t == '-':
                next_tok()
                v = v - parse_term()
            else:
                break
        return v

    def parse_term():
        v = parse_pow()
        while True:
            t = peek()
            if t == '*':
                next_tok()
                v = v * parse_pow()
            elif t == '/':
                next_tok()
                d = parse_pow()
                if d == 0:
                    raise ValueError("division by zero")
                v = v / d
            else:
                break
        return v

    def parse_pow():
        base = parse_unary()
        if peek() == '^':
            next_tok()
            exp = parse_pow()  # right-associative
            try:
                return base ** exp
            except (OverflowError, ZeroDivisionError):
                raise ValueError("invalid power")
        return base

    def parse_unary():
        t = peek()
        if t == '-':
            next_tok()
            return -parse_unary()
        if t == '+':
            next_tok()
            return parse_unary()
        return parse_primary()

    def parse_primary():
        t = peek()
        if t is None:
            raise ValueError("unexpected end")
        if isinstance(t, float):
            next_tok()
            return t
        if t == '(':
            next_tok()
            v = parse_expr()
            expect(')')
            return v
        raise ValueError("unexpected token")

    if not tokens:
        raise ValueError("empty expression")
    result = parse_expr()
    if pos != len(tokens):
        raise ValueError("unexpected trailing token")
    return result
