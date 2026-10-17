# -*- coding: utf-8 -*-
"""
Ostia - un lenguaje de programación en español con sintaxis al estilo de Java.

Uso:
    python ostia.py programa.ostia

Fases implementadas:
    1. Núcleo: variables con tipo, operadores, si/sino, para, mientras, hacer,
       funciones, imprimir.
    2. Excepciones: intentar / capturar / finalmente, lanzar, lanza.

Los acentos son opcionales en palabras clave, tipos y nombres
("Excepción" == "Excepcion", "vacío" == "vacio"). La ñ se conserva siempre:
"año" y "ano" son nombres distintos.
"""

import math
import random
import re
import sys
import unicodedata
from collections import namedtuple


# ---------------------------------------------------------------------------
# Errores y señales internas
# ---------------------------------------------------------------------------

class ErrorOstia(Exception):
    """Error fatal del programa (sintaxis, variable inexistente, tipos...)."""

    def __init__(self, mensaje, linea=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea


class Lanzado(Exception):
    """Una excepción de Ostia que está subiendo por la pila."""

    def __init__(self, obj):
        super().__init__(obj.texto())
        self.obj = obj


class Devolver(Exception):
    def __init__(self, valor, linea):
        super().__init__()
        self.valor = valor
        self.linea = linea


class Romper(Exception):
    def __init__(self, linea):
        super().__init__()
        self.linea = linea


class Continuar(Exception):
    def __init__(self, linea):
        super().__init__()
        self.linea = linea


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def normalizar(texto):
    """Quita las tildes pero conserva la ñ."""
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("ñ", "\x00n").replace("Ñ", "\x00N")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.replace("\x00n", "ñ").replace("\x00N", "Ñ")


PALABRAS_CLAVE = {
    "si", "sino", "para", "mientras", "hacer", "devolver", "romper",
    "continuar", "intentar", "capturar", "finalmente", "lanzar", "lanza",
    "nuevo", "verdadero", "falso", "nulo", "y", "o", "no",
}

TIPOS = {
    "entero", "largo", "corto", "decimal", "flotante", "booleano",
    "caracter", "Cadena", "vacio",
}

ENTEROS = {"entero", "largo", "corto"}
DECIMALES = {"decimal", "flotante"}

DEFECTOS = {
    "entero": 0, "largo": 0, "corto": 0, "decimal": 0.0, "flotante": 0.0,
    "booleano": False, "caracter": "\0", "Cadena": None,
}

# Jerarquía de excepciones: nombre -> clase padre
JERARQUIA = {
    "Excepcion": None,
    "ExcepcionAritmetica": "Excepcion",
    "ExcepcionNula": "Excepcion",
    "ExcepcionIndice": "Excepcion",
    "ExcepcionFormatoNumero": "Excepcion",
    "ExcepcionEjecucion": "Excepcion",
}


def es_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def es_entero(v):
    return isinstance(v, int) and not isinstance(v, bool)


def nombre_tipo(v):
    if v is None:
        return "nulo"
    if isinstance(v, bool):
        return "booleano"
    if isinstance(v, int):
        return "entero"
    if isinstance(v, float):
        return "decimal"
    if isinstance(v, str):
        return "Cadena"
    if isinstance(v, ObjetoExcepcion):
        return v.tipo
    return "objeto"


def texto_de(v):
    if v is None:
        return "nulo"
    if v is True:
        return "verdadero"
    if v is False:
        return "falso"
    if isinstance(v, float):
        if math.isnan(v):
            return "NaN"
        if math.isinf(v):
            return "Infinito" if v > 0 else "-Infinito"
        return repr(v)
    if isinstance(v, ObjetoExcepcion):
        return v.texto()
    return str(v)


def igual(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if es_num(a) and es_num(b):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return a is b


class ObjetoExcepcion:
    def __init__(self, tipo, mensaje=None, linea=None):
        self.tipo = tipo
        self.mensaje = mensaje
        self.linea = linea

    def texto(self):
        if self.mensaje is None:
            return self.tipo
        return f"{self.tipo}: {self.mensaje}"


class ObjetoNativo:
    """Objeto de la biblioteca estándar (Sistema, Matematica...)."""

    def __init__(self, atributos):
        self.atributos = atributos


# ---------------------------------------------------------------------------
# Analizador léxico
# ---------------------------------------------------------------------------

Tok = namedtuple("Tok", "tipo valor linea orig")

PATRON = re.compile(r"""
    (?P<ws>[ \t\r]+)
  | (?P<nl>\n)
  | (?P<lc>//[^\n]*)
  | (?P<bc>/\*.*?\*/)
  | (?P<num>\d+\.\d+|\d+)
  | (?P<str>"(?:\\.|[^"\\\n])*")
  | (?P<char>'(?:\\.|[^'\\\n])')
  | (?P<id>[^\W\d]\w*)
  | (?P<op>\+\+|--|\+=|-=|\*=|/=|%=|==|!=|<=|>=|&&|\|\||[-+*/%<>=!(){}\[\],;.?:])
""", re.VERBOSE | re.DOTALL)

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0",
           "\\": "\\", '"': '"', "'": "'"}


def desescapar(texto):
    salida = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == "\\" and i + 1 < len(texto):
            i += 1
            salida.append(ESCAPES.get(texto[i], texto[i]))
        else:
            salida.append(c)
        i += 1
    return "".join(salida)


def tokenizar(codigo):
    toks = []
    pos = 0
    linea = 1
    while pos < len(codigo):
        m = PATRON.match(codigo, pos)
        if not m:
            c = codigo[pos]
            if c == '"':
                raise ErrorOstia("error de sintaxis: cadena sin cerrar", linea)
            if c == "'":
                raise ErrorOstia("error de sintaxis: carácter mal formado", linea)
            raise ErrorOstia(f"error de sintaxis: carácter inesperado '{c}'", linea)
        tipo = m.lastgroup
        texto = m.group()
        if tipo in ("ws", "lc"):
            pass
        elif tipo == "nl":
            linea += 1
        elif tipo == "bc":
            linea += texto.count("\n")
        elif tipo == "num":
            valor = float(texto) if "." in texto else int(texto)
            toks.append(Tok("num", valor, linea, texto))
        elif tipo == "str":
            toks.append(Tok("str", desescapar(texto[1:-1]), linea, texto))
        elif tipo == "char":
            toks.append(Tok("char", desescapar(texto[1:-1]), linea, texto))
        elif tipo == "id":
            n = normalizar(texto)
            if n in PALABRAS_CLAVE:
                toks.append(Tok("kw", n, linea, texto))
            elif n in TIPOS:
                toks.append(Tok("tipo", n, linea, texto))
            else:
                toks.append(Tok("id", n, linea, texto))
        else:
            if texto == "/" and codigo.startswith("/*", pos):
                raise ErrorOstia("error de sintaxis: comentario sin cerrar", linea)
            toks.append(Tok("op", texto, linea, texto))
        pos = m.end()
    toks.append(Tok("eof", None, linea, ""))
    return toks


# ---------------------------------------------------------------------------
# Analizador sintáctico (descenso recursivo) -> árbol de tuplas
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def actual(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def es(self, tipo, valor=None, k=0):
        t = self.actual(k)
        return t.tipo == tipo and (valor is None or t.valor == valor)

    def avanzar(self):
        t = self.toks[self.i]
        if t.tipo != "eof":
            self.i += 1
        return t

    def acepta(self, tipo, valor=None):
        if self.es(tipo, valor):
            return self.avanzar()
        return None

    @staticmethod
    def describir(t):
        return "el final del archivo" if t.tipo == "eof" else f"'{t.orig}'"

    def espera(self, tipo, valor=None, que=None):
        if self.es(tipo, valor):
            return self.avanzar()
        t = self.actual()
        esperado = que or (f"'{valor}'" if valor else tipo)
        linea = t.linea
        if valor == ";" and self.i > 0:
            linea = self.toks[self.i - 1].linea
        raise ErrorOstia(
            f"error de sintaxis: se esperaba {esperado} pero se encontró "
            f"{self.describir(t)}", linea)

    def programa(self):
        nodos = []
        while not self.es("eof"):
            nodos.append(self.declaracion(nivel_superior=True))
        return nodos

    def declaracion(self, nivel_superior=False):
        if self.es("tipo") and self.es("id", k=1) and self.es("op", "(", k=2):
            if not nivel_superior:
                raise ErrorOstia(
                    "las funciones solo se pueden definir al nivel superior "
                    "del programa", self.actual().linea)
            return self.funcion()
        return self.sentencia()

    def funcion(self):
        tipo = self.avanzar()
        nombre = self.avanzar()
        self.espera("op", "(")
        params = []
        if not self.es("op", ")"):
            while True:
                t = self.espera("tipo", que="un tipo")
                if t.valor == "vacio":
                    raise ErrorOstia(
                        "un parámetro no puede ser de tipo vacio", t.linea)
                n = self.espera("id", que="el nombre del parámetro")
                params.append((t.valor, n.valor))
                if not self.acepta("op", ","):
                    break
        self.espera("op", ")")
        if self.acepta("kw", "lanza"):
            self.espera("id", que="un tipo de excepción")
            while self.acepta("op", ","):
                self.espera("id", que="un tipo de excepción")
        cuerpo = self.bloque()
        return ("func", tipo.linea, nombre.valor, params, tipo.valor, cuerpo)

    def bloque(self):
        t = self.espera("op", "{")
        sentencias = []
        while not self.es("op", "}"):
            if self.es("eof"):
                raise ErrorOstia(
                    f"error de sintaxis: falta cerrar la llave '{{' abierta "
                    f"en la línea {t.linea}", self.actual().linea)
            sentencias.append(self.declaracion())
        self.espera("op", "}")
        return ("bloque", t.linea, sentencias)

    def decl_variable(self):
        tipo = self.avanzar()
        if tipo.valor == "vacio":
            raise ErrorOstia(
                "no se puede declarar una variable de tipo vacio", tipo.linea)
        items = []
        while True:
            n = self.espera("id", que="el nombre de la variable")
            expr = None
            if self.acepta("op", "="):
                expr = self.expresion()
            items.append((tipo.valor, n.valor, expr))
            if not self.acepta("op", ","):
                break
        self.espera("op", ";", que="';'")
        return ("decl", tipo.linea, items)

    def sentencia(self):
        t = self.actual()
        if t.tipo == "op" and t.valor == "{":
            return self.bloque()
        if t.tipo == "op" and t.valor == ";":
            self.avanzar()
            return ("bloque", t.linea, [])
        if t.tipo == "tipo" and self.es("id", k=1):
            return self.decl_variable()
        if t.tipo == "kw":
            k = t.valor
            if k == "si":
                return self.s_si()
            if k == "mientras":
                return self.s_mientras()
            if k == "hacer":
                return self.s_hacer()
            if k == "para":
                return self.s_para()
            if k == "devolver":
                self.avanzar()
                expr = None if self.es("op", ";") else self.expresion()
                self.espera("op", ";", que="';'")
                return ("devolver", t.linea, expr)
            if k == "romper":
                self.avanzar()
                self.espera("op", ";", que="';'")
                return ("romper", t.linea)
            if k == "continuar":
                self.avanzar()
                self.espera("op", ";", que="';'")
                return ("continuar", t.linea)
            if k == "lanzar":
                self.avanzar()
                expr = self.expresion()
                self.espera("op", ";", que="';'")
                return ("lanzar", t.linea, expr)
            if k == "intentar":
                return self.s_intentar()
            if k in ("sino", "capturar", "finalmente"):
                raise ErrorOstia(
                    f"error de sintaxis: '{t.orig}' no puede aparecer aquí "
                    f"sin su 'si' o 'intentar' correspondiente", t.linea)
        expr = self.expresion()
        self.espera("op", ";", que="';' al final de la sentencia")
        return ("expr", t.linea, expr)

    def condicion(self):
        self.espera("op", "(")
        c = self.expresion()
        self.espera("op", ")")
        return c

    def s_si(self):
        t = self.avanzar()
        cond = self.condicion()
        entonces = self.sentencia()
        sino = None
        if self.acepta("kw", "sino"):
            sino = self.sentencia()
        return ("si", t.linea, cond, entonces, sino)

    def s_mientras(self):
        t = self.avanzar()
        cond = self.condicion()
        return ("mientras", t.linea, cond, self.sentencia())

    def s_hacer(self):
        t = self.avanzar()
        cuerpo = self.sentencia()
        self.espera("kw", "mientras")
        cond = self.condicion()
        self.espera("op", ";", que="';'")
        return ("hacer", t.linea, cond, cuerpo)

    def s_para(self):
        t = self.avanzar()
        self.espera("op", "(")
        if self.es("op", ";"):
            self.avanzar()
            init = None
        elif self.es("tipo") and self.es("id", k=1):
            init = self.decl_variable()
        else:
            init = ("expr", t.linea, self.expresion())
            self.espera("op", ";", que="';'")
        cond = None if self.es("op", ";") else self.expresion()
        self.espera("op", ";", que="';'")
        updates = []
        if not self.es("op", ")"):
            updates.append(self.expresion())
            while self.acepta("op", ","):
                updates.append(self.expresion())
        self.espera("op", ")")
        return ("para", t.linea, init, cond, updates, self.sentencia())

    def s_intentar(self):
        t = self.avanzar()
        cuerpo = self.bloque()
        capturas = []
        fin = None
        while self.es("kw", "capturar"):
            self.avanzar()
            self.espera("op", "(")
            tipo = self.espera("id", que="el tipo de excepción")
            nombre = self.espera("id", que="el nombre de la variable")
            self.espera("op", ")")
            capturas.append((tipo.valor, nombre.valor, self.bloque(), tipo.linea))
        if self.acepta("kw", "finalmente"):
            fin = self.bloque()
        if not capturas and fin is None:
            raise ErrorOstia(
                "'intentar' necesita al menos un 'capturar' o un 'finalmente'",
                t.linea)
        return ("intentar", t.linea, cuerpo, capturas, fin)

    def expresion(self):
        return self.asignacion()

    def asignacion(self):
        izq = self.ternario()
        t = self.actual()
        if t.tipo == "op" and t.valor in ("=", "+=", "-=", "*=", "/=", "%="):
            self.avanzar()
            if izq[0] != "var":
                raise ErrorOstia(
                    "la parte izquierda de una asignación debe ser una variable",
                    t.linea)
            der = self.asignacion()
            return ("asig", t.linea, izq[2], t.valor, der)
        return izq

    def ternario(self):
        cond = self.logico_o()
        if self.es("op", "?"):
            t = self.avanzar()
            a = self.expresion()
            self.espera("op", ":")
            b = self.ternario()
            return ("ternario", t.linea, cond, a, b)
        return cond

    def logico_o(self):
        izq = self.logico_y()
        while self.es("op", "||") or self.es("kw", "o"):
            t = self.avanzar()
            izq = ("log", t.linea, "||", izq, self.logico_y())
        return izq

    def logico_y(self):
        izq = self.igualdad()
        while self.es("op", "&&") or self.es("kw", "y"):
            t = self.avanzar()
            izq = ("log", t.linea, "&&", izq, self.igualdad())
        return izq

    def _binario(self, siguiente, operadores):
        izq = siguiente()
        while self.actual().tipo == "op" and self.actual().valor in operadores:
            t = self.avanzar()
            izq = ("bin", t.linea, t.valor, izq, siguiente())
        return izq

    def igualdad(self):
        return self._binario(self.comparacion, ("==", "!="))

    def comparacion(self):
        return self._binario(self.suma, ("<", ">", "<=", ">="))

    def suma(self):
        return self._binario(self.producto, ("+", "-"))

    def producto(self):
        return self._binario(self.unario, ("*", "/", "%"))

    def unario(self):
        t = self.actual()
        if (t.tipo == "op" and t.valor == "!") or (t.tipo == "kw" and t.valor == "no"):
            self.avanzar()
            return ("no", t.linea, self.unario())
        if t.tipo == "op" and t.valor == "-":
            self.avanzar()
            return ("neg", t.linea, self.unario())
        if t.tipo == "op" and t.valor == "+":
            self.avanzar()
            return self.unario()
        if t.tipo == "op" and t.valor in ("++", "--"):
            self.avanzar()
            v = self.unario()
            if v[0] != "var":
                raise ErrorOstia(f"'{t.valor}' solo se puede aplicar a una variable", t.linea)
            return ("incr", t.linea, v[2], 1 if t.valor == "++" else -1, True)
        return self.postfijo()

    def postfijo(self):
        e = self.primario()
        while True:
            t = self.actual()
            if t.tipo == "op" and t.valor == "(":
                self.avanzar()
                e = ("llamada", t.linea, e, self.argumentos())
            elif t.tipo == "op" and t.valor == ".":
                self.avanzar()
                n = self.espera("id", que="un nombre después del '.'")
                e = ("miembro", t.linea, e, n.valor)
            elif t.tipo == "op" and t.valor in ("++", "--") and e[0] == "var":
                self.avanzar()
                e = ("incr", t.linea, e[2], 1 if t.valor == "++" else -1, False)
            else:
                break
        return e

    def argumentos(self):
        args = []
        if not self.es("op", ")"):
            args.append(self.expresion())
            while self.acepta("op", ","):
                args.append(self.expresion())
        self.espera("op", ")")
        return args

    def primario(self):
        t = self.actual()
        if t.tipo in ("num", "str", "char"):
            self.avanzar()
            return ("lit", t.linea, t.valor)
        if t.tipo == "kw":
            if t.valor == "verdadero":
                self.avanzar()
                return ("lit", t.linea, True)
            if t.valor == "falso":
                self.avanzar()
                return ("lit", t.linea, False)
            if t.valor == "nulo":
                self.avanzar()
                return ("lit", t.linea, None)
            if t.valor == "nuevo":
                self.avanzar()
                n = self.espera("id", que="el nombre de una clase")
                self.espera("op", "(")
                return ("nuevo", t.linea, n.valor, self.argumentos())
        if t.tipo == "id":
            self.avanzar()
            return ("var", t.linea, t.valor, t.orig)
        if t.tipo == "op" and t.valor == "(":
            self.avanzar()
            e = self.expresion()
            self.espera("op", ")")
            return e
        raise ErrorOstia(
            f"error de sintaxis: no se esperaba {self.describir(t)}", t.linea)


# ---------------------------------------------------------------------------
# Intérprete
# ---------------------------------------------------------------------------

class Entorno:
    def __init__(self, padre=None):
        self.vars = {}
        self.padre = padre

    def declarar(self, nombre, tipo, valor, linea):
        if nombre in self.vars:
            raise ErrorOstia(f"la variable '{nombre}' ya está declarada", linea)
        self.vars[nombre] = [tipo, valor]

    def buscar(self, nombre):
        e = self
        while e is not None:
            if nombre in e.vars:
                return e.vars[nombre]
            e = e.padre
        return None


class Interprete:
    LIMITE_PILA = 600

    def __init__(self, salida=None, entrada=None):
        self.salida = salida or sys.stdout
        self.entrada = entrada or sys.stdin
        self.funciones = {}
        self.globales = Entorno()
        self.profundidad = 0
        self.builtins = self._crear_builtins()
        self.nativos = self._crear_nativos()

    def _crear_builtins(self):
        def imprimir(*a):
            if len(a) > 1:
                raise TypeError("imprimir recibe un solo valor")
            self.salida.write(texto_de(a[0]) if a else "")

        def imprimirln(*a):
            imprimir(*a)
            self.salida.write("\n")

        def leer_linea():
            linea = self.entrada.readline()
            return linea.rstrip("\r\n") if linea else None

        def a_entero(x):
            if isinstance(x, float):
                return int(x)
            if not isinstance(x, str):
                raise TypeError("aEntero espera una Cadena o un decimal")
            try:
                return int(x.strip())
            except ValueError:
                raise ValueError(f"no se puede convertir '{x}' a entero")

        def a_decimal(x):
            if es_num(x):
                return float(x)
            if not isinstance(x, str):
                raise TypeError("aDecimal espera una Cadena o un número")
            try:
                return float(x.strip())
            except ValueError:
                raise ValueError(f"no se puede convertir '{x}' a decimal")

        return {
            "imprimir": imprimir,
            "imprimirln": imprimirln,
            "leerLinea": leer_linea,
            "aEntero": a_entero,
            "aDecimal": a_decimal,
            "aCadena": texto_de,
        }

    def _crear_nativos(self):
        b = self.builtins

        def raiz(x):
            return math.sqrt(x) if x >= 0 else math.nan

        def potencia(a, c):
            try:
                return math.pow(a, c)
            except (ValueError, OverflowError):
                return math.nan

        sistema = ObjetoNativo({
            "salida": ObjetoNativo({
                "imprimir": b["imprimir"],
                "imprimirln": b["imprimirln"],
            }),
        })
        matematica = ObjetoNativo({
            "PI": math.pi,
            "E": math.e,
            "raiz": raiz,
            "potencia": potencia,
            "abs": abs,
            "max": max,
            "min": min,
            "piso": lambda x: float(math.floor(x)),
            "techo": lambda x: float(math.ceil(x)),
            "redondear": lambda x: int(math.floor(x + 0.5)),
            "aleatorio": random.random,
        })
        return {"Sistema": sistema, "Matematica": matematica}

    def _metodos_cadena(self, s):
        def revisar(i, tope):
            if i < 0 or i > tope:
                raise IndexError(f"índice fuera de rango: {i}")

        def subcadena(a, c=None):
            c = len(s) if c is None else c
            revisar(a, len(s))
            revisar(c, len(s))
            if a > c:
                raise IndexError(f"índice fuera de rango: {a}..{c}")
            return s[a:c]

        def caracter_en(i):
            revisar(i, len(s) - 1)
            return s[i]

        return {
            "longitud": lambda: len(s),
            "mayusculas": lambda: s.upper(),
            "minusculas": lambda: s.lower(),
            "contiene": lambda t: t in s,
            "subcadena": subcadena,
            "empiezaCon": lambda t: s.startswith(t),
            "terminaCon": lambda t: s.endswith(t),
            "caracterEn": caracter_en,
            "reemplazar": lambda a, c: s.replace(a, c),
            "recortar": lambda: s.strip(),
            "estaVacia": lambda: len(s) == 0,
            "indiceDe": lambda t: s.find(t),
        }

    def _metodos_excepcion(self, o):
        return {
            "obtenerMensaje": lambda: o.mensaje,
            "obtenerTipo": lambda: o.tipo,
            "obtenerLinea": lambda: o.linea,
            "aCadena": lambda: o.texto(),
        }

    def ejecutar(self, programa):
        for n in programa:
            if n[0] == "func":
                if n[2] in self.funciones:
                    raise ErrorOstia(f"la función '{n[2]}' ya está definida", n[1])
                self.funciones[n[2]] = n
        try:
            for n in programa:
                if n[0] != "func":
                    self.exec(n, self.globales)
        except Devolver as d:
            raise ErrorOstia("'devolver' solo se puede usar dentro de una función", d.linea)
        except (Romper, Continuar) as s:
            raise ErrorOstia("'romper' y 'continuar' solo se pueden usar dentro de un bucle", s.linea)

    def exec(self, n, env):
        return getattr(self, "x_" + n[0])(n, env)

    def eval(self, n, env):
        return getattr(self, "e_" + n[0])(n, env)

    def lanzar(self, tipo, mensaje, linea):
        raise Lanzado(ObjetoExcepcion(tipo, mensaje, linea))

    def es_subclase(self, tipo, base):
        while tipo is not None:
            if tipo == base:
                return True
            tipo = JERARQUIA.get(tipo)
        return False

    def comprobar(self, tipo, valor, linea):
        if tipo in ENTEROS:
            if es_entero(valor):
                return valor
        elif tipo in DECIMALES:
            if es_num(valor):
                return float(valor)
        elif tipo == "booleano":
            if isinstance(valor, bool):
                return valor
        elif tipo == "Cadena":
            if valor is None or isinstance(valor, str):
                return valor
        elif tipo == "caracter":
            if isinstance(valor, str) and len(valor) == 1:
                return valor
        else:
            return valor
        raise ErrorOstia(
            f"no se puede asignar un valor de tipo {nombre_tipo(valor)} "
            f"a algo de tipo {tipo}", linea)

    def condicion(self, nodo, env):
        v = self.eval(nodo, env)
        if not isinstance(v, bool):
            raise ErrorOstia(
                f"la condición debe ser booleano, no {nombre_tipo(v)}", nodo[1])
        return v

    def booleano(self, v, linea):
        if not isinstance(v, bool):
            raise ErrorOstia(f"se esperaba un booleano, no {nombre_tipo(v)}", linea)
        return v

    def x_bloque(self, n, env):
        nuevo = Entorno(env)
        for s in n[2]:
            self.exec(s, nuevo)

    def x_decl(self, n, env):
        for tipo, nombre, expr in n[2]:
            if expr is None:
                valor = DEFECTOS.get(tipo)
            else:
                valor = self.comprobar(tipo, self.eval(expr, env), n[1])
            env.declarar(nombre, tipo, valor, n[1])

    def x_expr(self, n, env):
        self.eval(n[2], env)

    def x_si(self, n, env):
        if self.condicion(n[2], env):
            self.exec(n[3], env)
        elif n[4] is not None:
            self.exec(n[4], env)

    def x_mientras(self, n, env):
        while self.condicion(n[2], env):
            try:
                self.exec(n[3], env)
            except Romper:
                break
            except Continuar:
                continue

    def x_hacer(self, n, env):
        while True:
            try:
                self.exec(n[3], env)
            except Romper:
                break
            except Continuar:
                pass
            if not self.condicion(n[2], env):
                break

    def x_para(self, n, env):
        _, _, init, cond, updates, cuerpo = n
        nuevo = Entorno(env)
        if init is not None:
            self.exec(init, nuevo)
        while cond is None or self.condicion(cond, nuevo):
            try:
                self.exec(cuerpo, nuevo)
            except Romper:
                break
            except Continuar:
                pass
            for u in updates:
                self.eval(u, nuevo)

    def x_devolver(self, n, env):
        valor = None if n[2] is None else self.eval(n[2], env)
        raise Devolver(valor, n[1])

    def x_romper(self, n, env):
        raise Romper(n[1])

    def x_continuar(self, n, env):
        raise Continuar(n[1])

    def x_lanzar(self, n, env):
        v = self.eval(n[2], env)
        if v is None:
            self.lanzar("ExcepcionNula", "no se puede lanzar un valor nulo", n[1])
        if not isinstance(v, ObjetoExcepcion):
            raise ErrorOstia(
                f"solo se pueden lanzar excepciones, no valores de tipo {nombre_tipo(v)}",
                n[1])
        raise Lanzado(v)

    def x_intentar(self, n, env):
        _, linea, cuerpo, capturas, fin = n
        for tipo, _, _, l in capturas:
            if tipo not in JERARQUIA:
                raise ErrorOstia(f"no existe la excepción '{tipo}'", l)
        try:
            try:
                self.exec(cuerpo, env)
            except Lanzado as lz:
                for tipo, nombre, bloque, _ in capturas:
                    if self.es_subclase(lz.obj.tipo, tipo):
                        ent = Entorno(env)
                        ent.declarar(nombre, tipo, lz.obj, linea)
                        self.exec(bloque, ent)
                        break
                else:
                    raise
        finally:
            if fin is not None:
                self.exec(fin, env)

    def e_lit(self, n, env):
        return n[2]

    def e_var(self, n, env):
        entrada = env.buscar(n[2])
        if entrada is not None:
            return entrada[1]
        if n[2] in self.nativos:
            return self.nativos[n[2]]
        raise ErrorOstia(f"no se encontró la variable '{n[3]}'", n[1])

    def e_asig(self, n, env):
        _, linea, nombre, op, expr = n
        entrada = env.buscar(nombre)
        if entrada is None:
            raise ErrorOstia(f"no se encontró la variable '{nombre}'", linea)
        valor = self.eval(expr, env)
        if op != "=":
            valor = self.binario(op[0], entrada[1], valor, linea)
            if entrada[0] in ENTEROS and isinstance(valor, float):
                valor = int(valor)
        entrada[1] = self.comprobar(entrada[0], valor, linea)
        return entrada[1]

    def e_incr(self, n, env):
        _, linea, nombre, delta, prefijo = n
        entrada = env.buscar(nombre)
        if entrada is None:
            raise ErrorOstia(f"no se encontró la variable '{nombre}'", linea)
        antes = entrada[1]
        if not es_num(antes):
            raise ErrorOstia(
                f"no se puede incrementar un valor de tipo {nombre_tipo(antes)}", linea)
        entrada[1] = self.comprobar(entrada[0], antes + delta, linea)
        return entrada[1] if prefijo else antes

    def e_ternario(self, n, env):
        return self.eval(n[3] if self.condicion(n[2], env) else n[4], env)

    def e_log(self, n, env):
        _, linea, op, izq, der = n
        a = self.booleano(self.eval(izq, env), linea)
        if op == "&&" and not a:
            return False
        if op == "||" and a:
            return True
        return self.booleano(self.eval(der, env), linea)

    def e_no(self, n, env):
        return not self.booleano(self.eval(n[2], env), n[1])

    def e_neg(self, n, env):
        v = self.eval(n[2], env)
        if not es_num(v):
            raise ErrorOstia(f"no se puede aplicar '-' a {nombre_tipo(v)}", n[1])
        return -v

    def e_bin(self, n, env):
        a = self.eval(n[3], env)
        b = self.eval(n[4], env)
        return self.binario(n[2], a, b, n[1])

    def e_miembro(self, n, env):
        return self.atributo(self.eval(n[2], env), n[3], n[1])

    def e_nuevo(self, n, env):
        _, linea, nombre, args = n
        if nombre not in JERARQUIA:
            raise ErrorOstia(f"no existe la clase '{nombre}'", linea)
        valores = [self.eval(a, env) for a in args]
        if len(valores) > 1:
            raise ErrorOstia(f"'{nombre}' recibe como máximo un argumento (el mensaje)", linea)
        mensaje = valores[0] if valores else None
        if mensaje is not None and not isinstance(mensaje, str):
            raise ErrorOstia("el mensaje de una excepción debe ser una Cadena", linea)
        return ObjetoExcepcion(nombre, mensaje, linea)

    def e_llamada(self, n, env):
        _, linea, callee, nodos_args = n
        args = [self.eval(a, env) for a in nodos_args]
        if callee[0] == "var":
            nombre = callee[2]
            if nombre in self.funciones:
                return self.llamar_funcion(self.funciones[nombre], args, linea)
            if nombre in self.builtins:
                return self.llamar_nativo(self.builtins[nombre], args, callee[3], linea)
            raise ErrorOstia(f"no se encontró la función '{callee[3]}'", linea)
        f = self.eval(callee, env)
        if not callable(f):
            raise ErrorOstia("esa expresión no se puede llamar como una función", linea)
        nombre = callee[3] if callee[0] == "miembro" else "?"
        return self.llamar_nativo(f, args, nombre, linea)

    def atributo(self, obj, nombre, linea):
        if obj is None:
            self.lanzar("ExcepcionNula",
                        f"no se puede acceder a '{nombre}' porque el valor es nulo", linea)
        if isinstance(obj, ObjetoNativo):
            if nombre in obj.atributos:
                return obj.atributos[nombre]
        elif isinstance(obj, str):
            m = self._metodos_cadena(obj)
            if nombre in m:
                return m[nombre]
        elif isinstance(obj, ObjetoExcepcion):
            m = self._metodos_excepcion(obj)
            if nombre in m:
                return m[nombre]
        raise ErrorOstia(f"un valor de tipo {nombre_tipo(obj)} no tiene '{nombre}'", linea)

    def llamar_nativo(self, f, args, nombre, linea):
        try:
            return f(*args)
        except (Lanzado, ErrorOstia):
            raise
        except IndexError as e:
            self.lanzar("ExcepcionIndice", str(e), linea)
        except ValueError as e:
            self.lanzar("ExcepcionFormatoNumero", str(e), linea)
        except TypeError:
            raise ErrorOstia(f"argumentos incorrectos al llamar a '{nombre}'", linea)

    def llamar_funcion(self, f, args, linea):
        _, _, nombre, params, tipo_ret, cuerpo = f
        if len(args) != len(params):
            raise ErrorOstia(
                f"'{nombre}' espera {len(params)} argumento(s) pero recibió {len(args)}",
                linea)
        ent = Entorno(self.globales)
        for (tipo, pnombre), valor in zip(params, args):
            ent.declarar(pnombre, tipo, self.comprobar(tipo, valor, linea), linea)
        if self.profundidad >= self.LIMITE_PILA:
            self.lanzar("ExcepcionEjecucion",
                        "desbordamiento de pila (recursión demasiado profunda)", linea)
        self.profundidad += 1
        try:
            for s in cuerpo[2]:
                self.exec(s, ent)
        except Devolver as r:
            if tipo_ret == "vacio":
                if r.valor is not None:
                    raise ErrorOstia(f"'{nombre}' es vacio y no puede devolver un valor", r.linea)
                return None
            return self.comprobar(tipo_ret, r.valor, r.linea)
        except (Romper, Continuar) as s:
            raise ErrorOstia(
                "'romper' y 'continuar' solo se pueden usar dentro de un bucle", s.linea)
        finally:
            self.profundidad -= 1
        if tipo_ret != "vacio":
            raise ErrorOstia(f"la función '{nombre}' debe devolver un valor de tipo {tipo_ret}", f[1])
        return None

    def binario(self, op, a, b, linea):
        if op == "+" and (isinstance(a, str) or isinstance(b, str)):
            return texto_de(a) + texto_de(b)
        if op in ("==", "!="):
            r = igual(a, b)
            return r if op == "==" else not r
        if op in ("<", ">", "<=", ">=") and isinstance(a, str) and isinstance(b, str):
            return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]
        if not (es_num(a) and es_num(b)):
            raise ErrorOstia(
                f"no se puede aplicar '{op}' a {nombre_tipo(a)} y {nombre_tipo(b)}", linea)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return self.dividir(a, b, linea)
        if op == "%":
            return self.resto(a, b, linea)
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        return a >= b

    def dividir(self, a, b, linea):
        if es_entero(a) and es_entero(b):
            if b == 0:
                self.lanzar("ExcepcionAritmetica", "/ por cero", linea)
            q = abs(a) // abs(b)
            return q if (a < 0) == (b < 0) else -q
        a, b = float(a), float(b)
        if b == 0:
            if a == 0 or math.isnan(a):
                return math.nan
            negativo = (a < 0) != (math.copysign(1, b) < 0)
            return -math.inf if negativo else math.inf
        return a / b

    def resto(self, a, b, linea):
        if es_entero(a) and es_entero(b):
            if b == 0:
                self.lanzar("ExcepcionAritmetica", "/ por cero", linea)
            r = abs(a) % abs(b)
            return -r if a < 0 else r
        a, b = float(a), float(b)
        if b == 0 or math.isinf(a) or math.isnan(a) or math.isnan(b):
            return math.nan
        return math.fmod(a, b)


def ejecutar_codigo(codigo, salida=None, entrada=None):
    tokens = tokenizar(codigo)
    programa = Parser(tokens).programa()
    Interprete(salida, entrada).ejecutar(programa)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    if len(argv) != 2:
        print("Uso: python ostia.py programa.ostia", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            codigo = f.read()
    except OSError as e:
        print(f"¡Ostia! No se puede abrir '{argv[1]}': {e.strerror}", file=sys.stderr)
        return 2
    sys.setrecursionlimit(20000)
    try:
        ejecutar_codigo(codigo)
    except ErrorOstia as e:
        sys.stdout.flush()
        donde = f"Línea {e.linea}: " if e.linea else ""
        print(f"¡Ostia! {donde}{e.mensaje}", file=sys.stderr)
        return 1
    except Lanzado as e:
        sys.stdout.flush()
        o = e.obj
        print(f"¡Ostia! Excepción no capturada (línea {o.linea}): {o.texto()}",
              file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())