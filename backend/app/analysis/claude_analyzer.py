"""Claude AI analyzer — async parallel analysis with timeout protection."""
from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta

import anthropic
from sqlalchemy.orm import Session

from app.core.exceptions import AnalysisError
from app.core.settings import settings
from app.models.db_models import ClaudeAnalysis, NewsItem, PegSetup, TechnicalSignal
from app.universe.sectors import ALL_TICKERS, TICKER_SECTOR

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a trading analyst specialising in growth stocks using the
William O'Neil CANSLIM methodology combined with Stan Weinstein stage analysis.

Evaluate stocks based on:
- Power Earnings Gap (PEG) setups and gap integrity
- Base patterns (1st, 2nd, 3rd, 4th base — later bases are riskier)
- Weinstein Stage (must be Stage 2 for buys)
- Moving average structure (9 EMA, 21 EMA, 50 SMA, 200 SMA)
- ADR sweet spot (3–10%)
- ATR extension from 50 SMA (>3× = extended, consider trim)
- Volume patterns (accumulation vs distribution)

You MUST respond with valid JSON only — no markdown, no explanation outside the JSON.
"""

_SCHEMA = {
    "ticker":      "string",
    "conviction":  "integer 1-10",
    "action":      "BUY | ADD | HOLD | TRIM | SELL | WATCH",
    "entry_zone":  "price range string e.g. '142-145'",
    "stop_loss":   "float",
    "risk_reward": "string e.g. '1:3'",
    "stage":       "Stage 1 | Stage 2 | Stage 3 | Stage 4",
    "base_number": "integer 1-4 or null",
    "key_levels":  {"support": "float", "resistance": "float"},
    "reasoning":   "2-3 sentence thesis",
    "warnings":    ["list of red flag strings"],
}


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseAnalyzer(ABC):
    """Interface that all AI analyzer implementations must satisfy."""

    @abstractmethod
    async def analyze_ticker_async(self, db: Session, ticker: str) -> dict | None: ...

    @abstractmethod
    def run_all(self, db: Session, tickers: list[str] | None = None) -> dict[str, str]: ...


# ── Concrete implementation ───────────────────────────────────────────────────

class ClaudeAnalyzer(BaseAnalyzer):
    """Calls Claude to produce structured trading analysis for each ticker.

    Uses asyncio.gather for parallel calls, asyncio.wait_for for per-ticker
    timeout protection, and asyncio.create_task for fire-and-forget DB saves
    while the next analysis is already running.
    """

    def __init__(
        self,
        api_key: str = settings.anthropic_api_key,
        model: str = settings.claude_model,
        concurrency: int = settings.claude_concurrency,
        timeout: float = settings.claude_timeout_sec,
    ) -> None:
        self._api_key    = api_key
        self._model      = model
        self._concurrency = concurrency
        self._timeout    = timeout
        self._async_client: anthropic.AsyncAnthropic | None = None

    @classmethod
    def from_settings(cls) -> "ClaudeAnalyzer":
        return cls(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            concurrency=settings.claude_concurrency,
            timeout=settings.claude_timeout_sec,
        )

    # ── async public interface ────────────────────────────────────────────────

    async def analyze_ticker_async(self, db: Session, ticker: str) -> dict | None:
        """Call Claude for a single ticker; return parsed JSON or None on failure."""
        context = self._build_context(db, ticker)
        prompt = (
            f"{context}\n\n"
            f"Analyse {ticker} using the criteria above. "
            f"Respond with JSON matching this schema:\n{json.dumps(_SCHEMA, indent=2)}"
        )
        try:
            client = self._get_async_client()
            response = await asyncio.wait_for(
                client.messages.create(
                    model=self._model,
                    max_tokens=1024,
                    system=_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=self._timeout,
            )
            raw    = response.content[0].text.strip()
            result = json.loads(raw)
            result["ticker"] = ticker
            return result
        except asyncio.TimeoutError:
            logger.warning("%s: Claude analysis timed out (%.0fs)", ticker, self._timeout)
            return None
        except json.JSONDecodeError as exc:
            logger.error("%s: JSON parse error — %s", ticker, exc)
            return None
        except Exception as exc:
            logger.error("%s: Claude API error — %s", ticker, exc)
            return None

    async def run_all_async(
        self, db: Session, tickers: list[str] | None = None
    ) -> dict[str, str]:
        """Analyse all tickers with bounded parallelism.

        asyncio.create_task fires off DB saves concurrently with the next
        ticker's analysis so saves don't block the analysis pipeline.
        """
        targets = tickers or ALL_TICKERS
        sem     = asyncio.Semaphore(self._concurrency)
        results: dict[str, str] = {}
        save_tasks: list[asyncio.Task] = []
        loop = asyncio.get_event_loop()

        async def _bounded(ticker: str):
            async with sem:
                return ticker, await self.analyze_ticker_async(db, ticker)

        items = await asyncio.gather(*[_bounded(t) for t in targets], return_exceptions=True)

        for item in items:
            if isinstance(item, BaseException):
                continue
            ticker, result = item
            if result:
                # Fire-and-forget: save to DB while next batch of analysis runs
                task = asyncio.create_task(
                    loop.run_in_executor(None, self._save_sync, db, ticker, result)
                )
                save_tasks.append(task)
                results[ticker] = result.get("action", "?")
                logger.info("%s: %s (conviction %s)", ticker, result.get("action"), result.get("conviction"))
            else:
                results[ticker] = "error"

        # Wait for all outstanding saves before returning
        if save_tasks:
            await asyncio.gather(*save_tasks, return_exceptions=True)

        return results

    # ── sync bridge for scheduler / background threads ────────────────────────

    def run_all(self, db: Session, tickers: list[str] | None = None) -> dict[str, str]:
        """Sync entry-point that runs the async pipeline in a fresh event loop."""
        return asyncio.run(self.run_all_async(db, tickers))

    # ── private helpers ───────────────────────────────────────────────────────

    def _get_async_client(self) -> anthropic.AsyncAnthropic:
        if self._async_client is None:
            self._async_client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._async_client

    def _build_context(self, db: Session, ticker: str) -> str:
        sector = TICKER_SECTOR.get(ticker, "Unknown")
        signal = (
            db.query(TechnicalSignal)
            .filter(TechnicalSignal.ticker == ticker)
            .order_by(TechnicalSignal.date.desc())
            .first()
        )
        peg = (
            db.query(PegSetup)
            .filter(PegSetup.ticker == ticker, PegSetup.gap_filled == False)  # noqa: E712
            .order_by(PegSetup.peg_date.desc())
            .first()
        )
        since = date.today() - timedelta(days=7)
        news = (
            db.query(NewsItem)
            .filter(NewsItem.ticker == ticker, NewsItem.published_at >= since)
            .order_by(NewsItem.published_at.desc())
            .limit(5)
            .all()
        )

        lines = [f"Ticker: {ticker}  Sector: {sector}"]
        if signal:
            lines += [
                f"Stage: {signal.weinstein_stage}  Base#: {signal.base_number}",
                f"Price MAs — EMA9:{signal.ema9}  EMA21:{signal.ema21}  SMA50:{signal.sma50}  SMA200:{signal.sma200}",
                f"ADR: {signal.adr_pct}%  ATR: {signal.atr}  ATR Extension: {signal.atr_extension}x",
                f"RVol: {signal.rvol}x  MA30W: {signal.ma30w}",
            ]
        if peg:
            lines.append(
                f"Active PEG: date={peg.peg_date}  low={peg.peg_low}"
                f"  gap={peg.gap_pct}%  vol_mult={peg.volume_multiple}x"
            )
        else:
            lines.append("No active PEG setup.")

        lines.append("Recent news:" if news else "No recent news.")
        lines += [f"  - {n.headline}" for n in news]

        return "\n".join(lines)

    @staticmethod
    def _save_sync(db: Session, ticker: str, result: dict) -> None:
        """Sync helper executed via run_in_executor so it doesn't block the loop."""
        try:
            record = ClaudeAnalysis(
                ticker=ticker,
                conviction=result.get("conviction"),
                action=result.get("action"),
                entry_zone=result.get("entry_zone"),
                stop_loss=result.get("stop_loss"),
                risk_reward=result.get("risk_reward"),
                stage=result.get("stage"),
                base_number=result.get("base_number"),
                reasoning=result.get("reasoning"),
                warnings=result.get("warnings", []),
                raw_json=result,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        except Exception as exc:
            logger.error("DB save failed for %s: %s", ticker, exc)
            db.rollback()


claude_analyzer = ClaudeAnalyzer.from_settings()
