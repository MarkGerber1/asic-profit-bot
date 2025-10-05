"""
Визуализация данных калькулятора майнинга с помощью Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import io
import base64

from calculator_core import CalculatorResult, ProfitabilityResult, CalculationPeriod


class MiningVisualizer:
    """Визуализатор данных майнинга"""

    @staticmethod
    def create_profitability_chart(result: CalculatorResult) -> str:
        """
        Создать график прибыльности по периодам
        Возвращает HTML строку с графиком
        """
        periods = []
        profits_rub = []
        profits_usd = []
        electricity_costs_rub = []
        electricity_costs_usd = []

        for res in result.results:
            period_name = MiningVisualizer._period_to_display_name(res.period)
            periods.append(period_name)
            profits_rub.append(res.net_profit_rub)
            profits_usd.append(res.net_profit_usd)
            electricity_costs_rub.append(res.electricity_cost_rub)
            electricity_costs_usd.append(res.electricity_cost_usd)

        # Создаем подграфики для RUB и USD
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Прибыльность (RUB)', 'Profitability (USD)'),
            shared_yaxes=False
        )

        # График для RUB
        fig.add_trace(
            go.Bar(
                name='Чистая прибыль',
                x=periods,
                y=profits_rub,
                marker_color='green',
                showlegend=False
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(
                name='Электричество',
                x=periods,
                y=electricity_costs_rub,
                marker_color='red',
                showlegend=False
            ),
            row=1, col=1
        )

        # График для USD
        fig.add_trace(
            go.Bar(
                name='Net Profit',
                x=periods,
                y=profits_usd,
                marker_color='green',
                showlegend=False
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Bar(
                name='Electricity',
                x=periods,
                y=electricity_costs_usd,
                marker_color='red',
                showlegend=False
            ),
            row=1, col=2
        )

        fig.update_layout(
            title=f'Прибыльность {result.miner.full_name}',
            barmode='group',
            height=400
        )

        # Преобразуем в HTML
        return MiningVisualizer._fig_to_html(fig)

    @staticmethod
    def create_roi_chart(result: CalculatorResult) -> str:
        """
        Создать график окупаемости (ROI)
        """
        if not result.roi_days_used and not result.roi_days_new:
            return ""

        periods = []
        cumulative_profit_used = []
        cumulative_profit_new = []
        equipment_price_used = result.miner.get_price_usd(True) * 85  # RUB
        equipment_price_new = result.miner.get_price_usd(False) * 85  # RUB

        current_profit = result.current_profit_rub_day
        cumulative = 0

        for i in range(1, 366):  # 365 дней
            periods.append(f"День {i}")
            cumulative += current_profit
            cumulative_profit_used.append(cumulative)
            cumulative_profit_new.append(cumulative)

        fig = go.Figure()

        # Линия цены БУ
        if equipment_price_used > 0:
            fig.add_trace(go.Scatter(
                x=periods,
                y=[equipment_price_used] * len(periods),
                mode='lines',
                name=f'Цена БУ ({equipment_price_used:,.0f} ₽)',
                line=dict(color='orange', dash='dash')
            ))

        # Линия цены НОВЫЙ
        if equipment_price_new > 0:
            fig.add_trace(go.Scatter(
                x=periods,
                y=[equipment_price_new] * len(periods),
                mode='lines',
                name=f'Цена НОВЫЙ ({equipment_price_new:,.0f} ₽)',
                line=dict(color='red', dash='dash')
            ))

        # Накопительная прибыль
        fig.add_trace(go.Scatter(
            x=periods,
            y=cumulative_profit_used,
            mode='lines',
            name='Накопительная прибыль',
            line=dict(color='green', width=3)
        ))

        # Точки пересечения (ROI)
        if result.roi_days_used and equipment_price_used > 0:
            roi_day = min(result.roi_days_used, 365)
            fig.add_trace(go.Scatter(
                x=[f"День {roi_day}"],
                y=[equipment_price_used],
                mode='markers',
                name=f'Окупаемость БУ (день {roi_day})',
                marker=dict(color='orange', size=12, symbol='star')
            ))

        if result.roi_days_new and equipment_price_new > 0:
            roi_day = min(result.roi_days_new, 365)
            fig.add_trace(go.Scatter(
                x=[f"День {roi_day}"],
                y=[equipment_price_new],
                mode='markers',
                name=f'Окупаемость НОВЫЙ (день {roi_day})',
                marker=dict(color='red', size=12, symbol='star')
            ))

        fig.update_layout(
            title='График окупаемости (ROI)',
            xaxis_title='Дни',
            yaxis_title='Рубли (₽)',
            height=400,
            showlegend=True
        )

        # Показываем только первые 90 дней для лучшей видимости
        fig.update_xaxes(range=[0, 90])

        return MiningVisualizer._fig_to_html(fig)

    @staticmethod
    def create_comparison_chart(results: List[CalculatorResult]) -> str:
        """
        Создать график сравнения нескольких майнеров
        """
        if len(results) < 2:
            return ""

        miner_names = [r.miner.full_name for r in results]
        daily_profits_rub = [r.current_profit_rub_day for r in results]
        daily_profits_usd = [r.current_profit_usd_day for r in results]
        powers = [r.miner.power_w for r in results]

        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Прибыль в день (RUB)', 'Daily Profit (USD)', 'Мощность (W)'),
            shared_yaxes=False
        )

        fig.add_trace(
            go.Bar(x=miner_names, y=daily_profits_rub, marker_color='green'),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(x=miner_names, y=daily_profits_usd, marker_color='blue'),
            row=1, col=2
        )

        fig.add_trace(
            go.Bar(x=miner_names, y=powers, marker_color='orange'),
            row=1, col=3
        )

        fig.update_layout(
            title='Сравнение майнеров',
            height=400,
            showlegend=False
        )

        return MiningVisualizer._fig_to_html(fig)

    @staticmethod
    def create_efficiency_chart(result: CalculatorResult) -> str:
        """
        Создать график эффективности (прибыль на ватт)
        """
        periods = []
        efficiency_rub = []
        efficiency_usd = []

        for res in result.results:
            period_name = MiningVisualizer._period_to_display_name(res.period)
            periods.append(period_name)
            efficiency_rub.append(res.profit_per_kwh_rub)
            efficiency_usd.append(res.profit_per_kwh_usd)

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Прибыль/кВт⋅ч (RUB)', 'Profit/kWh (USD)')
        )

        fig.add_trace(
            go.Scatter(
                x=periods,
                y=efficiency_rub,
                mode='lines+markers',
                name='RUB',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=periods,
                y=efficiency_usd,
                mode='lines+markers',
                name='USD',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ),
            row=1, col=2
        )

        fig.update_layout(
            title='Эффективность майнинга',
            height=400,
            showlegend=False
        )

        return MiningVisualizer._fig_to_html(fig)

    @staticmethod
    def create_summary_table(result: CalculatorResult) -> str:
        """
        Создать таблицу с сводными данными
        """
        data = []
        for res in result.results:
            data.append({
                'Период': MiningVisualizer._period_to_display_name(res.period),
                'Прибыль (₽)': f"{res.net_profit_rub:,.0f}",
                'Прибыль ($)': f"{res.net_profit_usd:,.2f}",
                'Электричество (₽)': f"{res.electricity_cost_rub:,.0f}",
                'Эффективность (₽/кВт⋅ч)': f"{res.profit_per_kwh_rub:.2f}"
            })

        df = pd.DataFrame(data)

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])

        fig.update_layout(
            title=f'Сводная таблица - {result.miner.full_name}',
            height=300
        )

        return MiningVisualizer._fig_to_html(fig)

    @staticmethod
    def _period_to_display_name(period: CalculationPeriod) -> str:
        """Конвертировать период в читаемое название"""
        names = {
            CalculationPeriod.HOUR: "1 час",
            CalculationPeriod.DAY: "1 день",
            CalculationPeriod.WEEK: "1 неделя",
            CalculationPeriod.MONTH: "1 месяц",
            CalculationPeriod.THREE_MONTHS: "3 месяца",
            CalculationPeriod.SIX_MONTHS: "6 месяцев",
            CalculationPeriod.YEAR: "1 год"
        }
        return names.get(period, str(period.value))

    @staticmethod
    def _fig_to_html(fig: go.Figure) -> str:
        """Конвертировать Plotly фигуру в HTML"""
        # Создаем HTML с inline JavaScript
        html = fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={'displayModeBar': False, 'displaylogo': False}
        )
        return html

    @staticmethod
    def create_combined_report(result: CalculatorResult) -> str:
        """
        Создать полный отчет с несколькими графиками
        """
        charts = []

        # Основной график прибыльности
        charts.append(MiningVisualizer.create_profitability_chart(result))

        # График окупаемости
        roi_chart = MiningVisualizer.create_roi_chart(result)
        if roi_chart:
            charts.append(roi_chart)

        # График эффективности
        charts.append(MiningVisualizer.create_efficiency_chart(result))

        # Сводная таблица
        charts.append(MiningVisualizer.create_summary_table(result))

        # Объединяем все графики
        html_parts = []
        for i, chart in enumerate(charts):
            html_parts.append(f'<div class="chart-container" style="margin: 20px 0;">{chart}</div>')

        full_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto;">
            <h2 style="text-align: center; color: #2c3e50;">📊 Отчет по майнингу</h2>
            <h3 style="text-align: center; color: #34495e;">{result.miner.full_name}</h3>
            <p style="text-align: center; color: #7f8c8d;">
                Рассчитано: {result.calculated_at.strftime('%d.%m.%Y %H:%M')}
                | Источник: {result.data_source}
            </p>
            {"".join(html_parts)}
        </div>
        """

        return full_html


# Глобальный визуализатор
visualizer = MiningVisualizer()


async def generate_profitability_chart(result: CalculatorResult) -> str:
    """Быстрая генерация графика прибыльности"""
    return visualizer.create_profitability_chart(result)


async def generate_roi_chart(result: CalculatorResult) -> str:
    """Быстрая генерация графика ROI"""
    return visualizer.create_roi_chart(result)


async def generate_comparison_chart(results: List[CalculatorResult]) -> str:
    """Быстрая генерация графика сравнения"""
    return visualizer.create_comparison_chart(results)


async def generate_full_report(result: CalculatorResult) -> str:
    """Генерация полного отчета"""
    return visualizer.create_combined_report(result)
