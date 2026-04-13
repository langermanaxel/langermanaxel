from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import flet as ft

DB_PATH = Path(__file__).with_name("gastos.db")


@dataclass
class Expense:
    amount: float
    category: str
    date: str
    description: str


CATEGORY_KEYWORDS = {
    "comida": ["pizza", "burger", "hamburguesa", "cafe", "restaurante", "super"],
    "transporte": ["uber", "taxi", "subte", "colectivo", "nafta", "combustible"],
    "ocio": ["cine", "netflix", "bar", "juego", "spotify", "salida"],
    "hogar": ["alquiler", "luz", "agua", "gas", "internet", "mercado"],
    "salud": ["farmacia", "medico", "clínica", "clinica", "seguro"],
}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT DEFAULT ''
            )
            """
        )


def classify_category(description: str, selected: str | None) -> str:
    if selected and selected != "Auto":
        return selected

    desc_lower = description.lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(word in desc_lower for word in words):
            return category
    return "otros"


def save_expense(expense: Expense) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO expenses(amount, category, date, description) VALUES (?, ?, ?, ?)",
            (expense.amount, expense.category, expense.date, expense.description),
        )


def fetch_month_summary(target: dt.date) -> tuple[float, dict[str, float], float]:
    first_day = target.replace(day=1)
    next_month = (first_day.replace(day=28) + dt.timedelta(days=4)).replace(day=1)

    prev_month_end = first_day - dt.timedelta(days=1)
    prev_first = prev_month_end.replace(day=1)

    with sqlite3.connect(DB_PATH) as conn:
        current_rows = conn.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date >= ? AND date < ?
            GROUP BY category
            """,
            (first_day.isoformat(), next_month.isoformat()),
        ).fetchall()
        prev_total_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE date >= ? AND date <= ?
            """,
            (prev_first.isoformat(), prev_month_end.isoformat()),
        ).fetchone()

    per_category = {category: total for category, total in current_rows}
    month_total = sum(per_category.values())
    prev_total = float(prev_total_row[0] if prev_total_row else 0)
    return month_total, per_category, prev_total


def build_recommendations(total: float, by_category: dict[str, float], prev_total: float, limit: float) -> list[str]:
    recs: list[str] = []
    if prev_total > 0 and total > prev_total:
        diff_pct = ((total - prev_total) / prev_total) * 100
        recs.append(f"Gastaste {diff_pct:.1f}% más que el mes pasado.")

    ocio = by_category.get("ocio", 0)
    if ocio > 0 and total > 0:
        ocio_pct = ocio / total
        if ocio_pct > 0.25:
            recs.append(f"Tu ocio representa {ocio_pct:.0%}. Reducirlo 20% ahorraría ${ocio * 0.2:.2f}.")

    comida = by_category.get("comida", 0)
    if comida > 0 and total > 0.35 * max(total, 1):
        recs.append("Comida es una de tus categorías más altas. Planificar menús semanales puede ayudar.")

    if total >= 0.9 * limit:
        recs.append("⚠️ Estás cerca de tu límite mensual.")

    if not recs:
        recs.append("¡Buen trabajo! Tus gastos están estables este mes.")
    return recs


def main(page: ft.Page) -> None:
    init_db()
    page.title = "Control de Gastos Inteligente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    monthly_limit = 1000.0

    amount_tf = ft.TextField(label="Monto", keyboard_type=ft.KeyboardType.NUMBER)
    category_dd = ft.Dropdown(
        label="Categoría",
        value="Auto",
        options=[ft.dropdown.Option("Auto"), *[ft.dropdown.Option(c) for c in ["comida", "transporte", "ocio", "hogar", "salud", "otros"]]],
    )
    date_tf = ft.TextField(label="Fecha (YYYY-MM-DD)", value=dt.date.today().isoformat())
    desc_tf = ft.TextField(label="Descripción", multiline=True)

    total_txt = ft.Text("Total mensual: $0.00", size=18, weight=ft.FontWeight.BOLD)
    compare_txt = ft.Text("Comparación mensual: sin datos")
    recs_col = ft.Column(spacing=6)
    chart = ft.BarChart(
        bar_groups=[],
        border=ft.border.all(1, ft.Colors.GREY_300),
        left_axis=ft.ChartAxis(labels_size=40),
        bottom_axis=ft.ChartAxis(labels_size=40),
        horizontal_grid_lines=ft.ChartGridLines(interval=50, color=ft.Colors.GREY_300, width=1),
        tooltip_bgcolor=ft.Colors.BLUE_GREY_200,
        max_y=500,
        interactive=True,
        expand=False,
        height=260,
    )

    def refresh_dashboard() -> None:
        now = dt.date.today()
        total, by_cat, prev_total = fetch_month_summary(now)

        total_txt.value = f"Total mensual: ${total:.2f}"
        if prev_total > 0:
            diff = ((total - prev_total) / prev_total) * 100
            compare_txt.value = f"Vs mes anterior: {diff:+.1f}% (anterior ${prev_total:.2f})"
        else:
            compare_txt.value = "Vs mes anterior: sin datos suficientes"

        categories = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
        max_value = max([v for _, v in categories], default=100)
        chart.max_y = max(max_value * 1.2, 100)
        chart.bar_groups = [
            ft.BarChartGroup(
                x=i,
                bar_rods=[ft.BarChartRod(from_y=0, to_y=amount, width=28, color=ft.Colors.BLUE)],
                tooltip=f"{cat}: ${amount:.2f}",
            )
            for i, (cat, amount) in enumerate(categories)
        ]
        chart.bottom_axis = ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(cat[:10]))
                for i, (cat, _) in enumerate(categories)
            ]
        )

        recs = build_recommendations(total, by_cat, prev_total, monthly_limit)
        recs_col.controls = [ft.Text(f"• {r}") for r in recs]
        page.update()

    def submit_expense(_: ft.ControlEvent) -> None:
        try:
            amount = float(amount_tf.value.strip())
            parsed_date = dt.date.fromisoformat(date_tf.value.strip())
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("Revisá monto y fecha (formato YYYY-MM-DD)."))
            page.snack_bar.open = True
            page.update()
            return

        description = (desc_tf.value or "").strip()
        category = classify_category(description, category_dd.value)

        expense = Expense(
            amount=amount,
            category=category,
            date=parsed_date.isoformat(),
            description=description,
        )
        save_expense(expense)

        amount_tf.value = ""
        desc_tf.value = ""
        page.snack_bar = ft.SnackBar(ft.Text(f"Gasto guardado en categoría: {category}"))
        page.snack_bar.open = True
        refresh_dashboard()

    submit_btn = ft.ElevatedButton("Guardar gasto", icon=ft.Icons.SAVE, on_click=submit_expense)

    page.add(
        ft.Text("📱 Control de Gastos Inteligente", size=26, weight=ft.FontWeight.BOLD),
        ft.Text("Registro diario + clasificación automática + recomendaciones simples"),
        ft.Divider(),
        ft.ResponsiveRow(
            controls=[
                ft.Column([amount_tf, category_dd], col={"sm": 12, "md": 6}),
                ft.Column([date_tf, desc_tf], col={"sm": 12, "md": 6}),
            ]
        ),
        submit_btn,
        ft.Divider(),
        ft.Text("📊 Dashboard", size=20, weight=ft.FontWeight.BOLD),
        total_txt,
        compare_txt,
        chart,
        ft.Text("💡 Recomendaciones", size=20, weight=ft.FontWeight.BOLD),
        recs_col,
    )

    refresh_dashboard()


if __name__ == "__main__":
    ft.app(target=main)
