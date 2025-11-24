#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI para el Explorador de C-rvicio Militar
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

import argparse
import json
import sys
from dataclasses import asdict
from typing import Iterable
from token_crvicio import Token
from lexer import Explorador, ExploradorError

# -------------------------
# Utilidades de salida
# -------------------------

# Genera un texto con los tokens, cada uno en formato:
# <"Tipo de componente léxico", "Texto del componente léxico", "Atributos adicionales del componente">
def tokens_a_texto(tokens: Iterable[Token]) -> str:
    lineas = []
    for t in tokens:
        attrs = json.dumps(t.atributos, ensure_ascii=False)
        lineas.append(f'<{t.tipo}, {t.lexema}, {attrs}>')
    return "\n".join(lineas)


def tokens_a_tabla(tokens: Iterable[Token]) -> str:
    # Tabla simple alineada
    filas = [("Lexema", "Tipo", "Atributos")]
    for t in tokens:
        attrs = json.dumps(t.atributos, ensure_ascii=False)
        filas.append((t.lexema, t.tipo, attrs))

    # Ancho de columnas
    anchos = [max(len(fila[i]) for fila in filas) for i in range(len(filas[0]))]
    lineas = []
    for i, fila in enumerate(filas):
        linea = " | ".join(val.ljust(anchos[j]) for j, val in enumerate(fila))
        lineas.append(linea)
        if i == 0:
            lineas.append("-+-".join("-" * w for w in anchos))
    return "\n".join(lineas)

# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Explorador (Explorador) para C-rvicio Militar: Texto -> Regex -> Lista"
    )
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente a leer, o '-' para stdin (default: '-')")
    parser.add_argument("--json", action="store_true",
                        help="Imprimir salida como JSON")
    parser.add_argument("--tabla", action="store_true",
                        help="Imprimir salida como tabla (ignorado si --json está presente)")
    parser.add_argument("--include-nl", action="store_true",
                        help="Incluir tokens NL (saltos de línea)")
    parser.add_argument("--tolerant", action="store_true",
                        help="En lugar de fallar, genera tokens ERROR para caracteres desconocidos")

    args = parser.parse_args()

    # Leer texto
    if args.fuente == "-" or args.fuente is None:
        source = sys.stdin.read()
    else:
        with open(args.fuente, "r", encoding="utf-8") as f:
            source = f.read()

    exp = Explorador(con_nuevaslineas=args.include_nl, tolerante=args.tolerant)
    try:
        tokens = exp.tokenizar(source)
    except ExploradorError as e:
        print(f"Error léxico: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        out = [asdict(t) for t in tokens]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.tabla:
        print(tokens_a_tabla(tokens))
    else:
        print(tokens_a_texto(tokens))


if __name__ == "__main__":
    main()