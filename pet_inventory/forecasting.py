"""Forecasting algorithms for inventory demand prediction."""

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from .models import Forecast, Sale


class Forecaster:
    """Demand forecasting engine with multiple algorithms."""

    def __init__(self, sales_data: list[Sale]):
        """Initialize forecaster with historical sales data."""
        self.sales_df = self._prepare_dataframe(sales_data)

    def _prepare_dataframe(self, sales: list[Sale]) -> pd.DataFrame:
        """Convert sales list to pandas DataFrame for analysis."""
        if not sales:
            return pd.DataFrame(columns=["date", "product_id", "quantity"])

        data = [
            {"date": s.date, "product_id": s.product_id, "quantity": s.quantity}
            for s in sales
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df

    def get_product_daily_sales(self, product_id: str) -> pd.Series:
        """Get daily sales time series for a product."""
        if self.sales_df.empty:
            return pd.Series(dtype=float)

        product_sales = self.sales_df[self.sales_df["product_id"] == product_id]
        if product_sales.empty:
            return pd.Series(dtype=float)

        daily = product_sales.groupby("date")["quantity"].sum()

        # Fill missing dates with 0
        if len(daily) > 1:
            date_range = pd.date_range(daily.index.min(), daily.index.max())
            daily = daily.reindex(date_range, fill_value=0)

        return daily

    def simple_moving_average(
        self, product_id: str, window: int = 7, forecast_days: int = 14
    ) -> list[Forecast]:
        """
        Forecast using Simple Moving Average (SMA).

        Uses the average of the last `window` days to predict future demand.
        Good for stable demand patterns.
        """
        daily_sales = self.get_product_daily_sales(product_id)

        if len(daily_sales) < window:
            # Not enough data, use overall average
            avg = daily_sales.mean() if len(daily_sales) > 0 else 0
            std = daily_sales.std() if len(daily_sales) > 1 else avg * 0.2
        else:
            avg = daily_sales.iloc[-window:].mean()
            std = daily_sales.iloc[-window:].std()

        forecasts = []
        start_date = date.today() + timedelta(days=1)

        for i in range(forecast_days):
            forecast_date = start_date + timedelta(days=i)
            forecasts.append(
                Forecast(
                    product_id=product_id,
                    product_name="",  # Will be filled by caller
                    forecast_date=forecast_date,
                    predicted_demand=float(avg),
                    method="Simple Moving Average",
                    confidence_lower=max(0, float(avg - 1.96 * std)),
                    confidence_upper=float(avg + 1.96 * std),
                )
            )

        return forecasts

    def weighted_moving_average(
        self, product_id: str, window: int = 7, forecast_days: int = 14
    ) -> list[Forecast]:
        """
        Forecast using Weighted Moving Average (WMA).

        Gives more weight to recent observations. Better for trending data.
        """
        daily_sales = self.get_product_daily_sales(product_id)

        if len(daily_sales) < 3:
            # Fall back to simple average
            return self.simple_moving_average(product_id, window, forecast_days)

        # Create weights (more recent = higher weight)
        actual_window = min(window, len(daily_sales))
        weights = np.arange(1, actual_window + 1, dtype=float)
        weights = weights / weights.sum()

        recent_sales = daily_sales.iloc[-actual_window:].values
        wma = np.sum(weights * recent_sales)

        # Estimate variance using recent data
        std = daily_sales.iloc[-actual_window:].std()

        forecasts = []
        start_date = date.today() + timedelta(days=1)

        for i in range(forecast_days):
            forecast_date = start_date + timedelta(days=i)
            forecasts.append(
                Forecast(
                    product_id=product_id,
                    product_name="",
                    forecast_date=forecast_date,
                    predicted_demand=float(wma),
                    method="Weighted Moving Average",
                    confidence_lower=max(0, float(wma - 1.96 * std)),
                    confidence_upper=float(wma + 1.96 * std),
                )
            )

        return forecasts

    def exponential_smoothing(
        self, product_id: str, alpha: float = 0.3, forecast_days: int = 14
    ) -> list[Forecast]:
        """
        Forecast using Simple Exponential Smoothing (SES).

        Alpha controls how much weight is given to recent observations.
        - Higher alpha (0.7-0.9): More responsive to recent changes
        - Lower alpha (0.1-0.3): More stable, smooths out noise

        Good for data with no clear trend or seasonality.
        """
        daily_sales = self.get_product_daily_sales(product_id)

        if len(daily_sales) < 2:
            return self.simple_moving_average(product_id, 7, forecast_days)

        # Apply exponential smoothing
        values = daily_sales.values.astype(float)
        smoothed = values[0]

        for val in values[1:]:
            smoothed = alpha * val + (1 - alpha) * smoothed

        # Calculate residual standard error
        predictions = [values[0]]
        for i in range(1, len(values)):
            predictions.append(alpha * values[i - 1] + (1 - alpha) * predictions[-1])
        residuals = values - np.array(predictions)
        std = np.std(residuals)

        forecasts = []
        start_date = date.today() + timedelta(days=1)

        for i in range(forecast_days):
            forecast_date = start_date + timedelta(days=i)
            forecasts.append(
                Forecast(
                    product_id=product_id,
                    product_name="",
                    forecast_date=forecast_date,
                    predicted_demand=float(smoothed),
                    method=f"Exponential Smoothing (α={alpha})",
                    confidence_lower=max(0, float(smoothed - 1.96 * std)),
                    confidence_upper=float(smoothed + 1.96 * std),
                )
            )

        return forecasts

    def forecast(
        self,
        product_id: str,
        method: str = "exponential",
        forecast_days: int = 14,
        **kwargs,
    ) -> list[Forecast]:
        """
        Generate forecast using specified method.

        Methods:
        - "sma" or "simple": Simple Moving Average
        - "wma" or "weighted": Weighted Moving Average
        - "ses" or "exponential": Exponential Smoothing (default)
        """
        method = method.lower()

        if method in ("sma", "simple"):
            window = kwargs.get("window", 7)
            return self.simple_moving_average(product_id, window, forecast_days)
        elif method in ("wma", "weighted"):
            window = kwargs.get("window", 7)
            return self.weighted_moving_average(product_id, window, forecast_days)
        else:  # exponential is default
            alpha = kwargs.get("alpha", 0.3)
            return self.exponential_smoothing(product_id, alpha, forecast_days)

    def get_average_daily_demand(self, product_id: str, days: int = 30) -> float:
        """Calculate average daily demand over recent period."""
        daily_sales = self.get_product_daily_sales(product_id)

        if daily_sales.empty:
            return 0.0

        if len(daily_sales) <= days:
            return float(daily_sales.mean())

        return float(daily_sales.iloc[-days:].mean())

    def get_demand_trend(self, product_id: str) -> str:
        """Determine if demand is increasing, decreasing, or stable."""
        daily_sales = self.get_product_daily_sales(product_id)

        if len(daily_sales) < 14:
            return "insufficient_data"

        # Compare recent week to previous week
        recent = daily_sales.iloc[-7:].mean()
        previous = daily_sales.iloc[-14:-7].mean()

        if previous == 0:
            return "stable" if recent == 0 else "increasing"

        change = (recent - previous) / previous

        if change > 0.1:
            return "increasing"
        elif change < -0.1:
            return "decreasing"
        else:
            return "stable"
