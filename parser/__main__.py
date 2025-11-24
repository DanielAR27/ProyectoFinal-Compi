#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI para el Parser de C-rvicio Militar
Permite visualizar el AST generado
"""

import argparse
import sys
import json
from dataclasses import asdict
from lexer import Explorador, ExploradorError
from parser import Analizador, ParserError


# -------------------------
# Utilidades de visualización
# -------------------------

def ast_a_dict(nodo):
    """Convierte un nodo AST a diccionario recursivamente"""
    if nodo is None:
        return None
    
    if isinstance(nodo, list):
        return [ast_a_dict(item) for item in nodo]
    
    if hasattr(nodo, '__dict__'):
        resultado = {'tipo': nodo.__class__.__name__}
        for key, value in nodo.__dict__.items():
            if isinstance(value, list):
                resultado[key] = [ast_a_dict(item) for item in value]
            elif hasattr(value, '__dict__'):
                resultado[key] = ast_a_dict(value)
            else:
                resultado[key] = value
        return resultado
    
    return nodo


def ast_a_texto(nodo, indent=0):
    """Convierte un nodo AST a texto legible con indentación"""
    prefix = "  " * indent
    
    if nodo is None:
        return f"{prefix}None"
    
    if isinstance(nodo, list):
        if not nodo:
            return f"{prefix}[]"
        resultado = f"{prefix}[\n"
        for item in nodo:
            resultado += ast_a_texto(item, indent + 1) + "\n"
        resultado += f"{prefix}]"
        return resultado
    
    if hasattr(nodo, '__dict__'):
        resultado = f"{prefix}{nodo.__class__.__name__}(\n"
        for key, value in nodo.__dict__.items():
            if isinstance(value, list):
                resultado += f"{prefix}  {key}=[\n"
                for item in value:
                    resultado += ast_a_texto(item, indent + 2) + "\n"
                resultado += f"{prefix}  ]\n"
            elif hasattr(value, '__dict__'):
                resultado += f"{prefix}  {key}=\n"
                resultado += ast_a_texto(value, indent + 2) + "\n"
            else:
                resultado += f"{prefix}  {key}={repr(value)}\n"
        resultado += f"{prefix})"
        return resultado
    
    return f"{prefix}{repr(nodo)}"


def ast_a_preorden(nodo):
    """Genera una representación en preorden del AST, una línea por nodo:
    <Tipo, Contenido, Atributos>
    """
    lines = []

    def es_primitivo(v):
        return isinstance(v, (str, int, float, bool)) or v is None

    def resumen_nodo(n):
        if n is None:
            return ("None", {})
        if not hasattr(n, '__dict__'):
            return (repr(n), {})

        # Buscar contenido principal (evitar elegir fila/columna como contenido)
        contenido = None
        attrs = {}
        preferidos = ('nombre', 'valor', 'operador', 'miembro', 'tipo')
        for key, val in n.__dict__.items():
            if key in preferidos and es_primitivo(val):
                contenido = val
                break

        if contenido is None:
            for key, val in n.__dict__.items():
                if key in ('fila', 'columna'):
                    continue
                if es_primitivo(val):
                    contenido = val
                    break

        # Construir atributos: incluir primitivos (incluye el contenido si existe)
        for key, val in n.__dict__.items():
            if not es_primitivo(val):
                continue
            if key in ('fila', 'columna'):
                if val is not None:
                    attrs[key] = val
                continue
            attrs[key] = val

        return (contenido, attrs)

    def visitar(n):
        if n is None:
            lines.append("<None, None, {}>")
            return

        if isinstance(n, list):
            for item in n:
                visitar(item)
            return

        if hasattr(n, '__dict__'):
            tipo = n.__class__.__name__
            contenido, attrs = resumen_nodo(n)
            contenido_repr = repr(contenido) if contenido is not None else ""
            try:
                import json as _json
                attrs_str = _json.dumps(attrs, ensure_ascii=False)
            except Exception:
                attrs_str = str(attrs)
            lines.append(f"<{tipo}, {contenido_repr}, {attrs_str}>")

            for key, val in n.__dict__.items():
                if isinstance(val, list):
                    for item in val:
                        visitar(item)
                elif hasattr(val, '__dict__'):
                    visitar(val)
            return

    visitar(nodo)
    return "\n".join(lines)


# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Parser para C-rvicio Militar: Tokens -> AST"
    )
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente a parsear, o '-' para stdin (default: '-')")
    parser.add_argument("--json", action="store_true",
                        help="Imprimir AST como JSON")
    parser.add_argument("--tolerant", action="store_true",
                        help="Modo tolerante en el lexer (genera tokens ERROR)")
    parser.add_argument("--preorden", action="store_true",
                        help="Imprimir AST en preorden: un nodo por línea en formato <Tipo, Contenido, Atributos>")
    
    args = parser.parse_args()
    
    # Leer texto
    if args.fuente == "-" or args.fuente is None:
        source = sys.stdin.read()
    else:
        with open(args.fuente, "r", encoding="utf-8") as f:
            source = f.read()
    
    # Fase 1: Lexer
    explorador = Explorador(con_nuevaslineas=False, tolerante=args.tolerant)
    try:
        tokens = explorador.tokenizar(source)
    except ExploradorError as e:
        print(f"Error léxico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fase 2: Parser
    analizador = Analizador(tokens)
    try:
        ast = analizador.parsear()
    except ParserError as e:
        print(f"Error sintáctico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Imprimir resultado
    if args.json:
        ast_dict = ast_a_dict(ast)
        print(json.dumps(ast_dict, ensure_ascii=False, indent=2))
    else:
        if args.preorden:
            print(ast_a_preorden(ast))
        else:
            print(ast_a_texto(ast))


if __name__ == "__main__":
    main()