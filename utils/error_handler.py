# -*- coding: utf-8 -*-
import traceback
def safe_run(func, *args, default=None, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        traceback.print_exc()
        return default
