from typing import Optional, Callable

def pass_exceptions(f, e: Optional[Callable[[Exception], None]] = None):
    def _f():
        try: f()
        except Exception as ex: 
            if e: e(ex)

    return _f