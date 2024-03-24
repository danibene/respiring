import argparse
import logging
import sys

import cv2
import numpy as np
from moviepy.editor import AudioFileClip, VideoClip
from scipy.io.wavfile import write

from respiring import __version__

__author__ = "danibene"
__copyright__ = "danibene"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


class BreathingExercise:
    def __init__(self, pattern: tuple = (4, 7, 8)):
        self.pattern = pattern  # (inhale, hold, exhale) in seconds
        self.cycle_duration = sum(pattern)

    # Function to generate bell sound
    @staticmethod
    def generate_bell_sound(
        fundamental_frequency: float, duration: float, sample_rate: int = 44100
    ) -> np.ndarray:
        harmonics = [1, 2, 2.8, 3.5, 4.5]
        harmonic_strengths = [0.5, 0.75, 0.33, 0.14, 0.05]
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        sound = np.zeros_like(t)
        for harmonic, strength in zip(harmonics, harmonic_strengths):
            sound += strength * np.sin(2 * np.pi * harmonic * fundamental_frequency * t)
        envelope = np.e ** (-3 * t)
        sound *= envelope
        sound /= np.max(np.abs(sound))
        return np.int16(sound * 32767)

    def sequence_bell_sounds(
        self, high_freq: float, low_freq: float, duration: int, sample_rate: int = 44100
    ) -> np.ndarray:
        inhale_sound = self.generate_bell_sound(high_freq, self.pattern[0], sample_rate)
        hold_sound = np.zeros(
            int(self.pattern[1] * sample_rate), dtype=np.int16
        )  # Silence for holding breath
        exhale_sound = self.generate_bell_sound(low_freq, self.pattern[2], sample_rate)
        sound_sequence = np.array([], dtype=np.int16)
        cycle_count = int(duration / self.cycle_duration)
        for _ in range(cycle_count):
            cycle_sounds = np.concatenate((inhale_sound, hold_sound, exhale_sound))
            sound_sequence = np.concatenate((sound_sequence, cycle_sounds))
        return sound_sequence

    # Function to create a frame with a circle
    def make_frame(self, t: float) -> np.ndarray:
        canvas_size = (640, 480)
        center = (int(canvas_size[0] / 2), int(canvas_size[1] / 2))
        max_radius = min(canvas_size) / 4

        phase_duration = self.cycle_duration  # Total duration of one breathing cycle
        inhale_duration, hold_duration, exhale_duration = self.pattern

        # Calculate the current phase of the breathing cycle and its progress
        cycle_progress = t % phase_duration
        if cycle_progress <= inhale_duration:
            # Inhale phase
            phase_progress = cycle_progress / inhale_duration
            radius = max_radius * phase_progress
            color = (150, 200, 150)  # Green for inhale
        elif cycle_progress <= inhale_duration + hold_duration:
            # Hold phase
            radius = max_radius  # Keep the circle fully expanded
            color = (220, 220, 250)  # Blue-ish white for hold
        else:
            # Exhale phase
            phase_progress = (
                cycle_progress - inhale_duration - hold_duration
            ) / exhale_duration
            radius = max_radius * (1 - phase_progress)
            color = (200, 150, 150)  # Red for exhale

        # Create an empty frame
        frame = np.zeros((canvas_size[1], canvas_size[0], 3), dtype=np.uint8)
        # Draw the circle
        cv2.circle(frame, center, int(radius), color, -1)

        return frame


def generate_video(duration: int = 300, pattern: tuple = (4, 7, 8)) -> None:
    """Generate a video with breathing instructions and bell sounds

    Args:
        duration (int): Duration of the video in seconds. Defaults to 300.
        pattern (tuple): The breathing pattern as a tuple (inhale, hold, exhale) in
            seconds. Defaults to (4, 7, 8).

    Returns:
        None
    """
    sample_rate = 44100  # Sample rate for audio
    frame_rate = 24  # Frames per second for video
    high_freq = 880  # Higher fundamental frequency for inhale
    low_freq = 440  # Lower fundamental frequency for exhale

    # Create the breathing exercise object with the specified pattern
    breathing_exercise = BreathingExercise(pattern=pattern)

    # Generate the sequence of bell sounds according to the pattern
    sound_sequence = breathing_exercise.sequence_bell_sounds(
        high_freq, low_freq, duration, sample_rate
    )

    # Save the generated sound sequence to a WAV file
    sound_filename = "breathing_bells.wav"
    write(sound_filename, sample_rate, sound_sequence)

    # Create the video clip with visual instructions based on the breathing exercise
    video_clip = VideoClip(breathing_exercise.make_frame, duration=duration).set_fps(
        frame_rate
    )

    # Add the generated audio to the video clip
    video_clip = video_clip.set_audio(AudioFileClip(sound_filename))

    # Write the final video file with audio
    final_filename = "breathing_instruction_with_sound.mp4"
    video_clip.write_videofile(
        final_filename, fps=frame_rate, codec="libx264", audio_codec="aac"
    )

    _logger.info(f"Breathing exercise video with bell sounds saved to {final_filename}")


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args: list) -> argparse.Namespace:
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"respiring {__version__}",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        help="Breathing pattern as a tuple (inhale, hold, exhale) in seconds",
        type=lambda x: tuple(map(int, x.split(","))),
        default=(4, 7, 8),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel: int) -> None:
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args: list) -> None:
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    parsed_args = parse_args(args)
    setup_logging(parsed_args.loglevel)
    _logger.debug("Starting crazy calculations...")
    generate_video(pattern=parsed_args.pattern)
    _logger.info("Script ends here")


def run() -> None:
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m respiring.skeleton 42
    #
    run()
