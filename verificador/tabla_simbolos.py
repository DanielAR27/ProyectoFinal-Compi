#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tabla de Símbolos para C-rvicio Militar
Maneja scopes y declaraciones de variables, misiones y ejércitos
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from typing import Optional, Dict, List, Any
from .tipos import (
    Tipo, TipoBase, 
    TIPO_CADENA, TIPO_ENTERO, TIPO_NULO
)

class Simbolo:
    """
    Representa un símbolo en la tabla (variable, misión o ejército).
    
    Atributos:
        nombre: Identificador del símbolo
        tipo: Tipo del símbolo (ENTERO, MISION, etc.)
        categoria: "variable", "mision", "ejercito"
        info_extra: Diccionario con información adicional
            - Para misiones: {"parametros": ["x", "y"], "tipos_params": [TIPO_ENTERO, ...]}
            - Para variables: puede estar vacío o tener valor inicial
    """
    
    def __init__(self, nombre: str, tipo: Tipo, categoria: str, info_extra: Optional[Dict[str, Any]] = None):
        self.nombre = nombre
        self.tipo = tipo
        self.categoria = categoria  # "variable", "mision", "ejercito"
        self.info_extra = info_extra if info_extra else {}
    
    def __repr__(self):
        return f"Simbolo({self.nombre}, {self.tipo}, {self.categoria})"


class Scope:
    """
    Representa un ámbito/scope.
    Cada scope tiene su propia tabla de símbolos y puede tener un scope padre.
    
    Atributos:
        nombre: Identificador del scope ("global", "Finanzas", "calcular", etc.)
        simbolos: Diccionario de símbolos declarados en este scope
        padre: Scope padre (None si es global)
    """
    
    def __init__(self, nombre: str, padre: Optional['Scope'] = None):
        self.nombre = nombre
        self.simbolos: Dict[str, Simbolo] = {}
        self.padre = padre
    
    def declarar(self, simbolo: Simbolo) -> bool:
        """
        Declara un símbolo en este scope.
        Retorna False si ya existe (redeclaración), True si se agregó exitosamente.
        """
        if simbolo.nombre in self.simbolos:
            return False  # Ya existe en este scope
        
        self.simbolos[simbolo.nombre] = simbolo
        return True
    
    def buscar_local(self, nombre: str) -> Optional[Simbolo]:
        """
        Busca un símbolo solo en este scope (no en padres).
        """
        return self.simbolos.get(nombre)
    
    def buscar(self, nombre: str) -> Optional[Simbolo]:
        """
        Busca un símbolo en este scope y, si no lo encuentra, en los padres.
        Implementa búsqueda en cadena de scopes.
        """
        # Buscar primero en este scope
        simbolo = self.buscar_local(nombre)
        if simbolo:
            return simbolo
        
        # Si no está, buscar en el padre
        if self.padre:
            return self.padre.buscar(nombre)
        
        return None  # No encontrado
    
    def __repr__(self):
        return f"Scope({self.nombre}, {len(self.simbolos)} símbolos)"


class TablaSimbolo:
    """
    Administra la pila de scopes durante la verificación semántica.
    
    Usa una pila para manejar scopes anidados:
    - Al entrar a un ejército/misión: push nuevo scope
    - Al salir: pop scope
    
    Atributos:
        pila_scopes: Lista que funciona como pila de scopes
        scope_actual: Scope en el tope de la pila
    """
    
    def __init__(self):
        # Crear scope global como base
        scope_global = Scope("global")
        self.pila_scopes: List[Scope] = [scope_global]
        self.scope_actual = scope_global
        
        # Registrar misiones de ambiente predefinidas
        self._registrar_misiones_ambiente()
    
    def _registrar_misiones_ambiente(self):
        """
        Registra las misiones de ambiente (funciones built-in) en el scope global.
        
        Misiones de ambiente según la gramática:
        - reportar(mensaje): imprime
        - recibir(): lee entrada
        - clasificarNumero(texto): parseInt
        - clasificarMensaje(valor): toString
        - azar(): random
        - aRangoSuperior(num): ceil
        - aRangoInferior(num): floor
        - acampar(ms): sleep
        - calibre(texto): len
        - truncar(num): trunc (parte entera)
        """
        
        misiones_ambiente = [
            # reportar(mensaje) → nulo
            ("reportar", TIPO_NULO, ["mensaje"]),
            
            # recibir() → cadena
            ("recibir", TIPO_CADENA, []),
            
            # clasificarNumero(texto) → entero
            ("clasificarNumero", TIPO_ENTERO, ["texto"]),
            
            # clasificarMensaje(valor) → cadena
            ("clasificarMensaje", TIPO_CADENA, ["valor"]),
            
            # azar() → entero
            ("azar", TIPO_ENTERO, []),
            
            # aRangoSuperior(num) → entero
            ("aRangoSuperior", TIPO_ENTERO, ["num"]),
            
            # aRangoInferior(num) → entero
            ("aRangoInferior", TIPO_ENTERO, ["num"]),
            
            # acampar(ms) → nulo
            ("acampar", TIPO_NULO, ["ms"]),
            
            # calibre(texto) → entero
            ("calibre", TIPO_ENTERO, ["texto"]),
            
            # truncar(num) → entero
            ("truncar", TIPO_ENTERO, ["num"]),
        ]
        
        for nombre, tipo_retorno, parametros in misiones_ambiente:
            simbolo = Simbolo(
                nombre=nombre,
                tipo=Tipo(TipoBase.MISION, nombre=nombre),
                categoria="mision",
                info_extra={
                    "parametros": parametros,
                    "tipo_retorno": tipo_retorno,
                    "es_ambiente": True
                }
            )
            self.scope_actual.declarar(simbolo)
    
    def entrar_scope(self, nombre: str) -> Scope:
        """
        Crea y entra a un nuevo scope hijo del actual.
        Usado al entrar a ejércitos y misiones.
        
        Ejemplo:
            tabla.entrar_scope("Finanzas")     # Al entrar a ejercito Finanzas
            tabla.entrar_scope("calcular")     # Al entrar a mision calcular
        """
        nuevo_scope = Scope(nombre, padre=self.scope_actual)
        self.pila_scopes.append(nuevo_scope)
        self.scope_actual = nuevo_scope
        return nuevo_scope
    
    def salir_scope(self) -> Optional[Scope]:
        """
        Sale del scope actual y vuelve al padre.
        Retorna el scope del que se salió, o None si ya estamos en global.
        
        Ejemplo:
            tabla.salir_scope()  # Al terminar de procesar una misión
        """
        if len(self.pila_scopes) <= 1:
            return None  # No se puede salir del scope global
        
        scope_saliente = self.pila_scopes.pop()
        self.scope_actual = self.pila_scopes[-1]
        return scope_saliente
    
    def declarar(self, nombre: str, tipo: Tipo, categoria: str, 
                 info_extra: Optional[Dict[str, Any]] = None) -> bool:
        """
        Declara un símbolo en el scope actual.
        Retorna False si ya existe en el scope actual (error de redeclaración).
        
        Ejemplo:
            tabla.declarar("total", TIPO_ENTERO, "variable")
            tabla.declarar("calcular", tipo_mision, "mision", {"parametros": ["x"]})
        """
        simbolo = Simbolo(nombre, tipo, categoria, info_extra)
        return self.scope_actual.declarar(simbolo)
    
    def buscar(self, nombre: str) -> Optional[Simbolo]:
        """
        Busca un símbolo comenzando desde el scope actual hacia arriba.
        
        Ejemplo:
            simbolo = tabla.buscar("total")
            if simbolo:
                print(f"Encontrado: {simbolo.tipo}")
        """
        return self.scope_actual.buscar(nombre)
    
    def buscar_local(self, nombre: str) -> Optional[Simbolo]:
        """
        Busca un símbolo solo en el scope actual (no en padres).
        Útil para verificar redeclaraciones.
        """
        return self.scope_actual.buscar_local(nombre)
    
    def esta_en_scope_global(self) -> bool:
        """Verifica si estamos en el scope global"""
        return len(self.pila_scopes) == 1
    
    def obtener_nombre_scope_actual(self) -> str:
        """Retorna el nombre del scope actual"""
        return self.scope_actual.nombre
    
    def __repr__(self):
        nombres_scopes = [scope.nombre for scope in self.pila_scopes]
        return f"TablaSimbolo(scopes: {' → '.join(nombres_scopes)})"