import asyncio
import platform
import pygame
import time
import numpy as np
import os
import sys
import note_seq
from note_seq.protobuf import music_pb2
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from com import initialize_serial, read_serial, close_serial
from converter import Converter
from music_extender import extend_midi

# Get resource path, compatible with PyInstaller packaging
def resource_path(relative_path):
    """Return the absolute path to a resource, handling PyInstaller's temporary folder."""
    if hasattr(sys, '_MEIPASS'):
        # Resources are in PyInstaller's temporary folder during execution
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Define directories using resource paths for PyInstaller compatibility
media_dir = resource_path('media')  # Directory for storing MIDI files
model_dir = resource_path('model')  # Directory for Magenta model files
os.makedirs(media_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# Model bundle mapping with resource paths
MODEL_BUNDLES = {
    'basic_rnn': os.path.join(model_dir, 'basic_rnn.mag'),
    'mono_rnn': os.path.join(model_dir, 'mono_rnn.mag'),
    'lookback_rnn': os.path.join(model_dir, 'lookback_rnn.mag'),
    'attention_rnn': os.path.join(model_dir, 'attention_rnn.mag')
}

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Euphony Studio")
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Set window icon
try:
    icon = pygame.image.load(resource_path('res/logo.png'))
    pygame.display.set_icon(icon)
except pygame.error:
    print("Failed to load logo.png for window icon")

def initialize_pygame():
    """Initialize Pygame mixer with increased channels for polyphony."""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)
        pygame.mixer.set_num_channels(16)  # Increase to 16 channels for polyphony
        return True, "Pygame mixer initialized successfully"
    except Exception as e:
        return False, f"Pygame mixer initialization failed: {e}"

def generate_tone(frequency, duration=1.0, sample_rate=22050):
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    audio = (tone * 32767).astype(np.int16)
    return audio

def play_tone(frequency):
    """Play a tone for the given frequency."""
    if frequency is None:
        return
    try:
        tone_data = generate_tone(frequency, duration=1.0)
        sound = pygame.mixer.Sound(tone_data.tobytes())
        channel = pygame.mixer.find_channel()  # Find an available channel
        if channel:
            channel.play(sound)
    except Exception as e:
        print(f"Playback error: {e}")

def play_piano_key(number):
    """Play MP3 file for piano key number on an available channel."""
    if number is None or not (1 <= number <= 88):
        return
    mp3_file = resource_path(f"res/raw/p{number:02d}.mp3")
    try:
        sound = pygame.mixer.Sound(mp3_file)
        channel = pygame.mixer.find_channel()  # Find an available channel
        if channel:
            channel.play(sound)
        else:
            print(f"No available channel to play: {mp3_file}")
    except Exception as e:
        print(f"Playback error: {e}")

def draw_button(screen, text, x, y, width, height, color, hover_color, font):
    """Draw a button and return its rect."""
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, width, height)
    color = hover_color if rect.collidepoint(mouse_pos) else color
    pygame.draw.rect(screen, color, rect)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return rect

def note_number_to_midi(note_number):
    """Convert piano key number (1-88) to MIDI note number (21-108)."""
    return note_number + 20  # Piano key 1 = MIDI note 21 (A0)

def midi_to_note_numbers(sequence):
    """Convert MIDI notes back to piano key numbers (1-88) for serial output."""
    return [note.pitch - 20 for note in sequence.notes if 21 <= note.pitch <= 108]

async def main():
    """Main GUI function."""
    # Initialize Pygame mixer
    mixer_success, mixer_message = initialize_pygame()
    print(mixer_message)

    # Initialize serial port
    ser = None
    serial_error = None
    settings = {'port': 'COM7', 'baud_rate': 9600, 'sample_rate': 22050}
    try:
        ser = initialize_serial(port=settings['port'], baud_rate=settings['baud_rate'])
        if not ser:
            serial_error = "Cannot open serial port: No devices found or port invalid. Check port in Settings."
    except Exception as e:
        serial_error = f"Cannot open serial port: {e}. Check port in Settings."

    # GUI state
    mode = 'splash'
    splash_start = time.time()
    piano_data = []  # Store multiple active keys
    input_text = ''
    active_field = None
    # AI mode state
    recording = False
    sequence = None
    start_time = 0
    ai_model = 'basic_rnn'  # Default AI model
    model_buttons = {}
    recorded_notes = []
    ai_error = None

    # Initialize button variables to None to avoid UnboundLocalError
    piano_button = None
    practice_button = None
    ai_button = None
    settings_button = None
    back_button = None
    record_button = None
    extend_button = None

    while True:
        screen.fill((255, 255, 255))  # White background
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_serial(ser)
                pygame.mixer.quit()
                pygame.quit()
                print("Pygame mixer closed")
                return

            # Handle clicks in main menu
            elif event.type == pygame.MOUSEBUTTONDOWN and mode == 'menu':
                mouse_pos = event.pos
                if piano_button is not None and piano_button.collidepoint(mouse_pos):
                    mode = 'piano'
                    piano_data = []
                elif practice_button is not None and practice_button.collidepoint(mouse_pos):
                    mode = 'practice'
                    piano_data = []
                elif ai_button is not None and ai_button.collidepoint(mouse_pos):
                    mode = 'ai'
                    recording = False
                    sequence = music_pb2.NoteSequence()
                    sequence.tempos.add(qpm=120)
                    recorded_notes = []
                    piano_data = []
                    ai_error = None
                elif settings_button is not None and settings_button.collidepoint(mouse_pos):
                    mode = 'settings'
                    input_text = ''
                    active_field = None

            # Handle clicks in sub-modes
            elif event.type == pygame.MOUSEBUTTONDOWN and mode in ['piano', 'practice', 'ai', 'settings']:
                if back_button is not None and back_button.collidepoint(event.pos):
                    mode = 'menu'
                    recording = False
                    sequence = None
                    recorded_notes = []
                    ai_error = None

                elif mode == 'ai':
                    mouse_pos = event.pos
                    if record_button is not None and record_button.collidepoint(mouse_pos):
                        if not recording:
                            # Start recording new notes
                            recording = True
                            sequence = music_pb2.NoteSequence()
                            sequence.tempos.add(qpm=120)
                            recorded_notes = []
                            start_time = time.time()
                            print("Started recording")
                            ai_error = None
                        else:
                            # Stop recording and process
                            recording = False
                            if not sequence.notes:
                                ai_error = "No notes recorded. No MIDI file saved."
                                print(ai_error)
                            else:
                                # Save recording
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                input_midi_path = os.path.join(media_dir, f"recording_{timestamp}.mid")
                                note_seq.sequence_proto_to_midi_file(sequence, input_midi_path)
                                print(f"Saved recording to {input_midi_path}")

                                # Verify content
                                try:
                                    saved_sequence = note_seq.midi_file_to_note_sequence(input_midi_path)
                                    if not saved_sequence.notes:
                                        os.remove(input_midi_path)
                                        ai_error = "Empty MIDI file deleted."
                                    else:
                                        # Extend MIDI
                                        output_midi_path = os.path.join(media_dir, f"extended_{timestamp}.mid")
                                        bundle_path = MODEL_BUNDLES.get(ai_model, MODEL_BUNDLES['basic_rnn'])
                                        success = extend_midi(
                                            input_midi_path=input_midi_path,
                                            output_midi_path=output_midi_path,
                                            num_steps=128,
                                            temperature=1.0,
                                            bundle_path=bundle_path,
                                            config=ai_model
                                        )
                                        if success:
                                            print(f"Extended MIDI saved: {output_midi_path}")
                                        else:
                                            ai_error = "MIDI extension failed."
                                except Exception as e:
                                    ai_error = f"Error verifying MIDI: {e}"
                                    print(ai_error)

                    elif extend_button is not None and extend_button.collidepoint(mouse_pos):
                        # Extend an existing MIDI file chosen by user
                        try:
                            root = tk.Tk()
                            root.withdraw()
                            midi_path = filedialog.askopenfilename(
                                title="Select MIDI File",
                                filetypes=[("MIDI files", "*.mid")]
                            )
                            if midi_path:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                output_midi_path = os.path.join(media_dir, f"extended_{timestamp}.mid")
                                bundle_path = MODEL_BUNDLES.get(ai_model, MODEL_BUNDLES['basic_rnn'])
                                success = extend_midi(
                                    input_midi_path=midi_path,
                                    output_midi_path=output_midi_path,
                                    num_steps=128,
                                    temperature=1.0,
                                    bundle_path=bundle_path,
                                    config=ai_model
                                )
                                if success:
                                    print(f"Extended MIDI saved: {output_midi_path}")
                                else:
                                    ai_error = "Failed to extend selected MIDI."
                        except Exception as e:
                            ai_error = f"Error extending MIDI: {e}"

                    # Change AI model selection
                    for model, button in model_buttons.items():
                        if button is not None and button.collidepoint(mouse_pos):
                            ai_model = model
                            print(f"Selected AI model: {ai_model}")

            # Handle keyboard in settings
            elif event.type == pygame.KEYDOWN and mode == 'settings' and active_field:
                if event.key == pygame.K_RETURN:
                    active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        # Splash screen
        if mode == 'splash':
            try:
                banner = pygame.image.load(resource_path('res/Banner.png'))
                banner_rect = banner.get_rect(center=(400, 300))
            except pygame.error:
                banner = pygame.Surface((310, 110))
                banner.fill((0, 0, 0))
                text = font.render("Euphony Studio", True, (255, 255, 255))
                banner.blit(text, text.get_rect(center=(155, 55)))
                banner_rect = banner.get_rect(center=(400, 300))
            screen.blit(banner, banner_rect)
            if time.time() - splash_start > 3:
                mode = 'menu'

        # Menu mode
        elif mode == 'menu':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            piano_button = draw_button(screen, "Piano Mode", 300, 100, 200, 50,
                                       (0, 120, 200), (100, 180, 255), font)
            practice_button = draw_button(screen, "Practice Mode", 300, 200, 200, 50,
                                          (0, 120, 200), (100, 180, 255), font)
            ai_button = draw_button(screen, "AI Composition", 300, 300, 200, 50,
                                    (0, 120, 200), (100, 180, 255), font)
            settings_button = draw_button(screen, "Settings", 300, 400, 200, 50,
                                          (0, 120, 200), (100, 180, 255), font)

        # Piano mode
        elif mode == 'piano':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            else:
                if ser and ser.in_waiting > 0:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        key_numbers = [int(num) for num in data.split(',') if num.strip().isdigit()]
                        print(f"Received numbers: {key_numbers}")
                        piano_data = key_numbers
                        for number in key_numbers:
                            if 1 <= number <= 88:
                                play_piano_key(number)
                            else:
                                print(f"Invalid number: {number}")
                    except ValueError:
                        print(f"Invalid data: {data}")
                    except Exception as e:
                        print(f"Playback error: {e}")
            text = font.render(f"Last Input: {', '.join(map(str, piano_data)) if piano_data else 'None'}", True, (0, 0, 0))
            screen.blit(text, (10, 50 if serial_error else 10))
            back_button = draw_button(screen, "Back", 10, 550, 100, 40, (200, 0, 0), (255, 100, 100), font)

        # Practice mode
        elif mode == 'practice':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            else:
                if ser and ser.in_waiting > 0:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        key_numbers = [int(num) for num in data.split(',') if num.strip().isdigit()]
                        print(f"Received numbers: {key_numbers}")
                        piano_data = key_numbers
                        for number in key_numbers:
                            if 1 <= number <= 88:
                                play_piano_key(number)
                            else:
                                print(f"Invalid number: {number}")
                    except ValueError:
                        print(f"Invalid data: {data}")
                    except Exception as e:
                        print(f"Playback error: {e}")
            for i in range(12):
                x = 200 + i * 40
                color = (255, 255, 255) if (i + 1) not in piano_data else (255, 255, 0)
                pygame.draw.rect(screen, color, (x, 300, 38, 100))
            text = font.render(f"Keys: {', '.join(map(str, piano_data)) if piano_data else 'None'}", True, (0, 0, 0))
            screen.blit(text, (10, 50 if serial_error else 10))
            back_button = draw_button(screen, "Back", 10, 550, 100, 40, (200, 0, 0), (255, 100, 100), font)

        # AI Composition mode
        elif mode == 'ai':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            if ai_error:
                error_text = small_font.render(ai_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 50 if serial_error else 10))

            # Draw model selection
            model_options = ["basic_rnn", "mono_rnn", "lookback_rnn", "attention_rnn"]
            for i, model in enumerate(model_options):
                model_buttons[model] = draw_button(
                    screen, model, 200, 100 + i * 60, 200, 50,
                    (0, 120, 200) if model != ai_model else (0, 200, 0),
                    (100, 180, 255) if model != ai_model else (100, 255, 100), font
                )

            # Recording button
            record_button = draw_button(
                screen, "Stop Recording" if recording else "Start Recording",
                200, 400, 200, 50, (200, 0, 0) if recording else (0, 120, 200),
                (255, 100, 100) if recording else (100, 180, 255), font
            )

            # New button: extend an existing MIDI file
            extend_button = draw_button(
                screen, "Extend Existing MIDI",
                450, 400, 250, 50, (0, 120, 200), (100, 180, 255), font
            )

            back_button = draw_button(screen, "Back", 10, 550, 100, 40,
                                      (200, 0, 0), (255, 100, 100), font)

        # Settings mode
        elif mode == 'settings':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            port_button = draw_button(screen, f"Port: {settings['port']}", 200, 100, 400, 50,
                                      (0, 120, 200), (100, 180, 255), font)
            baud_button = draw_button(screen, f"Baud Rate: {settings['baud_rate']}", 200, 200, 400, 50,
                                      (0, 120, 200), (100, 180, 255), font)
            sample_button = draw_button(screen, f"Sample Rate: {settings['sample_rate']}", 200, 300, 400, 50,
                                        (0, 120, 200), (100, 180, 255), font)
            if active_field:
                input_surface = font.render(f"Enter {active_field}: {input_text}", True, (0, 0, 0))
                screen.blit(input_surface, (200, 400))
            save_button = draw_button(screen, "Save", 200, 500, 100, 40,
                                      (0, 200, 0), (100, 255, 100), font)
            back_button = draw_button(screen, "Back", 10, 550, 100, 40,
                                      (200, 0, 0), (255, 100, 100), font)

        pygame.display.flip()
        await asyncio.sleep(1.0 / 60)  # Control frame rate

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())