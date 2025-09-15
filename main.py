import pygame
import numpy as np
import os
import time
from com import initialize_serial, read_serial, close_serial
from converter import Converter     #Converter class, 允许wav、midi文件与数字之间的转换

# Define the media directory (relative to this script, for potential future use)
media_dir = os.path.join(os.path.dirname(__file__), 'media')

def initialize_pygame():
    """Initialize Pygame mixer."""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)
        print("Pygame mixer 初始化成功")
        return True
    except Exception as e:
        print(f"Pygame mixer 初始化失败: {e}")
        return False

def generate_tone(frequency, duration=1.0, sample_rate=22050):
    """Generate a sine wave tone with specified frequency and duration."""
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
        sound.play()
        time.sleep(1.0)  # Wait for the sound to finish
    except Exception as e:
        print(f"播放错误: {e}")

def main():
    """Main function to integrate serial communication and tone playback."""
    # Ensure media directory exists (for potential future use)
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
        print(f"已创建媒体文件夹: {media_dir}")

    # Initialize Pygame
    if not initialize_pygame():
        return

    # Initialize serial port
    ser = initialize_serial(port='COM7', baud_rate=9600)
    if not ser:
        pygame.mixer.quit()
        return

    try:
        while True:
            # Read serial data
            frequency = read_serial(ser)
            # Play corresponding tone
            play_tone(frequency)
    except KeyboardInterrupt:
        print("程序中断")
    except Exception as e:
        print(f"运行时错误: {e}")
    finally:
        close_serial(ser)
        pygame.mixer.quit()
        print("Pygame mixer 已退出")

if __name__ == "__main__":
    main()