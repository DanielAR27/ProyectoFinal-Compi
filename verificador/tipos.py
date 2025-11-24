#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de tipos para C-rvicio Militar
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from enum import Enum, auto
from typing import Optional


class TipoBase(Enum):
    """Tipos primitivos del lenguaje C-rvicio Militar"""
    ENTERO = auto()      # Números enteros: 1, 42, -5
    FLOTANTE = auto()    # Números decimales: 3.14, -0.5
    CADENA = auto()      # Texto entre comillas: "Hola mundo"
    BOOLEANO = auto()    # afirmativo o negativo
    NULO = auto()        # nulo
    EJERCITO = auto()    # Clase/Módulo definido con 'ejercito'
    MISION = auto()      # Función definida con 'mision'
    DESCONOCIDO = auto() # Tipo no determinado aún


class Tipo:
    """
    Representa un tipo en el sistema de tipos.
    
    Atributos:
        base: El tipo primitivo (ENTERO, CADENA, etc.)
        nombre: Nombre del tipo para EJERCITO/MISION (ej: "Finanzas", "calcular")
    """
    
    def __init__(self, base: TipoBase, nombre: Optional[str] = None):
        self.base = base      # Tipo base del enum TipoBase
        self.nombre = nombre  # Solo usado para EJERCITO y MISION
    
    def __eq__(self, other):
        """
        Compara si dos tipos son iguales.
        Necesario para poder hacer: if tipo1 == tipo2
        """
        if not isinstance(other, Tipo):
            return False
        return self.base == other.base and self.nombre == other.nombre
    
    def __hash__(self):
        """
        Permite usar Tipo como clave de diccionario o en sets.
        Útil internamente en el verificador para optimizaciones.
        Ejemplo: cache = {(TIPO_ENTERO, TIPO_FLOTANTE): True}
        """
        return hash((self.base, self.nombre))
    
    def __repr__(self):
        """
        Representación legible del tipo para debugging y mensajes de error.
        Ejemplo: print(tipo) → "ENTERO" o "Ejercito(Finanzas)"
        """
        if self.base == TipoBase.EJERCITO and self.nombre:
            return f"Ejercito({self.nombre})"
        if self.base == TipoBase.MISION and self.nombre:
            return f"Mision({self.nombre})"
        return self.base.name
    
    def es_numerico(self) -> bool:
        """
        Verifica si el tipo es numérico (entero o flotante).
        Útil para validar operaciones aritméticas.
        """
        return self.base in (TipoBase.ENTERO, TipoBase.FLOTANTE)
    
    def es_comparable(self) -> bool:
        """
        Verifica si el tipo soporta comparaciones (<, >, <=, >=).
        En C-rvicio: números y cadenas son comparables.
        """
        return self.base in (TipoBase.ENTERO, TipoBase.FLOTANTE, TipoBase.CADENA)
    
    def es_iterable(self) -> bool:
        """
        Verifica si el tipo es iterable (puede usar [] para acceder elementos).
        En C-rvicio: solo las cadenas son iterables (texto[i])
        """
        return self.base == TipoBase.CADENA


# Tipos predefinidos comunes para usar en todo el verificador
TIPO_ENTERO = Tipo(TipoBase.ENTERO)
TIPO_FLOTANTE = Tipo(TipoBase.FLOTANTE)
TIPO_CADENA = Tipo(TipoBase.CADENA)
TIPO_BOOLEANO = Tipo(TipoBase.BOOLEANO)
TIPO_NULO = Tipo(TipoBase.NULO)
TIPO_DESCONOCIDO = Tipo(TipoBase.DESCONOCIDO)


class VerificadorTipos:
    """
    Utilidades estáticas para verificación y manipulación de tipos.
    Todas las funciones son estáticas porque no necesitan estado.
    """
    
    @staticmethod
    def son_compatibles(tipo1: Tipo, tipo2: Tipo) -> bool:
        """
        Verifica si dos tipos son compatibles para operaciones.
        
        Reglas de compatibilidad:
        - Mismo tipo exacto: siempre compatible
        - Nulo: compatible con todo (puede asignarse a cualquier variable)
        - Números: entero y flotante son compatibles entre sí
        
        Ejemplo:
            son_compatibles(TIPO_ENTERO, TIPO_FLOTANTE) → True
            son_compatibles(TIPO_CADENA, TIPO_ENTERO) → False
        """
        # Mismo tipo exacto
        if tipo1 == tipo2:
            return True
        
        # Nulo es compatible con cualquier tipo
        if tipo1.base == TipoBase.NULO or tipo2.base == TipoBase.NULO:
            return True
        
        # Coerción implícita entre números (entero ↔ flotante)
        if tipo1.es_numerico() and tipo2.es_numerico():
            return True
        
        return False
    
    @staticmethod
    def inferir_tipo_operacion_binaria(op: str, tipo_izq: Tipo, tipo_der: Tipo) -> Optional[Tipo]:
        """
        Infiere el tipo resultante de una operación binaria.
        Retorna None si la operación no es válida.
        """
        
        # Operadores aritméticos: +, -, *, /, %
        if op in ('+', '-', '*', '/', '%'):
            # Si alguno es desconocido, retornar el otro tipo (o desconocido si ambos lo son)
            if tipo_izq.base == TipoBase.DESCONOCIDO:
                return tipo_der if tipo_der.base != TipoBase.DESCONOCIDO else TIPO_DESCONOCIDO
            if tipo_der.base == TipoBase.DESCONOCIDO:
                return tipo_izq
            
            # Caso especial: suma con cadena es concatenación
            if op == '+' and (tipo_izq.base == TipoBase.CADENA or tipo_der.base == TipoBase.CADENA):
                return TIPO_CADENA
            
            # Operaciones numéricas estándar
            if tipo_izq.es_numerico() and tipo_der.es_numerico():
                # Si alguno es flotante, el resultado es flotante
                if tipo_izq.base == TipoBase.FLOTANTE or tipo_der.base == TipoBase.FLOTANTE:
                    return TIPO_FLOTANTE
                return TIPO_ENTERO
            
            return None  # Tipos incompatibles para aritmética
        
        # Operadores de igualdad: ==, !=
        # Funcionan con cualquier tipo y SIEMPRE retornan BOOLEANO
        if op in ('==', '!='):
            return TIPO_BOOLEANO
        
        # Operadores relacionales: <, <=, >, >=
        # SIEMPRE retornan BOOLEANO si los tipos son compatibles
        if op in ('<', '<=', '>', '>='):
            # Si alguno es desconocido, asumir que es válido
            if tipo_izq.base == TipoBase.DESCONOCIDO or tipo_der.base == TipoBase.DESCONOCIDO:
                return TIPO_BOOLEANO
            
            if tipo_izq.es_comparable() and tipo_der.es_comparable():
                if VerificadorTipos.son_compatibles(tipo_izq, tipo_der):
                    return TIPO_BOOLEANO
            return None
        
        # Operadores lógicos: &&, ||
        # Solo válidos con booleanos
        if op in ('&&', '||'):
            # Si alguno es desconocido, asumir que es válido
            if tipo_izq.base == TipoBase.DESCONOCIDO or tipo_der.base == TipoBase.DESCONOCIDO:
                return TIPO_BOOLEANO
            
            if tipo_izq.base == TipoBase.BOOLEANO and tipo_der.base == TipoBase.BOOLEANO:
                return TIPO_BOOLEANO
            return None
        
        return None  # Operador no reconocido
    
    @staticmethod
    def inferir_tipo_operacion_unaria(op: str, tipo: Tipo) -> Optional[Tipo]:
        """
        Infiere el tipo resultante de una operación unaria.
        Retorna None si la operación no es válida.
        
        Ejemplos:
            inferir("-", TIPO_ENTERO) → TIPO_ENTERO (negación numérica)
            inferir("!", TIPO_BOOLEANO) → TIPO_BOOLEANO (negación lógica)
            inferir("-", TIPO_CADENA) → None (error: no se puede negar una cadena)
        """
        # Si es desconocido, permitir la operación
        if tipo.base == TipoBase.DESCONOCIDO:
            return TIPO_DESCONOCIDO
        
        # Negación numérica: -expr
        if op == '-':
            if tipo.es_numerico():
                return tipo  # Mismo tipo (entero→entero, flotante→flotante)
            return None
        
        # Negación lógica: !expr
        if op == '!':
            if tipo.base == TipoBase.BOOLEANO:
                return TIPO_BOOLEANO
            return None
        
        return None
    
    @staticmethod
    def puede_asignar(tipo_destino: Tipo, tipo_valor: Tipo) -> bool:
        """
        Verifica si un valor puede asignarse a una variable.
        Usa las mismas reglas que son_compatibles.
        
        Ejemplo:
            var x = 5        # tipo_destino se infiere como ENTERO
            x = 3.14         # puede_asignar(ENTERO, FLOTANTE) → True (compatible)
            x = "texto"      # puede_asignar(ENTERO, CADENA) → False (error)
        """
        return VerificadorTipos.son_compatibles(tipo_destino, tipo_valor)
    
    @staticmethod
    def tipo_desde_literal(nodo_literal) -> Tipo:
        """
        Obtiene el tipo de un nodo literal del AST.
        
        Usado cuando encontramos literales en el código:
            42 → TIPO_ENTERO
            3.14 → TIPO_FLOTANTE
            "hola" → TIPO_CADENA
            afirmativo → TIPO_BOOLEANO
            nulo → TIPO_NULO
        """
        # Import local para evitar dependencia circular
        from ast_crvicio import (
            LiteralNumero, LiteralCadena, LiteralBooleano, LiteralNulo
        )
        
        if isinstance(nodo_literal, LiteralNumero):
            if nodo_literal.tipo == "entero":
                return TIPO_ENTERO
            return TIPO_FLOTANTE
        
        if isinstance(nodo_literal, LiteralCadena):
            return TIPO_CADENA
        
        if isinstance(nodo_literal, LiteralBooleano):
            return TIPO_BOOLEANO
        
        if isinstance(nodo_literal, LiteralNulo):
            return TIPO_NULO
        
        return TIPO_DESCONOCIDO