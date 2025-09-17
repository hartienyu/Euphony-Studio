import asyncio
import platform
import pygame
import time
import numpy as np
from com import initialize_serial, read_serial, close_serial
from converter import Converter

# Define directories
media_dir = 'res/raw'  # MP3 files stored here

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Euphony Studio")
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Set window icon
try:
    icon = pygame.image.load('res/logo.png')
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
    mp3_file = f"{media_dir}/p{number:02d}.mp3"
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
            serial_error = "Cannot open serial port: No devices found or port invalid"
    except Exception as e:
        serial_error = f"Cannot open serial port: {e}"

    # GUI state
    mode = 'splash'
    splash_start = time.time()
    piano_data = []  # Changed to a list to store multiple active keys
    input_text = ''
    active_field = None

    while True:
        screen.fill((255, 255, 255))  # White background
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_serial(ser)
                pygame.mixer.quit()
                pygame.quit()
                print("Pygame mixer closed")
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and mode == 'menu':
                mouse_pos = event.pos
                if piano_button.collidepoint(mouse_pos):
                    mode = 'piano'
                    piano_data = []
                elif practice_button.collidepoint(mouse_pos):
                    mode = 'practice'
                    piano_data = []
                elif ai_button.collidepoint(mouse_pos):
                    mode = 'ai'
                elif settings_button.collidepoint(mouse_pos):
                    mode = 'settings'
                    input_text = ''
                    active_field = None
            elif event.type == pygame.MOUSEBUTTONDOWN and mode in ['piano', 'practice', 'ai', 'settings']:
                if back_button.collidepoint(event.pos):
                    mode = 'menu'
                elif mode == 'settings':
                    if port_button.collidepoint(event.pos):
                        active_field = 'port'
                        input_text = settings['port']
                    elif baud_button.collidepoint(event.pos):
                        active_field = 'baud_rate'
                        input_text = str(settings['baud_rate'])
                    elif sample_button.collidepoint(event.pos):
                        active_field = 'sample_rate'
                        input_text = str(settings['sample_rate'])
                    elif save_button.collidepoint(event.pos):
                        try:
                            if active_field == 'port':
                                settings['port'] = input_text
                            elif active_field == 'baud_rate':
                                settings['baud_rate'] = int(input_text)
                            elif active_field == 'sample_rate':
                                settings['sample_rate'] = int(input_text)
                                pygame.mixer.quit()
                                mixer_success, mixer_message = initialize_pygame()
                                print(mixer_message)
                            print(f"Settings updated: {settings}")
                            close_serial(ser)
                            ser = None
                            serial_error = None
                            ser = initialize_serial(settings['port'], settings['baud_rate'])
                            if not ser:
                                serial_error = f"Cannot open serial port {settings['port']}: Port invalid or device not connected"
                        except Exception as e:
                            serial_error = f"Settings error: {e}"
            elif event.type == pygame.KEYDOWN and mode == 'settings' and active_field:
                if event.key == pygame.K_RETURN:
                    active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        if mode == 'splash':
            try:
                banner = pygame.image.load('res/Banner.png')
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
        
        elif mode == 'menu':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            piano_button = draw_button(screen, "Piano Mode", 300, 100, 200, 50, (0, 120, 200), (100, 180, 255), font)
            practice_button = draw_button(screen, "Practice Mode", 300, 200, 200, 50, (0, 120, 200), (100, 180, 255), font)
            ai_button = draw_button(screen, "AI Composition", 300, 300, 200, 50, (0, 120, 200), (100, 180, 255), font)
            settings_button = draw_button(screen, "Settings", 300, 400, 200, 50, (0, 120, 200), (100, 180, 255), font)
        
        elif mode == 'piano':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            else:
                if ser and ser.in_waiting > 0:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        # Assume input is comma-separated numbers (e.g., "1,2,3")
                        key_numbers = [int(num) for num in data.split(',') if num.strip().isdigit()]
                        print(f"Received numbers: {key_numbers}")
                        piano_data = key_numbers  # Store all active keys
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
        
        elif mode == 'practice':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            else:
                if ser and ser.in_waiting > 0:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        # Assume input is comma-separated numbers (e.g., "1,2,3")
                        key_numbers = [int(num) for num in data.split(',') if num.strip().isdigit()]
                        print(f"Received numbers: {key_numbers}")
                        piano_data = key_numbers  # Store all active keys
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
        
        elif mode == 'ai':
            text = font.render("AI Composition Under Development", True, (0, 0, 0))
            screen.blit(text, (10, 10))
            if pygame.mouse.get_pressed()[0]:
                print("AI Composition feature is not yet implemented.")
            back_button = draw_button(screen, "Back", 10, 550, 100, 40, (200, 0, 0), (255, 100, 100), font)
        
        elif mode == 'settings':
            if serial_error:
                error_text = small_font.render(serial_error, True, (255, 0, 0))
                screen.blit(error_text, (10, 10))
            port_button = draw_button(screen, f"Port: {settings['port']}", 200, 100, 400, 50, (0, 120, 200), (100, 180, 255), font)
            baud_button = draw_button(screen, f"Baud Rate: {settings['baud_rate']}", 200, 200, 400, 50, (0, 120, 200), (100, 180, 255), font)
            sample_button = draw_button(screen, f"Sample Rate: {settings['sample_rate']}", 200, 300, 400, 50, (0, 120, 200), (100, 180, 255), font)
            if active_field:
                input_surface = font.render(f"Enter {active_field}: {input_text}", True, (0, 0, 0))
                screen.blit(input_surface, (200, 400))
            save_button = draw_button(screen, "Save", 200, 500, 100, 40, (0, 200, 0), (100, 255, 100), font)
            back_button = draw_button(screen, "Back", 10, 550, 100, 40, (200, 0, 0), (255, 100, 100), font)

        pygame.display.flip()
        await asyncio.sleep(1.0 / 60)  # Control frame rate

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())