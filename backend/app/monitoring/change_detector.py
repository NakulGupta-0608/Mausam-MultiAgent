import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.schemas.weather import WeatherCondition
from backend.app.schemas.plan import NotificationPreferences, DetectedChange


class ChangeEvaluation(BaseModel):
    """Result of comparing current empirical telemetry against the baseline snapshot."""
    is_significant: bool
    changes: List[DetectedChange]
    summary: str


class ChangeDetector:
    """Evaluates atmospheric telemetry deltas against configurable thresholds.
    
    Filters out minor noise/fluctuations (e.g., ±0.4°C temp jitter) and identifies
    meaningful meteorological changes that warrant re-evaluating risk and recommendation.
    """

    @staticmethod
    def evaluate(
        current_weather: WeatherCondition,
        snapshot: Dict[str, Any],
        preferences: Optional[NotificationPreferences] = None
    ) -> ChangeEvaluation:
        prefs = preferences or NotificationPreferences()
        changes: List[DetectedChange] = []
        now = datetime.now(timezone.utc).isoformat()

        # 1. Precipitation Probability Check
        old_rain_prob = int(snapshot.get("precipitation_prob", 0))
        new_rain_prob = int(current_weather.precipitation_prob)
        rain_diff = new_rain_prob - old_rain_prob
        abs_rain_diff = abs(rain_diff)

        if abs_rain_diff >= prefs.rain_threshold_pct:
            sign = "+" if rain_diff > 0 else ""
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Precipitation Probability",
                old_value=f"{old_rain_prob}%",
                new_value=f"{new_rain_prob}%",
                delta=f"{sign}{rain_diff}%",
                significance_reason=f"Exceeded rain threshold delta of {prefs.rain_threshold_pct}% (Shift: {sign}{rain_diff}%).",
            ))
        elif old_rain_prob < 30 and new_rain_prob >= 50:
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Precipitation Probability",
                old_value=f"{old_rain_prob}%",
                new_value=f"{new_rain_prob}%",
                delta=f"+{rain_diff}%",
                significance_reason="Crossed critical precipitation boundary into likely convective showers (>=50%).",
            ))

        # 2. Wind Velocity Check
        old_wind = float(snapshot.get("wind_kph", 0.0))
        new_wind = float(current_weather.wind_kph)
        wind_diff = round(new_wind - old_wind, 1)
        abs_wind_diff = abs(wind_diff)

        if abs_wind_diff >= prefs.wind_threshold_kph:
            sign = "+" if wind_diff > 0 else ""
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Wind Velocity",
                old_value=f"{old_wind} km/h",
                new_value=f"{new_wind} km/h",
                delta=f"{sign}{wind_diff} km/h",
                significance_reason=f"Exceeded wind threshold delta of {prefs.wind_threshold_kph} km/h (Shift: {sign}{wind_diff} km/h).",
            ))
        elif old_wind < 25.0 and new_wind >= 35.0:
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Wind Velocity",
                old_value=f"{old_wind} km/h",
                new_value=f"{new_wind} km/h",
                delta=f"+{wind_diff} km/h",
                significance_reason="Exceeded high-altitude exposed safety limit (>=35 km/h gusts).",
            ))

        # 3. Ambient Temperature Check
        old_temp = float(snapshot.get("temp_c", 0.0))
        new_temp = float(current_weather.temp_c)
        temp_diff = round(new_temp - old_temp, 1)
        abs_temp_diff = abs(temp_diff)

        if abs_temp_diff >= prefs.temp_threshold_c:
            sign = "+" if temp_diff > 0 else ""
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Ambient Temperature",
                old_value=f"{old_temp}°C",
                new_value=f"{new_temp}°C",
                delta=f"{sign}{temp_diff}°C",
                significance_reason=f"Thermal variation exceeded threshold of {prefs.temp_threshold_c}°C.",
            ))

        # 4. Severe Atmospheric Condition Transition
        old_cond = str(snapshot.get("condition_text", "")).strip().lower()
        new_cond = str(current_weather.condition_text).strip().lower()

        severe_keywords = ["thunderstorm", "hail", "heavy rain", "snow", "squall", "dense fog", "gale", "freezing rain"]
        is_now_severe = any(k in new_cond for k in severe_keywords)
        was_severe = any(k in old_cond for k in severe_keywords)

        if is_now_severe and not was_severe:
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Severe Atmospheric Transition",
                old_value=snapshot.get("condition_text", "Normal"),
                new_value=current_weather.condition_text,
                delta="Severe Alert",
                significance_reason=f"Atmospheric condition transitioned into hazardous state: '{current_weather.condition_text}'.",
            ))
        elif old_cond != new_cond and abs_rain_diff >= 10:
            # Condition changed with notable moisture delta
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Condition Shift",
                old_value=snapshot.get("condition_text", ""),
                new_value=current_weather.condition_text,
                delta="Shift",
                significance_reason=f"Weather condition shifted from '{snapshot.get('condition_text')}' to '{current_weather.condition_text}'.",
            ))

        # 5. UV Index Check
        old_uv = float(snapshot.get("uv_index", 0.0))
        new_uv = float(current_weather.uv_index)
        uv_diff = round(new_uv - old_uv, 1)
        abs_uv_diff = abs(uv_diff)

        if abs_uv_diff >= prefs.uv_threshold:
            sign = "+" if uv_diff > 0 else ""
            changes.append(DetectedChange(
                id=str(uuid.uuid4())[:8],
                timestamp=now,
                metric="Solar UV Index",
                old_value=f"{old_uv}",
                new_value=f"{new_uv}",
                delta=f"{sign}{uv_diff}",
                significance_reason=f"UV index delta exceeded threshold of {prefs.uv_threshold}.",
            ))

        is_significant = len(changes) > 0
        if is_significant:
            summary_parts = [f"{c.metric}: {c.old_value} -> {c.new_value} ({c.delta})" for c in changes]
            summary = "Significant atmospheric shift detected: " + "; ".join(summary_parts)
        else:
            summary = "Telemetry consistent with baseline. No meaningful changes breaching threshold."

        return ChangeEvaluation(
            is_significant=is_significant,
            changes=changes,
            summary=summary,
        )


change_detector = ChangeDetector()
