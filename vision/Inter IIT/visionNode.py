# Auto-generated visionNode stub
class DummyVision:
    def capture(self, *a, **k): raise RuntimeError('Vision not implemented')
    def capture_once(self, *a, **k): raise RuntimeError('Vision not implemented')
    def led(self, *a, **k): return False
    def led_off(self, *a, **k): return False
    def wait_until_done(self, *a, **k): pass
    @property
    def scanner(self): return self
    def open_servo_debug_terminal(self): pass

def get():
    return DummyVision()
