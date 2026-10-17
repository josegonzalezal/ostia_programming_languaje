# Ostia Programming Language

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Zero-Install](https://img.shields.io/badge/environment-zero--install-brightgreen.svg)](#zero-install-standalone-binaries)

**Ostia** is a natural programming language written in Python, inspired by object-oriented and strongly-typed languages like Java, but completely designed with native **Spanish syntax**. It features native UTF-8 support for accented characters and `ñ`, strong typing with type inference, robust exception handling, interactive I/O, control flow constructs, and a built-in standard math library.

---

## Table of Contents
- [Features](#features)
- [Zero-Install Standalone Binaries](#zero-install-standalone-binaries)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Language Overview & Syntax](#language-overview--syntax)
  - [Data Types](#data-types)
  - [Variable Declarations](#variable-declarations)
  - [Input / Output](#input--output)
  - [Control Flow](#control-flow)
  - [Functions](#functions)
  - [Exception Handling](#exception-handling)
  - [Standard Math Library (`Matematica`)](#standard-math-library-matematica)
- [Code Examples](#code-examples)
- [Multi-Platform Compilation](#multi-platform-compilation)
- [License](#license)

---

## Features

- **Full Spanish Syntax:** Native keywords (`entero`, `si`, `sino`, `mientras`, `funcion`, `intentar`, etc.).
- **UTF-8 Identifier Support:** Full support for accented characters (`á`, `é`, `í`, `ó`, `ú`) and `ñ` in variable names, functions, and string literals.
- **Strong & Explicit Typing:** Standard explicit types (`entero`, `decimal`, `booleano`, `caracter`, `Cadena`) alongside type inference.
- **Structured Control Flow:** `si/sino` conditions, `mientras` loops, `hacer-mientras` loops, and `para` range/step loops.
- **Function Definitions:** Full support for functions with typed parameter lists and return values.
- **Robust Exception System:** Built-in error hierarchy with `intentar`, `capturar`, `finalmente`, and manual throwing using `lanza`/`lanzar`.
- **Standard Math Module:** Integrated constants ($ \pi $, $ e $) and trigonometric/logarithmic operations via the `Matematica` module.
- **Zero-Install Portability:** Native pre-compiled binaries (`ostia.exe`, `ostia-linux`) run out-of-the-box without requiring Python or system installation.

---

## Zero-Install Standalone Binaries

Ostia includes pre-compiled standalone executables in the root directory that eliminate external dependencies (such as Python or Node.js runtime requirements):

- **Windows:** `ostia.exe`
- **Linux:** `ostia-linux`

These binaries can be executed directly from any terminal or integrated seamlessly into local VS Code workflows across platforms.

---

## Installation & Setup

### Requirements
- **Standalone Mode:** No external dependencies or Python installation required.
- **Source Mode (Optional):** Python 3.8+ (only if running directly via `ostia.py`).

### Cloning / Setup
Clone the repository to your local machine:
```bash
git clone https://github.com/your-username/ostia.git
cd ostia
```

---

## Usage

### Running Standalone Executables (Zero-Install)

#### On Windows (PowerShell / CMD)
```powershell
.\ostia.exe path/to/script.ostia
```

#### On Linux
```bash
chmod +x ./ostia-linux
./ostia-linux path/to/script.ostia
```

### Running via Python Source
Run any `.ostia` source file directly using the Python interpreter:
```bash
python ostia.py examples/hello_world.ostia
```
or via module execution:
```bash
python -m ostia examples/hello_world.ostia
```

### VS Code Integration
This repository contains a pre-configured `.vscode/tasks.json` that automatically selects the appropriate platform binary (`ostia.exe` or `ostia-linux`) based on your operating system.

- Press **`Ctrl + Shift + B`** (or `Cmd + Shift + B` on macOS) while viewing any `.ostia` file to execute it instantly in the integrated terminal.

---

## Language Overview & Syntax

### Data Types

| Type Keyword | English Equivalent | Description |
| :--- | :--- | :--- |
| `entero` | `int` | 64-bit signed integers |
| `decimal` | `float` / `double` | Floating-point numbers |
| `booleano` | `boolean` | Logical values (`verdadero`, `falso`) |
| `caracter` | `char` | Single character literal (e.g., `'a'`) |
| `Cadena` | `String` | Text string literal |
| `nulo` | `null` / `None` | Null reference |

---

### Variable Declarations

Variables are declared using explicit types or inferred syntax:

```ostia
entero edad = 25;
decimal pi_aproximado = 3.14159;
booleano esMayor = verdadero;
caracter letra = 'ñ';
Cadena saludo = "¡Hola, mundo!";
```

---

### Input / Output

Ostia provides built-in functions for console interaction:

- `imprimir(...)`: Prints text without a trailing newline.
- `imprimirln(...)`: Prints text followed by a newline.
- `leerLinea(...)`: Reads a line of input from standard input as a `Cadena`.

```ostia
imprimir("Ingrese su nombre: ");
Cadena nombre = leerLinea();
imprimirln("Hola, " + nombre + "!");
```

---

### Control Flow

#### If / Else (`si` / `sino`)
```ostia
entero numero = 10;

si (numero > 0) {
    imprimirln("El número es positivo.");
} sino si (numero < 0) {
    imprimirln("El número es negativo.");
} sino {
    imprimirln("El número es cero.");
}
```

#### While Loop (`mientras`)
```ostia
entero contador = 0;
mientras (contador < 5) {
    imprimirln("Contador: " + contador);
    contador = contador + 1;
}
```

#### Do-While Loop (`hacer ... mientras`)
```ostia
entero i = 0;
hacer {
    imprimirln("Iteración: " + i);
    i = i + 1;
} mientras (i < 3);
```

#### For Loop (`para`)
```ostia
para (entero i = 0; i < 10; i = i + 1) {
    imprimirln("Valor de i: " + i);
}
```

---

### Functions

Functions are declared using the `funcion` keyword, specifying return types and parameter types:

```ostia
funcion entero sumar(entero a, entero b) {
    retornar a + b;
}

funcion nula saludar(Cadena nombre) {
    imprimirln("¡Saludos, " + nombre + "!");
}

// Function call
entero resultado = sumar(15, 27);
saludar("Carlos");
```

---

### Exception Handling

Ostia includes native exception mechanisms using `intentar`, `capturar`, `finalmente`, and `lanza`/`lanzar`.

#### Exception Hierarchy
- `Excepcion` (Base exception)
  - `ExcepcionAritmetica`
  - `ExcepcionNula`
  - `ExcepcionIndice`
  - `ExcepcionTipo`

```ostia
intentar {
    entero a = 10;
    entero b = 0;
    si (b == 0) {
        lanza ExcepcionAritmetica("División por cero no permitida.");
    }
    entero c = a / b;
} capturar (ExcepcionAritmetica e) {
    imprimirln("Error capturado: " + e.mensaje);
} finalmente {
    imprimirln("Bloque finalmente ejecutado.");
}
```

---

### Standard Math Library (`Matematica`)

The built-in `Matematica` module provides constants and mathematical utilities:

#### Constants
- `Matematica.PI` $\approx 3.141592653589793$
- `Matematica.E` $\approx 2.718281828459045$

#### Standard Functions
- `Matematica.sin(x)`, `Matematica.cos(x)`, `Matematica.tan(x)`
- `Matematica.abs(x)`
- `Matematica.sqrt(x)`
- `Matematica.pow(base, exponente)`
- `Matematica.log(x)`

```ostia
decimal radio = 5.0;
decimal area = Matematica.PI * Matematica.pow(radio, 2);
imprimirln("Área del círculo: " + area);
```

---

## Code Examples

### Calculating Factorial Recursively
```ostia
funcion entero factorial(entero n) {
    si (n <= 1) {
        retornar 1;
    }
    retornar n * factorial(n - 1);
}

imprimirln("Factorial de 5: " + factorial(5));
```

---

## Multi-Platform Compilation

Executables for **Windows**, **Linux**, and **macOS** can be generated automatically using PyInstaller via GitHub Actions.

A build workflow file located at `.github/workflows/build.yml` compiles binaries on every push:

```yaml
name: Build Ostia Executables

on: [push, pull_request]

jobs:
  build:
    name: Build on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller

    - name: Build Binary
      run: |
        pyinstaller --onefile --name ostia ostia.py

    - name: Upload Binaries
      uses: actions/upload-artifact@v4
      with:
        name: ostia-binary-${{ matrix.os }}
        path: dist/
```

To retrieve binaries:
1. Navigate to the **Actions** tab on your GitHub repository.
2. Select the latest workflow run.
3. Download the executable artifacts under **Artifacts**.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
