#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clase Token para el lenguaje C-rvicio Militar
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Token:
    lexema: str
    tipo: str
    atributos: Dict[str, Any]