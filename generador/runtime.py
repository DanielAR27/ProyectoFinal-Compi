#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime para C-rvicio Militar
Implementa las misiones ambiente (funciones built-in) del lenguaje
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

import sys
import random
import math
import time


class RuntimeCrvicio:
    """
    Funciones de ambiente (built-in) para C-rvicio Militar.
    Estas funciones están disponibles globalmente en los programas generados.
    """
    
    @staticmethod
    def reportar(mensaje):
        """Imprime un mensaje (equivalente a print)"""
        print(mensaje)
    
    @staticmethod
    def recibir(prompt=""):
        """Lee entrada del usuario (equivalente a input)"""
        if prompt:
            return input(prompt)
        return input()
    
    @staticmethod
    def clasificarNumero(texto):
        """Convierte texto a número entero (equivalente a parseInt)"""
        try:
            return int(texto)
        except (ValueError, TypeError):
            return 0  # Retorna 0 si falla la conversión
    
    @staticmethod
    def clasificarMensaje(valor):
        """Convierte valor a cadena (equivalente a toString)"""
        return str(valor)
    
    @staticmethod
    def azar():
        """Genera un número aleatorio entero (equivalente a random)"""
        return random.randint(0, 2147483647)  # Max int de 32 bits
    
    @staticmethod
    def aRangoSuperior(num):
        """Redondea hacia arriba (equivalente a ceil)"""
        return math.ceil(num)
    
    @staticmethod
    def aRangoInferior(num):
        """Redondea hacia abajo (equivalente a floor)"""
        return math.floor(num)
    
    @staticmethod
    def acampar(ms):
        """Pausa la ejecución (equivalente a sleep)"""
        time.sleep(ms / 1000.0)  # Convierte ms a segundos
    
    @staticmethod
    def calibre(texto):
        """Retorna la longitud de una cadena (equivalente a len)"""
        return len(texto)
    
    @staticmethod
    def truncar(num):
        """Obtiene la parte entera de un número (equivalente a trunc)"""
        return math.trunc(num)
    
    @classmethod
    def obtener_funciones_ambiente(cls):
        """
        Retorna un diccionario con todas las funciones ambiente
        para inyectarlas en el código generado.
        """
        return {
            'reportar': cls.reportar,
            'recibir': cls.recibir,
            'clasificarNumero': cls.clasificarNumero,
            'clasificarMensaje': cls.clasificarMensaje,
            'azar': cls.azar,
            'aRangoSuperior': cls.aRangoSuperior,
            'aRangoInferior': cls.aRangoInferior,
            'acampar': cls.acampar,
            'calibre': cls.calibre,
            'truncar': cls.truncar,
        }