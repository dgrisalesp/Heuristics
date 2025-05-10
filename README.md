# Heurísticas - Balanceo de Sistemas PTL

## Instalación y Configuración

Sigue estos pasos para configurar y ejecutar el proyecto:

### 1. Clonar el Repositorio
```sh
git clone https://github.com/Davidgp04/Heuristics.git
cd Heuristics
```

### 2. Moverse a la Carpeta `src`
```sh
cd src
```

### 3. Instalar Dependencias
Asegúrate de tener Python instalado y ejecuta:
```sh
pip install -r requirements.txt
```

## Ejecución del Código

### Método Constructivo Determinista
Para ejecutar la heurística constructiva, usa:
```sh
py main.py pedidos.xlsx resultado.xlsx [opcional]
```

### Variante Aleatorizada
Para ejecutar la variante aleatorizada, usa:
```sh
py randomized.py pedidos.xlsx resultado.xlsx [opcional]
```
### Recocido Simulado
```sh
py simulated_annealing.py pedidos.xlsx resultado.xlsx [opcional]
```
### Correr todos los algoritmos en todos los casos de prueba
```sh
py testing.py
```

### Parámetros:
- `pedidos.xlsx` → Archivo Excel de entrada con los datos de los pedidos (ubicado en la carpeta data).
- `resultado.xlsx` → Archivo Excel de salida donde se guardarán los resultados (ubicado en la carpeta output).
- `[opcional]` → Parámetro opcional (si aplica).

## Notas
- Los resultados se guardan en la ruta output
- Los archivos de entrada deben estar en la carpeta data.
- Asegúrate de que el archivo de entrada tenga el formato correcto.
- El archivo de salida contendrá la asignación procesada de los pedidos.
- Si tienes problemas, revisa que todas las dependencias estén instaladas correctamente.
