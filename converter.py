import os
from typing import List, Optional
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
import numpy as np
import wave

class Converter:
    """A class to handle conversions between piano note numbers (1-88), MIDI, and WAV files."""
    
    @staticmethod
    def midi_to_number(midi_note: int) -> int:
        """Convert MIDI note number to 88-key piano number (1 to 88).
        
        Args:
            midi_note: MIDI note number (21 to 108).
        
        Returns:
            Integer from 1 to 88 representing the piano key number.
        
        Raises:
            ValueError: If MIDI note is outside valid range (21-108).
        """
        if not 21 <= midi_note <= 108:
            raise ValueError(f"MIDI note {midi_note} is outside 88-key piano range (21-108)")
        return midi_note - 20

    @staticmethod
    def number_to_midi(number: int) -> int:
        """Convert 88-key piano number (1 to 88) to MIDI note number.
        
        Args:
            number: Piano key number (1 to 88).
        
        Returns:
            MIDI note number (21 to 108).
        
        Raises:
            ValueError: If number is outside valid range (1-88).
        """
        if not 1 <= number <= 88:
            raise ValueError(f"Number {number} is outside 88-key piano range (1-88)")
        return number + 20

    @staticmethod
    def numbers_to_midi_file(
        numbers: List[int],
        output_file: str,
        note_duration: int = 500,
        velocity: int = 100,
        bpm: int = 120
    ) -> None:
        """Convert a list of piano numbers to a MIDI file (piano sound).
        
        Args:
            numbers: List of piano key numbers (1 to 88).
            output_file: Path to save the MIDI file.
            note_duration: Duration of each note in milliseconds.
            velocity: MIDI velocity (0 to 127).
            bpm: Beats per minute for the MIDI tempo.
        
        Raises:
            ValueError: If any number is invalid or output path is invalid.
        """
        if not output_file.endswith('.mid'):
            output_file += '.mid'
        
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Set MIDI parameters (piano sound, tempo)
        tempo = bpm2tempo(bpm)
        track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
        track.append(Message('program_change', program=0, time=0))  # Acoustic Grand Piano
        
        ticks_per_beat = mid.ticks_per_beat
        ms_per_tick = (60000 / bpm) / ticks_per_beat
        current_time = 0
        
        for number in numbers:
            try:
                midi_note = Converter.number_to_midi(number)
                track.append(Message('note_on', note=midi_note, velocity=velocity, time=current_time))
                duration_ticks = int(note_duration / ms_per_tick)
                track.append(Message('note_off', note=midi_note, velocity=0, time=duration_ticks))
                current_time = 0
            except ValueError as e:
                print(f"Error: {e}")
                continue
        
        track.append(MetaMessage('end_of_track', time=1))
        try:
            mid.save(output_file)
            print(f"Saved MIDI file: {output_file}")
        except Exception as e:
            raise IOError(f"Failed to save MIDI file: {e}")

    @staticmethod
    def midi_file_to_numbers(midi_file_path: str) -> List[int]:
        """Read a MIDI file and convert notes to piano numbers (1 to 88).
        
        Args:
            midi_file_path: Path to the MIDI file.
        
        Returns:
            List of piano key numbers (1 to 88).
        
        Raises:
            FileNotFoundError: If MIDI file does not exist.
        """
        if not os.path.exists(midi_file_path):
            raise FileNotFoundError(f"MIDI file {midi_file_path} does not exist")
        
        midi = MidiFile(midi_file_path)
        numbers = []
        for msg in midi.play():
            if msg.type == 'note_on' and msg.velocity > 0:
                try:
                    number = Converter.midi_to_number(msg.note)
                    numbers.append(number)
                except ValueError as e:
                    print(f"Error: {e}")
                    continue
        return numbers

    @staticmethod
    def numbers_to_wav(
        numbers: List[int],
        output_file: str,
        note_duration: float = 0.5,
        sample_rate: int = 44100,
        amplitude: float = 0.5
    ) -> None:
        """Convert piano numbers to a WAV file with simple sine wave synthesis.
        
        Args:
            numbers: List of piano key numbers (1 to 88).
            output_file: Path to save the WAV file.
            note_duration: Duration of each note in seconds.
            sample_rate: Audio sample rate in Hz.
            amplitude: Amplitude of the sine wave (0 to 1).
        
        Raises:
            ValueError: If any number is invalid or output path is invalid.
        """
        if not output_file.endswith('.wav'):
            output_file += '.wav'
        
        # Generate audio data
        audio = []
        for number in numbers:
            try:
                midi_note = Converter.number_to_midi(number)
                # Calculate frequency (MIDI note to frequency conversion)
                frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
                t = np.linspace(0, note_duration, int(sample_rate * note_duration), False)
                note = np.sin(2 * np.pi * frequency * t) * amplitude
                audio.extend(note)
            except ValueError as e:
                print(f"Error: {e}")
                continue
        
        # Convert to 16-bit PCM
        audio_array = np.array(audio) * 32767
        audio_array = np.clip(audio_array, -32768, 32767).astype(np.int16)
        
        # Save WAV file
        try:
            with wave.open(output_file, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_array.tobytes())
            print(f"Saved WAV file: {output_file}")
        except Exception as e:
            raise IOError(f"Failed to save WAV file: {e}")

    @staticmethod
    def midi_to_wav(
        midi_file_path: str,
        output_file: str,
        note_duration: float = 0.5,
        sample_rate: int = 44100,
        amplitude: float = 0.5
    ) -> None:
        """Convert a MIDI file to a WAV file.
        
        Args:
            midi_file_path: Path to the MIDI file.
            output_file: Path to save the WAV file.
            note_duration: Duration of each note in seconds.
            sample_rate: Audio sample rate in Hz.
            amplitude: Amplitude of the sine wave (0 to 1).
        """
        numbers = Converter.midi_file_to_numbers(midi_file_path)
        Converter.numbers_to_wav(numbers, output_file, note_duration, sample_rate, amplitude)