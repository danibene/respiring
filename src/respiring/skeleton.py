"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = respiring.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

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


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from respiring.skeleton import fib`,
# when using this Python module as a library.


class BreathingExercise:
    def __init__(self, bpm: int):
        self.bpm = bpm
        self.cycle_duration = 60 / bpm

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

    # Function to sequence bell sounds
    def sequence_bell_sounds(
        self, high_freq: float, low_freq: float, duration: int, sample_rate: int = 44100
    ) -> np.ndarray:
        inhale_duration = self.cycle_duration / 2
        exhale_duration = self.cycle_duration / 2

        inhale_sound = self.generate_bell_sound(high_freq, inhale_duration, sample_rate)
        exhale_sound = self.generate_bell_sound(low_freq, exhale_duration, sample_rate)

        sound_sequence = np.array([], dtype=np.int16)
        for _ in range(int(duration / self.cycle_duration)):
            sound_sequence = np.concatenate(
                (sound_sequence, inhale_sound, exhale_sound)
            )

        return sound_sequence

    # Function to create a frame with a circle
    def make_frame(self, t: float) -> np.ndarray:
        canvas_size = (640, 480)
        center = (int(canvas_size[0] / 2), int(canvas_size[1] / 2))
        max_radius = min(canvas_size) / 4

        # Calculate the current phase of the breathing cycle
        phase = (t % self.cycle_duration) / self.cycle_duration
        if phase <= 0.5:
            # Inhale
            radius = max_radius * (2 * phase)
        else:
            # Exhale
            radius = max_radius * (2 * (1 - phase))

        # Create an empty frame
        frame = np.zeros((canvas_size[1], canvas_size[0], 3), dtype=np.uint8)
        # Draw the circle
        cv2.circle(frame, center, int(radius), (255, 255, 255), -1)

        return frame


def generate_video(bpm: int) -> None:
    """Generate a video with breathing instructions and bell sounds

    Args:
        bpm (int): Breaths per minute

    Returns:
        None
    """
    # Parameters for both sound and video
    duration = 60  # seconds
    sample_rate = 44100
    frame_rate = 24  # frames per second
    high_freq = 220  # Higher fundamental frequency for inhale
    low_freq = 110  # Lower fundamental frequency for exhale

    # Create the breathing exercise object
    breathing_exercise = BreathingExercise(bpm)

    # Generate the sequence
    sound_sequence = breathing_exercise.sequence_bell_sounds(
        high_freq, low_freq, duration, sample_rate
    )

    # Save to a WAV file
    sound_filename = "breathing_bells.wav"
    write(sound_filename, sample_rate, sound_sequence)

    # Create the video clip
    video_clip = VideoClip(breathing_exercise.make_frame, duration=duration).set_fps(
        frame_rate
    )

    # Add audio to the video clip
    video_clip = video_clip.set_audio(AudioFileClip(sound_filename))

    # Write the video file with audio
    final_filename = "breathing_instruction_with_sound.mp4"
    # video_clip.write_videofile(final_filename, fps=frame_rate)
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
    parser.add_argument(dest="bpm", help="Breaths per minute", type=int)
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
    generate_video(parsed_args.bpm)
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
