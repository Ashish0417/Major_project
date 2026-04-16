"""
Currency Converter Module
Handles currency conversion for multi-currency travel planning
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


class CurrencyConverter:
    """Currency converter with exchange rates"""
    
    def __init__(self):
        """Initialize with fixed exchange rates (as of Jan 2025)"""
        
        # Base currency: USD
        # All rates are USD to target currency
        self.rates = {
            'USD': 1.0,
            'EUR': 0.92,      # 1 USD = 0.92 EUR
            'GBP': 0.79,      # 1 USD = 0.79 GBP
            'INR': 83.50,     # 1 USD = 83.50 INR
            'JPY': 145.0,     # 1 USD = 145 JPY
            'SGD': 1.34,      # 1 USD = 1.34 SGD
            'AED': 3.67,      # 1 USD = 3.67 AED
            'CNY': 7.24,      # 1 USD = 7.24 CNY
            'AUD': 1.52,      # 1 USD = 1.52 AUD
            'CAD': 1.35,      # 1 USD = 1.35 CAD
            'CHF': 0.89,      # 1 USD = 0.89 CHF
            'HKD': 7.82,      # 1 USD = 7.82 HKD
            'NZD': 1.67,      # 1 USD = 1.67 NZD
            'SEK': 10.45,     # 1 USD = 10.45 SEK
            'KRW': 1320.0,    # 1 USD = 1320 KRW
            'NOK': 10.75,     # 1 USD = 10.75 NOK
            'MXN': 17.20,     # 1 USD = 17.20 MXN
            'BRL': 5.65,      # 1 USD = 5.65 BRL
            'ZAR': 18.50,     # 1 USD = 18.50 ZAR
            'THB': 34.50,     # 1 USD = 34.50 THB
        }
        
        # Last update timestamp
        self.last_update = datetime.now()
        
        # Currency symbols
        self.symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'INR': '₹',
            'JPY': '¥',
            'SGD': 'S$',
            'AED': 'د.إ',
            'CNY': '¥',
            'AUD': 'A$',
            'CAD': 'C$',
            'CHF': 'Fr',
        }
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'INR')
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        # Normalize currency codes
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        # Check if currencies are supported
        if from_curr not in self.rates:
            print(f"⚠️ Unsupported currency: {from_curr}, assuming USD")
            from_curr = 'USD'
        
        if to_curr not in self.rates:
            print(f"⚠️ Unsupported currency: {to_curr}, assuming USD")
            to_curr = 'USD'
        
        # Convert via USD
        # from_currency -> USD -> to_currency
        amount_in_usd = amount / self.rates[from_curr]
        amount_in_target = amount_in_usd * self.rates[to_curr]
        
        return amount_in_target
    
    def convert_to_base(self, amount: float, from_currency: str, base_currency: str = 'INR') -> float:
        """Convert any currency to base currency (default INR)"""
        return self.convert(amount, from_currency, base_currency)
    
    def format_amount(self, amount: float, currency: str) -> str:
        """Format amount with currency symbol"""
        symbol = self.symbols.get(currency.upper(), currency)
        return f"{symbol} {amount:,.2f}"
    
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies"""
        if from_currency == to_currency:
            return 1.0
        
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        if from_curr not in self.rates or to_curr not in self.rates:
            return 1.0
        
        # Rate = (1 / from_rate) * to_rate
        rate_from_usd = self.rates[from_curr]
        rate_to_usd = self.rates[to_curr]
        
        return rate_to_usd / rate_from_usd
    
    def is_rate_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if exchange rates are fresh"""
        age = datetime.now() - self.last_update
        return age < timedelta(hours=max_age_hours)
    
    def get_supported_currencies(self) -> list:
        """Get list of supported currency codes"""
        return list(self.rates.keys())


# Global currency converter instance
_converter = None

def get_converter() -> CurrencyConverter:
    """Get global currency converter instance"""
    global _converter
    if _converter is None:
        _converter = CurrencyConverter()
    return _converter


# Convenience functions
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert currency using global converter"""
    converter = get_converter()
    return converter.convert(amount, from_currency, to_currency)


def convert_to_inr(amount: float, from_currency: str) -> float:
    """Convert any currency to INR"""
    return convert_currency(amount, from_currency, 'INR')


def convert_to_usd(amount: float, from_currency: str) -> float:
    """Convert any currency to USD"""
    return convert_currency(amount, from_currency, 'USD')


if __name__ == "__main__":
    # Test the converter
    converter = CurrencyConverter()
    
    print("Currency Converter Test")
    print("="*50)
    
    # Test conversions
    print(f"\n100 EUR to INR: {converter.convert(100, 'EUR', 'INR'):.2f}")
    print(f"100 USD to INR: {converter.convert(100, 'USD', 'INR'):.2f}")
    print(f"10000 INR to EUR: {converter.convert(10000, 'INR', 'EUR'):.2f}")
    print(f"10000 INR to USD: {converter.convert(10000, 'INR', 'USD'):.2f}")
    
    # Test formatting
    print(f"\nFormatted: {converter.format_amount(100, 'EUR')}")
    print(f"Formatted: {converter.format_amount(10000, 'INR')}")
    
    # Test exchange rates
    print(f"\nExchange rate EUR/INR: {converter.get_rate('EUR', 'INR'):.4f}")
    print(f"Exchange rate USD/INR: {converter.get_rate('USD', 'INR'):.4f}")
    
    print(f"\n✅ Converter initialized with {len(converter.rates)} currencies")