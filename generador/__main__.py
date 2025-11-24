#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI para el Generador de C-rvicio Militar
Permite generar código Python desde archivos .crv
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

import argparse
import sys
from lexer import Explorador, ExploradorError
from parser import Analizador, ParserError
from verificador import Verificador
from generador import Generador, GeneradorError


def main():
    parser = argparse.ArgumentParser(
        description="Generador de código para C-rvicio Militar: AST → Python"
    )
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente a compilar, o '-' para stdin (default: '-')")
    parser.add_argument("-o", "--output", 
                        help="Archivo de salida (.py). Si no se especifica, imprime a stdout")
    parser.add_argument("--no-verificar", action="store_true",
                        help="Omitir verificación semántica (no recomendado)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Modo detallado: muestra información de cada fase")
    parser.add_argument("--ejecutar", action="store_true",
                        help="Ejecutar el código generado inmediatamente")
    
    args = parser.parse_args()
    
    # Leer código fuente
    if args.fuente == "-" or args.fuente is None:
        if args.verbose:
            print("Leyendo desde stdin...", file=sys.stderr)
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
        print("=" * 60, file=sys.stderr)
        print("FASE 1: Análisis Léxico", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    
    explorador = Explorador(con_nuevaslineas=False, tolerante=False)
    try:
        tokens = explorador.tokenizar(source)
        if args.verbose:
            print(f"✓ Tokenización exitosa: {len(tokens)} tokens", file=sys.stderr)
    except ExploradorError as e:
        print(f"Error léxico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fase 2: Parser
    if args.verbose:
        print("\n" + "=" * 60, file=sys.stderr)
        print("FASE 2: Análisis Sintáctico", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    
    analizador = Analizador(tokens)
    try:
        ast = analizador.parsear()
        if args.verbose:
            print("✓ Parsing exitoso: AST generado", file=sys.stderr)
    except ParserError as e:
        print(f"Error sintáctico: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fase 3: Verificador (opcional)
    if not args.no_verificar:
        if args.verbose:
            print("\n" + "=" * 60, file=sys.stderr)
            print("FASE 3: Verificación Semántica", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
        
        verificador = Verificador()
        errores = verificador.verificar(ast)
        
        if errores:
            print(f"\nSe encontraron {len(errores)} errores semánticos:\n", file=sys.stderr)
            for error in errores:
                print(f"  • {error}", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print("✓ Verificación exitosa: sin errores semánticos", file=sys.stderr)
    
    # Fase 4: Generador
    if args.verbose:
        print("\n" + "=" * 60, file=sys.stderr)
        print("FASE 4: Generación de Código", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    
    generador = Generador()
    try:
        codigo_python = generador.generar(ast)
        if args.verbose:
            print("✓ Código Python generado exitosamente", file=sys.stderr)
    except GeneradorError as e:
        print(f"Error en generación: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Salida del código generado
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(codigo_python)
            if args.verbose:
                print(f"\n✓ Código guardado en: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error al escribir archivo: {e}", file=sys.stderr)
            sys.exit(1)
    elif not args.ejecutar:
        # Solo imprimir a stdout si NO se va a ejecutar
        print(codigo_python)
    
    # Ejecutar si se solicita
    if args.ejecutar:
        if args.verbose:
            print("\n" + "=" * 60, file=sys.stderr)
            print("EJECUTANDO CÓDIGO GENERADO", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print("", file=sys.stderr)
        
        try:
            exec(codigo_python)
        except Exception as e:
            print(f"\nError durante la ejecución: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    
    if args.verbose and not args.ejecutar:
        print("\n✓ Compilación completa", file=sys.stderr)


if __name__ == "__main__":
    main()