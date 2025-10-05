"""
ROI Calculator for Mining Operations
Integrates with cryptocurrency APIs for real-time profitability analysis
"""

import requests
from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json


@dataclass
class CryptoPrice:
    """Cryptocurrency price data."""
    symbol: str
    price_usd: float
    change_24h: float
    timestamp: datetime


@dataclass
class MiningConfig:
    """Mining configuration for ROI calculation."""
    asic_model: str
    hashrate_ths: float  # TH/s
    power_consumption_w: float
    quantity: int
    asic_price_usd: float
    
    # Cooling system
    cooling_type: str  # 'air' or 'hydro'
    cooling_capex_usd: float
    cooling_power_w: float
    
    # Operating costs
    electricity_price_kwh: float
    pool_fee_percent: float = 1.0
    maintenance_monthly_usd: float = 0.0


@dataclass
class NetworkStats:
    """Bitcoin network statistics."""
    difficulty: float
    block_reward: float
    network_hashrate_ths: float
    timestamp: datetime


class CryptoAPIClient:
    """Client for cryptocurrency price and network data APIs."""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.blockchain_base = "https://blockchain.info"
        
    def get_btc_price(self) -> Optional[CryptoPrice]:
        """Get current Bitcoin price from CoinGecko."""
        try:
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return CryptoPrice(
                symbol='BTC',
                price_usd=data['bitcoin']['usd'],
                change_24h=data['bitcoin'].get('usd_24h_change', 0),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Ошибка получения цены BTC: {e}")
            # Fallback to default
            return CryptoPrice('BTC', 45000.0, 0.0, datetime.now())
    
    def get_network_stats(self) -> Optional[NetworkStats]:
        """Get Bitcoin network statistics."""
        try:
            url = f"{self.blockchain_base}/q/getdifficulty"
            difficulty = float(requests.get(url, timeout=10).text)
            
            # Approximate network hashrate (EH/s to TH/s)
            # Network hashrate ≈ difficulty * 2^32 / 600 / 10^12
            network_hashrate_ths = difficulty * 4.295e9 / 600
            
            return NetworkStats(
                difficulty=difficulty,
                block_reward=6.25,  # Current BTC block reward
                network_hashrate_ths=network_hashrate_ths,
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Ошибка получения сетевых данных: {e}")
            # Fallback defaults
            return NetworkStats(
                difficulty=60e12,
                block_reward=6.25,
                network_hashrate_ths=400e6,  # 400 EH/s
                timestamp=datetime.now()
            )


class ROICalculator:
    """Advanced ROI calculator for mining operations."""
    
    def __init__(self, config: MiningConfig):
        self.config = config
        self.api = CryptoAPIClient()
        
    def calculate_daily_revenue(self, btc_price: float, network_stats: NetworkStats) -> Dict:
        """Calculate daily mining revenue."""
        # Total hashrate
        total_hashrate_ths = self.config.hashrate_ths * self.config.quantity
        
        # Daily BTC mined = (your hashrate / network hashrate) * blocks per day * block reward
        # Blocks per day ≈ 144 (one every 10 minutes)
        blocks_per_day = 144
        
        btc_per_day = (total_hashrate_ths / network_stats.network_hashrate_ths) * \
                      blocks_per_day * network_stats.block_reward
        
        # Apply pool fee
        btc_per_day *= (1 - self.config.pool_fee_percent / 100)
        
        # Revenue in USD
        revenue_usd = btc_per_day * btc_price
        
        return {
            'btc_per_day': btc_per_day,
            'revenue_usd_per_day': revenue_usd,
            'revenue_usd_per_month': revenue_usd * 30,
            'revenue_usd_per_year': revenue_usd * 365
        }
    
    def calculate_daily_costs(self) -> Dict:
        """Calculate daily operating costs."""
        # ASIC power consumption
        asic_power_kw = (self.config.power_consumption_w * self.config.quantity) / 1000
        
        # Cooling power consumption
        cooling_power_kw = self.config.cooling_power_w / 1000
        
        # Total power
        total_power_kw = asic_power_kw + cooling_power_kw
        
        # Daily electricity cost
        electricity_cost_per_day = total_power_kw * 24 * self.config.electricity_price_kwh
        
        # Monthly maintenance
        maintenance_cost_per_day = self.config.maintenance_monthly_usd / 30
        
        total_cost_per_day = electricity_cost_per_day + maintenance_cost_per_day
        
        return {
            'electricity_cost_per_day': electricity_cost_per_day,
            'maintenance_cost_per_day': maintenance_cost_per_day,
            'total_cost_per_day': total_cost_per_day,
            'total_cost_per_month': total_cost_per_day * 30,
            'total_cost_per_year': total_cost_per_day * 365,
            'power_consumption_kw': total_power_kw
        }
    
    def calculate_roi(self, btc_price: Optional[float] = None, 
                     network_stats: Optional[NetworkStats] = None) -> Dict:
        """Calculate comprehensive ROI analysis."""
        # Get current market data
        if btc_price is None:
            price_data = self.api.get_btc_price()
            btc_price = price_data.price_usd
        
        if network_stats is None:
            network_stats = self.api.get_network_stats()
        
        # Calculate revenue and costs
        revenue = self.calculate_daily_revenue(btc_price, network_stats)
        costs = self.calculate_daily_costs()
        
        # Daily profit
        daily_profit = revenue['revenue_usd_per_day'] - costs['total_cost_per_day']
        monthly_profit = daily_profit * 30
        yearly_profit = daily_profit * 365
        
        # Initial investment (CAPEX)
        asic_investment = self.config.asic_price_usd * self.config.quantity
        cooling_investment = self.config.cooling_capex_usd
        total_investment = asic_investment + cooling_investment
        
        # ROI calculations
        if daily_profit > 0:
            payback_days = total_investment / daily_profit
            payback_months = payback_days / 30
            roi_1_year = (yearly_profit / total_investment) * 100
        else:
            payback_days = float('inf')
            payback_months = float('inf')
            roi_1_year = -100
        
        # Break-even electricity price
        if revenue['revenue_usd_per_day'] > costs['maintenance_cost_per_day']:
            breakeven_electricity = (revenue['revenue_usd_per_day'] - costs['maintenance_cost_per_day']) / \
                                   (costs['power_consumption_kw'] * 24)
        else:
            breakeven_electricity = 0
        
        return {
            'btc_price': btc_price,
            'network_difficulty': network_stats.difficulty,
            'network_hashrate_ehs': network_stats.network_hashrate_ths / 1e6,
            
            # Revenue
            'btc_per_day': revenue['btc_per_day'],
            'revenue_per_day': revenue['revenue_usd_per_day'],
            'revenue_per_month': revenue['revenue_usd_per_month'],
            'revenue_per_year': revenue['revenue_usd_per_year'],
            
            # Costs
            'electricity_cost_per_day': costs['electricity_cost_per_day'],
            'total_cost_per_day': costs['total_cost_per_day'],
            'total_cost_per_month': costs['total_cost_per_month'],
            'total_cost_per_year': costs['total_cost_per_year'],
            
            # Profit
            'profit_per_day': daily_profit,
            'profit_per_month': monthly_profit,
            'profit_per_year': yearly_profit,
            
            # Investment
            'total_investment': total_investment,
            'asic_investment': asic_investment,
            'cooling_investment': cooling_investment,
            
            # ROI metrics
            'payback_days': payback_days,
            'payback_months': payback_months,
            'roi_1_year_percent': roi_1_year,
            'breakeven_electricity_price': breakeven_electricity,
            
            # Efficiency
            'power_consumption_kw': costs['power_consumption_kw'],
            'efficiency_wth': self.config.power_consumption_w / self.config.hashrate_ths,
            
            # Profitability indicator
            'is_profitable': daily_profit > 0,
            'profit_margin_percent': (daily_profit / revenue['revenue_usd_per_day'] * 100) if revenue['revenue_usd_per_day'] > 0 else -100
        }
    
    def calculate_scenario_comparison(self, air_config: MiningConfig, 
                                     hydro_config: MiningConfig) -> Dict:
        """Compare air vs hydro cooling scenarios."""
        air_calc = ROICalculator(air_config)
        hydro_calc = ROICalculator(hydro_config)
        
        # Get shared market data
        price_data = self.api.get_btc_price()
        network_stats = self.api.get_network_stats()
        
        air_roi = air_calc.calculate_roi(price_data.price_usd, network_stats)
        hydro_roi = hydro_calc.calculate_roi(price_data.price_usd, network_stats)
        
        # Calculate differences
        capex_difference = hydro_roi['total_investment'] - air_roi['total_investment']
        daily_profit_difference = hydro_roi['profit_per_day'] - air_roi['profit_per_day']
        
        if daily_profit_difference > 0:
            hydro_payback_vs_air = capex_difference / daily_profit_difference
        else:
            hydro_payback_vs_air = float('inf')
        
        return {
            'air_cooling': air_roi,
            'hydro_cooling': hydro_roi,
            'comparison': {
                'capex_difference': capex_difference,
                'daily_profit_difference': daily_profit_difference,
                'monthly_profit_difference': daily_profit_difference * 30,
                'yearly_profit_difference': daily_profit_difference * 365,
                'hydro_payback_vs_air_days': hydro_payback_vs_air,
                'hydro_payback_vs_air_months': hydro_payback_vs_air / 30,
                'recommendation': 'hydro' if hydro_payback_vs_air < 365 else 'air'
            }
        }
    
    def generate_projection(self, months: int = 12, 
                           difficulty_increase_monthly: float = 3.0,
                           btc_price_change_monthly: float = 0.0) -> List[Dict]:
        """Generate multi-month profitability projection.
        
        Args:
            months: Number of months to project
            difficulty_increase_monthly: Monthly difficulty increase (%)
            btc_price_change_monthly: Monthly BTC price change (%)
        """
        projections = []
        
        # Get initial data
        price_data = self.api.get_btc_price()
        network_stats = self.api.get_network_stats()
        
        current_btc_price = price_data.price_usd
        current_difficulty = network_stats.difficulty
        current_network_hashrate = network_stats.network_hashrate_ths
        
        cumulative_profit = 0
        
        for month in range(months):
            # Update difficulty and price
            btc_price = current_btc_price * ((1 + btc_price_change_monthly / 100) ** month)
            difficulty = current_difficulty * ((1 + difficulty_increase_monthly / 100) ** month)
            network_hashrate = current_network_hashrate * ((1 + difficulty_increase_monthly / 100) ** month)
            
            # Create updated network stats
            month_network_stats = NetworkStats(
                difficulty=difficulty,
                block_reward=network_stats.block_reward,
                network_hashrate_ths=network_hashrate,
                timestamp=datetime.now() + timedelta(days=30*month)
            )
            
            # Calculate ROI for this month
            roi = self.calculate_roi(btc_price, month_network_stats)
            
            cumulative_profit += roi['profit_per_month']
            
            projections.append({
                'month': month + 1,
                'btc_price': btc_price,
                'difficulty': difficulty,
                'monthly_profit': roi['profit_per_month'],
                'cumulative_profit': cumulative_profit,
                'roi_to_date_percent': (cumulative_profit / roi['total_investment']) * 100
            })
        
        return projections


def format_roi_report(roi_data: Dict) -> str:
    """Format ROI data as readable report."""
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║          АНАЛИЗ ОКУПАЕМОСТИ МАЙНИНГ-ОПЕРАЦИИ                 ║
╚══════════════════════════════════════════════════════════════╝

📊 РЫНОЧНЫЕ ДАННЫЕ:
   • Цена BTC: ${roi_data['btc_price']:,.2f}
   • Сложность сети: {roi_data['network_difficulty']:.2e}
   • Хешрейт сети: {roi_data['network_hashrate_ehs']:.1f} EH/s

💰 ДОХОДЫ:
   • BTC в день: {roi_data['btc_per_day']:.8f} BTC
   • Доход в день: ${roi_data['revenue_per_day']:.2f}
   • Доход в месяц: ${roi_data['revenue_per_month']:.2f}
   • Доход в год: ${roi_data['revenue_per_year']:,.2f}

💸 РАСХОДЫ:
   • Электричество в день: ${roi_data['electricity_cost_per_day']:.2f}
   • Общие расходы в день: ${roi_data['total_cost_per_day']:.2f}
   • Общие расходы в месяц: ${roi_data['total_cost_per_month']:.2f}
   • Общие расходы в год: ${roi_data['total_cost_per_year']:,.2f}

📈 ПРИБЫЛЬ:
   • Прибыль в день: ${roi_data['profit_per_day']:.2f}
   • Прибыль в месяц: ${roi_data['profit_per_month']:.2f}
   • Прибыль в год: ${roi_data['profit_per_year']:,.2f}
   • Маржа прибыли: {roi_data['profit_margin_percent']:.1f}%

🏦 ИНВЕСТИЦИИ И ROI:
   • Общие инвестиции: ${roi_data['total_investment']:,.2f}
   • Срок окупаемости: {roi_data['payback_months']:.1f} месяцев
   • ROI за 1 год: {roi_data['roi_1_year_percent']:.1f}%
   • Точка безубыточности (электричество): ${roi_data['breakeven_electricity_price']:.4f}/кВт·ч

⚡ ЭФФЕКТИВНОСТЬ:
   • Потребление: {roi_data['power_consumption_kw']:.2f} кВт
   • Эффективность: {roi_data['efficiency_wth']:.1f} Вт/TH

{'✅ ПРИБЫЛЬНО' if roi_data['is_profitable'] else '❌ УБЫТОЧНО'}
"""
    return report


if __name__ == "__main__":
    # Demo
    config = MiningConfig(
        asic_model="Antminer S19 Pro",
        hashrate_ths=110,
        power_consumption_w=3250,
        quantity=10,
        asic_price_usd=2500,
        cooling_type='hydro',
        cooling_capex_usd=5000,
        cooling_power_w=500,
        electricity_price_kwh=0.08,
        pool_fee_percent=1.0,
        maintenance_monthly_usd=200
    )
    
    calc = ROICalculator(config)
    roi = calc.calculate_roi()
    
    print(format_roi_report(roi))
    
    # Projection
    print("\n📅 ПРОГНОЗ НА 12 МЕСЯЦЕВ (сложность +3%/мес):")
    projections = calc.generate_projection(12, difficulty_increase_monthly=3.0)
    for proj in projections[:6]:  # Show first 6 months
        print(f"Месяц {proj['month']}: Прибыль ${proj['monthly_profit']:.2f}, "
              f"Накопленная ${proj['cumulative_profit']:.2f}, "
              f"ROI {proj['roi_to_date_percent']:.1f}%")

