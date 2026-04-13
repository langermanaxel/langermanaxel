# 📱 Control de Gastos Inteligente (Flet + Python)

Mini app mobile/web para registrar gastos diarios, clasificarlos automáticamente y mostrar recomendaciones básicas de ahorro.

## Estructura del repo

- `app.py`: UI + lógica principal.
- `requirements.txt`: dependencias simples para entorno rápido.
- `pyproject.toml`: metadata del proyecto para empaquetado/build.
- `.gitignore`: exclusiones comunes para Python/Flet.

## Funcionalidades incluidas

- Carga de gastos con formulario (monto, categoría, fecha, descripción).
- Clasificación automática por palabras clave (si dejás categoría en `Auto`).
- Persistencia local en SQLite (`gastos.db`).
- Dashboard mensual:
  - total gastado,
  - comparación con mes anterior,
  - gráfico por categorías.
- Recomendaciones inteligentes simples:
  - alerta de aumento mensual,
  - sugerencia de ahorro en ocio,
  - alerta por cercanía al límite mensual.

## Ejecutar local

```bash
cd smart_expense_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Crear el repo en GitHub (pasos)

```bash
# desde la raíz del proyecto actual
git add .
git commit -m "feat: bootstrap control de gastos inteligente"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/control-gastos-inteligente.git
git push -u origin main
```

> Si querés, en el siguiente paso te preparo también `Issues` iniciales y un `Project board` sugerido.

## Ideas de mejora (bonus)

- Exportar a CSV.
- Login básico por usuario.
- Predicción de gasto fin de mes con regresión lineal.
- Modelo Naive Bayes con scikit-learn entrenado sobre descripciones reales.
