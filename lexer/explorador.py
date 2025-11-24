#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador (Explorador) para el lenguaje C-rvicio Militar
Texto -> Regex -> Lista de tokens
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)

Notas:
- Comentarios permitidos: // ... y /* ... */
- Preferencia: comentarios sin emojis ni adornos.
"""

import re
from typing import List, Dict, Tuple, Any
from token_crvicio import Token

# -------------------------
# Definiciones básicas
# -------------------------

# Palabras clave del lenguaje
PALABRAS_CLAVE = {
    # contenedores / estructura
    "ejercito", "global", "var", "mision", "severidad", "estricto", "advertencia",
    "revisar", "ejecutar", "confirmar",
    # control de flujo
    "si", "por", "defecto", "estrategia", "atacar", "mientras",
    "retirada", "con", "abortar", "avanzar",
    # literales lógicos y nulo
    "afirmativo", "negativo", "nulo",
    # misiones de ambiente (omitidas por ahora ya que son más identificadores)
    # "reportar", "recibir", "clasificarNumero", "clasificarMensaje", "azar",
    # "aRangoSuperior", "aRangoInferior", "acampar", "calibre", "truncar",
}

# Operadores multi-caracter que deben probarse antes que los de 1 caracter
MULTI_OPS = [
    r"\|\|", r"&&", r"==", r"!=", r"<=", r">=", r"\+=",
    r"-=", r"\*=", r"/=", r"%="
]

# Operadores de 1 caracter
SINGLE_OPS = [
    r"=", r"\+", r"-", r"\*", r"/", r"%", r"<", r">", r"!"
]

# Símbolos de puntuación / separación
PUNCT = [
    r"\(", r"\)", r"\{", r"\}", r"\[", r"\]", r"\.", r",", r":"
]

# Se formulan Regex no capturantes para un análisis posterior
OPS_RE = "(?:" + "|".join(MULTI_OPS + SINGLE_OPS) + ")"
PUNCT_RE = "(?:" + "|".join(PUNCT) + ")"

# Regex de tokens primarios
# Orden es importante: primero comentarios y espacios, luego NL, luego tokens más largos, etc.
TOKEN_SPEC = [
    # Comentarios
    ("COMENT_BLOQ", r"/\*(?:[^*]|\*[^/])*\*/"),
    ("COMENT_LINEA", r"//[^\n]*(?:\r?\n)?"),

    # Espacios (excepto saltos de línea)
    ("ESPACIO", r"[ \t\f\v\r]+"),

    # Saltos de línea (NL) — opcionalmente se pueden emitir
    ("NL", r"(?:\r?\n)+"),

    # Cadenas (doble comilla, sin saltos de línea)
    ("CADENA", r"\"[^\"\n]*\""),

    # Números (flotantes primero, luego enteros)
    ("NUM_FLOTANTE", r"[0-9]+\.[0-9]+"),
    ("NUM_ENTERO", r"[0-9]+"),

    # Operadores
    ("OPERADOR",     OPS_RE),   

    # Símbolos
    ("SIMBOLO",      PUNCT_RE),

    # Identificadores
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
]

MASTER_REGEX = "|".join(f"(?P<{nombre}>{patron})" for (nombre, patron) in TOKEN_SPEC)
MASTER_RE = re.compile(MASTER_REGEX)

# -------------------------
# Excepciones
# -------------------------

class ExploradorError(Exception):
    pass

# -------------------------
# Explorador
# -------------------------

class Explorador:
    def __init__(self, con_nuevaslineas: bool = False, tolerante: bool = False) -> None:
        self.con_nuevaslineas = con_nuevaslineas
        self.tolerante = tolerante

    def tokenizar(self, texto: str) -> List[Token]:
        tokens: List[Token] = []
        linea = 1
        linea_inicio = 0
        pos = 0
        longitud = len(texto)

        for m in MASTER_RE.finditer(texto):
            inicio, fin = m.start(), m.end()
            if inicio != pos:
                # Hay caracteres no reconocidos entre el último match y este
                bad_chunk = texto[pos:inicio]
                # Si sólo son espacios no contemplados, actualizamos línea/columna correctamente
                # pero en general tratamos esto como error.
                ok, nl_count, last_nl = self._consume_desconocido(bad_chunk, linea, pos - linea_inicio, texto, tokens)
                if not ok:
                    col = pos - linea_inicio + 1
                    excerpt = bad_chunk[:20].replace("\n", "\\n")
                    msg = f"Carácter no reconocido en fila {linea}, columna {col}: '{excerpt}'"
                    if self.tolerante:
                        attrs = {"fila": linea, "columna": col, "motivo": "desconocido"}
                        tokens.append(Token(bad_chunk, "ERROR", attrs))
                    else:
                        raise ExploradorError(msg)

                # Si _consume_desconocido reportó saltos de línea, actualizamos contadores
                if ok and nl_count:
                    linea += nl_count
                    if last_nl != -1:
                        linea_inicio = pos + last_nl + 1

            tipo = m.lastgroup
            lexema = m.group(tipo)

            # Posición del token
            tok_linea = linea
            tok_col = m.start() - linea_inicio + 1

            # Actualiza contadores si es NL
            if tipo == "NL":
                if self.con_nuevaslineas:
                    attrs = {"fila": tok_linea, "columna": tok_col}
                    tokens.append(Token(lexema, "NL", attrs))
                # contar saltos
                nl_count = lexema.count("\n")
                linea += nl_count
                # último \n redefine inicio de línea
                last_nl = lexema.rfind("\n")
                if last_nl != -1:
                    linea_inicio = m.start() + last_nl + 1

            elif tipo in ("ESPACIO", "COMENT_LINEA", "COMENT_BLOQ"):
                # Ignorar, pero contabilizar saltos de línea que puedan contener
                nl_count = lexema.count("\n")
                if nl_count:
                    linea += nl_count
                    last_nl = lexema.rfind("\n")
                    if last_nl != -1:
                        linea_inicio = m.start() + last_nl + 1

            else:
                # Clasificar y construir atributos
                tipo, attrs = self._clasificar(tipo, lexema)
                attrs.update({"fila": tok_linea, "columna": tok_col})
                tokens.append(Token(lexema, tipo, attrs))

            pos = fin

        # Sobra texto sin reconocer al final
        if pos < longitud:
            bad_chunk = texto[pos:longitud]
            ok, nl_count, last_nl = self._consume_desconocido(bad_chunk, linea, pos - linea_inicio, texto, tokens)
            if not ok:
                col = pos - linea_inicio + 1
                excerpt = bad_chunk[:20].replace("\n", "\\n")
                msg = f"Carácter no reconocido al final en fila {linea}, columna {col}: '{excerpt}'"
                if self.tolerante:
                    attrs = {"fila": linea, "columna": col, "motivo": "desconocido"}
                    tokens.append(Token(bad_chunk, "ERROR", attrs))
                else:
                    raise ExploradorError(msg)
            else:
                if nl_count:
                    linea += nl_count
                    if last_nl != -1:
                        linea_inicio = pos + last_nl + 1

        return tokens

    def _clasificar(self, tipo: str, lexema: str) -> Tuple[str, Dict[str, Any]]:
        """Devuelve (tipo, atributos) normalizados para la tabla Lexema/Tipo/Atributos."""
        if tipo == "IDENT":
            # Literales especiales: booleanos y nulo
            if lexema == "afirmativo":
                return ("LIT_BOOLEANO", {})
            if lexema == "negativo":
                return ("LIT_BOOLEANO", {})
            if lexema == "nulo":
                return ("LIT_NULO", {})

            if lexema in PALABRAS_CLAVE:
                return ("PALABRA_CLAVE", {})
            return ("IDENT", {})

        if tipo == "NUM_ENTERO":
            return ("NUM_ENTERO", {})

        if tipo == "NUM_FLOTANTE":
            return ("NUM_FLOTANTE", {})

        if tipo == "CADENA":
            return ("CADENA", {"valor": lexema[1:-1]})  # sin comillas

        if tipo == "OPERADOR":
            return ("OPERADOR", {})

        if tipo == "SIMBOLO":
            return ("SIMBOLO", {})

        # Fallback (No se sabe con exactitud)
        return (tipo, {})

    def _consume_desconocido(self, chunk: str, linea: int, col0: int, texto: str, tokens: List[Token]) -> Tuple[bool, int, int]:
        """
        Intenta consumir secuencias desconocidas formadas por espacios o controla NL manualmente.
        Devuelve (ok, nl_count, last_nl_pos):
        - ok: True si sólo hay espacios y saltos de línea, False si hay otros
        - nl_count: número de saltos de línea en el chunk
        - last_nl_pos: posición del último salto de línea en el chunk, o -1 si no hay
        """
        if not chunk:
            return (True, 0, -1)

        # Si contiene caracteres imprimibles no-espacio distintos a \n, se trata como error
        if re.search(r"[^\s]", chunk.replace("\n", "")):
            return (False, 0, -1)

        # Sólo espacios y saltos de línea: devolver cantidad de NL y la posición del último \n
        nl_count = chunk.count("\n")
        last_nl = chunk.rfind("\n") if nl_count else -1
        return (True, nl_count, last_nl)