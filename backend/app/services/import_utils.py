from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import math
import pandas as pd
from convertdate import persian

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, pd.Series) and value.empty:
        return None
    text = str(value).strip()
    return text or None


def normalize_code(value: Any) -> str | None:
    # Handle numeric values (int, float) - convert to int to remove decimals
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        # Convert to int to remove decimal part, then to string
        return str(int(value))
    
    text = normalize_str(value)
    if not text:
        return None
    # Translate Persian digits to English
    text = text.translate(PERSIAN_DIGITS)
    # Remove decimal part if present (e.g., "723.0" -> "723")
    if "." in text:
        # Split by dot and take the integer part
        parts = text.split(".")
        if parts[0]:  # If there's an integer part
            return parts[0]
    return text


def parse_jalali(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return None
        # Handle float values like 0.0 which are invalid dates
        if value == 0.0:
            return None
    
    # Handle pandas datetime objects - if pandas read it as datetime, we need to get original string
    # Excel might have stored it as a date serial number, but we expect Jalali date strings
    if isinstance(value, pd.Timestamp):
        # Try to get the original string representation
        # If pandas converted it, it's likely wrong for Jalali dates
        # Return None to skip this field rather than using incorrect date
        return None
    
    # Convert to string and process
    text = str(value).strip()
    if not text:
        return None
    
    # Translate Persian digits to English
    text = text.translate(PERSIAN_DIGITS)
    
    # Check for invalid values like "0.0", "0", "0/0", etc.
    # These are often used as placeholders for missing dates
    normalized_for_check = text.replace("-", "/").replace(".", "/").replace(" ", "")
    parts_for_check = [part for part in normalized_for_check.split("/") if part]
    # If all parts are "0" or empty, treat as None
    if all(part == "0" or not part for part in parts_for_check):
        return None
    
    # Replace various separators with /
    text = text.replace("-", "/").replace(".", "/")
    # Remove any extra spaces
    text = "".join(text.split())
    parts = [part for part in text.split("/") if part]
    if len(parts) != 3:
        return None  # Return None instead of raising error for invalid formats
    
    try:
        year, month, day = (int(part) for part in parts)
        # Validate Jalali date ranges (rough check)
        if not (1300 <= year <= 1500) or not (1 <= month <= 12) or not (1 <= day <= 31):
            raise ValueError(f"محدوده تاریخ نامعتبر است: {year}/{month}/{day}")
        g_year, g_month, g_day = persian.to_gregorian(year, month, day)
        return date(g_year, g_month, g_day)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"خطا در تبدیل تاریخ: {value}") from exc


def safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = normalize_str(value)
    if text is not None:
        return text
    return None


def row_payload_from_series(row: pd.Series) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column in row.index:
        payload[str(column)] = safe_value(row[column])
    return payload


def parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        return Decimal(str(value))

    text = normalize_str(value)
    if not text:
        return None
    normalized = (
        text.translate(PERSIAN_DIGITS)
        .replace(",", "")
        .replace("٬", "")
        .replace("٫", ".")
    )
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:  # pragma: no cover - validation path
        raise ValueError(f"مقدار عددی نامعتبر: {value}") from exc


