import numpy as np
from pytest import CaptureFixture, TempPathFactory

from respiring.skeleton import BreathingExercise, main

__author__ = "danibene"
__copyright__ = "danibene"
__license__ = "MIT"


class TestBreathingExercise:
    pattern: tuple
    exercise: BreathingExercise
    sample_rate: int

    @classmethod
    def setup_class(cls) -> None:
        cls.pattern = (4, 7, 8)  # Example pattern
        cls.exercise = BreathingExercise(pattern=cls.pattern)
        cls.sample_rate = 44100

    def test_generate_bell_sound(self) -> None:
        """Test the bell sound generation."""
        duration = 2  # seconds
        sound = self.exercise.generate_bell_sound(
            fundamental_frequency=440, duration=duration, sample_rate=self.sample_rate
        )
        expected_length = duration * self.sample_rate
        assert (
            len(sound) == expected_length
        ), "Generated sound length does not match expected duration."
        assert isinstance(sound, np.ndarray), "Generated sound is not a numpy array."
        assert (
            sound.dtype == np.int16
        ), "Generated sound array does not have the correct data type."

    def test_sequence_bell_sounds(self) -> None:
        """Test the sequencing of bell sounds."""
        duration = 60  # total duration in seconds for multiple cycles
        sound_sequence = self.exercise.sequence_bell_sounds(
            high_freq=880, low_freq=440, duration=duration, sample_rate=self.sample_rate
        )
        expected_cycles = duration // sum(self.pattern)
        expected_length = expected_cycles * sum(self.pattern) * self.sample_rate
        assert (
            len(sound_sequence) == expected_length
        ), "Sound sequence length does not match expected total duration."
        assert np.all(
            sound_sequence[
                self.pattern[0]
                * self.sample_rate : (self.pattern[0] + self.pattern[1])
                * self.sample_rate
            ]
            == 0
        ), "Hold phase is not silent."

    def test_make_frame(self) -> None:
        """Test frame generation at different timestamps."""
        # Test at different timestamps within the cycle
        for t in [0, 2, 6, 10, 14]:  # Covering different phases
            frame = self.exercise.make_frame(t)
            assert frame.shape == (
                480,
                640,
                3,
            ), "Generated frame does not have expected dimensions."
            assert np.all(
                frame[0, 0] == [0, 0, 0]
            ), "Frame background color is not black."


def test_main(capsys: CaptureFixture, tmp_path_factory: TempPathFactory) -> None:
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts against stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    # tmp_path_factory is a pytest fixture that creates temporary directories
    # https://docs.pytest.org/en/stable/tmpdir.html
    output_filepath = tmp_path_factory.mktemp("data") / "test.mp4"
    main(["--pattern", "6, 0, 6", "--output", str(output_filepath)])
    captured = capsys.readouterr()
    assert "Building video" in captured.out
