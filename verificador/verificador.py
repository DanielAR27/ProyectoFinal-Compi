#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador Semántico para C-rvicio Militar
Realiza análisis semántico sobre el AST
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)
"""

from typing import Optional, List, Dict, Any
import ast_crvicio as ast
from .tipos import (
    Tipo, TipoBase, VerificadorTipos,
    TIPO_ENTERO, TIPO_FLOTANTE, TIPO_CADENA, 
    TIPO_BOOLEANO, TIPO_NULO, TIPO_DESCONOCIDO
)
from .tabla_simbolos import TablaSimbolo


# -------------------------
# Excepciones
# -------------------------

class VerificadorError(Exception):
    """Error de verificación semántica"""
    pass


# -------------------------
# Verificador
# -------------------------

class Verificador:
    """
    Verificador semántico que recorre el AST y valida reglas semánticas.
    
    Usa el patrón Visitor: cada tipo de nodo tiene su método visitar_*.
    """
    
    def __init__(self):
        self.tabla = TablaSimbolo()
        self.errores: List[str] = []
        
        # Contexto durante la verificación
        self.mision_actual: Optional[ast.DefMision] = None
        self.en_bucle: bool = False
        self.tipo_retorno_esperado: Optional[Tipo] = None
        self.tipo_retorno_actual: Optional[Tipo] = None
    
    # -------------------------
    # Punto de entrada
    # -------------------------
    
    def verificar(self, programa: ast.Programa) -> List[str]:
        """
        Punto de entrada principal.
        Retorna lista de errores (vacía si no hay errores).
        """
        self.errores = []
        
        try:
            self.visitar_programa(programa)
        except VerificadorError as e:
            self.errores.append(str(e))
        
        return self.errores
    
    # -------------------------
    # Utilidades de error
    # -------------------------
    
    def error(self, mensaje: str, nodo: Optional[ast.NodoAST] = None):
        """
        Reporta un error y lo agrega a la lista.
        Si el nodo tiene posición, la incluye en el mensaje.
        """
        if nodo and hasattr(nodo, 'fila') and nodo.fila:
            ubicacion = f" en línea {nodo.fila}"
            if hasattr(nodo, 'columna') and nodo.columna:
                ubicacion += f", columna {nodo.columna}"
            mensaje_completo = f"Error semántico{ubicacion}: {mensaje}"
        else:
            mensaje_completo = f"Error semántico: {mensaje}"
        
        self.errores.append(mensaje_completo)
    
    # -------------------------
    # Visitors - Programa y Contenedores
    # -------------------------
    
    def visitar_programa(self, nodo: ast.Programa):
        """
        Programa ::= ( EjercitoDecl | DefMision | DeclaracionGlobal | Sentencia )+
        """
        # Primera pasada: declarar todos los ejércitos y misiones globales
        # (para permitir referencias forward)
        for item in nodo.cuerpo:
            if isinstance(item, ast.EjercitoDecl):
                self.pre_declarar_ejercito(item)
            elif isinstance(item, ast.DefMision):
                self.pre_declarar_mision(item)
        
        # Segunda pasada: verificar el contenido
        for item in nodo.cuerpo:
            if isinstance(item, ast.EjercitoDecl):
                self.visitar_ejercito_decl(item)
            elif isinstance(item, ast.DefMision):
                self.visitar_def_mision(item)
            elif isinstance(item, ast.DeclaracionGlobal):
                self.visitar_declaracion_global(item)
            elif isinstance(item, ast.Sentencia):
                self.visitar_sentencia(item)
    
    def pre_declarar_ejercito(self, nodo: ast.EjercitoDecl):
        """
        Pre-declara un ejército en el scope global sin procesar su contenido.
        Permite referencias forward (usar antes de definir completamente).
        """
        tipo_ejercito = Tipo(TipoBase.EJERCITO, nombre=nodo.nombre)
        
        if not self.tabla.declarar(nodo.nombre, tipo_ejercito, "ejercito"):
            self.error(f"El ejército '{nodo.nombre}' ya fue declarado", nodo)
    
    def pre_declarar_mision(self, nodo: ast.DefMision):
            """
            Pre-declara una misión sin procesar su cuerpo.
            """
            tipo_mision = Tipo(TipoBase.MISION, nombre=nodo.nombre)
            
            # Inferir tipos básicos de parámetros (por ahora todos DESCONOCIDO)
            tipos_params = self._inferir_tipos_parametros_basico(nodo)
            
            info_extra = {
                "parametros": nodo.parametros,
                "tipos_params": tipos_params,
                "severidad": nodo.severidad,
                "tipo_retorno": TIPO_DESCONOCIDO
            }
            
            if not self.tabla.declarar(nodo.nombre, tipo_mision, "mision", info_extra):
                self.error(f"La misión '{nodo.nombre}' ya fue declarada", nodo)
        
    def visitar_ejercito_decl(self, nodo: ast.EjercitoDecl):
        """
        EjercitoDecl ::= "ejercito" IDENT BloqueEjercito
        """
        # Buscar el símbolo del ejército ANTES de entrar a su scope
        simbolo_ejercito = self.tabla.buscar(nodo.nombre)
        
        # Entrar al scope del ejército
        scope_ejercito = self.tabla.entrar_scope(nodo.nombre)
        
        # Guardar INMEDIATAMENTE la referencia al scope (antes de procesar contenido)
        if simbolo_ejercito:
            simbolo_ejercito.info_extra["scope"] = scope_ejercito
        
        # Pre-declarar misiones del ejército (para referencias forward)
        for item in nodo.cuerpo:
            if isinstance(item, ast.DefMision):
                self.pre_declarar_mision(item)
        
        # Procesar contenido del ejército
        for item in nodo.cuerpo:
            if isinstance(item, ast.DefMision):
                self.visitar_def_mision(item)
            elif isinstance(item, ast.DeclaracionGlobal):
                self.visitar_declaracion_global(item)
            elif isinstance(item, ast.Sentencia):
                self.visitar_sentencia(item)
        
        # Salir del scope del ejército
        self.tabla.salir_scope()
    
    # -------------------------
    # Variables
    # -------------------------
    
    def visitar_declaracion_global(self, nodo: ast.DeclaracionGlobal):
        """
        DeclaracionGlobal ::= "global" "var" IDENT ( "=" Expresion )?
        """
        # Si tiene valor inicial, inferir tipo de la expresión
        if nodo.valor:
            tipo_valor = self.visitar_expresion(nodo.valor)
            
            # Declarar con el tipo inferido
            if not self.tabla.declarar(nodo.nombre, tipo_valor, "variable"):
                self.error(f"La variable '{nodo.nombre}' ya fue declarada", nodo)
        else:
            # Sin inicialización, tipo desconocido inicialmente
            if not self.tabla.declarar(nodo.nombre, TIPO_DESCONOCIDO, "variable"):
                self.error(f"La variable '{nodo.nombre}' ya fue declarada", nodo)
    
    def visitar_declaracion_local(self, nodo: ast.DeclaracionLocal):
        """
        DeclaracionLocal ::= "var" IDENT ( "=" Expresion )?
        """
        # Similar a global pero en scope local
        if nodo.valor:
            tipo_valor = self.visitar_expresion(nodo.valor)
            
            if not self.tabla.declarar(nodo.nombre, tipo_valor, "variable"):
                self.error(f"La variable '{nodo.nombre}' ya fue declarada en este scope", nodo)
        else:
            if not self.tabla.declarar(nodo.nombre, TIPO_DESCONOCIDO, "variable"):
                self.error(f"La variable '{nodo.nombre}' ya fue declarada en este scope", nodo)
    
    # -------------------------
    # Misiones
    # -------------------------
    
    def visitar_def_mision(self, nodo: ast.DefMision):
        """
        DefMision ::= "mision" IDENT "(" Parametros? ")" 
                    ( "severidad" "=" ( "estricto" | "advertencia" ) )?
                    BloqueMision
        """
        # Guardar contexto
        mision_anterior = self.mision_actual
        tipo_retorno_anterior = self.tipo_retorno_actual  
        
        self.mision_actual = nodo
        self.tipo_retorno_actual = None 
        
        # Entrar al scope de la misión
        self.tabla.entrar_scope(nodo.nombre)
        
        # Declarar parámetros como variables locales
        for param in nodo.parametros:
            # Los parámetros tienen tipo desconocido (inferencia dinámica)
            if not self.tabla.declarar(param, TIPO_DESCONOCIDO, "variable"):
                self.error(f"El parámetro '{param}' está duplicado", nodo)
        
        # Verificar sección revisar (precondiciones)
        if nodo.seccion_revisar:
            self.visitar_seccion_revisar(nodo.seccion_revisar)
        
        # Verificar sección ejecutar (cuerpo)
        if nodo.seccion_ejecutar:
            self.visitar_seccion_ejecutar(nodo.seccion_ejecutar)
        else:
            self.error("La misión debe tener una sección 'ejecutar'", nodo)
        
        # Verificar sección confirmar (postcondiciones)
        if nodo.seccion_confirmar:
            self.visitar_seccion_confirmar(nodo.seccion_confirmar)
        
        # Actualizar tipo de retorno inferido de la misión
        # CAMBIO: Buscar símbolo antes de salir del scope para poder inferir tipo
        simbolo = self.tabla.buscar(nodo.nombre)
        if simbolo:
            # Si hay retorno explícito (retirada con), usarlo
            if self.tipo_retorno_actual:
                tipo_retorno_inferido = self.tipo_retorno_actual
            # Si no hay retorno explícito pero hay confirmar, inferir desde ahí
            elif nodo.seccion_confirmar:
                tipo_retorno_inferido = self._inferir_tipo_desde_confirmar(nodo)
            # Si no hay ni retorno ni confirmar, es NULO
            else:
                tipo_retorno_inferido = TIPO_NULO
            
            simbolo.info_extra["tipo_retorno"] = tipo_retorno_inferido
        
        # Salir del scope de la misión
        self.tabla.salir_scope()
        
        # Restaurar contexto
        self.mision_actual = mision_anterior
        self.tipo_retorno_actual = tipo_retorno_anterior
 
    def _inferir_tipo_desde_confirmar(self, nodo: ast.DefMision) -> Tipo:
        """
        Infiere el tipo de retorno implícito analizando las variables locales
        mencionadas en la sección confirmar.
        
        Estrategia:
        1. Extraer todos los identificadores usados en confirmar
        2. Buscar el primero que sea una variable local (no parámetro, no global)
        3. Retornar el tipo de esa variable
        
        Ejemplo:
            confirmar:
                texto != nulo        # <- 'texto' es variable local de tipo CADENA
                calibre(texto) > 0
            
            Retorna: TIPO_CADENA
        """
        if not nodo.seccion_confirmar:
            return TIPO_NULO
        
        # Extraer identificadores de todas las condiciones en confirmar
        identificadores_usados = set()
        for condicion in nodo.seccion_confirmar.condiciones:
            ids = self._extraer_identificadores(condicion)
            identificadores_usados.update(ids)
        
        # Buscar el primer identificador que sea una variable local
        for nombre_var in identificadores_usados:
            simbolo = self.tabla.buscar_local(nombre_var)
            
            # Solo considerar variables locales (no parámetros de la misión)
            if simbolo and simbolo.categoria == "variable":
                # Verificar que no sea un parámetro
                if nombre_var not in nodo.parametros:
                    return simbolo.tipo
        
        # No se encontró ninguna variable local apropiada
        return TIPO_NULO

    def _extraer_identificadores(self, expresion) -> set:
        """
        Extrae recursivamente todos los nombres de identificadores de una expresión.
        
        Retorna un conjunto con los nombres encontrados.
        
        Ejemplo:
            texto != nulo && calibre(texto) > 0
            
            Retorna: {"texto", "nulo", "calibre"}
        """
        identificadores = set()
        
        # Caso base: Identificador simple
        if isinstance(expresion, ast.Identificador):
            identificadores.add(expresion.nombre)
            return identificadores
        
        # Caso: Referencia (puede tener múltiples nombres)
        if isinstance(expresion, ast.Referencia):
            # Solo tomar el primer nombre (antes del punto)
            if expresion.nombres:
                identificadores.add(expresion.nombres[0])
            return identificadores
        
        # Caso: Llamada (extraer el nombre de la función)
        if isinstance(expresion, ast.Llamada):
            identificadores.add(expresion.nombre)
            # También extraer identificadores de los argumentos
            for arg in expresion.argumentos:
                identificadores.update(self._extraer_identificadores(arg))
            return identificadores
        
        # Caso recursivo: cualquier nodo con atributos
        if hasattr(expresion, '__dict__'):
            for atributo, valor in expresion.__dict__.items():
                # Saltar atributos de metadatos
                if atributo in ('fila', 'columna', 'tipo'):
                    continue
                
                # Procesar listas
                if isinstance(valor, list):
                    for item in valor:
                        if hasattr(item, '__dict__'):
                            identificadores.update(self._extraer_identificadores(item))
                
                # Procesar nodos anidados
                elif hasattr(valor, '__dict__'):
                    identificadores.update(self._extraer_identificadores(valor))
        
        return identificadores
    
    def _inferir_tipos_parametros_basico(self, nodo: ast.DefMision) -> Dict[str, Tipo]:
            """
            Intenta inferir tipos básicos de parámetros analizando su primer uso.
            Esta es una inferencia simple: solo detecta literales o operaciones obvias.
            """
            tipos_inferidos = {}
            
            # Por ahora, no hacemos inferencia compleja
            # Solo marcamos que todos son TIPO_DESCONOCIDO
            for param in nodo.parametros:
                tipos_inferidos[param] = TIPO_DESCONOCIDO
            
            return tipos_inferidos
    
    def visitar_seccion_revisar(self, nodo: ast.SeccionRevisar):
        """
        SeccionRevisar ::= "revisar" ":" Condicion+
        Las condiciones deben ser expresiones booleanas
        """
        for condicion in nodo.condiciones:
            tipo = self.visitar_expresion(condicion)
            
            # Verificar que sea booleana o al menos comparable
            if tipo.base != TipoBase.BOOLEANO and tipo.base != TipoBase.DESCONOCIDO:
                self.error(f"La precondición debe ser una expresión booleana, pero es {tipo}", condicion)
    
    def visitar_seccion_ejecutar(self, nodo: ast.SeccionEjecutar):
        """
        SeccionEjecutar ::= "ejecutar" ":" ( Sentencia )+
        """
        for sentencia in nodo.sentencias:
            self.visitar_sentencia(sentencia)
    
    def visitar_seccion_confirmar(self, nodo: ast.SeccionConfirmar):
        """
        SeccionConfirmar ::= "confirmar" ":" Condicion+
        Las condiciones deben ser expresiones booleanas
        """
        for condicion in nodo.condiciones:
            tipo = self.visitar_expresion(condicion)
            
            if tipo.base != TipoBase.BOOLEANO and tipo.base != TipoBase.DESCONOCIDO:
                self.error(f"La postcondición debe ser una expresión booleana, pero es {tipo}", condicion)
    
    # -------------------------
    # Sentencias
    # -------------------------
    
    def visitar_sentencia(self, nodo: ast.Sentencia):
        """Dispatcher para diferentes tipos de sentencias"""
        if isinstance(nodo, ast.DeclaracionLocal):
            self.visitar_declaracion_local(nodo)
        
        elif isinstance(nodo, ast.Asignacion):
            self.visitar_asignacion(nodo)
        
        elif isinstance(nodo, ast.SentenciaLlamada):
            self.visitar_sentencia_llamada(nodo)
        
        elif isinstance(nodo, ast.BucleAtacar):
            self.visitar_bucle_atacar(nodo)
        
        elif isinstance(nodo, ast.Retirada):
            self.visitar_retirada(nodo)
        
        elif isinstance(nodo, ast.SentEstrategia):
            self.visitar_sent_estrategia(nodo)
        
        elif isinstance(nodo, ast.Abortar):
            self.visitar_abortar(nodo)
        
        elif isinstance(nodo, ast.Avanzar):
            self.visitar_avanzar(nodo)
        
        else:
            self.error(f"Tipo de sentencia no reconocido: {type(nodo).__name__}", nodo)
    
    def visitar_asignacion(self, nodo: ast.Asignacion):
        """
        Asignacion ::= Referencia OpAsignacion Expresion
        Permite declaración implícita: si la variable no existe, se crea automáticamente
        """
        # Obtener el símbolo de la variable
        nombre_var = nodo.referencia.nombres[0] if nodo.referencia.nombres else None
        
        if not nombre_var:
            self.error("Referencia inválida en asignación", nodo)
            return
        
        simbolo = self.tabla.buscar(nombre_var)
        
        # Si la variable no existe y es asignación simple (=), crearla implícitamente
        if not simbolo:
            if nodo.operador == "=":
                # Declaración implícita: evaluar el valor y crear la variable
                tipo_valor = self.visitar_expresion(nodo.valor)
                self.tabla.declarar(nombre_var, tipo_valor, "variable")
                return
            else:
                # Operadores compuestos requieren que la variable ya exista
                self.error(f"Variable '{nombre_var}' no declarada", nodo)
                return
        
        if simbolo.categoria != "variable":
            self.error(f"'{nombre_var}' no es una variable", nodo)
            return
        
        # Evaluar el lado derecho
        tipo_valor = self.visitar_expresion(nodo.valor)
        
        # Si la variable es DESCONOCIDO, actualizar su tipo
        if simbolo.tipo.base == TipoBase.DESCONOCIDO:
            simbolo.tipo = tipo_valor
        # Si el valor es DESCONOCIDO pero la variable tiene tipo, permitir (inferencia inversa)
        elif tipo_valor.base == TipoBase.DESCONOCIDO:
            # No hacer nada, permitir la asignación
            pass
        # Si no, verificar compatibilidad normal
        elif not VerificadorTipos.son_compatibles(simbolo.tipo, tipo_valor):
            self.error(
                f"No se puede asignar {tipo_valor} a {simbolo.tipo}",
                nodo
            )
        
        # Para operadores compuestos (+=, -=, etc.), verificar que sean numéricos
        if nodo.operador in ('+=', '-=', '*=', '/=', '%='):
            if not simbolo.tipo.es_numerico():
                self.error(f"El operador '{nodo.operador}' requiere tipos numéricos", nodo)
    
    def visitar_sentencia_llamada(self, nodo: ast.SentenciaLlamada):
        """Llamada a misión como sentencia (sin usar el retorno)"""
        self.visitar_llamada(nodo.llamada)
    
    def visitar_retirada(self, nodo: ast.Retirada):
        """
        Retirada ::= "retirada" ( "con" Expresion )?
        Verifica que estemos dentro de una misión y tipos consistentes
        """
        if self.mision_actual is None:
            self.error("'retirada' solo puede usarse dentro de una misión", nodo)
            return
        
        # Si retorna un valor
        if nodo.valor:
            tipo_valor = self.visitar_expresion(nodo.valor)
            
            # Verificar consistencia de tipos de retorno
            if self.tipo_retorno_actual is None:
                # Primer retorno: establecer el tipo esperado
                self.tipo_retorno_actual = tipo_valor
            else:
                # Si el tipo actual o el nuevo es DESCONOCIDO, permitir (inferencia dinámica)
                if tipo_valor.base == TipoBase.DESCONOCIDO or self.tipo_retorno_actual.base == TipoBase.DESCONOCIDO:
                    # Actualizar al tipo conocido si uno de los dos es DESCONOCIDO
                    if tipo_valor.base != TipoBase.DESCONOCIDO:
                        self.tipo_retorno_actual = tipo_valor
                # Verificar que coincida con retornos anteriores
                elif not VerificadorTipos.son_compatibles(self.tipo_retorno_actual, tipo_valor):
                    self.error(
                        f"Tipo de retorno inconsistente: se esperaba {self.tipo_retorno_actual}, "
                        f"pero se encontró {tipo_valor}",
                        nodo
                    )
        else:
            # Retorno sin valor: NULO
            if self.tipo_retorno_actual is None:
                self.tipo_retorno_actual = TIPO_NULO
            elif self.tipo_retorno_actual.base != TipoBase.NULO and self.tipo_retorno_actual.base != TipoBase.DESCONOCIDO:
                self.error(
                    f"Tipo de retorno inconsistente: se esperaba {self.tipo_retorno_actual}, "
                    f"pero 'retirada' sin valor retorna nulo",
                    nodo
                )
    
    def visitar_bucle_atacar(self, nodo: ast.BucleAtacar):
        """
        BucleAtacar ::= "atacar" "mientras" "(" Expresion ")" ComandoSimple
        """
        # Verificar que la condición sea booleana
        tipo_condicion = self.visitar_expresion(nodo.condicion)
        
        if tipo_condicion.base != TipoBase.BOOLEANO and tipo_condicion.base != TipoBase.DESCONOCIDO:
            self.error(
                f"La condición del bucle debe ser booleana, pero es {tipo_condicion}",
                nodo.condicion
            )
        
        # Marcar que estamos en un bucle (para validar abortar/avanzar)
        en_bucle_anterior = self.en_bucle
        self.en_bucle = True
        
        # Verificar el cuerpo
        self.visitar_comando_simple(nodo.cuerpo)
        
        # Restaurar estado
        self.en_bucle = en_bucle_anterior
    
    def visitar_sent_estrategia(self, nodo: ast.SentEstrategia):
        """
        SentEstrategia ::= "estrategia" RamaCondicional+ RamaDefecto?
        """
        # Verificar cada rama condicional
        for rama in nodo.ramas_condicionales:
            self.visitar_rama_condicional(rama)
        
        # Verificar rama por defecto si existe
        if nodo.rama_defecto:
            self.visitar_comando_simple(nodo.rama_defecto)
    
    def visitar_rama_condicional(self, nodo: ast.RamaCondicional):
        """RamaCondicional ::= "si" "(" Expresion ")" ComandoSimple"""
        # Verificar que la condición sea booleana
        tipo_condicion = self.visitar_expresion(nodo.condicion)
        
        if tipo_condicion.base != TipoBase.BOOLEANO and tipo_condicion.base != TipoBase.DESCONOCIDO:
            self.error(
                f"La condición debe ser booleana, pero es {tipo_condicion}",
                nodo.condicion
            )
        
        # Verificar el cuerpo
        self.visitar_comando_simple(nodo.cuerpo)
    
    def visitar_abortar(self, nodo: ast.Abortar):
        """Verifica que 'abortar' esté dentro de un bucle"""
        if not self.en_bucle:
            self.error("'abortar' solo puede usarse dentro de un bucle", nodo)
    
    def visitar_avanzar(self, nodo: ast.Avanzar):
        """Verifica que 'avanzar' esté dentro de un bucle"""
        if not self.en_bucle:
            self.error("'avanzar' solo puede usarse dentro de un bucle", nodo)
    
    def visitar_comando_simple(self, nodo: ast.ComandoSimple):
        """ComandoSimple ::= Bloque | Sentencia"""
        if isinstance(nodo.contenido, ast.Bloque):
            self.visitar_bloque(nodo.contenido)
        else:
            self.visitar_sentencia(nodo.contenido)
    
    def visitar_bloque(self, nodo: ast.Bloque):
        """Bloque ::= "{" ( Sentencia )* "}" """
        for sentencia in nodo.sentencias:
            self.visitar_sentencia(sentencia)
            
    # -------------------------
    # Expresiones
    # -------------------------
    
    def visitar_expresion(self, nodo: ast.Expresion) -> Tipo:
        """
        Dispatcher para expresiones.
        Retorna el tipo de la expresión.
        """
        if isinstance(nodo, ast.ExpBinaria):
            return self.visitar_exp_binaria(nodo)
        
        elif isinstance(nodo, ast.ExpUnaria):
            return self.visitar_exp_unaria(nodo)
        
        elif isinstance(nodo, ast.ExpPostfijo):
            return self.visitar_exp_postfijo(nodo)
        
        elif isinstance(nodo, ast.Llamada):
            return self.visitar_llamada(nodo)
        
        elif isinstance(nodo, ast.Referencia):
            return self.visitar_referencia(nodo)
        
        elif isinstance(nodo, ast.Identificador):
            return self.visitar_identificador(nodo)
        
        # Literales
        elif isinstance(nodo, ast.LiteralNumero):
            return self.visitar_literal_numero(nodo)
        
        elif isinstance(nodo, ast.LiteralCadena):
            return self.visitar_literal_cadena(nodo)
        
        elif isinstance(nodo, ast.LiteralBooleano):
            return self.visitar_literal_booleano(nodo)
        
        elif isinstance(nodo, ast.LiteralNulo):
            return self.visitar_literal_nulo(nodo)
        
        else:
            self.error(f"Tipo de expresión no reconocido: {type(nodo).__name__}", nodo)
            return TIPO_DESCONOCIDO
    
    def visitar_exp_binaria(self, nodo: ast.ExpBinaria) -> Tipo:
        """
        ExpBinaria ::= Expresion OPERADOR Expresion
        Verifica tipos y retorna el tipo del resultado
        """
        # Evaluar ambos lados
        tipo_izq = self.visitar_expresion(nodo.izquierda)
        tipo_der = self.visitar_expresion(nodo.derecha)
        
        # Inferir el tipo del resultado
        tipo_resultado = VerificadorTipos.inferir_tipo_operacion_binaria(
            nodo.operador, tipo_izq, tipo_der
        )
        
        if tipo_resultado is None:
            self.error(
                f"Operación '{nodo.operador}' no válida entre {tipo_izq} y {tipo_der}",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        return tipo_resultado
    
    def visitar_exp_unaria(self, nodo: ast.ExpUnaria) -> Tipo:
        """
        ExpUnaria ::= ("-" | "!") Expresion
        Verifica el tipo del operando
        """
        tipo_operando = self.visitar_expresion(nodo.operando)
        
        tipo_resultado = VerificadorTipos.inferir_tipo_operacion_unaria(
            nodo.operador, tipo_operando
        )
        
        if tipo_resultado is None:
            self.error(
                f"Operador unario '{nodo.operador}' no válido para {tipo_operando}",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        return tipo_resultado
    
    def visitar_exp_postfijo(self, nodo: ast.ExpPostfijo) -> Tipo:
        """
        ExpPostfijo ::= Primario ( Postfijo )*
        Postfijo ::= "." IDENT | "." Llamada | "[" Expresion "]"
        """
        # Evaluar la expresión base
        tipo_actual = self.visitar_expresion(nodo.expresion)
        
        # Procesar cada operación postfija en secuencia
        for postfijo in nodo.postfijos:
            if isinstance(postfijo, ast.AccesoMiembro):
                tipo_actual = self.visitar_acceso_miembro(postfijo, tipo_actual, nodo.expresion)
            
            elif isinstance(postfijo, ast.AccesoIndice):
                tipo_actual = self.visitar_acceso_indice(postfijo, tipo_actual, nodo.expresion)
            
            elif isinstance(postfijo, ast.LlamadaPostfijo):
                # Pasar el tipo actual como contexto (ejército)
                tipo_actual = self.visitar_llamada(postfijo.llamada, contexto_tipo=tipo_actual)
            
            else:
                self.error(f"Tipo de postfijo no reconocido: {type(postfijo).__name__}", postfijo)
                tipo_actual = TIPO_DESCONOCIDO
        
        return tipo_actual
    
    def visitar_acceso_miembro(self, nodo: ast.AccesoMiembro, tipo_base: Tipo, expr_base: ast.Expresion) -> Tipo:
        """
        Acceso a miembro: expr.miembro
        Verifica que el tipo base sea un ejército y el miembro existe
        """
        # Solo los ejércitos tienen miembros accesibles
        if tipo_base.base != TipoBase.EJERCITO:
            self.error(
                f"Intento de acceder a miembro '{nodo.miembro}' de tipo {tipo_base}, "
                f"pero solo los ejércitos tienen miembros",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        # Buscar el símbolo del ejército desde el scope global
        # Recorrer la pila de scopes desde el actual hasta encontrarlo
        simbolo_ejercito = None
        for scope in reversed(self.tabla.pila_scopes):
            simbolo_ejercito = scope.buscar_local(tipo_base.nombre)
            if simbolo_ejercito and simbolo_ejercito.categoria == "ejercito":
                break
        
        if not simbolo_ejercito:
            self.error(f"Ejército '{tipo_base.nombre}' no encontrado", nodo)
            return TIPO_DESCONOCIDO
        
        # Obtener el scope del ejército
        scope_ejercito = simbolo_ejercito.info_extra.get("scope")
        
        if not scope_ejercito:
            self.error(
                f"No se puede acceder a miembros de '{tipo_base.nombre}' "
                f"(scope no disponible)",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        # Buscar el miembro en el scope del ejército
        simbolo_miembro = scope_ejercito.buscar_local(nodo.miembro)
        
        if not simbolo_miembro:
            self.error(
                f"'{nodo.miembro}' no existe en el ejército '{tipo_base.nombre}'",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        return simbolo_miembro.tipo
    
    def visitar_acceso_indice(self, nodo: ast.AccesoIndice, tipo_base: Tipo, expr_base: ast.Expresion) -> Tipo:
        """
        Indexación: expr[indice]
        Solo válido para cadenas en C-rvicio Militar
        """
        # Si el tipo es DESCONOCIDO, permitir la indexación (inferencia dinámica)
        if tipo_base.base == TipoBase.DESCONOCIDO:
            tipo_indice = self.visitar_expresion(nodo.indice)
            return TIPO_CADENA  # Asumir que retorna CADENA
        
        # Verificar que el tipo base sea indexable (solo cadenas)
        if not tipo_base.es_iterable():
            self.error(
                f"Intento de indexar tipo {tipo_base}, pero solo las cadenas son indexables",
                nodo
            )
            return TIPO_DESCONOCIDO
        
        # Verificar que el índice sea numérico (entero)
        tipo_indice = self.visitar_expresion(nodo.indice)
        
        if tipo_indice.base != TipoBase.ENTERO and tipo_indice.base != TipoBase.DESCONOCIDO:
            self.error(
                f"El índice debe ser entero, pero es {tipo_indice}",
                nodo.indice
            )
        
        # Indexar una cadena retorna una cadena (un carácter)
        return TIPO_CADENA
    
    def visitar_llamada(self, nodo: ast.Llamada, contexto_tipo: Optional[Tipo] = None) -> Tipo:
        """
        Llamada ::= IDENT "(" Argumentos? ")"
        Verifica que la misión existe y los argumentos coinciden
        
        contexto_tipo: Si se provee, buscar la misión en el scope de ese tipo (ejército)
        """
        # Si hay contexto (llamada desde ejército: Finanzas.mision())
        if contexto_tipo and contexto_tipo.base == TipoBase.EJERCITO:
            simbolo_ejercito = self.tabla.buscar(contexto_tipo.nombre)
            
            if not simbolo_ejercito:
                self.error(f"Ejército '{contexto_tipo.nombre}' no encontrado", nodo)
                return TIPO_DESCONOCIDO
            
            scope_ejercito = simbolo_ejercito.info_extra.get("scope")
            
            if not scope_ejercito:
                self.error(f"No se puede acceder a misiones de '{contexto_tipo.nombre}'", nodo)
                return TIPO_DESCONOCIDO
            
            simbolo = scope_ejercito.buscar_local(nodo.nombre)
        else:
            # Búsqueda normal en scope actual
            simbolo = self.tabla.buscar(nodo.nombre)
        
        if not simbolo:
            self.error(f"Misión '{nodo.nombre}' no declarada", nodo)
            return TIPO_DESCONOCIDO
        
        if simbolo.categoria != "mision":
            self.error(f"'{nodo.nombre}' no es una misión", nodo)
            return TIPO_DESCONOCIDO
        
        # Verificar número de argumentos
        parametros = simbolo.info_extra.get("parametros", [])
        
        if len(nodo.argumentos) != len(parametros):
            self.error(
                f"La misión '{nodo.nombre}' espera {len(parametros)} argumentos, "
                f"pero se proporcionaron {len(nodo.argumentos)}",
                nodo
            )
        
        # Evaluar cada argumento y verificar tipos si están disponibles
        tipos_params = simbolo.info_extra.get("tipos_params", {})
        
        for i, argumento in enumerate(nodo.argumentos):
            tipo_arg = self.visitar_expresion(argumento)
            
            # Si tenemos información de tipos esperados, verificar
            if i < len(parametros):
                nombre_param = parametros[i]
                tipo_esperado = tipos_params.get(nombre_param)
                
                # Solo verificar si el tipo esperado no es DESCONOCIDO
                if tipo_esperado and tipo_esperado.base != TipoBase.DESCONOCIDO:
                    if not VerificadorTipos.son_compatibles(tipo_esperado, tipo_arg):
                        self.error(
                            f"Argumento {i+1} de '{nodo.nombre}': "
                            f"se esperaba {tipo_esperado}, pero se proporcionó {tipo_arg}",
                            argumento
                        )
        
        # Retornar el tipo de retorno de la misión
        tipo_retorno = simbolo.info_extra.get("tipo_retorno", TIPO_DESCONOCIDO)
        return tipo_retorno
    
    def visitar_referencia(self, nodo: ast.Referencia) -> Tipo:
            """
            Referencia ::= IDENT ( "." IDENT )*
            Ejemplo: Finanzas.total o simplemente x
            """
            if len(nodo.nombres) == 1:
                # Referencia simple: solo un nombre
                return self.visitar_identificador_nombre(nodo.nombres[0], nodo)
            
            else:
                # Referencia compuesta: Ejercito.miembro
                nombre_ejercito = nodo.nombres[0]
                
                # Buscar el ejército
                simbolo_ejercito = self.tabla.buscar(nombre_ejercito)
                
                if not simbolo_ejercito:
                    self.error(f"'{nombre_ejercito}' no declarado", nodo)
                    return TIPO_DESCONOCIDO
                
                if simbolo_ejercito.categoria != "ejercito":
                    self.error(f"'{nombre_ejercito}' no es un ejército", nodo)
                    return TIPO_DESCONOCIDO
                
                # Buscar el miembro en el scope del ejército
                scope_ejercito = simbolo_ejercito.info_extra.get("scope")
                
                if not scope_ejercito:
                    self.error(f"No se puede acceder a miembros de '{nombre_ejercito}'", nodo)
                    return TIPO_DESCONOCIDO
                
                # Solo soportamos un nivel: Ejercito.miembro (no Ejercito.a.b.c)
                nombre_miembro = nodo.nombres[1]
                simbolo_miembro = scope_ejercito.buscar_local(nombre_miembro)
                
                if not simbolo_miembro:
                    self.error(f"'{nombre_miembro}' no existe en '{nombre_ejercito}'", nodo)
                    return TIPO_DESCONOCIDO
                
                return simbolo_miembro.tipo
    
    def visitar_identificador(self, nodo: ast.Identificador) -> Tipo:
        """Identificador simple"""
        return self.visitar_identificador_nombre(nodo.nombre, nodo)
    
    def visitar_identificador_nombre(self, nombre: str, nodo: ast.NodoAST) -> Tipo:
        """
        Busca un identificador en la tabla de símbolos y retorna su tipo
        """
        simbolo = self.tabla.buscar(nombre)
        
        if not simbolo:
            self.error(f"Variable o identificador '{nombre}' no declarado", nodo)
            return TIPO_DESCONOCIDO
        
        return simbolo.tipo
    
    # -------------------------
    # Literales
    # -------------------------
    
    def visitar_literal_numero(self, nodo: ast.LiteralNumero) -> Tipo:
        """Literal numérico (entero o flotante)"""
        if nodo.tipo == "entero":
            return TIPO_ENTERO
        return TIPO_FLOTANTE
    
    def visitar_literal_cadena(self, nodo: ast.LiteralCadena) -> Tipo:
        """Literal de cadena"""
        return TIPO_CADENA
    
    def visitar_literal_booleano(self, nodo: ast.LiteralBooleano) -> Tipo:
        """Literal booleano (afirmativo/negativo)"""
        return TIPO_BOOLEANO
    
    def visitar_literal_nulo(self, nodo: ast.LiteralNulo) -> Tipo:
        """Literal nulo"""
        return TIPO_NULO