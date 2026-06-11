"""Audio module for The Pitch.

Provides the AudioManager class that handles loading and playing
goal sound effects via pygame.mixer.

pygame.mixer is imported lazily so that headless / cloud deployments
(which do not install pygame) can import this module without crashing.
"""

import logging
import os

logger = logging.getLogger(__name__)


class AudioManager:
    """Manages audio playback for game events.

    Loads a goal sound file and plays it when a goal is scored.
    Handles missing files, missing pygame, and playback failures
    gracefully by logging warnings and continuing without sound.
    """

    def __init__(self, sound_path: str = "goal.wav") -> None:
        """Initialize the AudioManager.

        Args:
            sound_path: Path to the goal sound WAV file.
                        Defaults to "goal.wav".
                        Pass an empty string to disable audio entirely
                        (used in headless / cloud mode).
        """
        self._sound_path = sound_path
        self._sound = None  # pygame.mixer.Sound or None
        self._load_sound()

    def _load_sound(self) -> None:
        """Attempt to load the sound file.

        Logs a warning and continues if pygame is unavailable,
        the file is missing, or the file cannot be loaded.
        """
        # Empty path = caller explicitly disabled audio (headless mode)
        if not self._sound_path:
            logger.info("Audio disabled (empty sound_path).")
            return

        if not os.path.isfile(self._sound_path):
            logger.warning(
                "Audio file not found: %s. Goal sounds will be disabled.",
                self._sound_path,
            )
            return

        # Lazy import — pygame may not be installed in headless/cloud mode
        try:
            import pygame.mixer as _mixer
            self._sound = _mixer.Sound(self._sound_path)
        except ImportError:
            logger.warning(
                "pygame not installed — audio disabled (headless mode)."
            )
        except Exception as e:
            logger.warning(
                "Failed to load audio file '%s': %s. Goal sounds will be disabled.",
                self._sound_path,
                e,
            )
            self._sound = None

    def play_goal_sound(self) -> None:
        """Play the goal sound effect.

        If the sound was not loaded (missing file, missing pygame, or load
        failure), this method does nothing silently.
        """
        if self._sound is None:
            return

        try:
            self._sound.play()
        except Exception as e:
            logger.warning("Failed to play goal sound: %s", e)
