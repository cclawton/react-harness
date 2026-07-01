"""Tests for the weather client — do not modify this file."""
import pytest
from client import WeatherClient, Forecast, DayForecast


@pytest.fixture
def client():
    return WeatherClient(api_key="test-key")


@pytest.fixture
def melbourne_forecast(client):
    return client.get_forecast("melbourne")


class TestGetForecast:
    def test_returns_forecast_object(self, melbourne_forecast):
        assert isinstance(melbourne_forecast, Forecast)

    def test_city_name(self, melbourne_forecast):
        assert melbourne_forecast.city == "melbourne"

    def test_has_five_days(self, melbourne_forecast):
        assert len(melbourne_forecast.days) == 5

    def test_days_are_dayforecast_objects(self, melbourne_forecast):
        assert all(isinstance(d, DayForecast) for d in melbourne_forecast.days)

    def test_days_in_chronological_order(self, melbourne_forecast):
        dates = [d.date for d in melbourne_forecast.days]
        assert dates == sorted(dates), f"Dates not in order: {dates}"

    def test_first_day_date(self, melbourne_forecast):
        assert melbourne_forecast.days[0].date == "2026-07-01"

    def test_unknown_city_raises(self, client):
        with pytest.raises(ValueError, match="Unknown city"):
            client.get_forecast("brisbane")


class TestAvgTemp:
    def test_melbourne_avg(self, melbourne_forecast):
        expected = (15.2 + 17.5 + 12.0 + 13.0 + 14.0) / 5
        assert melbourne_forecast.avg_temp == pytest.approx(expected)

    def test_empty_forecast(self):
        f = Forecast(city="nowhere", days=[])
        assert f.avg_temp == 0.0


class TestHottestDay:
    def test_melbourne_hottest(self, melbourne_forecast):
        hottest = melbourne_forecast.hottest_day
        assert hottest is not None
        assert hottest.temp_high == 17.5
        assert hottest.date == "2026-07-02"

    def test_hottest_not_by_low(self, melbourne_forecast):
        """Ensure hottest_day uses temp_high, not temp_low."""
        hottest = melbourne_forecast.hottest_day
        # 2026-07-01 has the highest temp_low (9.0) but not the highest temp_high
        # 2026-07-02 has the highest temp_high (17.5)
        assert hottest.date == "2026-07-02"
        assert hottest.temp_low == 8.1  # NOT 9.0

    def test_empty_forecast(self):
        f = Forecast(city="nowhere", days=[])
        assert f.hottest_day is None


class TestColdestDay:
    def test_melbourne_coldest(self, melbourne_forecast):
        coldest = melbourne_forecast.coldest_day
        assert coldest is not None
        assert coldest.temp_low == 1.2
        assert coldest.date == "2026-07-04"

    def test_coldest_not_by_high(self, melbourne_forecast):
        """Ensure coldest_day uses temp_low, not temp_high."""
        coldest = melbourne_forecast.coldest_day
        # 2026-07-03 has the lowest temp_high (12.0) but not the lowest temp_low
        # 2026-07-04 has the lowest temp_low (1.2)
        assert coldest.date == "2026-07-04"
        assert coldest.temp_high == 13.0  # NOT 12.0

    def test_empty_forecast(self):
        f = Forecast(city="nowhere", days=[])
        assert f.coldest_day is None


class TestConvenienceMethods:
    def test_get_hottest_day(self, client):
        day = client.get_hottest_day("sydney")
        assert day is not None
        assert day.temp_high == 22.5

    def test_get_coldest_day(self, client):
        day = client.get_coldest_day("sydney")
        assert day is not None
        assert day.temp_low == 11.0
