#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de código Python para C-rvicio Militar
Transpila AST verificado a código Python ejecutable
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from typing import Any, List, Optional
from ast_crvicio import *


class GeneradorError(Exception):
    """Excepción para errores durante la generación de código"""
    pass


class Generador:
    """
    Transpilador de AST a código Python.
    Recorre el AST verificado y genera código Python equivalente.
    """
    
    def __init__(self):
        self.nivel_indentacion = 0
        self.codigo_generado = []
        self.en_mision = False
        self.nombre_mision_actual = None
    
    def generar(self, ast: Programa) -> str:
        """
        Punto de entrada principal.
        Genera código Python completo desde el AST.
        
        Args:
            ast: Nodo raíz del programa (Programa)
        
        Returns:
            Código Python como string
        """
        self.codigo_generado = []
        self.nivel_indentacion = 0
        
        # Header: imports y setup del runtime
        self._generar_header()
        
        # Generar el cuerpo del programa
        self._generar_programa(ast)
        
        # Footer: punto de entrada principal
        self._generar_footer()
        
        return "\n".join(self.codigo_generado)
    
    def _generar_header(self):
        """Genera el encabezado del archivo Python (imports, runtime)"""
        self._emit("#!/usr/bin/env python3")
        self._emit("# -*- coding: utf-8 -*-")
        self._emit('"""')
        self._emit("Código generado por el compilador C-rvicio Militar")
        self._emit('"""')
        self._emit("")
        self._emit("import sys")
        self._emit("import random")
        self._emit("import math")
        self._emit("import time")
        self._emit("")
        self._emit("# ===== RUNTIME: Misiones Ambiente =====")
        self._emit("")
        
        # Definir funciones ambiente inline
        self._emit("def reportar(mensaje):")
        self._emit("    print(mensaje)")
        self._emit("")
        
        self._emit("def recibir(prompt=''):")
        self._emit("    if prompt:")
        self._emit("        return input(prompt)")
        self._emit("    return input()")
        self._emit("")
        
        self._emit("def clasificarNumero(texto):")
        self._emit("    try:")
        self._emit("        return int(texto)")
        self._emit("    except (ValueError, TypeError):")
        self._emit("        return 0")
        self._emit("")
        
        self._emit("def clasificarMensaje(valor):")
        self._emit("    return str(valor)")
        self._emit("")
        
        self._emit("def azar():")
        self._emit("    return random.randint(0, 2147483647)")
        self._emit("")
        
        self._emit("def aRangoSuperior(num):")
        self._emit("    return math.ceil(num)")
        self._emit("")
        
        self._emit("def aRangoInferior(num):")
        self._emit("    return math.floor(num)")
        self._emit("")
        
        self._emit("def acampar(ms):")
        self._emit("    time.sleep(ms / 1000.0)")
        self._emit("")
        
        self._emit("def calibre(texto):")
        self._emit("    return len(texto)")
        self._emit("")
        
        self._emit("def truncar(num):")
        self._emit("    return math.trunc(num)")
        self._emit("")
        
        self._emit("# ===== CÓDIGO DEL PROGRAMA =====")
        self._emit("")
    
    def _generar_footer(self):
        """Genera el pie del archivo (punto de entrada si es necesario)"""
        # No necesitamos main() explícito, el código se ejecuta secuencialmente
        pass
    
    def _generar_programa(self, nodo: Programa):
        """Genera el cuerpo principal del programa"""
        for item in nodo.cuerpo:
            if isinstance(item, EjercitoDecl):
                self._generar_ejercito(item)
            elif isinstance(item, DefMision):
                self._generar_def_mision(item)
            elif isinstance(item, DeclaracionGlobal):
                self._generar_declaracion_global(item)
            elif isinstance(item, Sentencia):
                self._generar_sentencia(item)
            # Ignorar NL (saltos de línea ya manejados)
    
    def _generar_ejercito(self, nodo: EjercitoDecl):
        """Genera código para un ejército (namespace/módulo)"""
        # En Python, un ejército se traduce a una clase
        self._emit(f"class {nodo.nombre}:")
        self._indent()
        
        if not nodo.cuerpo:
            self._emit("pass")
        else:
            tiene_contenido = False
            for item in nodo.cuerpo:
                if isinstance(item, DefMision):
                    self._generar_def_mision(item, es_metodo=True)
                    tiene_contenido = True
                elif isinstance(item, DeclaracionGlobal):
                    # Variables globales del ejército -> atributos de clase
                    var_name = item.nombre
                    if item.valor:
                        valor_code = self._generar_expresion(item.valor)
                        self._emit(f"{var_name} = {valor_code}")
                    else:
                        self._emit(f"{var_name} = None")
                    tiene_contenido = True
                elif isinstance(item, Sentencia):
                    # Sentencias a nivel de clase (raro pero permitido)
                    self._generar_sentencia(item)
                    tiene_contenido = True
            
            if not tiene_contenido:
                self._emit("pass")
        
        self._dedent()
        self._emit("")
    
    def _generar_def_mision(self, nodo: DefMision, es_metodo: bool = False):
        """Genera código para una definición de misión (función)"""
        self.en_mision = True
        self.nombre_mision_actual = nodo.nombre
        
        # Parámetros
        if es_metodo:
            params = ["self"] + nodo.parametros
        else:
            params = nodo.parametros
        
        params_str = ", ".join(params) if params else ""
        self._emit(f"def {nodo.nombre}({params_str}):")
        self._indent()
        
        # Sección revisar (precondiciones)
        if nodo.seccion_revisar:
            self._emit("# Sección revisar: precondiciones")
            for condicion in nodo.seccion_revisar.condiciones:
                cond_code = self._generar_expresion(condicion)
                if nodo.severidad == "estricto":
                    self._emit(f"assert {cond_code}, 'Precondición falló en {nodo.nombre}'")
                else:  # advertencia o None
                    self._emit(f"if not ({cond_code}):")
                    self._indent()
                    self._emit(f"print('Advertencia: precondición falló en {nodo.nombre}', file=sys.stderr)")
                    self._dedent()
            self._emit("")
        
        # Sección ejecutar (cuerpo)
        tiene_contenido = False
        for sentencia in nodo.seccion_ejecutar.sentencias:
            self._generar_sentencia(sentencia)
            tiene_contenido = True
        
        if not tiene_contenido:
            self._emit("pass")
        
        # Sección confirmar (postcondiciones)
        if nodo.seccion_confirmar:
            self._emit("")
            self._emit("# Sección confirmar: postcondiciones")
            for condicion in nodo.seccion_confirmar.condiciones:
                cond_code = self._generar_expresion(condicion)
                if nodo.severidad == "estricto":
                    self._emit(f"assert {cond_code}, 'Postcondición falló en {nodo.nombre}'")
                else:
                    self._emit(f"if not ({cond_code}):")
                    self._indent()
                    self._emit(f"print('Advertencia: postcondición falló en {nodo.nombre}', file=sys.stderr)")
                    self._dedent()
        
        self._dedent()
        self._emit("")
        
        self.en_mision = False
        self.nombre_mision_actual = None
    
    def _generar_declaracion_global(self, nodo: DeclaracionGlobal):
        """Genera código para una variable global"""
        if nodo.valor:
            valor_code = self._generar_expresion(nodo.valor)
            self._emit(f"{nodo.nombre} = {valor_code}")
        else:
            self._emit(f"{nodo.nombre} = None")
    
    def _generar_sentencia(self, nodo: Sentencia):
        """Dispatcher para generar diferentes tipos de sentencias"""
        if isinstance(nodo, DeclaracionLocal):
            self._generar_declaracion_local(nodo)
        elif isinstance(nodo, Asignacion):
            self._generar_asignacion(nodo)
        elif isinstance(nodo, SentenciaLlamada):
            llamada_code = self._generar_expresion(nodo.llamada)
            self._emit(llamada_code)
        elif isinstance(nodo, Retirada):
            self._generar_retirada(nodo)
        elif isinstance(nodo, BucleAtacar):
            self._generar_bucle_atacar(nodo)
        elif isinstance(nodo, SentEstrategia):
            self._generar_sent_estrategia(nodo)
        elif isinstance(nodo, Abortar):
            self._emit("break")
        elif isinstance(nodo, Avanzar):
            self._emit("continue")
        else:
            raise GeneradorError(f"Tipo de sentencia no soportado: {type(nodo).__name__}")
    
    def _generar_declaracion_local(self, nodo: DeclaracionLocal):
        """Genera código para una variable local"""
        if nodo.valor:
            valor_code = self._generar_expresion(nodo.valor)
            self._emit(f"{nodo.nombre} = {valor_code}")
        else:
            self._emit(f"{nodo.nombre} = None")
    
    def _generar_asignacion(self, nodo: Asignacion):
        """Genera código para una asignación"""
        ref_code = self._generar_referencia(nodo.referencia)
        valor_code = self._generar_expresion(nodo.valor)
        
        if nodo.operador == "=":
            self._emit(f"{ref_code} = {valor_code}")
        elif nodo.operador == "+=":
            self._emit(f"{ref_code} += {valor_code}")
        elif nodo.operador == "-=":
            self._emit(f"{ref_code} -= {valor_code}")
        elif nodo.operador == "*=":
            self._emit(f"{ref_code} *= {valor_code}")
        elif nodo.operador == "/=":
            self._emit(f"{ref_code} /= {valor_code}")
        elif nodo.operador == "%=":
            self._emit(f"{ref_code} %= {valor_code}")
        else:
            raise GeneradorError(f"Operador de asignación no soportado: {nodo.operador}")
    
    def _generar_retirada(self, nodo: Retirada):
        """Genera código para retirada (return)"""
        if nodo.valor:
            valor_code = self._generar_expresion(nodo.valor)
            self._emit(f"return {valor_code}")
        else:
            self._emit("return")
    
    def _generar_bucle_atacar(self, nodo: BucleAtacar):
        """Genera código para bucle atacar mientras (while)"""
        cond_code = self._generar_expresion(nodo.condicion)
        self._emit(f"while {cond_code}:")
        self._indent()
        
        # Generar cuerpo del bucle
        if isinstance(nodo.cuerpo.contenido, Bloque):
            tiene_contenido = False
            for sentencia in nodo.cuerpo.contenido.sentencias:
                self._generar_sentencia(sentencia)
                tiene_contenido = True
            if not tiene_contenido:
                self._emit("pass")
        else:
            # Sentencia única
            self._generar_sentencia(nodo.cuerpo.contenido)
        
        self._dedent()
    
    def _generar_sent_estrategia(self, nodo: SentEstrategia):
        """Genera código para estrategia si (if-elif-else)"""
        primera = True
        
        for rama in nodo.ramas_condicionales:
            cond_code = self._generar_expresion(rama.condicion)
            
            if primera:
                self._emit(f"if {cond_code}:")
                primera = False
            else:
                self._emit(f"elif {cond_code}:")
            
            self._indent()
            
            # Generar cuerpo de la rama
            if isinstance(rama.cuerpo.contenido, Bloque):
                tiene_contenido = False
                for sentencia in rama.cuerpo.contenido.sentencias:
                    self._generar_sentencia(sentencia)
                    tiene_contenido = True
                if not tiene_contenido:
                    self._emit("pass")
            else:
                # Sentencia única
                self._generar_sentencia(rama.cuerpo.contenido)
            
            self._dedent()
        
        # Rama por defecto (else)
        if nodo.rama_defecto:
            self._emit("else:")
            self._indent()
            
            if isinstance(nodo.rama_defecto.contenido, Bloque):
                tiene_contenido = False
                for sentencia in nodo.rama_defecto.contenido.sentencias:
                    self._generar_sentencia(sentencia)
                    tiene_contenido = True
                if not tiene_contenido:
                    self._emit("pass")
            else:
                self._generar_sentencia(nodo.rama_defecto.contenido)
            
            self._dedent()
    
    def _generar_expresion(self, nodo: Expresion) -> str:
        """
        Genera código para una expresión.
        Retorna el código como string (no lo emite directamente).
        """
        if isinstance(nodo, ExpBinaria):
            return self._generar_exp_binaria(nodo)
        elif isinstance(nodo, ExpUnaria):
            return self._generar_exp_unaria(nodo)
        elif isinstance(nodo, ExpPostfijo):
            return self._generar_exp_postfijo(nodo)
        elif isinstance(nodo, Llamada):
            return self._generar_llamada(nodo)
        elif isinstance(nodo, Referencia):
            return self._generar_referencia(nodo)
        elif isinstance(nodo, LiteralNumero):
            return str(nodo.valor)
        elif isinstance(nodo, LiteralCadena):
            # Escapar comillas en la cadena
            valor_escapado = nodo.valor.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{valor_escapado}"'
        elif isinstance(nodo, LiteralBooleano):
            return "True" if nodo.valor else "False"
        elif isinstance(nodo, LiteralNulo):
            return "None"
        elif isinstance(nodo, Identificador):
            return nodo.nombre
        else:
            raise GeneradorError(f"Tipo de expresión no soportado: {type(nodo).__name__}")
    
    def _generar_exp_binaria(self, nodo: ExpBinaria) -> str:
        """Genera código para expresión binaria"""
        izq = self._generar_expresion(nodo.izquierda)
        der = self._generar_expresion(nodo.derecha)
        op = nodo.operador
        
        # Mapear operadores de C-rvicio a Python
        if op == "&&":
            op = "and"
        elif op == "||":
            op = "or"
        
        return f"({izq} {op} {der})"
    
    def _generar_exp_unaria(self, nodo: ExpUnaria) -> str:
        """Genera código para expresión unaria"""
        operando = self._generar_expresion(nodo.operando)
        op = nodo.operador
        
        # Mapear operadores
        if op == "!":
            op = "not"
        
        return f"({op} {operando})"
    
    def _generar_exp_postfijo(self, nodo: ExpPostfijo) -> str:
        """Genera código para expresión postfija (acceso a miembro o indexación)"""
        base = self._generar_expresion(nodo.expresion)
        
        for postfijo in nodo.postfijos:
            if isinstance(postfijo, AccesoMiembro):
                base = f"{base}.{postfijo.miembro}"
            elif isinstance(postfijo, AccesoIndice):
                indice = self._generar_expresion(postfijo.indice)
                base = f"{base}[{indice}]"
            elif isinstance(postfijo, LlamadaPostfijo):
                # Llamada como postfijo (ej: obj.metodo())
                args = ", ".join(self._generar_expresion(arg) for arg in postfijo.llamada.argumentos)
                base = f"{base}.{postfijo.llamada.nombre}({args})"
        
        return base
    
    def _generar_llamada(self, nodo: Llamada) -> str:
        """Genera código para llamada a función"""
        args = ", ".join(self._generar_expresion(arg) for arg in nodo.argumentos)
        return f"{nodo.nombre}({args})"
    
    def _generar_referencia(self, nodo: Referencia) -> str:
        """Genera código para referencia a variable (puede ser con punto: a.b.c)"""
        return ".".join(nodo.nombres)
    
    # ===== Utilidades de indentación =====
    
    def _emit(self, linea: str):
        """Emite una línea de código con la indentación actual"""
        if linea.strip():  # No indentar líneas vacías
            self.codigo_generado.append("    " * self.nivel_indentacion + linea)
        else:
            self.codigo_generado.append("")
    
    def _indent(self):
        """Incrementa el nivel de indentación"""
        self.nivel_indentacion += 1
    
    def _dedent(self):
        """Decrementa el nivel de indentación"""
        self.nivel_indentacion = max(0, self.nivel_indentacion - 1)