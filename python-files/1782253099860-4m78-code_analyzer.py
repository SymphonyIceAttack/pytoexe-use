# -*- coding: utf-8 -*-
"""
КодАнализатор — Человек vs ИИ  v4.8
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
import ast
import math
from datetime import datetime


# ══════════════════════════════════════════════════════════════════
#  Цветовые палитры (Catppuccin Mocha & Catppuccin Latte)
# ══════════════════════════════════════════════════════════════════
MOCHA = dict(
    base     = "#0f0f1a", # Глубокий космический темный
    mantle   = "#090911", # Фоновый оттенок боковых панелей
    surface0 = "#161626", # Карточки и плоские контейнеры
    surface1 = "#202036", # Кнопки в обычном состоянии
    surface2 = "#2a2a4b", # Кнопки при наведении
    overlay0 = "#8c90a6", # Приглушенный текст
    text     = "#cdd6f4", # Основной текст
    blue     = "#89b4fa",
    sky      = "#89dceb",
    green    = "#a6e3a1",
    yellow   = "#f9e2af",
    peach    = "#fab387",
    red      = "#f38ba8",
    pink     = "#f5c2e7",
    mauve    = "#cba6f7",
)

LATTE = dict(
    base     = "#f8fafc", # Светлый slate-50
    mantle   = "#f1f5f9", # Мягкий slate-100
    surface0 = "#ffffff", # Чистый белый для карточек
    surface1 = "#e2e8f0", # Мягкие кнопки slate-200
    surface2 = "#cbd5e1", # Кнопки при наведении slate-300
    overlay0 = "#475569", # Приглушенный slate-500
    text     = "#0f172a", # Контрастный темный slate-900
    blue     = "#1d4ed8", # Насыщенный синий
    sky      = "#0369a1",
    green    = "#15803d", # Контрастный зеленый
    yellow   = "#a16207",
    peach    = "#c2410c",
    red      = "#b91c1c",
    pink     = "#be185d",
    mauve    = "#6d28d9",
)


# ══════════════════════════════════════════════════════════════════
#  АВТОМАТИЧЕСКИЙ ОПРЕДЕЛИТЕЛЬ ЯЗЫКА ПРОГРАММИРОВАНИЯ
# ══════════════════════════════════════════════════════════════════
class LanguageDetectorHeuristic:
    """Определяет язык программирования на основе частотного и регулярного анализа."""

    @staticmethod
    def detect(code: str) -> str:
        if not code.strip():
            return "Python"

        scores = {
            "Python": 0, "C++": 0, "JavaScript": 0, "Алгоритмический язык": 0,
            "Java": 0, "Kotlin": 0, "C": 0, "C#": 0, "HTML": 0, "Pascal": 0,
            "SQL": 0, "Go": 0
        }

        # Жесткие регулярные сигнатуры
        signatures = {
            "Python": [r'\bdef\s+\w+\s*\(', r'\belif\b', r'\bimport\s+\w+', r'__main__', r'print\s*\([^)]*\)', r'list\[\w+\]'],
            "C++": [r'#include\s*<\w+>', r'std::', r'using\s+namespace\s+std', r'cout\s*<<', r'vector\s*<\w+>', r'cin\s*>>'],
            "JavaScript": [r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=', r'console\.log', r'\bfunction\s+\w+\s*\(', r'document\.', r'\b=>\s*\{'],
            "Алгоритмический язык": [r'\bалг\b', r'\bнач\b', r'\bкон\b', r'\bцел\b', r'\bвещ\b', r'\bвывод\b', r'\bесли\b', r'\bнц\b', r'\bкц\b'],
            "Java": [r'public\s+class\s+\w+', r'public\s+static\s+void\s+main', r'System\.out\.print', r'import\s+java\.', r'\bextends\b'],
            "Kotlin": [r'\bfun\s+\w+', r'\bval\s+\w+', r'\bvar\s+\w+\s*:', r'println\s*\(', r'listOf\s*\('],
            "C": [r'#include\s*<\w+\.h>', r'printf\s*\(', r'scanf\s*\(', r'malloc\s*\(', r'\bstruct\s+\w+\s*\{'],
            "C#": [r'using\s+System', r'Console\.Write', r'namespace\s+\w+', r'public\s+class\s+\w+', r'static\s+void\s+Main'],
            "HTML": [r'<!DOCTYPE\s+html>', r'<html\b', r'<body\b', r'</\w+>', r'class\s*=\s*["\']', r'id\s*=\s*["\']'],
            "Pascal": [r'\bprogram\s+\w+', r'\bbegin\b', r'\bend\.', r'writeln\s*\(', r':=\s*', r'\bvar\b\s+\w+'],
            "SQL": [r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bLEFT\b\s+\bJOIN\b', r'\bGROUP\b\s+\bBY\b', r'\bINSERT\b\s+\bINTO\b'],
            "Go": [r'\bpackage\s+main', r'\bfunc\s+\w+\s*\(', r'import\s+\(', r'fmt\.Print']
        }

        for lang, regexes in signatures.items():
            for rx in regexes:
                matches = len(re.findall(rx, code, re.IGNORECASE if lang in ("SQL", "Pascal", "Алгоритмический язык") else 0))
                scores[lang] += matches * 12

        # Ключевые слова
        keywords = {
            "Python": ["def", "import", "from", "elif", "not in", "is None"],
            "C++": ["include", "iostream", "vector", "std", "namespace", "cout"],
            "JavaScript": ["const", "let", "var", "function", "console", "require", "typeof"],
            "Алгоритмический язык": ["алг", "нач", "кон", "если", "иначе", "вывод", "цел", "вещ"],
            "Java": ["public", "private", "protected", "static", "void", "class", "import"],
            "Kotlin": ["fun", "val", "var", "println", "mapOf", "listOf"],
            "C": ["include", "printf", "scanf", "malloc", "struct", "free"],
            "C#": ["using", "namespace", "Console", "WriteLine", "class"],
            "HTML": ["div", "span", "href", "src", "class", "head", "link"],
            "Pascal": ["program", "begin", "end", "writeln", "readln", "procedure", "function"],
            "SQL": ["select", "from", "where", "group", "by", "order", "join"],
            "Go": ["func", "package", "import", "fmt", "chan", "go", "defer"]
        }

        for lang, words in keywords.items():
            for word in words:
                matches = len(re.findall(r'\b' + re.escape(word) + r'\b', code, re.IGNORECASE if lang in ("SQL", "Pascal", "Алгоритмический язык") else 0))
                scores[lang] += matches * 3

        return max(scores, key=scores.get)


# ══════════════════════════════════════════════════════════════════
#  AST VISITOR (Для Python)
# ══════════════════════════════════════════════════════════════════
class MetricsVisitor(ast.NodeVisitor):
    """Обходит AST Python и собирает метрики качества кода."""

    TRIVIAL  = frozenset("_ i j k x y z n m".split())
    SAFE_NUM = frozenset({0, 1, 2, 10, 100, -1, 255, 360, 1000})

    def __init__(self):
        self.functions: list = []
        self.classes:   list = []
        self.imports        = 0
        self.docstrings     = 0
        self.magic_numbers  = 0
        self.for_loops      = 0
        self.while_loops    = 0
        self.if_stmts       = 0
        self.try_blocks     = 0
        self.type_hints     = 0
        self.lambda_count   = 0
        self.comprehensions = 0
        self.all_names: set = set()
        self.short_names    = 0
        self.descriptive    = 0
        self.cyclomatic     = 1
        self._depth         = 0
        self.max_depth      = 0

    def _push(self):
        self._depth += 1
        if self._depth > self.max_depth:
            self.max_depth = self._depth

    def _pop(self):
        self._depth -= 1

    def _track(self, name: str):
        self.all_names.add(name)
        if len(name) <= 1 and name not in self.TRIVIAL:
            self.short_names += 1
        elif len(name) >= 4:
            self.descriptive += 1

    def _has_docstring(self, node) -> bool:
        return (
            bool(node.body)
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )

    def visit_FunctionDef(self, node):
        self.functions.append(node)
        self._track(node.name)
        if self._has_docstring(node):
            self.docstrings += 1
        if node.returns:
            self.type_hints += 1
        self.type_hints += sum(1 for a in node.args.args if a.annotation)
        self._push()
        self.generic_visit(node)
        self._pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.classes.append(node)
        self._track(node.name)
        if self._has_docstring(node):
            self.docstrings += 1
        self._push()
        self.generic_visit(node)
        self._pop()

    def visit_Import(self, node):
        self.imports += len(node.names)

    def visit_ImportFrom(self, node):
        self.imports += max(len(node.names), 1)

    def visit_Constant(self, node):
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if v not in self.SAFE_NUM and abs(v) >= 3:
                self.magic_numbers += 1

    def visit_If(self, node):
        self.if_stmts += 1
        self.cyclomatic += 1
        self._push()
        self.generic_visit(node)
        self._pop()

    def visit_For(self, node):
        self.for_loops += 1
        self.cyclomatic += 1
        self._push()
        self.generic_visit(node)
        self._pop()

    def visit_While(self, node):
        self.while_loops += 1
        self.cyclomatic += 1
        self._push()
        self.generic_visit(node)
        self._pop()

    def visit_Try(self, node):
        self.try_blocks += 1
        self.cyclomatic += max(len(node.handlers), 1)
        self.generic_visit(node)

    def visit_Lambda(self, node):
        self.lambda_count += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.comprehensions += 1
        self.generic_visit(node)

    visit_DictComp = visit_SetComp = visit_GeneratorExp = visit_ListComp

    def visit_Assign(self, node):
        def _names(t):
            if isinstance(t, ast.Name):
                self._track(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                for e in t.elts:
                    _names(e)
        for t in node.targets:
            _names(t)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            self._track(node.target.id)
        self.type_hints += 1
        self.generic_visit(node)

    def avg_func_length(self) -> float:
        if not self.functions:
            return 0.0
        lens = [
            getattr(f, "end_lineno", f.lineno + 1) - f.lineno + 1
            for f in self.functions
        ]
        return round(sum(lens) / len(lens), 1)

    def name_quality(self) -> float:
        total = len(self.all_names)
        return round(self.descriptive / total, 3) if total else 1.0


# ══════════════════════════════════════════════════════════════════
#  МУЛЬТИЯЗЫЧНАЯ ПОДСВЕТКА СИНТАКСИСА
# ══════════════════════════════════════════════════════════════════
class SyntaxHighlighter:
    """Динамический синтаксический анализатор для редактора кода."""

    LANG_KEYWORDS = {
        "Python": frozenset([
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "not", "or", "pass", "raise", "return", "try", "while",
            "with", "yield"
        ]),
        "C++": frozenset([
            "auto", "bool", "break", "case", "catch", "char", "class", "const",
            "continue", "default", "delete", "do", "double", "else", "enum",
            "explicit", "export", "extern", "false", "float", "for", "friend",
            "goto", "if", "inline", "int", "long", "namespace", "new", "nullptr",
            "private", "protected", "public", "return", "short", "signed",
            "sizeof", "static", "struct", "switch", "template", "this", "throw",
            "true", "try", "typedef", "typename", "union", "unsigned", "using",
            "virtual", "void", "while"
        ]),
        "JavaScript": frozenset([
            "break", "case", "catch", "class", "const", "continue", "debugger",
            "default", "delete", "do", "else", "export", "extends", "finally",
            "for", "function", "if", "import", "in", "instanceof", "new",
            "return", "super", "switch", "this", "throw", "try", "typeof",
            "var", "void", "while", "with", "yield", "let", "async", "await",
            "null", "undefined", "true", "false"
        ]),
        "Алгоритмический язык": frozenset([
            "алг", "нач", "кон", "дано", "надо", "если", "то", "иначе", "все",
            "выбор", "при", "нц", "кц", "пока", "для", "цел", "вещ", "сим",
            "лит", "лог", "да", "нет", "раз", "знач", "вывод", "ввод"
        ]),
        "Java": frozenset([
            "class", "interface", "public", "private", "protected", "static", "void",
            "int", "double", "float", "boolean", "char", "if", "else", "for", "while",
            "do", "try", "catch", "finally", "throw", "new", "return", "import",
            "package", "this", "super", "true", "false", "null", "final"
        ]),
        "Kotlin": frozenset([
            "fun", "class", "interface", "val", "var", "if", "else", "for", "while",
            "do", "try", "catch", "finally", "throw", "return", "import", "package",
            "this", "super", "true", "false", "null", "when", "object"
        ]),
        "C": frozenset([
            "int", "float", "double", "char", "void", "struct", "if", "else", "for",
            "while", "do", "switch", "case", "break", "continue", "return", "typedef",
            "const", "static", "unsigned"
        ]),
        "C#": frozenset([
            "using", "namespace", "class", "struct", "interface", "public", "private",
            "protected", "internal", "static", "void", "int", "double", "float", "bool",
            "string", "char", "if", "else", "for", "foreach", "while", "do", "try", "catch",
            "finally", "throw", "new", "return", "this", "true", "false", "null", "var"
        ]),
        "HTML": frozenset([
            "doctype", "html", "head", "body", "div", "span", "p", "a", "img", "script",
            "style", "h1", "h2", "h3", "ul", "li", "table", "tr", "td", "form", "input",
            "button", "class", "id", "href", "src", "rel", "type"
        ]),
        "Pascal": frozenset([
            "program", "begin", "end", "var", "integer", "real", "char", "string",
            "boolean", "if", "then", "else", "for", "to", "do", "while", "repeat",
            "until", "procedure", "function", "const", "type", "array", "of", "not",
            "and", "or", "true", "false", "exit"
        ]),
        "SQL": frozenset([
            "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "ON", "GROUP",
            "BY", "HAVING", "ORDER", "INSERT", "INTO", "UPDATE", "SET", "DELETE",
            "CREATE", "TABLE", "DROP", "INDEX", "AND", "OR", "NOT", "IN", "IS", "NULL",
            "AS", "WITH"
        ]),
        "Go": frozenset([
            "func", "package", "import", "const", "var", "type", "struct", "interface",
            "map", "chan", "if", "else", "for", "switch", "case", "default", "select",
            "defer", "go", "return", "range", "nil", "true", "false"
        ])
    }

    LANG_BUILTINS = {
        "Python": frozenset([
            "print", "len", "range", "int", "str", "float", "list", "dict",
            "tuple", "set", "bool", "type", "isinstance", "hasattr", "getattr",
            "enumerate", "zip", "map", "filter", "sorted", "sum", "min", "max"
        ]),
        "C++": frozenset([
            "std", "cout", "cin", "endl", "vector", "string", "map", "set",
            "printf", "scanf", "size", "push_back"
        ]),
        "JavaScript": frozenset([
            "console", "log", "window", "document", "Math", "JSON", "Promise",
            "Array", "Object", "String", "Number", "setTimeout"
        ]),
        "Алгоритмический язык": frozenset([
            "утв", "арг", "рез"
        ]),
        "Java": frozenset([
            "System", "out", "println", "print", "Math", "String", "List", "ArrayList"
        ]),
        "Kotlin": frozenset([
            "println", "print", "Array", "List", "Map", "listOf", "mutableListOf"
        ]),
        "C": frozenset([
            "printf", "scanf", "malloc", "free", "size_t", "NULL"
        ]),
        "C#": frozenset([
            "Console", "WriteLine", "Write", "Math", "List", "Dictionary"
        ]),
        "HTML": frozenset([
            "meta", "title", "link", "footer", "header", "section", "article"
        ]),
        "Pascal": frozenset([
            "Write", "WriteLine", "Read", "ReadLine", "Abs", "Sqrt", "Length"
        ]),
        "SQL": frozenset([
            "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "NOW"
        ]),
        "Go": frozenset([
            "fmt", "Println", "Printf", "make", "new", "len", "cap", "append"
        ])
    }

    def __init__(self, text: tk.Text, app):
        self.t = text
        self.app = app
        self._setup()
        text.bind("<KeyRelease>", lambda _: self.highlight(), add=True)

    def _setup(self):
        self._setup_colors()

    def _setup_colors(self):
        t = self.t
        c = self.app.C
        t.tag_configure("kw",      foreground=c["mauve"])
        t.tag_configure("builtin", foreground=c["sky"])
        t.tag_configure("string",  foreground=c["green"])
        t.tag_configure("comment", foreground=c["overlay0"], font=("Consolas", 10, "italic"))
        t.tag_configure("number",  foreground=c["peach"])
        t.tag_configure("deco",    foreground=c["pink"])
        t.tag_configure("defname", foreground=c["blue"])

    def highlight(self):
        t = self.t
        lang = self.app.current_lang.get()

        for tag in ("kw", "builtin", "string", "comment", "number", "deco", "defname"):
            t.tag_remove(tag, "1.0", tk.END)

        src = t.get("1.0", tk.END)

        def mark(tag, s, e):
            t.tag_add(tag, f"1.0+{s}c", f"1.0+{e}c")

        protected: list[tuple[int, int]] = []

        def is_protected(pos):
            return any(s <= pos < e for s, e in protected)

        # 1. Многострочные строки / Комментарии
        if lang == "Python":
            for m in re.finditer(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', src):
                mark("string", m.start(), m.end())
                protected.append((m.start(), m.end()))
        elif lang in ("C++", "JavaScript", "Java", "Kotlin", "C", "C#", "Go", "Pascal", "SQL"):
            block_comment_patterns = {
                "Pascal": r'\b\(\*[\s\S]*?\*\)|\{[\s\S]*?\}',
                "SQL": r'/\*[\s\S]*?\*/'
            }
            pat = block_comment_patterns.get(lang, r'/\*[\s\S]*?\*/')
            for m in re.finditer(pat, src):
                mark("comment", m.start(), m.end())
                protected.append((m.start(), m.end()))
        elif lang == "HTML":
            for m in re.finditer(r'<!--[\s\S]*?-->', src):
                mark("comment", m.start(), m.end())
                protected.append((m.start(), m.end()))

        # 2. Строковые литералы
        str_pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
        if lang == "JavaScript":
            str_pattern += r'|`(?:\\.|[^`\\])*`'
        for m in re.finditer(str_pattern, src):
            if not is_protected(m.start()):
                mark("string", m.start(), m.end())
                protected.append((m.start(), m.end()))

        # 3. Однострочные комментарии
        comment_patterns = {
            "Python": r"#[^\n]*",
            "C++": r"//[^\n]*",
            "JavaScript": r"//[^\n]*",
            "Алгоритмический язык": r"(?:#|\|)[^\n]*",
            "Java": r"//[^\n]*",
            "Kotlin": r"//[^\n]*",
            "C": r"//[^\n]*",
            "C#": r"//[^\n]*",
            "HTML": r"<!--[^\n]*",
            "Pascal": r"//[^\n]*",
            "SQL": r"--[^\n]*",
            "Go": r"//[^\n]*"
        }
        for m in re.finditer(comment_patterns.get(lang, r"#[^\n]*"), src):
            if not is_protected(m.start()):
                mark("comment", m.start(), m.end())
                protected.append((m.start(), m.end()))

        # 4. Препроцессор / Декораторы
        deco_pat = r"@[\w.]+" if lang in ("Python", "JavaScript", "Java", "Kotlin") else r"#\s*\w+"
        for m in re.finditer(deco_pat, src):
            if not is_protected(m.start()):
                mark("deco", m.start(), m.end())

        # 5. Имена определений функций / классов
        def_patterns = {
            "Python": r"\b(?:def|class)\s+(\w+)",
            "C++": r"\b(?:class|struct)\s+(\w+)",
            "JavaScript": r"\b(?:class|function)\s+(\w+)",
            "Алгоритмический язык": r"\bалг\s+([а-яА-ЯёЁa-zA-Z_]\w*)",
            "Java": r"\b(?:class|interface)\s+(\w+)",
            "Kotlin": r"\b(?:class|fun)\s+(\w+)",
            "C": r"\b[a-zA-Z_]\w*(?:\s+[*&]?\s*|\s+)([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{",
            "C#": r"\b(?:class|interface)\s+(\w+)",
            "HTML": r"<([a-zA-Z1-6]+)\b",
            "Pascal": r"\b(?:procedure|function)\s+(\w+)",
            "SQL": r"\b(?:TABLE|PROCEDURE|FUNCTION)\s+([a-zA-Z_]\w*)",
            "Go": r"\b(?:func|struct)\s+(\w+)"
        }
        for m in re.finditer(def_patterns.get(lang, r"\b\w+"), src):
            try:
                start_idx = m.start(1)
                end_idx = m.end(1)
                if start_idx != -1 and not is_protected(start_idx):
                    mark("defname", start_idx, end_idx)
            except IndexError:
                pass

        # 6. Числа
        for m in re.finditer(r"\b\d+\.?\d*\b", src):
            if not is_protected(m.start()):
                mark("number", m.start(), m.end())

        # 7. Ключевые слова
        kw_list = self.LANG_KEYWORDS.get(lang, frozenset())
        bi_list = self.LANG_BUILTINS.get(lang, frozenset())
        word_pattern = r"\b[A-Za-z_А-Яа-яёЁ][\wА-Яа-яёЁ]*\b"
        for m in re.finditer(word_pattern, src):
            if is_protected(m.start()):
                continue
            w = m.group()
            if w in kw_list:
                mark("kw", m.start(), m.end())
            elif w in bi_list:
                mark("builtin", m.start(), m.end())


# ══════════════════════════════════════════════════════════════════
#  НОМЕРА СТРОК
# ══════════════════════════════════════════════════════════════════
class LineNumbers(tk.Canvas):
    """Синхронизированная боковая полоса с номерами строк."""

    def __init__(self, parent, text_widget: tk.Text, app, **kw):
        self.app = app
        super().__init__(parent, bg=app.C["mantle"], width=44, highlightthickness=0, **kw)
        self.text = text_widget
        text_widget.bind("<KeyRelease>", self.redraw, add=True)
        text_widget.bind("<MouseWheel>", self.redraw, add=True)
        text_widget.bind("<Configure>",  self.redraw, add=True)

    def redraw(self, _=None):
        try:
            self.delete("all")
            self.configure(bg=self.app.C["mantle"])
            i = self.text.index("@0,0")
            while True:
                dline = self.text.dlineinfo(i)
                if dline is None:
                    break
                y = dline[1]
                lineno = str(i).split(".")[0]
                self.create_text(40, y, anchor="ne", text=lineno,
                                 fill=self.app.C["overlay0"], font=("Consolas", 9))
                nxt = self.text.index(f"{i}+1line")
                if nxt == i:
                    break
                i = nxt
        except tk.TclError:
            pass


# ══════════════════════════════════════════════════════════════════
#  SPIDER CHART — паутинная диаграмма по 6 измерениям
# ══════════════════════════════════════════════════════════════════
class SpiderChart(tk.Canvas):
    """Визуализирует качество архитектурного построения кода."""

    def __init__(self, parent, app, size: int = 220, **kw):
        self.app = app
        super().__init__(parent, bg=app.C["base"], width=size, height=size, highlightthickness=0, **kw)
        self.size = size
        self.cx   = size // 2
        self.cy   = size // 2
        self.r    = size // 2 - 30
        self._vals = [0.0] * 6
        self._draw()

    def set_scores(self, scores: list[float]):
        self._vals = [max(0.0, min(1.0, v)) for v in scores]
        self._draw()

    def _pt(self, axis_i: int, frac: float, offset=math.pi / 2):
        angle = 2 * math.pi * axis_i / 6 - offset
        r = self.r * frac
        return self.cx + r * math.cos(angle), self.cy - r * math.sin(angle)

    def _draw(self):
        self.delete("all")
        self.configure(bg=self.app.C["base"])
        n = 6
        axes_labels = [
            ("Документация", self.app.C["blue"]),
            ("Именование",   self.app.C["green"]),
            ("Структура",    self.app.C["mauve"]),
            ("Надёжность",   self.app.C["yellow"]),
            ("Лаконичность", self.app.C["sky"]),
            ("Архитектура",  self.app.C["peach"]),
        ]

        # Концентрические сетки
        for pct in (0.25, 0.5, 0.75, 1.0):
            pts = []
            for i in range(n):
                pts.extend(self._pt(i, pct))
            self.create_polygon(*pts, outline=self.app.C["surface1"], fill="", width=1)

        # Оси и подписи
        for i, (label, color) in enumerate(axes_labels):
            ox, oy = self._pt(i, 0.0)
            ex, ey = self._pt(i, 1.0)
            self.create_line(ox, oy, ex, ey, fill=self.app.C["surface2"], width=1)
            lx, ly = self._pt(i, 1.22)
            self.create_text(lx, ly, text=label, fill=color,
                             font=("Segoe UI", 7, "bold"), anchor="center")

        # Полигон значений
        pts = []
        for i, v in enumerate(self._vals):
            pts.extend(self._pt(i, max(v, 0.03)))
        poly_color = self.app.C["surface1"]
        self.create_polygon(*pts, fill=poly_color, outline=self.app.C["blue"], width=2)

        # Точки
        for i, (_, color) in enumerate(axes_labels):
            x, y = self._pt(i, max(self._vals[i], 0.03))
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")


# ══════════════════════════════════════════════════════════════════
#  GAUGE — полукруговой индикатор оценки
# ══════════════════════════════════════════════════════════════════
class ScoreGauge(tk.Canvas):
    """Стрелочный индикатор общего рейтинга кода."""

    def __init__(self, parent, app, size: int = 160, **kw):
        self.app = app
        super().__init__(parent, bg=app.C["base"], width=size, height=size // 2 + 36, highlightthickness=0, **kw)
        self.size = size
        self._score = 0
        self._draw(0)

    def set_score(self, score: int):
        self._score = score
        self._draw(score)

    def _color(self, score: int) -> str:
        if score >= 75: return self.app.C["green"]
        if score >= 50: return self.app.C["yellow"]
        if score >= 25: return self.app.C["peach"]
        return self.app.C["red"]

    def _draw(self, score: int):
        self.delete("all")
        self.configure(bg=self.app.C["base"])
        m  = 14
        s  = self.size
        cx = s // 2
        cy = s // 2

        self.create_arc(m, m, s - m, s - m, start=180, extent=-180,
                        outline=self.app.C["surface1"], width=16, style=tk.ARC)

        if score > 0:
            ext = int(score / 100 * 180)
            self.create_arc(m, m, s - m, s - m, start=180, extent=-ext,
                            outline=self._color(score), width=16, style=tk.ARC)

        self.create_text(cx, cy + 4, text=str(score), fill=self._color(score), font=("Segoe UI", 24, "bold"))
        self.create_text(cx, cy + 24, text="/ 100", fill=self.app.C["overlay0"], font=("Segoe UI", 9))


# ══════════════════════════════════════════════════════════════════
#  ШКАЛА ВЕРОЯТНОСТИ ИИ-ГЕНЕРАЦИИ (Rounded Progress Indicator)
# ══════════════════════════════════════════════════════════════════
class ProbabilityIndicator(tk.Canvas):
    """Визуализатор уровня присутствия генеративных паттернов ИИ (0–100%)."""

    def __init__(self, parent, app, size: int = 180, **kw):
        self.app = app
        super().__init__(parent, bg=app.C["base"], width=size, height=30, highlightthickness=0, **kw)
        self.size = size
        self._pct = 0
        self._draw()

    def set_percentage(self, pct: int):
        self._pct = max(0, min(100, pct))
        self._draw()

    def _draw(self):
        self.delete("all")
        self.configure(bg=self.app.C["base"])
        w = self.size
        h = 18
        pad = 2

        # Трек фона
        self.create_rectangle(0, pad, w, pad + h, fill=self.app.C["surface1"], outline="", width=0)

        # Заполнение шкалы
        if self._pct > 0:
            fill_w = int(w * (self._pct / 100))
            color = self.app.C["peach"] if self._pct > 50 else self.app.C["green"]
            self.create_rectangle(0, pad, fill_w, pad + h, fill=color, outline="", width=0)

        # Текстовое значение
        self.create_text(w // 2, pad + h // 2, text=f"Анализ ИИ: {self._pct}%",
                         fill=self.app.C["text"], font=("Segoe UI", 8, "bold"))


# ══════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ══════════════════════════════════════════════════════════════════
class CodeAnalyzer:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("КодАнализатор — Человек vs ИИ  v4.8")
        self.root.geometry("1240x780")
        self.theme_mode = "dark"
        self.C = MOCHA
        self.root.configure(bg=self.C["base"])
        self.root.minsize(1000, 640)

        self._last_metrics = None
        self._last_score   = 0

        self.language_detector = LanguageDetectorHeuristic()

        self._create_widgets()
        self._apply_theme()
        self._setup_shortcuts()

    def _create_styles(self):
        st = ttk.Style()
        st.theme_use("clam")

        bg     = self.C["base"]
        s0     = self.C["surface0"]
        s1     = self.C["surface1"]
        s2     = self.C["surface2"]
        text   = self.C["text"]
        blue   = self.C["blue"]
        pink   = self.C["pink"]
        mantle = self.C["mantle"]

        st.configure(".", background=bg, foreground=text, font=("Segoe UI", 10))
        st.configure("TNotebook", background=bg, borderwidth=0)
        st.configure("TNotebook.Tab", background=s0, foreground=text, padding=[14, 7], font=("Segoe UI", 10), borderwidth=0)
        st.map("TNotebook.Tab", background=[("selected", s1)], foreground=[("selected", pink)])
        st.configure("TFrame", background=bg)
        st.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
        st.configure("Title.TLabel", background=bg, foreground=pink, font=("Segoe UI", 14, "bold"))
        st.configure("Header.TLabel", background=bg, foreground=blue, font=("Segoe UI", 11, "bold"))
        st.configure("Sub.TLabel", background=bg, foreground=self.C["overlay0"], font=("Segoe UI", 9))
        st.configure("TButton", background=s1, foreground=text, borderwidth=0, focuscolor="", font=("Segoe UI", 10), padding=[10, 5])
        st.map("TButton", background=[("active", s2), ("pressed", s0)], foreground=[("active", text)])
        st.configure("Accent.TButton", background=s2, foreground=pink, font=("Segoe UI", 10, "bold"), borderwidth=0)
        st.map("Accent.TButton", background=[("active", s0), ("pressed", s1)], foreground=[("active", pink)])

        st.configure("Treeview", background=s0, foreground=text, fieldbackground=s0, font=("Consolas", 9), rowheight=22, borderwidth=0)
        st.configure("Treeview.Heading", background=s1, foreground=blue, font=("Segoe UI", 9, "bold"), borderwidth=0)
        st.map("Treeview", background=[("selected", s2)])

        st.configure("TCombobox", fieldbackground=s0, background=s1, foreground=text, borderwidth=0)
        st.map("TCombobox", fieldbackground=[("readonly", s0)], background=[("readonly", s1)], foreground=[("readonly", text)])
        st.configure("TScrollbar", background=s0, troughcolor=bg, borderwidth=0, arrowsize=12)

    def _configure_widget_colors(self, widget, bg, mantle, s0, text):
        w_class = widget.winfo_class()
        # Изменяем цвета только у нативных (не-ttk) элементов
        if not w_class.startswith("T") and w_class != "Treeview":
            try:
                if w_class in ("Frame", "LabelFrame"):
                    widget.configure(bg=bg)
                elif w_class == "Label":
                    widget.configure(bg=bg, fg=text)
                elif w_class == "Canvas":
                    widget.configure(bg=bg)
            except Exception:
                pass
        
        # Рекурсивный обход всех дочерних элементов
        for child in widget.winfo_children():
            self._configure_widget_colors(child, bg, mantle, s0, text)

    def _create_widgets(self):
        # Хедер
        hf = ttk.Frame(self.root)
        hf.pack(fill=tk.X, padx=12, pady=(10, 2))

        ttk.Label(hf, text="КодАнализатор — Человек vs ИИ", style="Title.TLabel").pack(side=tk.LEFT)

        cf = ttk.Frame(hf)
        cf.pack(side=tk.RIGHT)

        # Выделенный контейнер для бэйджа определенного языка
        self.badge_frame = tk.Frame(cf, bg=self.C["surface1"], padx=10, pady=4)
        self.badge_frame.pack(side=tk.LEFT, padx=5)
        self.badge_label = tk.Label(self.badge_frame, text="Язык: Python", bg=self.C["surface1"], fg=self.C["pink"], font=("Segoe UI", 9, "bold"))
        self.badge_label.pack()

        self.theme_btn = ttk.Button(cf, text="🌙 Тёмная", command=self._toggle_theme, width=12)
        self.theme_btn.pack(side=tk.LEFT, padx=5)

        mf = ttk.Frame(self.root)
        mf.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.nb = ttk.Notebook(mf)
        self.nb.pack(fill=tk.BOTH, expand=True)

        for attr, label, builder in [
            ("tab_input",   "  Ввод кода  ",            self._create_input_tab),
            ("tab_results", "  Результаты анализа  ",   self._create_results_tab),
            ("tab_compare", "  Человек vs ИИ  ",        self._create_compare_tab),
            ("tab_about",   "  О проекте  ",            self._create_about_tab),
        ]:
            frame = ttk.Frame(self.nb)
            setattr(self, attr, frame)
            self.nb.add(frame, text=label)
            builder()

    def _create_input_tab(self):
        top = ttk.Frame(self.tab_input)
        top.pack(fill=tk.X, padx=6, pady=(6, 4))

        ttk.Label(top, text="Исходный код для анализа (автоопределение включено):", style="Header.TLabel").pack(anchor=tk.W)

        btn = ttk.Frame(top)
        btn.pack(fill=tk.X, pady=(6, 2))

        # Комбобокс выбора примеров перемещен в секцию кнопок
        ttk.Label(btn, text="Пример для языка: ", style="Sub.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.example_lang = tk.StringVar(value="Python")
        self.example_combo = ttk.Combobox(
            btn, textvariable=self.example_lang,
            values=["Python", "C++", "JavaScript", "Алгоритмический язык", "Java", "Kotlin", "C", "C#", "HTML", "Pascal", "SQL", "Go"],
            state="readonly", width=18
        )
        self.example_combo.pack(side=tk.LEFT, padx=(0, 8))

        for text, cmd in [
            ("👤 Пример: человек",  self._insert_human),
            ("🤖 Пример: ИИ",      self._insert_ai),
            ("📂 Загрузить файл",   self._load_file),
            ("🗑  Очистить",        self._clear),
        ]:
            ttk.Button(btn, text=text, command=cmd).pack(side=tk.LEFT, padx=(0, 4))

        self.editor_frame = tk.Frame(self.tab_input, bg=self.C["surface0"])
        self.editor_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 0))

        self.code_text = tk.Text(
            self.editor_frame, wrap=tk.NONE, font=("Consolas", 10),
            bg=self.C["surface0"], fg=self.C["text"],
            insertbackground=self.C["pink"], selectbackground=self.C["surface2"],
            relief=tk.FLAT, padx=6, pady=6, undo=True,
        )
        hbar = ttk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL, command=self.code_text.xview)
        vbar = ttk.Scrollbar(self.editor_frame, orient=tk.VERTICAL,   command=self.code_text.yview)
        self.code_text.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        self.line_nums = LineNumbers(self.editor_frame, self.code_text, self)
        self.line_nums.grid(row=0, column=0, sticky="ns")
        self.code_text.grid(row=0, column=1, sticky="nsew")
        vbar.grid(row=0, column=2, sticky="ns")
        hbar.grid(row=1, column=1, sticky="ew")
        self.editor_frame.rowconfigure(0, weight=1)
        self.editor_frame.columnconfigure(1, weight=1)

        self.highlighter = SyntaxHighlighter(self.code_text, self)

        sb = tk.Frame(self.tab_input, bg=self.C["mantle"])
        sb.pack(fill=tk.X, padx=6, pady=(4, 4))

        self.status_var = tk.StringVar(value="Готов к анализу")
        self.stats_var  = tk.StringVar(value="")

        tk.Label(sb, textvariable=self.status_var, bg=self.C["mantle"], fg=self.C["overlay0"], font=("Segoe UI", 9), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Label(sb, textvariable=self.stats_var, bg=self.C["mantle"], fg=self.C["overlay0"], font=("Consolas", 9)).pack(side=tk.RIGHT, padx=6)

        # Мгновенные биндинги на ввод и вставку из буфера
        self.code_text.bind("<KeyRelease>", self._on_edit, add=True)
        self.code_text.bind("<<Paste>>", lambda _: self.root.after(10, self._on_edit), add=True)
        self.code_text.bind("<ButtonRelease-1>", self._on_edit, add=True)

        self.current_lang = tk.StringVar(value="Python")

        # Оставлена только одна главная кнопка "Анализировать"
        ttk.Button(sb, text="🔍 Анализировать", style="Accent.TButton", command=self._analyze).pack(side=tk.RIGHT, padx=(4, 0))

    def _on_edit(self, _=None):
        code = self.code_text.get("1.0", tk.END)
        lines = code.count("\n")
        chars = len(code.strip())
        self.stats_var.set(f"Строк: {lines}   Символов: {chars}")
        self.line_nums.redraw()

        # Автоопределение синтаксического контекста
        detected_lang = self.language_detector.detect(code)
        if detected_lang != self.current_lang.get():
            self.current_lang.set(detected_lang)
            self._update_language_badge()
            self.highlighter.highlight()
            self.status_var.set(f"Автоопределение языка: {detected_lang}")

    def _create_results_tab(self):
        paned = ttk.PanedWindow(self.tab_results, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Дерево метрик
        lf = ttk.Frame(paned)
        paned.add(lf, weight=5)

        ttk.Label(lf, text="Метрики качества", style="Header.TLabel").pack(anchor=tk.W, pady=(4, 2))

        # Перенастройка колонок Treeview для поддержки древовидной раскрывающейся структуры
        self.tree = ttk.Treeview(lf, columns=("m", "v"), show="tree headings", height=22)
        self.tree.heading("#0", text="Категория")
        self.tree.heading("m", text="Метрика")
        self.tree.heading("v", text="Значение")
        self.tree.column("#0", width=140, minwidth=100, stretch=True)
        self.tree.column("m", width=180, minwidth=140, stretch=True)
        self.tree.column("v", width=90, minwidth=70, anchor="e", stretch=False)

        ts = ttk.Scrollbar(lf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ts.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ts.pack(side=tk.RIGHT, fill=tk.Y)

        # Детали анализа
        mf = ttk.Frame(paned)
        paned.add(mf, weight=5)

        ttk.Label(mf, text="Отчёт и замечания", style="Header.TLabel").pack(anchor=tk.W, pady=(4, 2))

        self.details = tk.Text(
            mf, wrap=tk.WORD, font=("Consolas", 9),
            bg=self.C["surface0"], fg=self.C["text"],
            relief=tk.FLAT, padx=8, pady=8, state=tk.DISABLED,
        )
        ds = ttk.Scrollbar(mf, command=self.details.yview)
        self.details.configure(yscrollcommand=ds.set)
        self.details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ds.pack(side=tk.RIGHT, fill=tk.Y)

        # Визуализация (Диаграммы)
        rf = ttk.Frame(paned)
        paned.add(rf, weight=3)

        ttk.Label(rf, text="Интегральный рейтинг", style="Header.TLabel").pack(pady=(4, 0))
        self.gauge = ScoreGauge(rf, app=self, size=160)
        self.gauge.pack(pady=(4, 8))

        ttk.Label(rf, text="Анализ фингерпринта ИИ", style="Header.TLabel").pack(pady=(4, 0))
        self.probability_indicator = ProbabilityIndicator(rf, app=self, size=180)
        self.probability_indicator.pack(pady=(4, 12))

        ttk.Label(rf, text="Профиль качества", style="Header.TLabel").pack()
        self.spider = SpiderChart(rf, app=self, size=220)
        self.spider.pack(pady=(4, 8))

        ttk.Button(rf, text="💾 Сохранить отчёт", command=self._export).pack(pady=4, fill=tk.X, padx=10)
        ttk.Button(rf, text="📋 Копировать результаты", command=self._copy_results).pack(pady=4, fill=tk.X, padx=10)

    def _create_compare_tab(self):
        ttk.Label(self.tab_compare, text="Сравнение стилей: Человек vs Генеративный ИИ", style="Header.TLabel").pack(anchor=tk.W, pady=(10, 4), padx=6)
        ttk.Label(self.tab_compare, text="Различия подходов к проектированию и написанию архитектуры систем на выбранном языке.", style="Sub.TLabel", wraplength=1000).pack(anchor=tk.W, padx=6, pady=(0, 6))

        bf = ttk.Frame(self.tab_compare)
        bf.pack(anchor=tk.W, padx=6, pady=(0, 6))
        ttk.Button(bf, text="📊 Сравнить паттерны", style="Accent.TButton", command=self._show_comparison).pack(side=tk.LEFT, padx=(0, 6))

        pw = ttk.PanedWindow(self.tab_compare, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True, padx=6)

        def side_panel(parent, label, fg):
            f = ttk.Frame(parent)
            tk.Label(f, text=label, bg=self.C["base"], fg=fg, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
            t = tk.Text(f, wrap=tk.WORD, font=("Consolas", 9), bg=self.C["surface0"], fg=fg, relief=tk.FLAT, padx=8, pady=8)
            t.pack(fill=tk.BOTH, expand=True)
            return f, t

        lf, self.human_text = side_panel(pw, "👤 Код человека", self.C["green"])
        rf, self.ai_text    = side_panel(pw, "🤖 Код ИИ",       self.C["peach"])
        pw.add(lf, weight=1)
        pw.add(rf, weight=1)

        self.notes_text = tk.Text(self.tab_compare, wrap=tk.WORD, font=("Segoe UI", 10), bg=self.C["mantle"], fg=self.C["yellow"], relief=tk.FLAT, padx=10, pady=8, height=7)
        self.notes_text.pack(fill=tk.X, padx=6, pady=(6, 6))

    def _create_about_tab(self):
        about = (
            "ПРОЕКТ: «Исследование влияния ИИ на современное программирование»\n\n"
            "ЦЕЛЬ:\n"
            "Объективное сравнение качественных характеристик исходного кода, написанного опытным разработчиком, "
            "и кода, сгенерированного большими языковыми моделями (LLM). Программа доказывает, что ИИ является "
            "мощным ассистентом, но не заменяет человека в проектировании сложных и расширяемых систем.\n\n"
            "ПОДДЕРЖИВАЕМЫЕ ЯЗЫКИ:\n"
            "  • Python, C++, JavaScript, Алгоритмический язык,\n"
            "  • Java, Kotlin, C, C#,\n"
            "  • HTML, Pascal, SQL, Go\n\n"
            "МЕТРИКИ И АНАЛИЗ:\n"
            "  • Сложность Холстеда (Halstead): Объем программы (V), Сложность понимания (D), Усилия (E)\n"
            "  • Цикломатическая сложность (метрика Маккейба)\n"
            "  • Анализ глубины вложенности и структуры выражений\n"
            "  • Проверка качества именования переменных и констант\n"
            "  • Полноценный анализ комментариев и документации кода\n\n"
            "ТЕХНОЛОГИИ: Python 3, Tkinter, AST API (без сторонних зависимостей)\n"
        )
        tw = tk.Text(self.tab_about, wrap=tk.WORD, font=("Segoe UI", 10), bg=self.C["surface0"], fg=self.C["text"], relief=tk.FLAT, padx=15, pady=15)
        tw.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tw.insert(tk.END, about)
        tw.config(state=tk.DISABLED)

    # ──────────────────────────────────────────────────────────────
    #  Управление темами
    # ──────────────────────────────────────────────────────────────
    def _toggle_theme(self):
        if self.theme_mode == "dark":
            self.C = LATTE
            self.theme_mode = "light"
            self.theme_btn.config(text="☀️ Светлая")
        else:
            self.C = MOCHA
            self.theme_mode = "dark"
            self.theme_btn.config(text="🌙 Тёмная")
        self._apply_theme()

    def _apply_theme(self):
        self._create_styles()
        bg     = self.C["base"]
        s0     = self.C["surface0"]
        text   = self.C["text"]
        pink   = self.C["pink"]
        s2     = self.C["surface2"]
        mantle = self.C["mantle"]

        self.root.configure(bg=bg)

        # Конфигурируем все стандартные виджеты
        self._configure_widget_colors(self.root, bg, mantle, s0, text)

        # Принудительная подкраска контейнера редактора
        self.editor_frame.configure(bg=s0)

        # Explicit overrides для виджетов вывода текста
        for text_widget in [self.code_text, self.details, self.human_text, self.ai_text, self.notes_text]:
            if text_widget == self.notes_text:
                text_widget.configure(bg=mantle, fg=self.C["yellow"])
            elif text_widget == self.human_text:
                text_widget.configure(bg=s0, fg=self.C["green"])
            elif text_widget == self.ai_text:
                text_widget.configure(bg=s0, fg=self.C["peach"])
            else:
                text_widget.configure(bg=s0, fg=text)
            text_widget.configure(insertbackground=pink, selectbackground=s2)

        self.line_nums.configure(bg=mantle)
        self.line_nums.redraw()

        self.highlighter._setup_colors()
        self.highlighter.highlight()

        self._update_text_tags()
        self._update_treeview_tags()
        self._update_language_badge()

        if hasattr(self, 'gauge'):
            self.gauge.set_score(self._last_score)
        if hasattr(self, 'probability_indicator'):
            self.probability_indicator.set_percentage(self._last_metrics.get("ai_probability", 0) if self._last_metrics else 0)
        if hasattr(self, 'spider') and self._last_metrics:
            self.spider.set_scores(self._spider_scores(self._last_metrics))
        elif hasattr(self, 'spider'):
            self.spider.set_scores([0.0]*6)

    def _update_text_tags(self):
        self.details.tag_configure("good",    foreground=self.C["green"])
        self.details.tag_configure("warn",    foreground=self.C["yellow"])
        self.details.tag_configure("bad",     foreground=self.C["red"])
        self.details.tag_configure("header",  foreground=self.C["pink"], font=("Consolas", 9, "bold"))
        self.details.tag_configure("section", foreground=self.C["blue"])
        self.details.tag_configure("muted",   foreground=self.C["overlay0"])

    def _update_treeview_tags(self):
        self.tree.tag_configure("good",    foreground=self.C["green"])
        self.tree.tag_configure("warn",    foreground=self.C["yellow"])
        self.tree.tag_configure("bad",     foreground=self.C["red"])
        self.tree.tag_configure("neutral", foreground=self.C["text"])
        self.tree.tag_configure("section", foreground=self.C["blue"], font=("Segoe UI", 8, "bold"))

    def _update_language_badge(self):
        lang = self.current_lang.get()
        self.badge_frame.configure(bg=self.C["surface1"])
        self.badge_label.configure(bg=self.C["surface1"], fg=self.C["pink"])
        self.badge_label.config(text=f"Язык: {lang}")

    # ──────────────────────────────────────────────────────────────
    #  Конфигурация клавиатурных сокращений
    # ──────────────────────────────────────────────────────────────
    def _setup_shortcuts(self):
        self.code_text.bind("<Control-Return>", lambda _: self._analyze_shortcut())
        self.code_text.bind("<Control-o>",      lambda _: self._load_shortcut())
        self.code_text.bind("<Control-s>",      lambda _: self._export_shortcut())
        self.code_text.bind("<Control-l>",      lambda _: self._clear_shortcut())
        self.code_text.bind("<Tab>",            self._tab_shortcut)
        self.code_text.bind("<Shift-Tab>",      self._shift_tab_shortcut)

    def _analyze_shortcut(self):
        self._analyze()
        return "break"

    def _load_shortcut(self):
        self._load_file()
        return "break"

    def _export_shortcut(self):
        self._export()
        return "break"

    def _clear_shortcut(self):
        self._clear()
        return "break"

    def _tab_shortcut(self, event):
        self.code_text.insert(tk.INSERT, "    ")
        return "break"

    def _shift_tab_shortcut(self, event):
        ls = self.code_text.index("insert linestart")
        le = self.code_text.index("insert lineend")
        text = self.code_text.get(ls, le)
        if text.startswith("    "):
            self.code_text.delete(ls, f"{ls}+4c")
        elif text.startswith("\t"):
            self.code_text.delete(ls, f"{ls}+1c")
        return "break"

    # ──────────────────────────────────────────────────────────────
    #  Файловые операции
    # ──────────────────────────────────────────────────────────────
    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Выберите файл исходного кода",
            filetypes=[("Исходные файлы", "*.py;*.cpp;*.h;*.js;*.java;*.kt;*.c;*.cs;*.html;*.pas;*.sql;*.go;*.txt"), ("Все файлы", "*.*")]
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    code = f.read()
                self.code_text.delete("1.0", tk.END)
                self.code_text.insert(tk.END, code)
                self._on_edit()
                self.status_var.set(f"Загружен файл: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")

    def _clear(self):
        self.code_text.delete("1.0", tk.END)
        self.status_var.set("Редактор очищен")
        self.stats_var.set("")
        self.line_nums.redraw()

    def _insert_human(self):
        lang = self.example_lang.get()
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, EXAMPLES[lang]["human"])
        self.current_lang.set(lang)
        self._update_language_badge()
        self.highlighter.highlight()
        self._on_edit()
        self.status_var.set(f"Загружен пример человека ({lang})")

    def _insert_ai(self):
        lang = self.example_lang.get()
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, EXAMPLES[lang]["ai"])
        self.current_lang.set(lang)
        self._update_language_badge()
        self.highlighter.highlight()
        self._on_edit()
        self.status_var.set(f"Загружен шаблонный код ИИ ({lang})")

    # ──────────────────────────────────────────────────────────────
    #  Анализ
    # ──────────────────────────────────────────────────────────────
    def _analyze(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Внимание", "Поле ввода пусто.")
            return

        metrics, warning = self._calc_metrics(code)
        lang = self.current_lang.get()

        # Оценка ИИ Фингерпринта
        ai_prob, ai_reasons = self._calc_ai_probability(code, metrics, lang)
        metrics["ai_probability"] = ai_prob
        metrics["ai_reasons"] = ai_reasons

        if warning:
            self.status_var.set("Анализ завершен с замечаниями")
        else:
            self.status_var.set("Анализ успешно завершен")

        score = self._quality_score(metrics)
        self._last_metrics = metrics
        self._last_score   = score

        self._fill_tree(metrics)
        self._fill_details(metrics, score, warning, lang)
        self.gauge.set_score(score)
        self.probability_indicator.set_percentage(ai_prob)
        self.spider.set_scores(self._spider_scores(metrics))

        self.nb.select(self.tab_results)

    def _quick_compare(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Внимание", "Загрузите исходный код.")
            return
        m, _ = self._calc_metrics(code)
        lang = self.current_lang.get()
        ai_prob, _ = self._calc_ai_probability(code, m, lang)

        if ai_prob > 55:
            style = "ai"
        elif ai_prob < 25:
            style = "human"
        else:
            style = "mixed"

        msgs = {
            "human": ("ЧЕЛОВЕК 👤", f"Код демонстрирует чистые архитектурные приёмы разработчика-человека. (ИИ: {ai_prob}%)"),
            "ai":    ("ИИ 🤖", f"В кодовой базе выявлен шаблонный стиль генеративного ИИ. (ИИ: {ai_prob}%)"),
            "mixed": ("СМЕШАННЫЙ 🔄", f"Обнаружено совместное редактирование или использование AI-ассистентов. (ИИ: {ai_prob}%)"),
        }
        title, body = msgs[style]
        messagebox.showinfo(f"Стиль кода: {title}", body)

    def _show_comparison(self):
        lang = self.current_lang.get()
        data = EXAMPLES.get(lang)
        if not data or "human_compare" not in data:
            messagebox.showinfo("Нет данных", f"Сравнение для {lang} пока не добавлено.")
            return

        self.human_text.delete("1.0", tk.END)
        self.human_text.insert(tk.END, data["human_compare"])

        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, data["ai_compare"])

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, data.get("compare_notes", ""))

    # ──────────────────────────────────────────────────────────────
    #  Алгоритмы расчета метрик
    # ──────────────────────────────────────────────────────────────
    def _calc_metrics(self, code: str) -> tuple[dict, str | None]:
        lang = self.current_lang.get()
        if lang == "Python":
            try:
                tree = ast.parse(code)
                v = MetricsVisitor()
                v.visit(tree)

                lines   = code.split("\n")
                total   = len(lines)
                blank   = sum(1 for l in lines if not l.strip())
                comment = sum(1 for l in lines if l.strip().startswith("#"))
                code_l  = total - blank - comment
                cr      = comment / total if total else 0.0
                long_l  = sum(1 for l in lines if len(l) > 79)
                hal     = self._calc_halstead(code, "Python")

                return dict(
                    total_lines     = total,
                    code_lines      = code_l,
                    comment_lines   = comment,
                    blank_lines     = blank,
                    long_lines      = long_l,
                    comment_ratio   = round(cr, 3),
                    docstrings      = v.docstrings,
                    functions       = len(v.functions),
                    classes         = len(v.classes),
                    imports         = v.imports,
                    variables       = len(v.all_names),
                    descriptive     = v.descriptive,
                    short_names     = v.short_names,
                    name_quality    = v.name_quality(),
                    magic_numbers   = v.magic_numbers,
                    for_loops       = v.for_loops + v.while_loops,
                    while_loops     = v.while_loops,
                    if_stmts        = v.if_stmts,
                    try_blocks      = v.try_blocks,
                    type_hints      = v.type_hints,
                    lambda_count    = v.lambda_count,
                    comprehensions  = v.comprehensions,
                    max_nesting     = v.max_depth + 1,
                    cyclomatic      = v.cyclomatic,
                    avg_func_length = v.avg_func_length(),
                    hal_volume      = hal["volume"],
                    hal_difficulty  = hal["difficulty"],
                    hal_effort      = hal["effort"]
                ), None
            except SyntaxError as e:
                warning = f"Ошибки синтаксиса Python ({e}). Переключено в режим лексического сканирования."
                return self._calc_metrics_lexical(code, "Python"), warning
        else:
            return self._calc_metrics_lexical(code, lang), None

    def _calc_metrics_lexical(self, code: str, lang: str) -> dict:
        lines = code.split("\n")
        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())

        comment = 0
        docstrings = 0
        if lang in ("Python", "Алгоритмический язык"):
            comment = sum(1 for l in lines if l.strip().startswith("#") or (lang == "Алгоритмический язык" and l.strip().startswith("|")))
            code_clean = re.sub(r'#.*|\|.*', '', code)
            if lang == "Python":
                docstrings = len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code))
        elif lang == "HTML":
            comment = sum(1 for l in lines if l.strip().startswith("<!--") or l.strip().endswith("-->"))
            code_clean = re.sub(r'<!--[\s\S]*?-->', '', code)
        elif lang == "SQL":
            comment = sum(1 for l in lines if l.strip().startswith("--") or l.strip().startswith("/*"))
            code_clean = re.sub(r'--.*|/\*[\s\S]*?\*/', '', code)
        elif lang == "Pascal":
            comment = sum(1 for l in lines if l.strip().startswith("//") or l.strip().startswith("{") or l.strip().startswith("(*"))
            code_clean = re.sub(r'//.*|\{[\s\S]*?\}|\(\*[\s\S]*?\*\)', '', code)
        else:
            comment = sum(1 for l in lines if l.strip().startswith("//") or l.strip().startswith("/*"))
            code_clean = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code)
            docstrings = len(re.findall(r'/\*\*[\s\S]*?\*/', code))

        code_l = total - blank - comment
        cr = comment / total if total else 0.0
        long_l = sum(1 for l in lines if len(l) > 79)

        # Регулярные выражения определений функций
        func_patterns = {
            "Python": r'\bdef\s+([a-zA-Z_]\w*)',
            "C++": r'\b[a-zA-Z_]\w*(?:\s+[*&]?\s*|\s+)([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{',
            "JavaScript": r'\bfunction\s+([a-zA-Z_]\w*)|\bconst\s+([a-zA-Z_]\w*)\s*=\s*\([^)]*\)\s*=>',
            "Алгоритмический язык": r'\bалг\s+([а-яА-ЯёЁa-zA-Z_]\w*)|\balg\s+([a-zA-Z_]\w*)',
            "Java": r'\b(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{',
            "Kotlin": r'\bfun\s+(\w+)',
            "C": r'\b[a-zA-Z_]\w*(?:\s+[*&]?\s*|\s+)([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{',
            "C#": r'\b(?:public|private|protected|static|internal|\s) +[\w\<\>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{',
            "HTML": r'<([a-zA-Z1-6]+)\b',
            "Pascal": r'\b(?:function|procedure)\s+(\w+)',
            "SQL": r'\b(?:CREATE\s+(?:PROCEDURE|FUNCTION)|WITH)\s+([a-zA-Z_]\w*)',
            "Go": r'\bfunc\s+(?:\([^)]*\)\s*)?([a-zA-Z_]\w*)\s*\('
        }
        funcs = re.findall(func_patterns.get(lang, r''), code_clean)
        func_names = []
        for f in funcs:
            if isinstance(f, tuple):
                func_names.append([x for x in f if x][0])
            else:
                func_names.append(f)
        functions_count = len(func_names)

        # Классы
        class_patterns = {
            "Python": r'\bclass\s+([a-zA-Z_]\w*)',
            "C++": r'\b(?:class|struct)\s+([a-zA-Z_]\w*)',
            "JavaScript": r'\bclass\s+([a-zA-Z_]\w*)',
            "Алгоритмический язык": r'\b(?!)\b',
            "Java": r'\b(?:class|interface)\s+(\w+)',
            "Kotlin": r'\b(?:class|interface|object)\s+(\w+)',
            "C": r'\bstruct\s+(\w+)',
            "C#": r'\b(?:class|struct|interface)\s+(\w+)',
            "HTML": r'\b(?:class|id)\s*=\s*["\']([^"\']+)["\']',
            "Pascal": r'\b(?:object|record)\b',
            "SQL": r'\bCREATE\s+TABLE\s+([a-zA-Z_]\w*)',
            "Go": r'\btype\s+(\w+)\s+struct'
        }
        classes_count = len(re.findall(class_patterns.get(lang, r''), code_clean))

        # Импорты
        import_patterns = {
            "Python": r'\b(?:import|from)\b',
            "C++": r'#\s*include\b',
            "JavaScript": r'\b(?:import|require)\b',
            "Алгоритмический язык": r'\bисп\b',
            "Java": r'\bimport\b',
            "Kotlin": r'\bimport\b',
            "C": r'#\s*include\b',
            "C#": r'\busing\b',
            "HTML": r'<(?:link|script|img)\b',
            "Pascal": r'\buses\b',
            "SQL": r'\b(?!)\b',
            "Go": r'\bimport\b'
        }
        imports_count = len(re.findall(import_patterns.get(lang, r''), code_clean))

        # Качество имен переменных
        var_patterns = {
            "Python": r'\b([a-zA-Z_]\w*)\s*=',
            "C++": r'\b(?:int|double|float|char|bool|auto|string|vector)\s+([a-zA-Z_]\w*)',
            "JavaScript": r'\b(?:let|const|var)\s+([a-zA-Z_]\w*)',
            "Алгоритмический язык": r'\b(?:цел|вещ|сим|лит|лог|integer|real|char|string|boolean)\s+([а-яА-ЯёЁa-zA-Z_]\w*)',
            "Java": r'\b(?:int|double|float|boolean|char|String|var)\s+([a-zA-Z_]\w*)',
            "Kotlin": r'\b(?:val|var)\s+([a-zA-Z_]\w*)',
            "C": r'\b(?:int|double|float|char|auto)\s+([a-zA-Z_]\w*)',
            "C#": r'\b(?:int|double|float|bool|string|char|var)\s+([a-zA-Z_]\w*)',
            "HTML": r'\b([a-zA-Z_]\w*)\s*=\s*["\']',
            "Pascal": r'\b([a-zA-Z_]\w*)\s*:\s*(?:integer|real|char|string|boolean)',
            "SQL": r'\bDECLARE\s+@([a-zA-Z_]\w*)',
            "Go": r'\b(?:var\s+)?([a-zA-Z_]\w*)\s*(?::=|=)'
        }
        vars_found = re.findall(var_patterns.get(lang, r''), code_clean)

        all_names = set(func_names + vars_found)
        TRIVIAL = {"_", "i", "j", "k", "x", "y", "z", "n", "m", "и", "ж", "к"}
        short_names_count = sum(1 for name in all_names if len(name) <= 1 and name not in TRIVIAL)
        descriptive_count = sum(1 for name in all_names if len(name) >= 4)
        name_quality = descriptive_count / len(all_names) if all_names else 1.0

        # Магические числа
        magic_numbers = 0
        SAFE_NUMS = {0, 1, 2, 10, 100, -1, 255, 360, 1000}
        nums = re.findall(r'\b\d+\.?\d*\b', code_clean)
        for num_str in nums:
            try:
                val = float(num_str) if '.' in num_str else int(num_str)
                if val not in SAFE_NUMS and abs(val) >= 3:
                    magic_numbers += 1
            except ValueError:
                pass

        # Циклы, Ветвления, Ошибки
        loop_patterns = {
            "Python": r'\b(?:for|while)\b',
            "C++": r'\b(?:for|while)\s*\(',
            "JavaScript": r'\b(?:for|while)\s*\(',
            "Алгоритмический язык": r'\b(?:нц|пока|для|while|for)\b',
            "Java": r'\b(?:for|while)\s*\(',
            "Kotlin": r'\b(?:for|while)\s*\(',
            "C": r'\b(?:for|while)\s*\(',
            "C#": r'\b(?:for|foreach|while)\s*\(',
            "HTML": r'\b(?!)\b',
            "Pascal": r'\b(?:for|while|repeat)\b',
            "SQL": r'\b(?:CURSOR|WHILE)\b',
            "Go": r'\bfor\b'
        }
        loops_count = len(re.findall(loop_patterns.get(lang, r''), code_clean))

        cond_patterns = {
            "Python": r'\b(?:if|elif)\b',
            "C++": r'\b(?:if|switch)\b',
            "JavaScript": r'\b(?:if|switch)\b',
            "Алгоритмический язык": r'\b(?:если|выбор|if|case)\b',
            "Java": r'\b(?:if|switch)\b',
            "Kotlin": r'\b(?:if|when)\b',
            "C": r'\b(?:if|switch)\b',
            "C#": r'\b(?:if|switch)\b',
            "HTML": r'\b(?!)\b',
            "Pascal": r'\b(?:if|case)\b',
            "SQL": r'\b(?:WHERE|HAVING|CASE)\b',
            "Go": r'\b(?:if|switch|select)\b'
        }
        conditionals_count = len(re.findall(cond_patterns.get(lang, r''), code_clean))

        try_patterns = {
            "Python": r'\btry\b',
            "C++": r'\btry\b',
            "JavaScript": r'\btry\b',
            "Алгоритмический язык": r'\b(?!)\b',
            "Java": r'\btry\b',
            "Kotlin": r'\btry\b',
            "C": r'\b(?!)\b',
            "C#": r'\btry\b',
            "HTML": r'\b(?!)\b',
            "Pascal": r'\b(?:try|except)\b',
            "SQL": r'\b(?:TRY|CATCH)\b',
            "Go": r'\b(?:panic|recover)\b'
        }
        try_blocks = len(re.findall(try_patterns.get(lang, r''), code_clean))

        type_patterns = {
            "Python": r':\s*[a-zA-Z_]\w*|\b->\b',
            "C++": r'\b(?:int|float|double|char|bool|string|void|auto)\b',
            "JavaScript": r'\b(?:let|const|var)\b',
            "Алгоритмический язык": r'\b(?:цел|вещ|сим|лит|лог|integer|real|char|string|boolean)\b',
            "Java": r'\b(?:int|double|float|boolean|char|String|void)\b',
            "Kotlin": r'\b(?:Int|Double|Float|Boolean|Char|String|Any|Unit)\b',
            "C": r'\b(?:int|float|double|char|void)\b',
            "C#": r'\b(?:int|float|double|bool|string|char|void)\b',
            "HTML": r'\b(?:type|class|id|style)\b',
            "Pascal": r'\b(?:integer|real|char|string|boolean)\b',
            "SQL": r'\b(?:INT|VARCHAR|CHAR|NUMERIC|DECIMAL|DATE|TIMESTAMP|BOOLEAN)\b',
            "Go": r'\b(?:int|float64|string|bool|struct|interface)\b'
        }
        type_hints_count = len(re.findall(type_patterns.get(lang, r''), code_clean))

        max_nesting = self._estimate_max_nesting(code)
        cyclomatic_count = 1 + loops_count + conditionals_count + try_blocks
        avg_func_length = round(code_l / functions_count, 1) if functions_count else 0.0

        hal = self._calc_halstead(code, lang)

        return dict(
            total_lines     = total,
            code_lines      = code_l,
            comment_lines   = comment,
            blank_lines     = blank,
            long_lines      = long_l,
            comment_ratio   = round(cr, 3),
            docstrings      = docstrings,
            functions       = functions_count,
            classes         = classes_count,
            imports         = imports_count,
            variables       = len(all_names),
            descriptive     = descriptive_count,
            short_names     = short_names_count,
            name_quality    = name_quality,
            magic_numbers   = magic_numbers,
            for_loops       = loops_count,
            while_loops     = 0,
            if_stmts        = conditionals_count,
            try_blocks      = try_blocks,
            type_hints      = type_hints_count,
            lambda_count    = 0,
            comprehensions  = 0,
            max_nesting     = max_nesting,
            cyclomatic      = cyclomatic_count,
            avg_func_length = avg_func_length,
            hal_volume      = hal["volume"],
            hal_difficulty  = hal["difficulty"],
            hal_effort      = hal["effort"]
        )

    def _estimate_max_nesting(self, code: str) -> int:
        lines = [l for l in code.split('\n') if l.strip()]
        if not lines:
            return 0
        indents = []
        for line in lines:
            ls = len(line) - len(line.lstrip(' '))
            lt = len(line) - len(line.lstrip('\t'))
            indents.append(ls + lt * 4)
        unique = sorted(list(set(i for i in indents if i > 0)))
        if not unique:
            return 1
        step = unique[0]
        if step < 2:
            step = 4
        return (max(indents) // step) + 1

    def _calc_halstead(self, code: str, lang: str) -> dict:
        if lang in ("Python", "Алгоритмический язык"):
            clean = re.sub(r'#.*|\|.*', '', code)
            clean = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', '', clean)
            clean = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', '', clean)
        elif lang == "HTML":
            clean = re.sub(r'<!--[\s\S]*?-->', '', code)
        else:
            clean = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code)
            clean = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|`[^`\\]*(?:\\.[^`\\]*)*`', '', clean)

        op_patterns = {
            "Python": r'\+|-|\*|/|//|%|\*\*|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|\band\b|\bor\b|\bnot\b|\bin\b|\bis\b',
            "C++": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|&&|\|\||!|\+\+|--|<<|>>',
            "JavaScript": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|===|==|!==|!=|<|>|<=|>=|&&|\|\||!|\+\+|--|\?|:',
            "Алгоритмический язык": r'\+|-|\*|/|:=|=|<|>|<=|>=|\bи\b|\били\b|\бне\b',
            "Java": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|&&|\|\||!|\+\+|--',
            "Kotlin": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|&&|\|\||!',
            "C": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|&&|\|\||!|\+\+|--',
            "C#": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|==|!=|<|>|<=|>=|&&|\|\||!|\+\+|--',
            "HTML": r'</?|[=>]',
            "Pascal": r'\+|-|\*|/|:=|=|<|>|<=|>=|<>|\band\b|\bor\b|\bnot\b',
            "SQL": r'\+|-|\*|/|=|<|>|<=|>=|<>|\bAND\b|\bOR\b|\bNOT\b',
            "Go": r'\+|-|\*|/|%|=|\+=|-=|\*=|/=|:=|==|!=|<|>|<=|>=|&&|\|\||!'
        }

        op_rx = op_patterns.get(lang, r'\+|-|\*|/|=')
        operators = re.findall(op_rx, clean)

        no_ops = re.sub(op_rx, ' ', clean)
        operands = re.findall(r'\b[a-zA-Z_а-яА-ЯёЁ][\wа-яА-ЯёЁ]*\b|\b\d+\.?\d*\b', no_ops)

        kws = SyntaxHighlighter.LANG_KEYWORDS.get(lang, set())
        operands = [op for op in operands if op not in kws]

        n1, n2 = len(set(operators)), len(set(operands))
        N1, N2 = len(operators), len(operands)

        vocab = n1 + n2
        length = N1 + N2

        vol = length * math.log2(vocab) if vocab > 0 else 0.0
        diff = (n1 / 2) * (N2 / n2) if n2 > 0 else 0.0
        eff = diff * vol

        return {
            "volume": round(vol, 1),
            "difficulty": round(diff, 1),
            "effort": round(eff, 1)
        }

    # ══════════════════════════════════════════════════════════════════
    #  АНАЛИЗАТОР ЦИФРОВОГО ОТПЕЧАТКА (Human vs AI Fingerprinting)
    # ══════════════════════════════════════════════════════════════════
    def _calc_ai_probability(self, code: str, m: dict, lang: str) -> tuple[int, list[str]]:
        ai_score = 0
        reasons = []

        # 1. Анализ плотности шаблонных переменных-заполнителей ИИ
        strict_ai_patterns = {
            "function_1", "function_2", "function_3",
            "param_1", "param_2", "param_3", "param_4",
            "temp_var", "temp_1", "temp_2",
            "result_1", "result_2", "result_3",
            "func_1", "func_2", "func_3",
            "p1", "p2", "p3", "t1", "t2", "r_1", "r_2", "ц_1",
            "item_1", "item_2", "data_1", "data_2",
        }

        words = re.findall(r'\b\w+\b', code)
        found_strict = [w for w in words if w in strict_ai_patterns]

        if len(found_strict) >= 3:
            ai_score += 40
            reasons.append(f"Высокая частотность шаблонных переменных ИИ ({len(found_strict)}): {', '.join(set(found_strict))}")
        elif len(found_strict) >= 1:
            ai_score += 20
            reasons.append(f"Обнаружены характерные маркеры ИИ: {', '.join(set(found_strict))}")

        # 2. Избыточная вложенность + шаблонная структура
        if m.get("max_nesting", 0) >= 5 and m.get("cyclomatic", 0) >= 8:
            ai_score += 10
            reasons.append("Высокая вложенность в сочетании с избыточными ветвлениями")

        # 3. Избыточные условные конструкции (redundant else)
        redundant_else = len(re.findall(r'return\s+[^;}\n]+\s*[\n;}]+\s*else\b', code))
        if redundant_else > 1:
            ai_score += 10
            reasons.append("Многократный избыточный 'else' после прямого прерывания 'return'")

        # 4. Шаблонная инициализация накопителя перед циклом
        if len(re.findall(r'\w+\s*=\s*0\.?0?\s*[\n;]\s*for\b', code)) > 0:
            ai_score += 10
            reasons.append("Шаблонная инициализация накопителя перед циклом")

        # 5. Цепочки if/elif вместо словарей или switch
        if m.get("if_stmts", 0) >= 4 and m.get("functions", 0) <= 1:
            ai_score += 10
            reasons.append("Длинная цепочка if/elif без выделения в отдельные функции")

        # 6. Маркеры человека (снижают оценку ИИ)
        comment_ratio = m.get("comment_ratio", 0.0)
        docstrings    = m.get("docstrings", 0)
        nq            = m.get("name_quality", 0)
        type_hints    = m.get("type_hints", 0)

        human_score = 0
        if docstrings >= 2:
            human_score += 30
            reasons.insert(0, "Наличие документации (docstrings)")
        elif docstrings >= 1:
            human_score += 15

        if comment_ratio > 0.08:
            human_score += 15
        if nq >= 0.5:
            human_score += 15
        if type_hints >= 2:
            human_score += 10
        if m.get("try_blocks", 0) > 0:
            human_score += 5
        if m.get("functions", 0) >= 2:
            human_score += 10

        final_probability = max(0, min(100, ai_score - human_score))
        return final_probability, reasons

    def _quality_score(self, m: dict) -> int:
        s = 0
        cr = m["comment_ratio"]
        if cr > 0.12:   s += 15
        elif cr > 0.04: s += 8

        if m["docstrings"] >= 2:   s += 10
        elif m["docstrings"] == 1: s += 5

        if m["type_hints"] >= 3:   s += 5
        elif m["type_hints"] >= 1: s += 2

        nq = m["name_quality"]
        if nq >= 0.6:    s += 15
        elif nq >= 0.35: s += 8

        if m["short_names"] == 0:   s += 10
        elif m["short_names"] <= 2: s += 5

        if m["functions"] > 0:  s += 8
        if m["classes"] > 0:    s += 7

        afl = m["avg_func_length"]
        if 0 < afl <= 15:   s += 5
        elif 0 < afl <= 30: s += 2

        if m["max_nesting"] <= 3:   s += 8
        elif m["max_nesting"] <= 5: s += 4

        cyc = m["cyclomatic"]
        if cyc <= 5:    s += 7
        elif cyc <= 10: s += 4

        if m["try_blocks"] > 0:     s += 7
        if m["magic_numbers"] == 0: s += 3
        elif m["magic_numbers"] <= 2: s += 1

        hd = m.get("hal_difficulty", 999)
        if hd < 8: s += 5
        elif hd < 15: s += 2

        return min(s, 100)

    def _detect_style(self, m: dict) -> str:
        ai, hu = 0, 0
        nq = m["name_quality"]
        if nq < 0.25:   ai += 3
        elif nq > 0.5:  hu += 3
        else:           hu += 1

        if m["short_names"] > 4: ai += 2
        else:                     hu += 1

        if m["comment_ratio"] < 0.02 and m["docstrings"] == 0:
            ai += 2
        elif m["comment_ratio"] >= 0.04 or m["docstrings"] > 0:
            hu += 2

        if m.get("type_hints", 0) > 0: hu += 1
        if m["magic_numbers"] > 5:     ai += 2
        else:                           hu += 1

        if m.get("hal_difficulty", 0) > 25: ai += 1
        else: hu += 1

        if m["max_nesting"] > 5: ai += 2
        else:                     hu += 1

        if m["functions"] >= 2:  hu += 1
        if m.get("try_blocks", 0) > 0: hu += 1

        if ai > hu + 2:  return "ai"
        if hu > ai + 2:  return "human"
        return "mixed"

    def _spider_scores(self, m: dict) -> list[float]:
        doc = (min(m["comment_ratio"] / 0.15, 1) * 0.4 +
               min(m["docstrings"] / 3, 1) * 0.4 +
               min(m["type_hints"] / 5, 1) * 0.2)
        nam = m["name_quality"]
        struct = (min(m["functions"] / 5, 1) * 0.4 +
                  min(m["classes"] / 2, 1) * 0.3 +
                  (1 - min(m["avg_func_length"] / 50, 1)) * 0.3)
        rel = (min(m["try_blocks"] / 2, 1) * 0.5 +
               (1 - min(m["magic_numbers"] / 10, 1)) * 0.5)
        lac = (min((m["comprehensions"] + m["lambda_count"] + 1) / 3, 1) * 0.5 +
               max(1 - m["long_lines"] / 10, 0) * 0.5)
        arch = ((1 - min(m["max_nesting"] / 8, 1)) * 0.4 +
                (1 - min(m["cyclomatic"] / 15, 1)) * 0.6)
        return [min(1.0, max(0.0, v)) for v in [doc, nam, struct, rel, lac, arch]]

    # ══════════════════════════════════════════════════════════════════
    #  ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ (Иерархическая структура Treeview)
    # ══════════════════════════════════════════════════════════════════
    def _fill_tree(self, m: dict):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.tag_configure("parent", font=("Segoe UI", 9, "bold"), foreground=self.C["pink"])

        # Группа 1: Основные показатели (Развернуты по умолчанию)
        g1 = self.tree.insert("", tk.END, text="Основное", values=("Основные показатели", ""), open=True, tags=("parent",))
        self.tree.insert(g1, tk.END, values=("  Оценка качества", f"{self._last_score} / 100"))
        style_labels = {"human": "ЧЕЛОВЕК 👤", "ai": "ИИ 🤖", "mixed": "СМЕШАННЫЙ 🔄"}
        self.tree.insert(g1, tk.END, values=("  Определенный стиль", style_labels.get(self._detect_style(m), "Смешанный")))
        self.tree.insert(g1, tk.END, values=("  Вероятность ИИ", f"{m.get('ai_probability', 0)}%"))
        self.tree.insert(g1, tk.END, values=("  Цикломатическая сложность", m["cyclomatic"]))
        self.tree.insert(g1, tk.END, values=("  Максимальная вложенность", m["max_nesting"]))
        self.tree.insert(g1, tk.END, values=("  Плотность комментариев", f'{m["comment_ratio"]:.1%}'))
        self.tree.insert(g1, tk.END, values=("  Качество имен переменных", f'{m["name_quality"]:.0%}'))

        # Группа 2: Детальные метрики структуры (Свернуты по умолчанию)
        g2 = self.tree.insert("", tk.END, text="Детали", values=("Другие метрики (структура)", ""), open=False, tags=("parent",))
        self.tree.insert(g2, tk.END, values=("  Всего строк", m["total_lines"]))
        self.tree.insert(g2, tk.END, values=("  Чистых строк кода", m["code_lines"]))
        self.tree.insert(g2, tk.END, values=("  Пустых строк", m["blank_lines"]))
        self.tree.insert(g2, tk.END, values=("  Строк комментариев", m["comment_lines"]))
        self.tree.insert(g2, tk.END, values=("  Docstring / Спецификации", m["docstrings"]))
        self.tree.insert(g2, tk.END, values=("  Аннотации типов", m["type_hints"]))
        self.tree.insert(g2, tk.END, values=("  Определено функций", m["functions"]))
        self.tree.insert(g2, tk.END, values=("  Определено классов", m["classes"]))
        self.tree.insert(g2, tk.END, values=("  Импортов / Подключений", m["imports"]))
        self.tree.insert(g2, tk.END, values=("  Всего переменных", m["variables"]))
        self.tree.insert(g2, tk.END, values=("  Коротких имён (≤1 симв.)", m["short_names"]))
        self.tree.insert(g2, tk.END, values=("  Магических чисел", m["magic_numbers"]))
        self.tree.insert(g2, tk.END, values=("  Средняя длина функции", f'{m["avg_func_length"]} строк'))
        self.tree.insert(g2, tk.END, values=("  Длинных строк (>79 симв.)", m["long_lines"]))

        # Группа 3: Метрики Холстеда (Свернуты по умолчанию)
        g3 = self.tree.insert("", tk.END, text="Холстед", values=("Сложность Холстеда", ""), open=False, tags=("parent",))
        self.tree.insert(g3, tk.END, values=("  Объём программы (V)", f'{m["hal_volume"]:.1f}'))
        self.tree.insert(g3, tk.END, values=("  Сложность понимания (D)", f'{m["hal_difficulty"]:.1f}'))
        self.tree.insert(g3, tk.END, values=("  Интеллектуальные усилия (E)", f'{m["hal_effort"]:.1f}'))

    def _fill_details(self, m: dict, score: int, warning: str | None, lang: str = "Python"):
        self.details.config(state=tk.NORMAL)
        self.details.delete("1.0", tk.END)

        style = self._detect_style(m)
        ai_prob = m.get("ai_probability", 0)

        lines = [
            "=" * 50,
            "  ОТЧЁТ АНАЛИЗА КОДА",
            "=" * 50,
            "",
            f"Язык: {lang}",
            "",
        ]

        if warning:
            lines.append(f"⚠ {warning}")
            lines.append("")

        style_labels = {
            "human": "ЧЕЛОВЕК 👤",
            "ai":    "ИИ 🤖",
            "mixed": "СМЕШАННЫЙ 🔄",
        }
        lines.append(f"СТИЛЬ: {style_labels.get(style, style)}")
        lines.append(f"Вероятность ИИ: {ai_prob}%")
        lines.append(f"ОЦЕНКА КАЧЕСТВА: {score} / 100")
        lines.append("")

        lines.append("-" * 50)
        lines.append("ПОЗИТИВНЫЕ МОМЕНТЫ:")
        lines.append("-" * 50)

        if m["comment_ratio"] > 0.12:
            lines.append("✓ Хороший уровень комментирования")
        elif m["comment_ratio"] > 0.04:
            lines.append("~ Есть комментарии (можно улучшить)")
        else:
            lines.append("✗ Мало комментариев")

        if lang == "Python":
            if m["docstrings"] > 0:
                lines.append("✓ Есть docstring-документация")
            else:
                lines.append("✗ Нет docstring")

        if lang in ("C++", "C", "C#", "Java", "Kotlin", "Go"):
            if m["try_blocks"] > 0:
                lines.append("✓ Есть обработка ошибок")
            else:
                lines.append("✗ Нет обработки ошибок")
        elif lang == "Python":
            if m["try_blocks"] > 0:
                lines.append("✓ Есть обработка ошибок (try/except)")
            else:
                lines.append("✗ Нет обработки ошибок")

        if lang in ("Python",):
            if m["type_hints"] > 0:
                lines.append(f"✓ Используются type hints ({m['type_hints']})")
        elif lang in ("Kotlin", "Java", "C#", "Go"):
            if m["type_hints"] > 0:
                lines.append(f"✓ Статическая типизация ({m['type_hints']} объявлений)")

        nq = m["name_quality"]
        if nq >= 0.6:
            lines.append("✓ Качественные имена переменных")
        elif nq >= 0.35:
            lines.append("~ Имена переменных среднего качества")
        else:
            lines.append("✗ Некачественные имена переменных")

        if m["magic_numbers"] == 0:
            lines.append("✓ Нет магических чисел")
        else:
            lines.append(f"✗ {m['magic_numbers']} магических чисел")

        if m["classes"] > 0:
            lines.append(f"✓ {m['classes']} класс(ов)")
        if m["functions"] > 0:
            lines.append(f"✓ {m['functions']} функций")

        lines.append("")
        lines.append("-" * 50)
        lines.append("ОГРАНИЧЕНИЯ / ЗАМЕЧАНИЯ:")
        lines.append("-" * 50)

        afl = m["avg_func_length"]
        if afl > 20:
            lines.append(f"! Средняя длина функции {afl} строк (рек. ≤15)")
        if m["max_nesting"] > 4:
            lines.append(f"! Высокая вложенность: {m['max_nesting']} (рек. ≤3)")
        if m["cyclomatic"] > 10:
            lines.append(f"! Высокая цикломатическая сложность: {m['cyclomatic']} (рек. ≤10)")
        if m["short_names"] > 3:
            lines.append(f"! Много коротких имён: {m['short_names']}")
        if m["magic_numbers"] > 4:
            lines.append(f"! Много магических чисел: {m['magic_numbers']}")
        if m["functions"] == 0 and m["code_lines"] > 10:
            lines.append("! Нет функций при большом объёме кода")
        if m["long_lines"] > 5:
            lines.append(f"! {m['long_lines']} строк длиннее 79 символов")

        hd = m.get("hal_difficulty", 0)
        if hd > 20:
            lines.append(f"! Высокая Halstead-сложность: {hd:.1f}")

        lines.append("")
        lines.append("-" * 50)
        lines.append("АНАЛИЗ ИИ ФИНГЕРПРИНТА:")
        lines.append("-" * 50)

        for reason in m.get("ai_reasons", []):
            lines.append(f"  • {reason}")
        if not m.get("ai_reasons"):
            lines.append("  Признаков генеративного ИИ не обнаружено.")

        lines.append("")
        lines.append("=" * 50)

        self.details.insert(tk.END, "\n".join(lines))
        self.details.config(state=tk.DISABLED)

    def _export(self):
        if not self._last_metrics:
            messagebox.showwarning("Внимание", "Сначала выполните анализ.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить отчёт",
            defaultextension=".txt",
            filetypes=[("Текстовый файл", "*.txt"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        m = self._last_metrics
        score = self._last_score
        report = self.details.get("1.0", tk.END)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"КодАнализатор v4.8 — Отчёт\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Язык: {self.current_lang.get()}\n\n")
                f.write(report)
            self.status_var.set(f"Отчёт сохранён: {os.path.basename(path)}")
            messagebox.showinfo("Готово", f"Отчёт сохранён:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}")

    def _copy_results(self):
        if not self._last_metrics:
            messagebox.showwarning("Внимание", "Сначала выполните анализ.")
            return
        report = self.details.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(report)
        self.status_var.set("Результаты скопированы в буфер обмена")

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════════════════
#  БАЗА ПРИМЕРОВ КОДА НА РАЗНЫХ ЯЗЫКАХ
# ══════════════════════════════════════════════════════════════════
EXAMPLES = {
    "Python": {
        "human": '''\
class GradeCalculator:
    """Manages student grade calculations and reporting."""

    MAX_SCORE = 100

    def __init__(self, student_name: str, scores: list[int]):
        """Initialize with student name and a list of integer scores."""
        self.student_name = student_name
        self.scores = scores

    def average(self) -> float:
        """Return the arithmetic mean of all scores."""
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)

    def highest(self) -> int:
        """Return the highest score achieved."""
        try:
            return max(self.scores)
        except ValueError:
            return 0

    def is_passing(self) -> bool:
        """Check whether the student has a passing average."""
        return self.average() >= (self.MAX_SCORE // 2)

    def summary(self) -> str:
        """Generate a human-readable summary report."""
        avg = self.average()
        status = "PASS" if self.is_passing() else "FAIL"
        return (
            f"Student: {self.student_name}\\n"
            f"Average: {avg:.1f}\\n"
            f"Status: {status}"
        )


# Example: calculate grades for a student
grades = GradeCalculator("Alice", [85, 92, 78, 90, 88])
print(grades.summary())
''',
        "ai": '''\
def function_1(param_1):
    result = 0
    for i in range(len(param_1)):
        result = result + param_1[i]
    if len(param_1) == 0:
        return 0
    else:
        return result / len(param_1)

data = [85, 92, 78, 90]
print(function_1(data))
''',
        "human_compare": '''\
def calculate_discount(price: float, customer_type: str) -> float:
    """Calculate price after discount application."""
    DISCOUNT_RATES = {
        "regular":   0.0,
        "vip":       0.15,
        "wholesale": 0.25,
    }
    MIN_PRICE = 10.0
    rate = DISCOUNT_RATES.get(customer_type, 0.0)
    return max(price * (1 - rate), MIN_PRICE)
''',
        "ai_compare": '''\
def function_1(param_1, param_2):
    if param_2 == "regular":
        temp_var = 0.0
    elif param_2 == "vip":
        temp_var = 0.15
    elif param_2 == "wholesale":
        temp_var = 0.25
    if param_1 > 0:
        res = param_1 - (param_1 * temp_var)
        if res < 10:
            res = 10
        return res
    return 0
''',
        "compare_notes": "АНАЛИЗ PYTHON:\n\nУ человека: Использование словаря, типизация параметров, docstring-контракт.\nУ ИИ: Избыточный каскад условий, неочевидные имена, магические числа."
    },
    "C++": {
        "human": '''\
#include <vector>
#include <numeric>
#include <iostream>

// Вычисление среднего значения числового вектора
double calculate_average(const std::vector<double>& numbers) {
    if (numbers.empty()) {
        return 0.0;
    }
    double sum = std::accumulate(numbers.begin(), numbers.end(), 0.0);
    return sum / numbers.size();
}

int main() {
    std::vector<double> scores = {85.5, 92.0, 78.5, 90.0};
    std::cout << calculate_average(scores) << std::endl;
    return 0;
}
''',
        "ai": '''\
#include <iostream>
using namespace std;
double function_1(double param_1[], int param_2) {
    double temp_var = 0;
    for (int i = 0; i < param_2; i++) {
        temp_var = temp_var + param_1[i];
    }
    if (param_2 == 0) return 0;
    else return temp_var / param_2;
}
''',
        "human_compare": '''\
#include <string>
#include <unordered_map>
#include <algorithm>

double calculate_discount(double price, const std::string& customer_type) {
    const std::unordered_map<std::string, double> DISCOUNT_RATES = {
        {"regular",   0.0},
        {"vip",       0.15},
        {"wholesale", 0.25}
    };
    const double MIN_PRICE = 10.0;
    auto it = DISCOUNT_RATES.find(customer_type);
    double rate = (it != DISCOUNT_RATES.end()) ? it->second : 0.0;
    return std::max(price * (1.0 - rate), MIN_PRICE);
}
''',
        "ai_compare": '''\
#include <string>
double function_1(double param_1, std::string param_2) {
    double temp_var = 0.0;
    if (param_2 == "regular") temp_var = 0.0;
    else if (param_2 == "vip") temp_var = 0.15;
    else if (param_2 == "wholesale") temp_var = 0.25;
    double result = param_1 - (param_1 * temp_var);
    if (result < 10) return 10;
    return result;
}
''',
        "compare_notes": "АНАЛИЗ C++:\n\nУ человека: Передача объектов по ссылке, константная безопасность (const), ассоциативный контейнер std::unordered_map.\nУ ИИ: Низкоуровневые си-массивы без контроля размера, использование условного каскада."
    },
    "JavaScript": {
        "human": '''\
/**
 * Вычисляет среднее значение массива чисел.
 * @param {number[]} numbers
 * @returns {number}
 */
function calculateAverage(numbers) {
    if (!numbers || numbers.length === 0) {
        return 0.0;
    }
    const sum = numbers.reduce((acc, val) => acc + val, 0);
    return sum / numbers.length;
}
''',
        "ai": '''\
function function_1(param_1) {
    var temp_var = 0;
    for (var i = 0; i < param_1.length; i++) {
        temp_var = temp_var + param_1[i];
    }
    if (param_1.length == 0) {
        return 0;
    } else {
        return temp_var / param_1.length;
    }
}
''',
        "human_compare": '''\
function calculateDiscount(price, customerType) {
    const DISCOUNT_RATES = {
        regular: 0.0,
        vip: 0.15,
        wholesale: 0.25
    };
    const MIN_PRICE = 10.0;
    const rate = DISCOUNT_RATES[customerType] || 0.0;
    return Math.max(price * (1 - rate), MIN_PRICE);
}
''',
        "ai_compare": '''\
function function_1(param_1, param_2) {
    let temp_var = 0.0;
    if (param_2 == "regular") {
        temp_var = 0.0;
    } else if (param_2 == "vip") {
        temp_var = 0.15;
    } else if (param_2 == "wholesale") {
        temp_var = 0.25;
    }
    let res = param_1 - (param_1 * temp_var);
    if (res < 10) return 10;
    return res;
}
''',
        "compare_notes": "АНАЛИЗ JAVASCRIPT:\n\nУ человека: Использование функциональных методов ES6 (reduce), JSDoc-описания, логических операторов выбора по умолчанию.\nУ ИИ: Устаревшие конструкции циклов и ключевое слово var, слабая масштабируемость кода."
    },
    "Алгоритмический язык": {
        "human": '''\
алг вещ среднее_значение(вещ_таб числа, цел размер)
| Вычисление среднего арифметического значений в массиве
нач
  если размер = 0 то
    знач := 0.0
  иначе
    вещ сумма
    сумма := 0.0
    цел и
    для и от 1 до размер
      сумма := сумма + числа[и]
    все
    знач := сумма / размер
  все
кон
''',
        "ai": '''\
алг ф_1(таб_1, р_1)
нач
  п_1 := 0.0
  с_1 := 1
  нц пока с_1 <= р_1
    п_1 := п_1 + таб_1[с_1]
    с_1 := с_1 + 1
  кц
  вывод п_1 / р_1
кон
''',
        "human_compare": '''\
алг вещ рассчитать_цену(вещ базовая_цена, лит тип_клиента)
| Определение цены товара с учётом скидки
нач
  вещ скидка, мин_цена
  мин_цена := 10.0
  скидка := 0.0
  если тип_клиента = "vip" то
    скидка := 0.15
  иначе
    если тип_клиента = "wholesale" то
      скидка := 0.25
    все
  все
  вещ итоговая_цена
  итоговая_цена := базовая_цена * (1.0 - скидка)
  если итоговая_цена < мин_цена то
    знач := мин_цена
  иначе
    знач := итоговая_цена
  все
кон
''',
        "ai_compare": '''\
алг ф_1(ц_1, т_1)
нач
  п_1 := 0.0
  если т_1 = "vip" то
    п_1 := 0.15
  все
  если т_1 = "wholesale" то
    п_1 := 0.25
  все
  р_1 := ц_1 - ц_1 * п_1
  если р_1 < 10 то
    р_1 := 10
  все
  вывод р_1
кон
''',
        "compare_notes": "АНАЛИЗ АЛГОРИТМИЧЕСКОГО ЯЗЫКА:\n\nУ человека: Логичное использование структуры ветвления 'если-то-иначе', возвращаемое значение через 'знач'.\nУ ИИ: Использование неявного вывода вместо возврата значения, отсутствие содержательных имен."
    },
    "Java": {
        "human": '''\
import java.util.List;

public class MathUtils {
    /**
     * Calculates the arithmetic mean of a double list.
     */
    public static double calculateAverage(List<Double> numbers) {
        if (numbers == null || numbers.isEmpty()) {
            return 0.0;
        }
        double sum = 0.0;
        for (double num : numbers) {
            sum += num;
        }
        return sum / numbers.size();
    }
}
''',
        "ai": '''\
public class Main {
    public static double function_1(double[] param_1, int param_2) {
        double temp_var = 0;
        for (int i = 0; i < param_2; i++) {
            temp_var = temp_var + param_1[i];
        }
        if (param_2 == 0) return 0;
        else return temp_var / param_2;
    }
}
''',
        "human_compare": '''\
import java.util.Map;

public class DiscountManager {
    private static final double MIN_PRICE = 10.0;
    private static final Map<String, Double> RATES = Map.of(
        "regular", 0.0,
        "vip", 0.15,
        "wholesale", 0.25
    );

    public static double getFinalPrice(double price, String type) {
        double rate = RATES.getOrDefault(type, 0.0);
        return Math.max(price * (1 - rate), MIN_PRICE);
    }
}
''',
        "ai_compare": '''\
public class Discount {
    public double function_1(double param_1, String param_2) {
        double temp_var = 0;
        if (param_2.equals("regular")) temp_var = 0.0;
        else if (param_2.equals("vip")) temp_var = 0.15;
        else if (param_2.equals("wholesale")) temp_var = 0.25;
        double res = param_1 - (param_1 * temp_var);
        if (res < 10) return 10;
        return res;
    }
}
''',
        "compare_notes": "АНАЛИЗ JAVA:\n\nУ человека: Константное описание правил через Map.of, безопасные обращения через getOrDefault.\nУ ИИ: Ручное строковое сравнение через цепочку if-else, жестко закодированные магические числа."
    },
    "Kotlin": {
        "human": '''\
/**
 * Calculates the arithmetic mean of the given list.
 */
fun calculateAverage(numbers: List<Double>): Double {
    if (numbers.isEmpty()) return 0.0
    return numbers.sum() / numbers.size
}
''',
        "ai": '''\
fun function_1(param_1: DoubleArray): Double {
    var temp_var = 0.0
    for (i in 0 until param_1.size) {
        temp_var = temp_var + param_1[i]
    }
    if (param_1.size == 0) return 0.0
    else return temp_var / param_1.size
}
''',
        "human_compare": '''\
fun calculateDiscount(price: Double, customerType: String): Double {
    val discountRates = mapOf(
        "regular" to 0.0,
        "vip" to 0.15,
        "wholesale" to 0.25
    )
    val minPrice = 10.0
    val rate = discountRates[customerType] ?: 0.0
    return (price * (1 - rate)).coerceAtLeast(minPrice)
}
''',
        "ai_compare": '''\
fun function_1(param_1: Double, param_2: String): Double {
    var temp_var = 0.0
    if (param_2 == "regular") temp_var = 0.0
    else if (param_2 == "vip") temp_var = 0.15
    else if (param_2 == "wholesale") temp_var = 0.25
    var result = param_1 - (param_1 * temp_var)
    if (result < 10) return 10.0
    return result
}
''',
        "compare_notes": "АНАЛИЗ KOTLIN:\n\nУ человека: Идиоматичный синтаксис (coerceAtLeast, оператор элвис ?:).\nУ ИИ: Обычный процедурный шаблон без использования возможностей стандартной библиотеки Kotlin."
    },
    "C": {
        "human": '''\
#include <stdio.h>

// Расчёт среднего арифметического значений массива
double calculate_average(const double numbers[], int size) {
    if (size <= 0 || numbers == NULL) {
        return 0.0;
    }
    double sum = 0.0;
    for (int i = 0; i < size; ++i) {
        sum += numbers[i];
    }
    return sum / size;
}
''',
        "ai": '''\
double function_1(double param_1[], int param_2) {
    double temp_var = 0;
    for (int i = 0; i < param_2; i++) {
        temp_var = temp_var + param_1[i];
    }
    if (param_2 == 0) return 0;
    else return temp_var / param_2;
}
''',
        "human_compare": '''\
#include <string.h>

double calculate_discount(double price, const char* customer_type) {
    double rate = 0.0;
    const double min_price = 10.0;

    if (strcmp(customer_type, "vip") == 0) {
        rate = 0.15;
    } else if (strcmp(customer_type, "wholesale") == 0) {
        rate = 0.25;
    }
    
    double final_price = price * (1.0 - rate);
    return (final_price < min_price) ? min_price : final_price;
}
''',
        "ai_compare": '''\
double function_1(double param_1, char* param_2) {
    double temp_var = 0.0;
    if (param_2 == "regular") temp_var = 0.0; // Логическая ошибка сравнения указателей!
    if (param_1 > 0) {
        double res = param_1 - (param_1 * temp_var);
        if (res < 10) return 10;
        return res;
    }
    return 0;
}
''',
        "compare_notes": "АНАЛИЗ С:\n\nУ человека: Безопасное сравнение строк strcmp(), валидация указателей на NULL.\nУ ИИ: Опасное прямое сравнение указателей (param_2 == \"regular\"), приводящее к неопределенному поведению."
    },
    "C#": {
        "human": '''\
using System;
using System.Collections.Generic;
using System.Linq;

public class MathMetrics {
    /// <summary>
    /// Calculates the arithmetic average of numbers.
    /// </summary>
    public static double CalculateAverage(IEnumerable<double> numbers) {
        if (numbers == null || !numbers.Any()) {
            return 0.0;
        }
        return numbers.Average();
    }
}
''',
        "ai": '''\
public class MainClass {
    public static double function_1(double[] param_1, int param_2) {
        double temp_var = 0;
        for (int i = 0; i < param_2; i++) {
            temp_var = temp_var + param_1[i];
        }
        if (param_2 == 0) return 0;
        else return temp_var / param_2;
    }
}
''',
        "human_compare": '''\
using System;
using System.Collections.Generic;

public class PricingCalculator {
    private static readonly Dictionary<string, double> DiscountRates = new() {
        { "regular", 0.0 },
        { "vip", 0.15 },
        { "wholesale", 0.25 }
    };
    private const double MinPrice = 10.0;

    public static double GetDiscountedPrice(double price, string customerType) {
        double rate = DiscountRates.GetValueOrDefault(customerType, 0.0);
        return Math.Max(price * (1 - rate), MinPrice);
    }
}
''',
        "ai_compare": '''\
public class Discount {
    public double function_1(double param_1, string param_2) {
        double temp_var = 0;
        if (param_2 == "regular") temp_var = 0.0;
        else if (param_2 == "vip") temp_var = 0.15;
        else if (param_2 == "wholesale") temp_var = 0.25;
        double result = param_1 - (param_1 * temp_var);
        if (result < 10) return 10;
        return result;
    }
}
''',
        "compare_notes": "АНАЛИЗ C#:\n\nУ человека: Использование обобщений IEnumerable, XML-документирование, безопасный метод GetValueOrDefault.\nУ ИИ: Статичные жесткие условные конструкции без использования возможностей CLR и LINQ."
    },
    "HTML": {
        "human": '''\
<!-- Семантическая и доступная карточка товара -->
<article class="product-card" aria-labelledby="product-title">
    <header class="product-card__header">
        <h2 id="product-title" class="product-card__title">Премиум Курс</h2>
    </header>
    <div class="product-card__body">
        <p class="product-card__price">Цена: <span class="price-val">100.00 USD</span></p>
    </div>
</article>
''',
        "ai": '''\
<div id="wrapper">
    <div id="content">
        <center>
            <font size="5"><b>Премиум Курс</b></font>
        </center>
        <p>Цена: 100.00 USD</p>
    </div>
</div>
''',
        "human_compare": '''\
<form class="feedback-form" action="/submit" method="POST">
    <fieldset class="feedback-form__section">
        <legend class="feedback-form__title">Обратная связь</legend>
        <label for="email" class="feedback-form__label">Email:</label>
        <input type="email" id="email" name="email" required placeholder="name@example.com">
    </fieldset>
</form>
''',
        "ai_compare": '''\
<div id="form-div">
    <span><b>Обратная связь</b></span><br>
    Email: <input type="text" name="email" id="input1">
</div>
''',
        "compare_notes": "АНАЛИЗ HTML:\n\nУ человека: Семантические теги (<article>, <fieldset>, <legend>), соответствие спецификациям доступности (ARIA, теги <label>).\nУ ИИ: Устаревшая верстка таблицами или несемантическими <div>-блоками, использование тегов стилизации (<font>, <center>)."
    },
    "Pascal": {
        "human": '''\
// Вычисление среднего значения элементов массива вещественных чисел
function CalculateAverage(const arr: array of Double): Double;
var
  sum: Double;
  i: Integer;
begin
  if Length(arr) = 0 then Exit(0.0);
  sum := 0.0;
  for i := Low(arr) to High(arr) do
    sum := sum + arr[i];
  Result := sum / Length(arr);
end;
''',
        "ai": '''\
function function_1(param_1: array of Double; param_2: Integer): Double;
var
  temp_var: Double;
  i: Integer;
begin
  temp_var := 0;
  for i := 0 to param_2 - 1 do
    temp_var := temp_var + param_1[i];
  if param_2 = 0 then function_1 := 0
  else function_1 := temp_var / param_2;
end;
''',
        "human_compare": '''\
function GetDiscountedPrice(price: Double; customerType: string): Double;
const
  MinPrice = 10.0;
var
  rate: Double;
begin
  rate := 0.0;
  if customerType = 'vip' then rate := 0.15
  else if customerType = 'wholesale' then rate := 0.25;
  
  Result := price * (1.0 - rate);
  if Result < MinPrice then Result := MinPrice;
end;
''',
        "ai_compare": '''\
function function_1(param_1: Double; param_2: string): Double;
var
  temp_var: Double;
begin
  if param_2 = 'vip' then temp_var := 0.15;
  if param_2 = 'wholesale' then temp_var := 0.25;
  function_1 := param_1 - (param_1 * temp_var);
  if function_1 < 10 then function_1 := 10;
end;
''',
        "compare_notes": "АНАЛИЗ PASCAL:\n\nУ человека: Константное объявление неизменяемых величин, использование встроенного ключевого слова Result.\nУ ИИ: Ручное переназначение имени функции для вывода значения, отсутствие обработки некорректных типов."
    },
    "SQL": {
        "human": '''\
-- Читаемое построение запроса с использованием обобщенных табличных выражений (CTE)
WITH ActivePurchases AS (
    SELECT user_id, amount
    FROM orders
    WHERE status = 'completed' AND amount > 0.0
)
SELECT 
    user_id, 
    AVG(amount) AS average_order_value
FROM ActivePurchases
GROUP BY user_id;
''',
        "ai": '''\
SELECT user_id, avg(amount) FROM orders WHERE status = 'completed' GROUP BY user_id;
''',
        "human_compare": '''\
-- Оптимальный выбор данных из связанных таблиц
SELECT 
    u.id, 
    u.username, 
    COALESCE(SUM(o.amount), 0.0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.username;
''',
        "ai_compare": '''\
SELECT u.id, u.username, sum(o.amount)
FROM users u, orders o
WHERE u.id = o.user_id AND u.status = 'active'
GROUP BY u.id, u.username;
''',
        "compare_notes": "АНАЛИЗ SQL:\n\nУ человека: Безопасное левое соединение (LEFT JOIN), замена пустых значений через COALESCE, форматирование ключевых слов.\nУ ИИ: Устаревшее неявное перекрестное соединение (через запятую в FROM), которое может вызывать потерю строк без заказов."
    },
    "Go": {
        "human": '''\
package main

import "errors"

// CalculateAverage computes the mean of floats safely.
func CalculateAverage(numbers []float64) (float64, error) {
    if len(numbers) == 0 {
        return 0.0, errors.New("empty slice")
    }
    sum := 0.0
    for _, val := range numbers {
        sum += val
    }
    return sum / float64(len(numbers)), nil
}
''',
        "ai": '''\
package main
func function_1(param_1 []float64, param_2 int) float64 {
    temp_var := 0.0
    for i := 0; i < param_2; i++ {
        temp_var = temp_var + param_1[i]
    }
    if param_2 == 0 {
        return 0
    } else {
        return temp_var / float64(param_2)
    }
}
''',
        "human_compare": '''\
package main

const MinPrice = 10.0

func CalculateDiscount(price float64, customerType string) float64 {
    rates := map[string]float64{
        "regular":   0.0,
        "vip":       0.15,
        "wholesale": 0.25,
    }
    rate, exists := rates[customerType]
    if !exists {
        rate = 0.0
    }
    finalPrice := price * (1.0 - rate)
    if finalPrice < MinPrice {
        return MinPrice
    }
    return finalPrice
}
''',
        "ai_compare": '''\
package main
func function_1(param_1 float64, param_2 string) float64 {
    temp_var := 0.0
    if param_2 == "vip" {
        temp_var = 0.15
    }
    if param_2 == "wholesale" {
        temp_var = 0.25
    }
    res := param_1 - (param_1 * temp_var)
    if res < 10 {
        return 10
    }
    return res
}
''',
        "compare_notes": "АНАЛИЗ GO:\n\nУ человека: Возврат ошибок (error) согласно Go-идиоматике, безопасная проверка существования ключа в map.\nУ ИИ: Си-подобный стиль написания без обработки пограничных ситуаций и проверки валидности данных."
    }
}


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CodeAnalyzer()
    app.run()
