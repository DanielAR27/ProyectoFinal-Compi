# Analizador Léxico y Sintáctico — Lenguaje **C-rvicio Militar**

## Integrantes
- Daniel Alemán Ruiz  
- José Julián Brenes Garro  
- Luis Ángel Meza Chavarría  
- Oscar Roni Ordoñez  
- Sebastián Calvo Hernández  

## Profesor
- Aurelio Sanabria Rodríguez  
- Curso: IC-5701 — Compiladores e Intérpretes  
- Instituto Tecnológico de Costa Rica (ITCR)  
- II Semestre 2025

---

## Introducción
Este repositorio contiene el **analizador léxico y sintáctico** (lexer + parser) del lenguaje **C-rvicio Militar**.  

El compilador procesa código fuente en dos fases:
1. **Análisis Léxico (Explorador)**: Lee texto fuente y produce una lista de tokens con su **lexema**, **tipo** y **atributos**.
2. **Análisis Sintáctico (Parser)**: Consume los tokens y construye un **Árbol de Sintaxis Abstracta (AST)** que representa la estructura del programa.

**Flujo general**: `Código fuente → Tokens → AST`

---

## Estructura del proyecto

```
proyecto4_verificador_y_generador/
├── main.py                  # Pipeline completo
├── token_crvicio.py         # Definición de la clase Token
├── ast_crvicio.py           # Definición de nodos del AST
├── demo.crv                 # Código de ejemplo del lenguaje
├── ejemplos/                # Ejemplos válidos según la gramática
├── lexer/
│   ├── __init__.py
│   ├── explorador.py        # Explorador (Analizador léxico)
│   └── __main__.py          # CLI del lexer independiente
├── parser/
│   ├── __init__.py
│   ├── analizador.py        # Analizador sintáctico LL(1)
│   └── __main__.py          # CLI del parser independiente
├── verificador/
│   ├── __init__.py       
│   ├── __main__.py          # CLI del verificador independiente
│   ├── tabla_simbolos.py
│   ├── tipos.py        
│   └── verificador.py
└── README.md
```

---

## ¿Cómo funciona?

### Fase 1: Análisis Léxico (Explorador)
El archivo `lexer/explorador.py` implementa el explorador léxico:

1. **Tabla de patrones (regex)**: define reglas para comentarios, espacios, saltos de línea, cadenas, números, operadores, símbolos e identificadores.
2. **Clasificación**:
   - Identificadores que coinciden con **palabras clave** se reclasifican como `PALABRA_CLAVE`.
   - Los literales `afirmativo`, `negativo` y `nulo` se clasifican como `LIT_BOOLEANO` y `LIT_NULO`.
   - Números enteros y flotantes se clasifican como `NUM_ENTERO` y `NUM_FLOTANTE`.
   - Cadenas se clasifican como `CADENA` (sin las comillas).
3. **Ignora** espacios y comentarios.
4. **Opcional**: puede emitir tokens de salto de línea (`NL`) y operar en **modo tolerante** para no detenerse ante caracteres desconocidos.

### Fase 2: Análisis Sintáctico (Parser)
El archivo `parser/analizador.py` implementa un parser LL(1) con descenso recursivo:

1. **Consume tokens** generados por el lexer.
2. **Verifica la gramática** del lenguaje C-rvicio Militar.
3. **Construye el AST** con nodos definidos en `ast_crvicio.py`.
4. **Maneja precedencia** de operadores: `||` < `&&` < `==, !=` < `<, <=, >, >=` < `+, -` < `*, /, %` < unarios (`-`, `!`)

### Tokens reconocidos (resumen)
- **Palabras clave**: `ejercito`, `global`, `var`, `mision`, `severidad`, `estricto`, `advertencia`,  
  `revisar`, `ejecutar`, `confirmar`, `si`, `por`, `defecto`, `estrategia`, `atacar`, `mientras`,  
  `retirada`, `con`, `abortar`, `avanzar`
- **Literales especiales**: `afirmativo` (LIT_BOOLEANO), `negativo` (LIT_BOOLEANO), `nulo` (LIT_NULO)
- **Misiones de ambiente** (identificadores especiales): `reportar`, `recibir`, `clasificarNumero`, `clasificarMensaje`, `azar`, `aRangoSuperior`, `aRangoInferior`, `acampar`, `calibre`, `truncar`
- **Números**: `NUM_ENTERO`, `NUM_FLOTANTE`
- **Cadenas**: `CADENA` (entre comillas dobles, sin saltos de línea)
- **Operadores**: `|| && == != <= >= += -= *= /= %= = + - * / % < > !`
- **Símbolos**: `(` `)` `{` `}` `[` `]` `.` `,` `:`
- **Identificadores**: `IDENT` (letra o `_` seguido de letras, dígitos o `_`)

---

## Requisitos
- Python **3.10** o superior

---

## Uso

### 1) Pipeline completo (Lexer + Parser)

```bash
# Compilar un archivo (muestra el AST)
python main.py programa.crvicio

# Modo detallado (muestra cada fase)
python main.py programa.crvicio --verbose

# AST en formato JSON
python main.py programa.crvicio --json

# Ver tokens y AST
python main.py programa.crvicio --tokens --verbose

# Solo análisis léxico
python main.py programa.crvicio --solo-tokens

# Leer desde stdin
cat programa.crvicio | python main.py -
echo "mision test() { ejecutar: var x = 5 }" | python main.py -

# Modo tolerante (lexer no falla con caracteres desconocidos)
python main.py programa.crvicio --tolerant
```

### 2) Usar el lexer independientemente

```bash
# Ejecutar solo el lexer (como módulo)
python -m lexer programa.crvicio

# Tabla de tokens
python -m lexer programa.crvicio --tabla

# JSON de tokens
python -m lexer programa.crvicio --json

# Incluir saltos de línea
python -m lexer programa.crvicio --include-nl

# Modo tolerante
python -m lexer programa.crvicio --tolerant
```

### 3) Usar el parser independientemente

```bash
# Ejecutar solo el parser (asume que el código es válido léxicamente)
python -m parser programa.crvicio

# AST en JSON
python -m parser programa.crvicio --json

# Con modo tolerante en el lexer
python -m parser programa.crvicio --tolerant
```

---

## Ejemplos

### Ejemplo 1: Programa válido

**archivo: `ejemplo.crvicio`**
```
ejercito Finanzas {
  global var total = 100
  
  mision calcular(cuotas) severidad=estricto {
    revisar:
      cuotas > 0
    
    ejecutar:
      var base = truncar(total / cuotas)
      reportar("Cuota base: " + base)
      retirada con base
    
    confirmar:
      base > 0
  }
}
```

**Comando:**
```bash
python main.py ejemplo.crvicio --verbose
```

**Salida:**
```
============================================================
FASE 1: Análisis Léxico (Explorador)
============================================================
✓ Tokenización exitosa: 49 tokens generados

============================================================
FASE 2: Análisis Sintáctico (Parser)
============================================================
✓ Parsing exitoso: AST generado correctamente

============================================================
RESULTADO: AST Generado
============================================================
Programa(
  cuerpo=[
    EjercitoDecl(
      nombre='Finanzas'
      cuerpo=[
        DeclaracionGlobal(
          nombre='total'
          valor=LiteralNumero(valor=100, tipo='entero')
        )
        DefMision(
          nombre='calcular'
          parametros=['cuotas']
          seccion_ejecutar=SeccionEjecutar(...)
          severidad='estricto'
          seccion_revisar=SeccionRevisar(...)
          seccion_confirmar=SeccionConfirmar(...)
        )
      ]
    )
  ]
)

✓ Compilación exitosa
```

### Ejemplo 2: Ver solo los tokens

**Comando:**
```bash
python main.py ejemplo.crvicio --solo-tokens
```

**Salida:**
```
Lexema     | Tipo          | Atributos                                
-----------+---------------+------------------------------------------
ejercito   | PALABRA_CLAVE | {"fila": 1, "columna": 1}                
Finanzas   | IDENT         | {"fila": 1, "columna": 10}               
{          | SIMBOLO       | {"fila": 1, "columna": 19}               
global     | PALABRA_CLAVE | {"fila": 2, "columna": 3}                
var        | PALABRA_CLAVE | {"fila": 2, "columna": 10}               
...
```

### Ejemplo 3: Error léxico

**archivo: `error_lexico.crvicio`**
```
ejercito Test {
  var x = 10 @ 5
}
```

**Comando:**
```bash
python main.py error_lexico.crvicio
```

**Salida:**
```
Error léxico: Carácter no reconocido en fila 2, columna 14: '@'
```

**Modo tolerante:**
```bash
python main.py error_lexico.crvicio --tolerant
```
El lexer genera un token ERROR pero continúa. El parser probablemente falle después.

### Ejemplo 4: Error sintáctico

**archivo: `error_sintactico.crvicio`**
```
mision test() {
  var x = 
}
```

**Comando:**
```bash
python main.py error_sintactico.crvicio
```

**Salida:**
```
Error sintáctico: Expresión primaria no reconocida: } (tipo: SIMBOLO) en fila 3
```

---

## Opciones de línea de comandos (main.py)

### Opciones de salida:
- `--json` - Imprime el AST en formato JSON
- `--tokens` - Muestra la tabla de tokens antes del AST
- `--solo-tokens` - Solo ejecuta el lexer (no parsea)

### Opciones de compilación:
- `--tolerant` - Modo tolerante: el lexer genera tokens ERROR en vez de fallar
- `--verbose`, `-v` - Modo detallado: muestra información de cada fase

### Entrada:
- `archivo.crvicio` - Archivo de código fuente
- `-` - Lee desde stdin

---

## Nodos del AST

El AST está definido en `ast_crvicio.py` con los siguientes tipos de nodos:

**Programa y contenedores:**
- `Programa`: Raíz del programa
- `EjercitoDecl`: Declaración de ejército (namespace/módulo)

**Variables:**
- `DeclaracionGlobal`: Variable global
- `DeclaracionLocal`: Variable local

**Misiones (funciones):**
- `DefMision`: Definición de misión con secciones revisar/ejecutar/confirmar
- `SeccionRevisar`, `SeccionEjecutar`, `SeccionConfirmar`

**Sentencias:**
- `Asignacion`: Asignación a variable
- `BucleAtacar`: Bucle while
- `SentEstrategia`: Condicional if-elif-else
- `Retirada`: Return
- `Abortar`: Break
- `Avanzar`: Continue
- `SentenciaLlamada`: Llamada a función como sentencia
- `Bloque`, `ComandoSimple`

**Expresiones:**
- `ExpBinaria`: Operador binario
- `ExpUnaria`: Operador unario
- `ExpPostfijo`: Acceso a miembros, indexación
- `Llamada`: Llamada a función
- `Referencia`: Referencia a variable (puede tener punto: `a.b.c`)
- `Identificador`: Identificador simple

**Literales:**
- `LiteralNumero`: Entero o flotante
- `LiteralCadena`: Cadena de texto
- `LiteralBooleano`: `afirmativo` o `negativo`
- `LiteralNulo`: `nulo`

Todos los nodos tienen campos opcionales `fila` y `columna` para diagnósticos.

---

## Notas técnicas

### Análisis Léxico (Explorador)
- Utiliza expresiones regulares compiladas con el módulo `re` de Python
- Clasifica tokens en una sola pasada sobre el código fuente
- Mantiene seguimiento de línea y columna para mensajes de error precisos
- Modo tolerante: genera tokens `ERROR` en lugar de abortar

### Análisis Sintáctico (Parser)
- **Técnica**: Descenso recursivo (LL(1))
- **Precedencia de operadores**: Implementada mediante niveles de parsing recursivo
- **Lookahead**: Usa 1 token de lookahead para distinguir entre construcciones similares
- **Manejo de errores**: Reporta posición exacta del error con contexto
- **Restricción top-level**: Solo permite `ejercito`, `mision` y `global` en el nivel superior del programa

### Consideraciones
- El código fuente utiliza nombres en español sin tildes (por ejemplo, `tokenizar`, `Explorador`, `Analizador`)
- Comentarios soportados: `//` y `/* */`
- Los identificadores de misiones ambiente (`reportar`, `recibir`, etc.) se tratan como identificadores normales en el lexer; el parser los reconoce por contexto

---

## Testing

Para probar el compilador con los ejemplos de la gramática:

```bash
# Ejemplo 1: Repartición de pagos
python main.py ejemplos/ejercicio1.crvicio --verbose

# Ejemplo 2: Verificador de palíndromos
python main.py ejemplos/ejercicio2.crvicio --json

# Ejemplo 3: Contador de palabras
python main.py ejemplos/ejercicio3.crvicio --tokens
```

---

## Próximas fases

Este proyecto implementa las dos primeras fases del compilador. Las siguientes fases serán:

1. **Análisis Semántico (Verificador)**: Verificación de tipos, variables declaradas, etc.
2. **Generación de Código**: Traducción del AST a código objetivo

---

## Ayuda

Para ver todas las opciones disponibles:

```bash
python main.py --help
python -m lexer --help
python -m parser --help
```

---