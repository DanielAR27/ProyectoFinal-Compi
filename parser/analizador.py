#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador Sintáctico (Parser) LL(1) para C-rvicio Militar
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from typing import List, Optional
from token_crvicio import Token
import ast_crvicio as ast_nodes


# -------------------------
# Excepciones
# -------------------------

class ParserError(Exception):
    """Error de parsing"""
    pass


# -------------------------
# Parser LL(1)
# -------------------------

class Analizador:
    """Parser LL(1) para C-rvicio Militar"""
    
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.token_actual = self.tokens[0] if tokens else None
    
    # -------------------------
    # Utilidades
    # -------------------------
    
    def avanzar(self) -> None:
        """Avanza al siguiente token"""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.token_actual = self.tokens[self.pos]
        else:
            self.token_actual = None
    
    def mirar_adelante(self, n: int = 1) -> Optional[Token]:
        """Mira n tokens adelante sin consumir"""
        idx = self.pos + n
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None
    
    def peek(self, k: int = 0) -> Optional[Token]:
        """
        Alias más legible de mirar_adelante.
        peek(0) = token_actual, peek(1) = siguiente token, etc.
        """
        if k == 0:
            return self.token_actual
        return self.mirar_adelante(k)
    
    def skip_nl(self) -> None:
        """Consume todos los tokens NL consecutivos"""
        while self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
    
    def consumir(self, tipo: str, lexema: Optional[str] = None) -> Token:
        """
        Consume un token del tipo esperado.
        Si lexema es provisto, también valida el lexema.
        """
        if self.token_actual is None:
            raise ParserError(f"Se esperaba {tipo}, pero no hay más tokens")
        
        if self.token_actual.tipo != tipo:
            raise ParserError(
                f"Se esperaba token {tipo}, pero se encontró {self.token_actual.tipo} "
                f"('{self.token_actual.lexema}') en fila {self.token_actual.atributos.get('fila', '?')}, "
                f"columna {self.token_actual.atributos.get('columna', '?')}"
            )
        
        if lexema is not None and self.token_actual.lexema != lexema:
            raise ParserError(
                f"Se esperaba '{lexema}', pero se encontró '{self.token_actual.lexema}' "
                f"en fila {self.token_actual.atributos.get('fila', '?')}, "
                f"columna {self.token_actual.atributos.get('columna', '?')}"
            )
        
        token = self.token_actual
        self.avanzar()
        return token
    
    def es_palabra_clave(self, lexema: str) -> bool:
        """Verifica si el token actual es una palabra clave específica"""
        return (self.token_actual is not None and 
                self.token_actual.tipo == "PALABRA_CLAVE" and 
                self.token_actual.lexema == lexema)
    
    def es_operador(self, lexema: str) -> bool:
        """Verifica si el token actual es un operador específico"""
        return (self.token_actual is not None and 
                self.token_actual.tipo == "OPERADOR" and 
                self.token_actual.lexema == lexema)
    
    def es_simbolo(self, lexema: str) -> bool:
        """Verifica si el token actual es un símbolo específico"""
        return (self.token_actual is not None and 
                self.token_actual.tipo == "SIMBOLO" and 
                self.token_actual.lexema == lexema)
    
    # -------------------------
    # Punto de entrada
    # -------------------------
    
    def parsear(self) -> ast_nodes.Programa:
        """Punto de entrada del parser"""
        return self.programa()
    
    # -------------------------
    # Programa y contenedores
    # -------------------------
    
    def programa(self) -> ast_nodes.Programa:
        """
        Programa ::= ( EjercitoDecl | DefMision | DeclaracionGlobal 
                     | Sentencia | NL )+
        """
        cuerpo = []
        
        while self.token_actual is not None:
            if self.es_palabra_clave("ejercito"):
                cuerpo.append(self.ejercito_decl())
            elif self.es_palabra_clave("mision"):
                cuerpo.append(self.def_mision())
            elif self.es_palabra_clave("global"):
                cuerpo.append(self.declaracion_global())
            elif self.token_actual.tipo == "NL":
                self.avanzar()  # Ignorar líneas en blanco
            else:
                # Permitir sentencias ejecutables a nivel global
                cuerpo.append(self.sentencia())
        
        return ast_nodes.Programa(cuerpo=cuerpo)
    
    def ejercito_decl(self) -> ast_nodes.EjercitoDecl:
        """
        EjercitoDecl ::= "ejercito" IDENT BloqueEjercito
        """
        self.consumir("PALABRA_CLAVE", "ejercito")
        nombre_token = self.consumir("IDENT")
        nombre = nombre_token.lexema
        cuerpo = self.bloque_ejercito()
        
        return ast_nodes.EjercitoDecl(
            nombre=nombre,
            cuerpo=cuerpo,
            fila=nombre_token.atributos.get('fila'),
            columna=nombre_token.atributos.get('columna')
        )
    
    def bloque_ejercito(self) -> List[ast_nodes.NodoAST]:
        """
        BloqueEjercito ::= "{" ( DefMision | DeclaracionGlobal | Sentencia | NL )* "}"
        """
        self.consumir("SIMBOLO", "{")
        cuerpo = []
        
        while not self.es_simbolo("}"):
            if self.token_actual is None:
                raise ParserError("Se esperaba '}' pero se alcanzó el fin del archivo")
            
            if self.es_palabra_clave("mision"):
                cuerpo.append(self.def_mision())
            elif self.es_palabra_clave("global"):
                cuerpo.append(self.declaracion_global())
            elif self.token_actual.tipo == "NL":
                self.avanzar()
            else:
                cuerpo.append(self.sentencia())
        
        self.consumir("SIMBOLO", "}")
        return cuerpo
    
    # -------------------------
    # Variables
    # -------------------------
    
    def declaracion_global(self) -> ast_nodes.DeclaracionGlobal:
        """
        DeclaracionGlobal ::= "global" "var" IDENT ( "=" Expresion )? NL
        """
        self.consumir("PALABRA_CLAVE", "global")
        self.consumir("PALABRA_CLAVE", "var")
        nombre_token = self.consumir("IDENT")
        nombre = nombre_token.lexema
        
        valor = None
        if self.es_operador("="):
            self.avanzar()
            valor = self.expresion()
        
        # Consumir NL si existe
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        return ast_nodes.DeclaracionGlobal(
            nombre=nombre,
            valor=valor,
            fila=nombre_token.atributos.get('fila'),
            columna=nombre_token.atributos.get('columna')
        )
    
    def declaracion_local(self) -> ast_nodes.DeclaracionLocal:
        """
        DeclaracionLocal ::= "var" IDENT ( "=" Expresion )? NL
        """
        self.consumir("PALABRA_CLAVE", "var")
        nombre_token = self.consumir("IDENT")
        nombre = nombre_token.lexema
        
        valor = None
        if self.es_operador("="):
            self.avanzar()
            valor = self.expresion()
        
        # Consumir NL si existe
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        return ast_nodes.DeclaracionLocal(
            nombre=nombre,
            valor=valor,
            fila=nombre_token.atributos.get('fila'),
            columna=nombre_token.atributos.get('columna')
        )
    
    # -------------------------
    # Misiones
    # -------------------------
    
    def def_mision(self) -> ast_nodes.DefMision:
        """
        DefMision ::= "mision" IDENT "(" Parametros? ")"
                     ( "severidad" "=" ( "estricto" | "advertencia" ) )?
                     BloqueMision
        """
        self.consumir("PALABRA_CLAVE", "mision")
        nombre_token = self.consumir("IDENT")
        nombre = nombre_token.lexema
        
        self.consumir("SIMBOLO", "(")
        parametros = []
        if not self.es_simbolo(")"):
            parametros = self.parametros()
        self.consumir("SIMBOLO", ")")
        
        # Severidad opcional
        severidad = None
        if self.es_palabra_clave("severidad"):
            self.avanzar()
            self.consumir("OPERADOR", "=")
            if self.es_palabra_clave("estricto"):
                severidad = "estricto"
                self.avanzar()
            elif self.es_palabra_clave("advertencia"):
                severidad = "advertencia"
                self.avanzar()
            else:
                raise ParserError("Se esperaba 'estricto' o 'advertencia' después de 'severidad='")
        
        # Bloque de misión
        revisar, ejecutar, confirmar = self.bloque_mision()
        
        return ast_nodes.DefMision(
            nombre=nombre,
            parametros=parametros,
            severidad=severidad,
            seccion_revisar=revisar,
            seccion_ejecutar=ejecutar,
            seccion_confirmar=confirmar,
            fila=nombre_token.atributos.get('fila'),
            columna=nombre_token.atributos.get('columna')
        )
    
    def parametros(self) -> List[str]:
        """
        Parametros ::= Parametro ( "," Parametro )*
        Parametro ::= IDENT
        """
        params = []
        first_param = self.consumir("IDENT")
        params.append(first_param.lexema)

        while self.es_simbolo(","):
            self.avanzar()
            t = self.consumir("IDENT")
            params.append(t.lexema)

        return params
    
    def bloque_mision(self) -> tuple:
        """
        BloqueMision ::= "{"
                         SeccionRevisar?
                         SeccionEjecutar
                         SeccionConfirmar?
                         "}"
        """
        self.consumir("SIMBOLO", "{")
        
        revisar = None
        ejecutar = None
        confirmar = None
        
        # Saltar NL
        self.skip_nl()
        
        # SeccionRevisar (opcional)
        if self.es_palabra_clave("revisar"):
            revisar = self.seccion_revisar()
        
        # Saltar NL
        self.skip_nl()
        
        # SeccionEjecutar (obligatoria)
        if self.es_palabra_clave("ejecutar"):
            ejecutar = self.seccion_ejecutar()
        else:
            raise ParserError("Se esperaba sección 'ejecutar' en la misión")
        
        # Saltar NL
        self.skip_nl()
        
        # SeccionConfirmar (opcional)
        if self.es_palabra_clave("confirmar"):
            confirmar = self.seccion_confirmar()
        
        # Saltar NL
        self.skip_nl()
        
        self.consumir("SIMBOLO", "}")
        
        return (revisar, ejecutar, confirmar)
    
    def seccion_revisar(self) -> ast_nodes.SeccionRevisar:
        """
        SeccionRevisar ::= "revisar" ":" NL Condicion+
        Condicion ::= Expresion NL
        """
        self.consumir("PALABRA_CLAVE", "revisar")
        self.consumir("SIMBOLO", ":")
        
        # Consumir NL obligatorio
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        condiciones = []
        # Leer al menos una condición
        while not self.es_palabra_clave("ejecutar") and not self.es_simbolo("}"):
            if self.token_actual is None:
                raise ParserError("Se esperaba condición en sección 'revisar'")
            
            if self.token_actual.tipo == "NL":
                self.avanzar()
                continue
            
            condiciones.append(self.expresion())
            
            # Consumir NL después de condición si existe
            if self.token_actual and self.token_actual.tipo == "NL":
                self.avanzar()
        
        return ast_nodes.SeccionRevisar(condiciones=condiciones)
    
    def seccion_ejecutar(self) -> ast_nodes.SeccionEjecutar:
        """
        SeccionEjecutar ::= "ejecutar" ":" NL ( Sentencia | NL )+
        """
        self.consumir("PALABRA_CLAVE", "ejecutar")
        self.consumir("SIMBOLO", ":")
        
        # Consumir NL obligatorio
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        sentencias = []
        # Leer sentencias hasta encontrar "confirmar" o "}"
        while not self.es_palabra_clave("confirmar") and not self.es_simbolo("}"):
            if self.token_actual is None:
                raise ParserError("Se esperaba sentencia en sección 'ejecutar'")
            
            if self.token_actual.tipo == "NL":
                self.avanzar()
                continue
            
            sentencias.append(self.sentencia())
        
        return ast_nodes.SeccionEjecutar(sentencias=sentencias)
    
    def seccion_confirmar(self) -> ast_nodes.SeccionConfirmar:
        """
        SeccionConfirmar ::= "confirmar" ":" NL Condicion+
        """
        self.consumir("PALABRA_CLAVE", "confirmar")
        self.consumir("SIMBOLO", ":")
        
        # Consumir NL obligatorio
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        condiciones = []
        # Leer condiciones hasta encontrar "}"
        while not self.es_simbolo("}"):
            if self.token_actual is None:
                raise ParserError("Se esperaba condición en sección 'confirmar'")
            
            if self.token_actual.tipo == "NL":
                self.avanzar()
                continue
            
            condiciones.append(self.expresion())
            
            # Consumir NL después de condición si existe
            if self.token_actual and self.token_actual.tipo == "NL":
                self.avanzar()
        
        return ast_nodes.SeccionConfirmar(condiciones=condiciones)
    
    # -------------------------
    # Sentencias
    # -------------------------
    
    def sentencia(self) -> ast_nodes.Sentencia:
        """
        Sentencia ::= DeclaracionLocal
                    | Asignacion NL
                    | Llamada NL
                    | BucleAtacar
                    | Retirada NL
                    | SentEstrategia
                    | "abortar"
                    | "avanzar"
        """
        # DeclaracionLocal
        if self.es_palabra_clave("var"):
            return self.declaracion_local()
        
        # BucleAtacar
        if self.es_palabra_clave("atacar"):
            return self.bucle_atacar()
        
        # Retirada
        if self.es_palabra_clave("retirada"):
            return self.retirada()
        
        # SentEstrategia
        if self.es_palabra_clave("estrategia"):
            return self.sent_estrategia()
        
        # Abortar
        if self.es_palabra_clave("abortar"):
            self.avanzar()
            if self.token_actual and self.token_actual.tipo == "NL":
                self.avanzar()
            return ast_nodes.Abortar()
        
        # Avanzar
        if self.es_palabra_clave("avanzar"):
            self.avanzar()
            if self.token_actual and self.token_actual.tipo == "NL":
                self.avanzar()
            return ast_nodes.Avanzar()
        
        # Asignacion o Llamada
        # Necesitamos lookahead para distinguir
        if self.token_actual and self.token_actual.tipo == "IDENT":
            # Guardar posición para backtracking si es necesario
            pos_guardada = self.pos
            
            # Intentar parsear como referencia
            ref = self.referencia()
            
            # Si después hay operador de asignación, es asignación
            if self.token_actual and self.token_actual.tipo == "OPERADOR" and \
               self.token_actual.lexema in ["=", "+=", "-=", "*=", "/=", "%="]:
                token_op = self.token_actual
                op = token_op.lexema
                self.avanzar()
                valor = self.expresion()
                
                if self.token_actual and self.token_actual.tipo == "NL":
                    self.avanzar()

                return ast_nodes.Asignacion(
                    referencia=ref,
                    operador=op,
                    valor=valor,
                    fila=token_op.atributos.get('fila'),
                    columna=token_op.atributos.get('columna')
                )

            # Si después hay "(", es llamada
            if self.token_actual and self.es_simbolo("("):
                # Retroceder y parsear como llamada
                self.pos = pos_guardada
                self.token_actual = self.tokens[self.pos]
                llamada = self.llamada()
                
                if self.token_actual and self.token_actual.tipo == "NL":
                    self.avanzar()
                
                return ast_nodes.SentenciaLlamada(llamada=llamada)

            # Si no es ninguna de las anteriores, error
            raise ParserError(
                f"Sentencia inválida comenzando con '{ref}' "
                f"en fila {self.token_actual.atributos.get('fila', '?') if self.token_actual else '?'}"
            )
        
        raise ParserError(
            f"Sentencia no reconocida: {self.token_actual.lexema if self.token_actual else 'EOF'}"
        )
    
    def retirada(self) -> ast_nodes.Retirada:
        """
        Retirada ::= "retirada" ( "con" Expresion )?
        """
        self.consumir("PALABRA_CLAVE", "retirada")
        
        valor = None
        if self.es_palabra_clave("con"):
            self.avanzar()
            valor = self.expresion()
        
        if self.token_actual and self.token_actual.tipo == "NL":
            self.avanzar()
        
        return ast_nodes.Retirada(valor=valor)
    
    def bucle_atacar(self) -> ast_nodes.BucleAtacar:
        """
        BucleAtacar ::= "atacar" "mientras" "(" Expresion ")" ComandoSimple
        """
        self.consumir("PALABRA_CLAVE", "atacar")
        self.consumir("PALABRA_CLAVE", "mientras")
        self.consumir("SIMBOLO", "(")
        condicion = self.expresion()
        self.consumir("SIMBOLO", ")")
        cuerpo = self.comando_simple()
        
        return ast_nodes.BucleAtacar(condicion=condicion, cuerpo=cuerpo)
    
    def sent_estrategia(self) -> ast_nodes.SentEstrategia:
        """
        SentEstrategia ::= "estrategia" RamaCondicional+ RamaDefecto?
        RamaCondicional ::= "si" "(" Expresion ")" ComandoSimple
        RamaDefecto ::= "por defecto" ComandoSimple
        """
        self.consumir("PALABRA_CLAVE", "estrategia")
        
        ramas = []
        # Al menos una rama "si"
        while self.es_palabra_clave("si"):
            self.avanzar()
            self.consumir("SIMBOLO", "(")
            condicion = self.expresion()
            self.consumir("SIMBOLO", ")")
            cuerpo = self.comando_simple()
            ramas.append(ast_nodes.RamaCondicional(condicion=condicion, cuerpo=cuerpo))
        
        # Rama por defecto opcional
        defecto = None
        if self.es_palabra_clave("por"):
            self.avanzar()
            self.consumir("PALABRA_CLAVE", "defecto")
            defecto = self.comando_simple()
        
        return ast_nodes.SentEstrategia(ramas_condicionales=ramas, rama_defecto=defecto)
    
    def comando_simple(self) -> ast_nodes.ComandoSimple:
        """
        ComandoSimple ::= Bloque | Sentencia
        """
        if self.es_simbolo("{"):
            bloque = self.bloque()
            return ast_nodes.ComandoSimple(contenido=bloque)
        else:
            sentencia = self.sentencia()
            return ast_nodes.ComandoSimple(contenido=sentencia)
    
    def bloque(self) -> ast_nodes.Bloque:
        """
        Bloque ::= "{" ( Sentencia | NL )* "}"
        """
        self.consumir("SIMBOLO", "{")
        sentencias = []
        
        while not self.es_simbolo("}"):
            if self.token_actual is None:
                raise ParserError("Se esperaba '}' pero se alcanzó el fin del archivo")
            
            if self.token_actual.tipo == "NL":
                self.avanzar()
                continue
            
            sentencias.append(self.sentencia())
        
        self.consumir("SIMBOLO", "}")
        return ast_nodes.Bloque(sentencias=sentencias)
    
    # -------------------------
    # Expresiones (con precedencia)
    # -------------------------
    
    def expresion(self) -> ast_nodes.Expresion:
        """Expresion ::= ExpOr"""
        return self.exp_or()
    
    def exp_or(self) -> ast_nodes.Expresion:
        """ExpOr ::= ExpAnd ( "||" ExpAnd )*"""
        izq = self.exp_and()
        
        while self.es_operador("||"):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_and()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_and(self) -> ast_nodes.Expresion:
        """ExpAnd ::= ExpIgualdad ( "&&" ExpIgualdad )*"""
        izq = self.exp_igualdad()
        
        while self.es_operador("&&"):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_igualdad()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_igualdad(self) -> ast_nodes.Expresion:
        """ExpIgualdad ::= ExpRelacional ( ( "==" | "!=" ) ExpRelacional )*"""
        izq = self.exp_relacional()
        
        while self.token_actual and (self.es_operador("==") or self.es_operador("!=")):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_relacional()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_relacional(self) -> ast_nodes.Expresion:
        """ExpRelacional ::= ExpAditiva ( ( "<" | "<=" | ">" | ">=" ) ExpAditiva )*"""
        izq = self.exp_aditiva()
        
        while self.token_actual and (self.es_operador("<") or self.es_operador("<=") or 
                                      self.es_operador(">") or self.es_operador(">=")):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_aditiva()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_aditiva(self) -> ast_nodes.Expresion:
        """ExpAditiva ::= ExpMultiplicativa ( ( "+" | "-" ) ExpMultiplicativa )*"""
        izq = self.exp_multiplicativa()
        
        while self.token_actual and (self.es_operador("+") or self.es_operador("-")):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_multiplicativa()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_multiplicativa(self) -> ast_nodes.Expresion:
        """ExpMultiplicativa ::= ExpUnaria ( ( "*" | "/" | "%" ) ExpUnaria )*"""
        izq = self.exp_unaria()
        
        while self.token_actual and (self.es_operador("*") or self.es_operador("/") or 
                                      self.es_operador("%")):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            der = self.exp_unaria()
            izq = ast_nodes.ExpBinaria(
                izquierda=izq,
                operador=op,
                derecha=der,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return izq
    
    def exp_unaria(self) -> ast_nodes.Expresion:
        """ExpUnaria ::= ( "-" | "!" )? ExpPostfijo"""
        if self.token_actual and (self.es_operador("-") or self.es_operador("!")):
            token_op = self.token_actual
            op = token_op.lexema
            self.avanzar()
            operando = self.exp_postfijo()
            return ast_nodes.ExpUnaria(
                operador=op,
                operando=operando,
                fila=token_op.atributos.get('fila'),
                columna=token_op.atributos.get('columna')
            )
        
        return self.exp_postfijo()
    
    def exp_postfijo(self) -> ast_nodes.Expresion:
        """
        ExpPostfijo ::= Primario ( Postfijo )*
        Postfijo ::= "." IDENT | "." Llamada | "[" Expresion "]"
        """
        expr = self.primario()
        postfijos = []
        
        while self.token_actual:
            # Acceso a miembro: .IDENT
            if self.es_simbolo("."):
                self.avanzar()
                
                # Puede ser .IDENT o .llamada()
                if self.token_actual and self.token_actual.tipo == "IDENT":
                    # Mirar adelante para ver si hay "("
                    siguiente = self.mirar_adelante(1)
                    if siguiente and siguiente.tipo == "SIMBOLO" and siguiente.lexema == "(":
                        # Es una llamada
                        llamada = self.llamada()
                        postfijos.append(ast_nodes.LlamadaPostfijo(llamada=llamada))
                    else:
                        # Es acceso a miembro simple
                        miembro_token = self.consumir("IDENT")
                        miembro = miembro_token.lexema
                        postfijos.append(ast_nodes.AccesoMiembro(
                            miembro=miembro,
                            fila=miembro_token.atributos.get('fila'),
                            columna=miembro_token.atributos.get('columna')
                        ))
                else:
                    raise ParserError("Se esperaba identificador después de '.'")
            
            # Indexación: [Expresion]
            elif self.es_simbolo("["):
                self.avanzar()
                indice = self.expresion()
                self.consumir("SIMBOLO", "]")
                postfijos.append(ast_nodes.AccesoIndice(indice=indice))
            
            else:
                break
        
        if postfijos:
            return ast_nodes.ExpPostfijo(expresion=expr, postfijos=postfijos)
        return expr
    
    def primario(self) -> ast_nodes.Expresion:
        """
        Primario ::= NUM_FLOTANTE
                   | NUM_ENTERO
                   | CADENA
                   | "afirmativo"
                   | "negativo"
                   | "nulo"
                   | IDENT
                   | Llamada
                   | "(" Expresion ")"
        """
        if self.token_actual is None:
            raise ParserError("Se esperaba expresión pero se alcanzó el fin del archivo")
        
        # Literales numéricos
        if self.token_actual.tipo == "NUM_FLOTANTE":
            token_num = self.token_actual
            valor = float(token_num.lexema)
            self.avanzar()
            return ast_nodes.LiteralNumero(
                valor=valor,
                tipo="flotante",
                fila=token_num.atributos.get('fila'),
                columna=token_num.atributos.get('columna')
            )
        
        if self.token_actual.tipo == "NUM_ENTERO":
            token_num = self.token_actual
            valor = int(token_num.lexema)
            self.avanzar()
            return ast_nodes.LiteralNumero(
                valor=valor,
                tipo="entero",
                fila=token_num.atributos.get('fila'),
                columna=token_num.atributos.get('columna')
            )
        
        # Cadenas
        if self.token_actual.tipo == "CADENA":
            token_str = self.token_actual
            valor = token_str.atributos.get("valor", "")
            self.avanzar()
            return ast_nodes.LiteralCadena(
                valor=valor,
                fila=token_str.atributos.get('fila'),
                columna=token_str.atributos.get('columna')
            )
        
        # Literales booleanos
        if self.token_actual.tipo == "LIT_BOOLEANO":
            token_bool = self.token_actual
            valor = token_bool.lexema == "afirmativo"
            self.avanzar()
            return ast_nodes.LiteralBooleano(
                valor=valor,
                fila=token_bool.atributos.get('fila'),
                columna=token_bool.atributos.get('columna')
            )
        
        # Literal nulo
        if self.token_actual.tipo == "LIT_NULO":
            token_nulo = self.token_actual
            self.avanzar()
            return ast_nodes.LiteralNulo(
                fila=token_nulo.atributos.get('fila'),
                columna=token_nulo.atributos.get('columna')
            )
        
        # Expresión entre paréntesis
        if self.es_simbolo("("):
            self.avanzar()
            expr = self.expresion()
            self.consumir("SIMBOLO", ")")
            return expr
        
        # Identificador o Llamada
        if self.token_actual.tipo == "IDENT":
            # Mirar adelante para distinguir entre IDENT y Llamada
            siguiente = self.mirar_adelante(1)
            if siguiente and siguiente.tipo == "SIMBOLO" and siguiente.lexema == "(":
                # Es una llamada
                return self.llamada()
            else:
                # Es un identificador simple
                token_id = self.token_actual
                nombre = token_id.lexema
                self.avanzar()
                return ast_nodes.Identificador(
                    nombre=nombre,
                    fila=token_id.atributos.get('fila'),
                    columna=token_id.atributos.get('columna')
                )
        
        raise ParserError(
            f"Expresión primaria no reconocida: {self.token_actual.lexema} "
            f"(tipo: {self.token_actual.tipo}) en fila {self.token_actual.atributos.get('fila', '?')}"
        )
    
    # -------------------------
    # Llamadas y referencias
    # -------------------------
    
    def llamada(self) -> ast_nodes.Llamada:
        """
        Llamada ::= IDENT "(" Argumentos? ")"
                  | MisionAmbiente "(" Argumentos? ")"
        Argumentos ::= Expresion ( "," Expresion )*
        """
        nombre_token = self.consumir("IDENT")
        nombre = nombre_token.lexema
        self.consumir("SIMBOLO", "(")
        
        argumentos = []
        if not self.es_simbolo(")"):
            argumentos = self.argumentos()
        
        self.consumir("SIMBOLO", ")")

        return ast_nodes.Llamada(
            nombre=nombre,
            argumentos=argumentos,
            fila=nombre_token.atributos.get('fila'),
            columna=nombre_token.atributos.get('columna')
        )
    
    def argumentos(self) -> List[ast_nodes.Expresion]:
        """Argumentos ::= Expresion ( "," Expresion )*"""
        args = []
        args.append(self.expresion())
        
        while self.es_simbolo(","):
            self.avanzar()
            args.append(self.expresion())
        
        return args
    
    def referencia(self) -> ast_nodes.Referencia:
        """
        Referencia ::= IDENT ( "." IDENT )*
        """
        nombres = []
        first = self.consumir("IDENT")
        nombres.append(first.lexema)
        first_fila = first.atributos.get('fila')
        first_col = first.atributos.get('columna')

        while self.es_simbolo("."):
            self.avanzar()
            # Verificar que no sea seguido por paréntesis (sería una llamada)
            if self.token_actual and self.token_actual.tipo == "IDENT":
                siguiente = self.mirar_adelante(1)
                if siguiente and siguiente.tipo == "SIMBOLO" and siguiente.lexema == "(":
                    # Es una llamada, no continuar la referencia
                    break
                t = self.consumir("IDENT")
                nombres.append(t.lexema)
            else:
                raise ParserError("Se esperaba identificador después de '.'")

        return ast_nodes.Referencia(nombres=nombres, fila=first_fila, columna=first_col)