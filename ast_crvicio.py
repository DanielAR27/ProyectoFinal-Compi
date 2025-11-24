#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nodos del AST para el lenguaje C-rvicio Militar
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from dataclasses import dataclass
from typing import List, Optional, Any


# -------------------------
# Nodo base
# -------------------------

@dataclass(kw_only=True)
class NodoAST:
    """Clase base para todos los nodos del AST"""
    # Posición opcional (llenada por el parser cuando sea posible)
    fila: Optional[int] = None
    columna: Optional[int] = None


# -------------------------
# Programa y contenedores
# -------------------------

@dataclass
class Programa(NodoAST):
    """Nodo raíz del programa"""
    cuerpo: List[NodoAST]  # Lista de EjercitoDecl, DefMision, DeclaracionGlobal, Sentencia


@dataclass
class EjercitoDecl(NodoAST):
    """Declaración de un ejército (namespace/módulo)"""
    nombre: str
    cuerpo: List[NodoAST]  # DefMision, DeclaracionGlobal, Sentencia


# -------------------------
# Variables
# -------------------------

@dataclass
class DeclaracionGlobal(NodoAST):
    """Declaración de variable global"""
    nombre: str
    valor: Optional['Expresion']  # None si no tiene inicialización


@dataclass
class DeclaracionLocal(NodoAST):
    """Declaración de variable local"""
    nombre: str
    valor: Optional['Expresion']


# -------------------------
# Misiones (funciones)
# -------------------------

@dataclass
class DefMision(NodoAST):
    """Definición de una misión (función)"""
    nombre: str
    parametros: List[str]  # Lista de nombres de parámetros
    severidad: Optional[str]  # "estricto" | "advertencia" | None
    seccion_revisar: Optional['SeccionRevisar']
    seccion_ejecutar: 'SeccionEjecutar'
    seccion_confirmar: Optional['SeccionConfirmar']


@dataclass
class SeccionRevisar(NodoAST):
    """Sección revisar: precondiciones"""
    condiciones: List['Expresion']


@dataclass
class SeccionEjecutar(NodoAST):
    """Sección ejecutar: cuerpo de la misión"""
    sentencias: List['Sentencia']


@dataclass
class SeccionConfirmar(NodoAST):
    """Sección confirmar: postcondiciones"""
    condiciones: List['Expresion']


# -------------------------
# Sentencias
# -------------------------

@dataclass
class Sentencia(NodoAST):
    """Clase base para sentencias"""
    pass


@dataclass
class Asignacion(Sentencia):
    """Asignación a una variable"""
    referencia: 'Referencia'
    operador: str  # "=", "+=", "-=", "*=", "/=", "%="
    valor: 'Expresion'


@dataclass
class Retirada(Sentencia):
    """Sentencia de retorno (return)"""
    valor: Optional['Expresion']  # None si es solo "retirada"


@dataclass
class BucleAtacar(Sentencia):
    """Bucle while"""
    condicion: 'Expresion'
    cuerpo: 'ComandoSimple'


@dataclass
class SentEstrategia(Sentencia):
    """Condicional if-elif-else"""
    ramas_condicionales: List['RamaCondicional']
    rama_defecto: Optional['ComandoSimple']


@dataclass
class RamaCondicional(NodoAST):
    """Rama condicional (if/elif)"""
    condicion: 'Expresion'
    cuerpo: 'ComandoSimple'


@dataclass
class Abortar(Sentencia):
    """Sentencia break"""
    pass


@dataclass
class Avanzar(Sentencia):
    """Sentencia continue"""
    pass


@dataclass
class SentenciaLlamada(Sentencia):
    """Llamada a función como sentencia"""
    llamada: 'Llamada'


# -------------------------
# Comandos y bloques
# -------------------------

@dataclass
class ComandoSimple(NodoAST):
    """Puede ser un Bloque o una Sentencia única"""
    contenido: Any  # Bloque | Sentencia


@dataclass
class Bloque(NodoAST):
    """Bloque de sentencias entre llaves"""
    sentencias: List[Sentencia]


# -------------------------
# Expresiones
# -------------------------

@dataclass
class Expresion(NodoAST):
    """Clase base para expresiones"""
    pass


@dataclass
class ExpBinaria(Expresion):
    """Expresión binaria (operador entre dos operandos)"""
    izquierda: Expresion
    operador: str  # "+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"
    derecha: Expresion


@dataclass
class ExpUnaria(Expresion):
    """Expresión unaria (operador prefijo)"""
    operador: str  # "-", "!"
    operando: Expresion


@dataclass
class ExpPostfijo(Expresion):
    """Expresión con acceso a miembro o indexación"""
    expresion: Expresion
    postfijos: List['Postfijo']


@dataclass
class Postfijo(NodoAST):
    """Operación postfija"""
    pass


@dataclass
class AccesoMiembro(Postfijo):
    """Acceso a miembro con punto"""
    miembro: str


@dataclass
class AccesoIndice(Postfijo):
    """Indexación con corchetes"""
    indice: Expresion


@dataclass
class LlamadaPostfijo(Postfijo):
    """Llamada como postfijo"""
    llamada: 'Llamada'


# -------------------------
# Llamadas y referencias
# -------------------------

@dataclass
class Llamada(Expresion):
    """Llamada a función o misión ambiente"""
    nombre: str
    argumentos: List[Expresion]


@dataclass
class Referencia(Expresion):
    """Referencia a variable (puede ser con punto: a.b.c)"""
    nombres: List[str]  # ["a", "b", "c"] para a.b.c


# -------------------------
# Literales
# -------------------------

@dataclass
class LiteralNumero(Expresion):
    """Literal numérico (entero o flotante)"""
    valor: Any  # int o float
    tipo: str  # "entero" | "flotante"


@dataclass
class LiteralCadena(Expresion):
    """Literal de cadena"""
    valor: str


@dataclass
class LiteralBooleano(Expresion):
    """Literal booleano"""
    valor: bool  # True para "afirmativo", False para "negativo"


@dataclass
class LiteralNulo(Expresion):
    """Literal nulo"""
    pass


@dataclass
class Identificador(Expresion):
    """Identificador simple"""
    nombre: str