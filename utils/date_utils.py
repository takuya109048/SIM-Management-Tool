# -*- coding: utf-8 -*-
from datetime import datetime, date
from typing import Optional

DATE_FORMATS = ['%Y-%m-%d', '%Y/%m/%d']

def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def days_between(a: Optional[date], b: Optional[date]) -> Optional[int]:
    """2つの日付の間の日数を計算する。bがaより前の場合はNoneを返す。"""
    if not a or not b or b < a:
        return None
    return (b - a).days

def months_ceil_between(a: Optional[date], b: Optional[date]) -> Optional[int]:
    """2つの日付の間の月数を計算する（切り上げ）。"""
    d = days_between(a, b)
    if d is None:
        return None
    # 0日の場合は0ヶ月
    if d == 0:
        return 0
    # 日数を30で割り、切り上げる
    return (d - 1) // 30 + 1
