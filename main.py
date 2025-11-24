#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador C-rvicio Militar
Pipeline completo: Código fuente -> Tokens -> AST -> Verificación Semántica

Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
Curso: IC-5701 - Compiladores e Intérpretes
Profesor: Aurelio Sanabria Rodriguez
II Semestre 2025
"""

import argparse
import sys
import json
from typing import Any, Dict

# Importar componentes del compilador
from lexer import Explorador, ExploradorError
from parser import Analizador, ParserError
from verificador import Verificador


# -------------------------
# Utilidades de visualización
# -------------------------

def ast_a_dict(nodo) -> Any:
    """Convierte un nodo AST a diccionario recursivamente (para JSON)"""
    if nodo is None:
        return None
    
    if isinstance(nodo, list):
        return [ast_a_dict(item) for item in nodo]
    
    if hasattr(nodo, '__dict__'):
        resultado = {'_tipo': nodo.__class__.__name__}
        for key, value in nodo.__dict__.items():
            # Omitir campos de posición si son None
            if key in ('fila', 'columna') and value is None:
                continue
            
            if isinstance(value, list):
                resultado[key] = [ast_a_dict(item) for item in value]
            elif hasattr(value, '__dict__'):
                resultado[key] = ast_a_dict(value)
            else:
                resultado[key] = value
        return resultado
    
    return nodo


def ast_a_texto(nodo, indent=0) -> str:
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
        resultado = f"{prefix}{nodo.__class__.__name__}("
        campos = []
        for key, value in nodo.__dict__.items():
            # Omitir campos de posición si son None
            if key in ('fila', 'columna') and value is None:
                continue
            
            if isinstance(value, list):
                if not value:
                    campos.append(f"\n{prefix}  {key}=[]")
                else:
                    campos.append(f"\n{prefix}  {key}=[")
                    for item in value:
                        campos.append("\n" + ast_a_texto(item, indent + 2))
                    campos.append(f"\n{prefix}  ]")
            elif hasattr(value, '__dict__'):
                campos.append(f"\n{prefix}  {key}=")
                campos.append("\n" + ast_a_texto(value, indent + 2))
            else:
                campos.append(f"\n{prefix}  {key}={repr(value)}")
        
        if campos:
            resultado += "".join(campos) + f"\n{prefix}"
        resultado += ")"
        return resultado
    
    return f"{prefix}{repr(nodo)}"


def ast_a_preorden(nodo) -> str:
    """Recorre el AST en preorden y genera una línea por nodo con el formato
    <Tipo, Contenido, Atributos>

    - Tipo: nombre de la clase del nodo
    - Contenido: un valor representativo (nombre, valor, operador, miembro, etc.)
    - Atributos: diccionario reducido con atributos primitivos (fila, columna, tipo, etc.)
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

        # Si no encontramos preferido, tomar el primer primitivo
        if contenido is None:
            for key, val in n.__dict__.items():
                # saltar atributos posicionales cuando buscamos contenido
                if key in ('fila', 'columna'):
                    continue
                if es_primitivo(val):
                    contenido = val
                    break

        # Construir atributos con primitivos (incluye el campo usado como contenido
        # si está presente; también incluye fila/columna si no son None)
        for key, val in n.__dict__.items():
            if not es_primitivo(val):
                continue
            if key in ('fila', 'columna'):
                if val is not None:
                    attrs[key] = val
                continue
            attrs[key] = val

        # Representaciones seguras
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
            # Normalizar contenido para impresión
            contenido_repr = repr(contenido) if contenido is not None else ""
            # Formatear attrs como JSON-like sin espacios innecesarios
            try:
                import json as _json
                attrs_str = _json.dumps(attrs, ensure_ascii=False)
            except Exception:
                attrs_str = str(attrs)

            lines.append(f"<{tipo}, {contenido_repr}, {attrs_str}>")

            # Recurse into fields (lists and nested nodes)
            for key, val in n.__dict__.items():
                if isinstance(val, list):
                    for item in val:
                        visitar(item)
                elif hasattr(val, '__dict__'):
                    visitar(val)
                # ignorar primitivos (ya mostrados)
            return

        # Fallback: imprimir el valor repr del nodo
        lines.append("<" + repr(n) + ", , {}>")
        return

    visitar(nodo)
    return "\n".join(lines)


def tokens_a_tabla(tokens) -> str:
    """Genera una tabla formateada de tokens"""
    if not tokens:
        return "No hay tokens para mostrar."
    
    filas = [("Lexema", "Tipo", "Atributos")]
    for t in tokens:
        attrs = json.dumps(t.atributos, ensure_ascii=False)
        filas.append((t.lexema, t.tipo, attrs))
    
    # Calcular anchos de columna
    anchos = [max(len(str(fila[i])) for fila in filas) for i in range(len(filas[0]))]
    
    lineas = []
    for i, fila in enumerate(filas):
        linea = " | ".join(str(val).ljust(anchos[j]) for j, val in enumerate(fila))
        lineas.append(linea)
        if i == 0:
            lineas.append("-+-".join("-" * w for w in anchos))
    
    return "\n".join(lineas)


# -------------------------
# Pipeline del compilador
# -------------------------

def compilar(codigo_fuente: str, mostrar_tokens: bool = False, 
             tolerante: bool = False, verbose: bool = False,
             verificar: bool = True) -> Dict[str, Any]:
    """
    Pipeline completo: Código -> Tokens -> AST -> Verificación
    
    Args:
        codigo_fuente: Código fuente en C-rvicio Militar
        mostrar_tokens: Si True, imprime los tokens generados
        tolerante: Si True, el lexer genera tokens ERROR en vez de fallar
        verbose: Si True, imprime información de cada fase
        verificar: Si True, ejecuta verificación semántica
    
    Returns:
        Dict con 'exito', 'tokens', 'ast', 'errores_semanticos', 'error'
    """
    resultado = {
        'exito': False,
        'tokens': None,
        'ast': None,
        'errores_semanticos': None,
        'error': None
    }
    
    # -------------------------
    # FASE 1: Análisis Léxico
    # -------------------------
    if verbose:
        print("=" * 60)
        print("FASE 1: Análisis Léxico (Explorador)")
        print("=" * 60)
    
    explorador = Explorador(con_nuevaslineas=False, tolerante=tolerante)
    
    try:
        tokens = explorador.tokenizar(codigo_fuente)
        resultado['tokens'] = tokens
        
        if verbose:
            print(f"✓ Tokenización exitosa: {len(tokens)} tokens generados")
        
        if mostrar_tokens:
            print("\n--- Tokens generados ---")
            print(tokens_a_tabla(tokens))
            print()
        
    except ExploradorError as e:
        resultado['error'] = f"Error léxico: {e}"
        return resultado
    
    # -------------------------
    # FASE 2: Análisis Sintáctico
    # -------------------------
    if verbose:
        print("\n" + "=" * 60)
        print("FASE 2: Análisis Sintáctico (Parser)")
        print("=" * 60)
    
    analizador = Analizador(tokens)
    
    try:
        ast = analizador.parsear()
        resultado['ast'] = ast
        
        if verbose:
            print("✓ Parsing exitoso: AST generado correctamente")
        
    except ParserError as e:
        resultado['error'] = f"Error sintáctico: {e}"
        return resultado
    
    # -------------------------
    # FASE 3: Verificación Semántica
    # -------------------------
    if verificar:
        if verbose:
            print("\n" + "=" * 60)
            print("FASE 3: Verificación Semántica")
            print("=" * 60)
        
        verificador = Verificador()
        errores = verificador.verificar(ast)
        resultado['errores_semanticos'] = errores
        
        if errores:
            if verbose:
                print(f"✗ Se encontraron {len(errores)} errores semánticos")
            resultado['error'] = f"Errores semánticos: {len(errores)} encontrados"
            return resultado
        
        if verbose:
            print("✓ Verificación exitosa: sin errores semánticos")
    
    resultado['exito'] = True
    return resultado


# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compilador C-rvicio Militar (Lexer + Parser + Verificador)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py programa.crv                  # Compila y verifica
  python main.py programa.crv --json           # AST en formato JSON
  python main.py programa.crv --tokens         # Muestra tokens
  python main.py programa.crv --verbose        # Modo detallado
  python main.py programa.crv --no-verificar   # Solo lexer + parser
  python main.py -                             # Lee desde stdin
        """
    )
    
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente (.crv), o '-' para stdin")
    
    # Opciones de salida
    parser.add_argument("--json", action="store_true",
                        help="Imprimir AST en formato JSON")
    parser.add_argument("--tokens", action="store_true",
                        help="Mostrar tokens generados por el lexer")
    parser.add_argument("--solo-tokens", action="store_true",
                        help="Solo ejecutar el lexer (no parsear)")
    parser.add_argument("--preorden", action="store_true",
                        help="Imprimir AST en preorden: <Tipo, Contenido, Atributos>")
    
    # Opciones de compilación
    parser.add_argument("--tolerant", action="store_true",
                        help="Modo tolerante: el lexer genera tokens ERROR")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Modo detallado: mostrar información de cada fase")
    parser.add_argument("--no-verificar", action="store_true",
                        help="Omitir verificación semántica")
    
    args = parser.parse_args()
    
    # Leer código fuente
    if args.fuente == "-":
        if args.verbose:
            print("Leyendo desde stdin... (Ctrl+D para terminar)")
        codigo_fuente = sys.stdin.read()
    else:
        try:
            with open(args.fuente, "r", encoding="utf-8") as f:
                codigo_fuente = f.read()
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{args.fuente}'", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error al leer archivo: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Solo lexer
    if args.solo_tokens:
        explorador = Explorador(con_nuevaslineas=False, tolerante=args.tolerant)
        try:
            tokens = explorador.tokenizar(codigo_fuente)
            print(tokens_a_tabla(tokens))
            sys.exit(0)
        except ExploradorError as e:
            print(f"Error léxico: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Pipeline completo
    resultado = compilar(
        codigo_fuente, 
        mostrar_tokens=args.tokens,
        tolerante=args.tolerant,
        verbose=args.verbose,
        verificar=not args.no_verificar
    )
    
    # Manejar errores
    if not resultado['exito']:
        print(f"\n✗ {resultado['error']}", file=sys.stderr)
        
        # Mostrar errores semánticos si existen
        if resultado['errores_semanticos']:
            print(f"\nSe encontraron {len(resultado['errores_semanticos'])} errores semánticos:\n", file=sys.stderr)
            for error in resultado['errores_semanticos']:
                print(f"  • {error}", file=sys.stderr)
        
        sys.exit(1)
    
    # Imprimir AST
    if args.verbose:
        print("\n" + "=" * 60)
        print("RESULTADO: AST Generado")
        print("=" * 60)
    
    if args.json:
        ast_dict = ast_a_dict(resultado['ast'])
        print(json.dumps(ast_dict, ensure_ascii=False, indent=2))
    else:
        if args.preorden:
            print(ast_a_preorden(resultado['ast']))
        else:
            print(ast_a_texto(resultado['ast']))
    
    if args.verbose:
        print("\n✓ Compilación exitosa")


if __name__ == "__main__":
    main()