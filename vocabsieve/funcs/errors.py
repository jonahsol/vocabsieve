from typing import Optional

def pass_exceptions(f):
    def _f():
        try: f()
        except: pass
    return _f