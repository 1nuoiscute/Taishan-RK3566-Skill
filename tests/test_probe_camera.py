import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "probe_camera.py"
SPEC = importlib.util.spec_from_file_location("probe_camera", MODULE_PATH)
probe_camera = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_camera)


class FakeFrame:
    shape = (2, 3, 3)

    def __init__(self, brightness=100.0):
        self._brightness = brightness

    def mean(self):
        return self._brightness


class FakeCapture:
    def __init__(self, frames):
        self.frames = iter(frames)

    def read(self):
        try:
            return True, next(self.frames)
        except StopIteration:
            return False, None


class FakeClock:
    def __init__(self, step=0.04):
        self.value = 0.0
        self.step = step

    def monotonic(self):
        self.value += self.step
        return self.value


class Args:
    stable_condition = "fps"
    stable_window = 5
    stable_tolerance = 5.0
    stable_timeout = 2.0


class StabilityTests(unittest.TestCase):
    def test_fps_condition_can_reach_stable(self):
        capture = FakeCapture([FakeFrame() for _ in range(12)])
        clock = FakeClock(step=0.04)
        result, total = probe_camera.monitor_until_stable(
            capture, FakeFrame(), 640, 480, Args(),
            monotonic=clock.monotonic, sleep=lambda _: None,
        )
        self.assertEqual("stable", result["outcome"])
        self.assertGreaterEqual(result["history_size"], 5)
        self.assertGreaterEqual(total, 6)

    def test_brightness_condition_times_out_when_unstable(self):
        class BrightnessArgs(Args):
            stable_condition = "brightness"
            stable_timeout = 0.5

        capture = FakeCapture(
            [FakeFrame(50.0 if index % 2 else 150.0) for index in range(20)]
        )
        clock = FakeClock(step=0.04)
        result, _ = probe_camera.monitor_until_stable(
            capture, FakeFrame(50.0), 640, 480, BrightnessArgs(),
            monotonic=clock.monotonic, sleep=lambda _: None,
        )
        self.assertEqual("timeout", result["outcome"])


if __name__ == "__main__":
    unittest.main()
