"""Unit tests for screener classes."""
import pytest
import pandas as pd
from datetime import date

from app.screener.technical import TechnicalAnalyzer, SignalSnapshot
from app.screener.peg_scanner import PegScanner, PegCandidate


@pytest.mark.unit
class TestTechnicalAnalyzer:
    """Test TechnicalAnalyzer indicator computation."""

    def test_compute_signals_success(self):
        """Test indicator computation on valid data."""
        df = pd.DataFrame({
            "close": [100 + i for i in range(100)],
            "high":  [105 + i for i in range(100)],
            "low":   [95 + i for i in range(100)],
            "volume": [1_000_000] * 100,
        })
        df.index = pd.date_range("2026-01-01", periods=100)

        analyzer = TechnicalAnalyzer()
        signal = analyzer.compute_signals(df)

        assert isinstance(signal, SignalSnapshot)
        assert signal.ema9 > 0
        assert signal.sma50 > 0
        assert signal.adr_pct > 0
        assert signal.rvol > 0

    def test_compute_signals_insufficient_data(self):
        """Test with less than 200 rows returns None."""
        df = pd.DataFrame({
            "close": [100, 101, 102],
            "high":  [105, 106, 107],
            "low":   [95, 96, 97],
            "volume": [1_000_000, 1_000_000, 1_000_000],
        })
        df.index = pd.date_range("2026-01-01", periods=3)

        analyzer = TechnicalAnalyzer()
        signal = analyzer.compute_signals(df)
        assert signal is None


@pytest.mark.unit
class TestPegScanner:
    """Test PEG scanner logic."""

    def test_detect_pegs_valid_gap(self):
        """Test PEG detection with a valid gap."""
        # Need 25+ rows (scanner checks len >= 25)
        base_data = {
            "open":   [100.0] * 24,
            "close":  [100.0] * 24,
            "high":   [102.0] * 24,
            "low":    [98.0] * 24,
            "volume": [1_000_000] * 24,
        }
        # Add a PEG day on day 25
        for key in base_data:
            if key == "open":
                base_data[key].append(110.0)  # 10% gap
            elif key == "close":
                base_data[key].append(112.0)
            elif key == "high":
                base_data[key].append(115.0)
            elif key == "low":
                base_data[key].append(110.0)
            elif key == "volume":
                base_data[key].append(5_000_000)  # 5x volume

        df = pd.DataFrame(base_data)
        df.index = pd.date_range("2026-05-01", periods=25)

        scanner = PegScanner(gap_min_pct=3.0, vol_multiple=2.0)
        pegs = scanner.detect_pegs(df)

        assert len(pegs) >= 1
        peg = pegs[0]
        assert isinstance(peg, PegCandidate)
        assert peg.gap_pct >= 3.0
        assert peg.volume_multiple >= 2.0

    def test_detect_pegs_no_gap(self):
        """Test with no qualifying gaps."""
        df = pd.DataFrame({
            "open":   [100, 101, 102, 103],  # small moves
            "close":  [100, 101, 102, 103],
            "high":   [101, 102, 103, 104],
            "low":    [99,  100, 101, 102],
            "volume": [1_000_000] * 4,
        })
        df.index = pd.date_range("2026-05-01", periods=4)

        scanner = PegScanner(gap_min_pct=3.0, vol_multiple=2.0)
        pegs = scanner.detect_pegs(df)
        assert len(pegs) == 0

    def test_check_gap_filled_true(self):
        """Test gap fill detection when low breaks peg_low."""
        df = pd.DataFrame({
            "low": [110, 111, 108, 107],  # day 3 low=108 < peg_low=109
        })
        df.index = pd.date_range("2026-05-01", periods=4)

        filled = PegScanner.check_gap_filled(df, date(2026, 5, 1), peg_low=109.0)
        assert filled is True

    def test_check_gap_filled_false(self):
        """Test gap hold when all lows stay above peg_low."""
        df = pd.DataFrame({
            "low": [110, 111, 112, 113],
        })
        df.index = pd.date_range("2026-05-01", periods=4)

        filled = PegScanner.check_gap_filled(df, date(2026, 5, 1), peg_low=109.0)
        assert filled is False
