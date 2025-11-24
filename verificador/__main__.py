#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI para el Verificador de C-rvicio Militar
Permite verificar semánticamente el AST generado
"""

import argparse
import sys
import json
from lexer import Explorador, ExploradorError
from parser import Analizador, ParserError
from verificador import Verificador, VerificadorError


def main():
    parser = argparse.ArgumentParser(
        description="Verificador semántico para C-rvicio Militar: AST → Verificación"
    )
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente a verificar, o '-' para stdin (default: '-')")
    parser.add_argument("--tolerant", action="store_true",
                        help="Modo tolerante en el lexer (genera tokens ERROR)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Modo detallado: muestra información de cada fase")
    parser.add_argument("--show-ast", action="store_true",
                        help="Mostrar el AST antes de verificar")
    
    args = parser.parse_args()
    
    # Leer texto
    if args.fuente == "-" or args.fuente is None:
        source = sys.stdin.read()
    else:
        try:
            with open(args.fuente, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{args.fuente}'", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error al leer archivo: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Fase 1: Lexer
    if args.verbose:
        print("=" * 60)
        print("FASE 1: Análisis Léxico")
        print("=" * 60)
    
    explorador = Explorador(con_nuevaslineas=False, tolerante=args.tolerant)
    try:
        tokens = explorador.tokenizar(source)
        if args.verbose:
            print(f"✓ Tokenización exitosa: {len(tokens)} tokens generados")
    except ExploradorError as e:
        print(f"Error léxico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fase 2: Parser
    if args.verbose:
        print("\n" + "=" * 60)
        print("FASE 2: Análisis Sintáctico")
        print("=" * 60)
    
    analizador = Analizador(tokens)
    try:
        ast = analizador.parsear()
        if args.verbose:
            print("✓ Parsing exitoso: AST generado")
        
        if args.show_ast:
            print("\nAST generado:")
            print(ast)
            print()
    except ParserError as e:
        print(f"Error sintáctico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fase 3: Verificador
    if args.verbose:
        print("\n" + "=" * 60)
        print("FASE 3: Verificación Semántica")
        print("=" * 60)
    
    verificador = Verificador()
    errores = verificador.verificar(ast)
    
    if errores:
        print(f"\nSe encontraron {len(errores)} errores semánticos:\n", file=sys.stderr)
        for error in errores:
            print(f"  • {error}", file=sys.stderr)
        sys.exit(1)
    else:
        if args.verbose:
            print("✓ Verificación exitosa: sin errores semánticos")
        print("\n✓ Código semánticamente correcto")
        sys.exit(0)


if __name__ == "__main__":
    main()