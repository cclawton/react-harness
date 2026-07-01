"""API client for a fictional weather service.

This module has a bug — the `get_forecast` method incorrectly
handles the daily forecast list. The tests in test_client.py
will fail. Fix the bug without changing the test file.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DayForecast:
    date: str
    temp_high: float
    temp_low: float
    conditions: str


@dataclass
class Forecast:
    city: str
    days: list[DayForecast]

    @property
    def avg_temp(self) -> float:
        """Average of all daily high temperatures."""
        if not self.days:
            return 0.0
        return sum(d.temp_high for d in self.days) / len(self.days)

    @property
    def hottest_day(self) -> Optional[DayForecast]:
        """The day with the highest temperature."""
        if not self.days:
            return None
        return max(self.days, key=lambda d: d.temp_high)

    @property
    def coldest_day(self) -> Optional[DayForecast]:
        """The day with the lowest temperature."""
        if not self.days:
            return None
        return min(self.days, key=lambda d: d.temp_low)


class WeatherClient:
    """Simulated weather API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._mock_data = {
            "melbourne": [
                {"date": "2026-07-01", "temp_high": 15.2, "temp_low": 9.0, "conditions": "cloudy"},
                {"date": "2026-07-02", "temp_high": 17.5, "temp_low": 8.1, "conditions": "sunny"},
                {"date": "2026-07-03", "temp_high": 12.0, "temp_low": 3.5, "conditions": "rain"},
                {"date": "2026-07-04", "temp_high": 13.0, "temp_low": 1.2, "conditions": "snow"},
                {"date": "2026-07-05", "temp_high": 14.0, "temp_low": 5.0, "conditions": "windy"},
            ],
            "sydney": [
                {"date": "2026-07-01", "temp_high": 21.3, "temp_low": 12.5, "conditions": "sunny"},
                {"date": "2026-07-02", "temp_high": 19.8, "temp_low": 11.0, "conditions": "cloudy"},
                {"date": "2026-07-03", "temp_high": 22.5, "temp_low": 13.8, "conditions": "sunny"},
            ],
        }

    def get_forecast(self, city: str) -> Forecast:
        """Get a 5-day forecast for a city."""
        city = city.lower()
        if city not in self._mock_data:
            raise ValueError(f"Unknown city: {city}")

        raw = self._mock_data[city]
        days = [DayForecast(**d) for d in raw]

        return Forecast(city=city, days=days)

    def get_hottest_day(self, city: str) -> Optional[DayForecast]:
        """Convenience method — returns the hottest day in the forecast."""
        forecast = self.get_forecast(city)
        return forecast.hottest_day

    def get_coldest_day(self, city: str) -> Optional[DayForecast]:
        """Convenience method — returns the coldest day in the forecast."""
        forecast = self.get_forecast(city)
        return forecast.coldest_day
