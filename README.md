# Euphony-Studio

Euphony-Studio is an AI-powered soft piano application designed for musicians and developers, offering interactive music creation with expressive control and real-time sound customization. It supports real-time piano playback via Bluetooth (HC-05) and provides tools for converting between piano key numbers, MIDI files, and WAV audio. The application features a modular architecture, enabling seamless integration of serial communication, audio playback, and file conversion.

## Features

- **Real-Time Piano Playback**: Receives piano key numbers (1–88) or frequency data (20–20,000 Hz) via Bluetooth (HC-05) and plays corresponding MP3 files or generated sine wave tones.
- **MIDI and WAV Conversion**: Converts piano key sequences to MIDI or WAV files and extracts key numbers from MIDI files for playback or further processing.
- **Expressive Control**: Supports dynamic tone generation with customizable frequency, duration, and amplitude for realistic piano sound synthesis.
- **Modular Architecture**: Separates serial communication (`com.py`), audio playback (`main.py`), and file conversion (`converter.py`) for easy maintenance and extensibility.
- **Cross-Platform Potential**: Designed for compatibility across platforms, with low-latency performance for real-time applications.
- **Extensible Design**: Ready for GUI integration (e.g., Pygame or Tkinter) to visualize piano keys or frequencies.

## Prerequisites

- **Hardware**:
  - HC-05 Bluetooth module configured on a serial port (default: `COM7`, 9600 baud).
  - Audio output device (speakers or headphones).
- **Software**:
  - Python 3.8+.
  - Required Python packages: `pyserial`, `pygame`, `numpy`, `mido`.
  - Optional: `pydub` for audio file conversion.
- **Media Files**:
  - Place MP3 files (e.g., `p1.mp3` to `p88.mp3` for piano keys) in the `media` folder for key-based playback (optional for tone generation mode).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/Euphony-Studio.git
   cd Euphony-Studio
   ```

2. **Set Up Python Environment**:
   Create a Conda environment (recommended):
   ```bash
   conda create -n euphony_env python=3.8
   conda activate euphony_env
   ```
   Or use a virtual environment:
   ```bash
   python -m venv euphony_env
   source euphony_env/bin/activate  # Linux/macOS
   euphony_env\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:
   ```bash
   conda install pyserial pygame numpy mido
   ```
   Or with pip:
   ```bash
   pip install pyserial pygame numpy mido
   ```
   Optional for audio processing:
   ```bash
   pip install pydub
   ```

4. **Configure Media Folder**:
   - The application automatically creates a `media` folder in the project directory (`Euphony-Studio/media`).
   - For key-based playback, place MP3 files (`p1.mp3` to `p88.mp3`) in the `media` folder.
   - For tone generation, no audio files are required.

5. **Verify HC-05 Bluetooth**:
   - Ensure the HC-05 module is paired and assigned to a serial port (e.g., `COM7` on Windows, `/dev/ttyS0` on Linux).
   - Check the port using:
     ```bash
     python -m serial.tools.miniterm
     ```

## Usage

1. **Prepare Audio Files (Optional)**:
   - For key-based playback, place MP3 files in `Euphony-Studio/media` (e.g., `p1.mp3` for key 1).
   - For tone generation, no files are needed; frequencies are synthesized dynamically.

2. **Run the Application**:
   - For real-time playback via HC-05:
     ```bash
     conda activate euphony_env
     cd Euphony-Studio
     python main.py
     ```
   - For MIDI/WAV conversion (example):
     ```bash
     python -c "from converter import Converter; Converter.numbers_to_midi_file([1, 3, 5], 'output.mid')"
     python -c "from converter import Converter; Converter.numbers_to_wav([1, 3, 5], 'output.wav')"
     python -c "from converter import Converter; Converter.midi_to_wav('input.mid', 'output.wav')"
     ```

3. **Expected Output**:
   - Lists available serial ports and connects to the HC-05.
   - Initializes Pygame mixer at 22,050 Hz.
   - Plays MP3s (for key numbers 1–88) or generates tones (for frequencies 20–20,000 Hz) based on HC-05 input.
   - Saves MIDI/WAV files for conversion tasks.
   - Example log for playback:
     ```
     可用串口：
      - COM7: Bluetooth Device
     已连接到 COM7
     Pygame mixer 初始化成功
     已创建媒体文件夹: Euphony-Studio/media
     接收到频率: 440.0 Hz
     ```
   - Example log for conversion:
     ```
     Saved MIDI file: output.mid
     Saved WAV file: output.wav
     ```

4. **Stop the Application**:
   - Press `Ctrl+C` to exit, closing the serial port and Pygame mixer.

## File Structure

```
Euphony-Studio/
├── com.py              # Serial communication with HC-05 Bluetooth module
├── main.py             # Audio playback and tone generation (Pygame)
├── converter.py        # MIDI and WAV file conversion for piano keys
├── media/              # Folder for MP3 files (auto-created)
└── README.md           # Project documentation
```

- **`com.py`**: Manages HC-05 connection and reading of key numbers or frequencies.
- **`main.py`**: Handles Pygame initialization, tone generation, and MP3 playback, with GUI extensibility.
- **`converter.py`**: Converts between piano key numbers (1–88), MIDI files, and WAV files.
- **`media/`**: Stores MP3 files for key-based playback (optional for tone generation).

## Audio Conversion

Use `converter.py` for MIDI/WAV processing:
- **Convert Piano Keys to MIDI**:
  ```python
  from converter import Converter
  Converter.numbers_to_midi_file([1, 3, 5, 10], "output.mid", note_duration=500, velocity=100, bpm=120)
  ```
- **Convert Piano Keys to WAV**:
  ```python
  from converter import Converter
  Converter.numbers_to_wav([1, 3, 5, 10], "output.wav", note_duration=0.5, sample_rate=22050)
  ```
- **Convert MIDI to WAV**:
  ```python
  from converter import Converter
  Converter.midi_to_wav("input.mid", "output.wav", note_duration=0.5, sample_rate=22050)
  ```
- **Extract Keys from MIDI**:
  ```python
  from converter import Converter
  numbers = Converter.midi_file_to_numbers("input.mid")
  print(numbers)
  ```

## Troubleshooting

- **ModuleNotFoundError**:
  - Ensure dependencies are installed:
    ```bash
    conda install pyserial pygame numpy mido
    ```
  - Verify environment:
    ```bash
    conda list | grep "pyserial\|pygame\|numpy\|mido"
    ```
- **Serial Port Errors**:
  - If `无法打开串口`, update `port='COM7'` in `main.py` to match your HC-05 port.
  - Run as administrator:
    ```bash
    python main.py
    ```
  - Test HC-05:
    ```bash
    python -m serial.tools.miniterm <port> 9600
    ```
- **Pygame Initialization Failure**:
  - If `frequency=22050` fails, try `44100` in `main.py`:
    ```python
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=4096)
    ```
- **No Audio Output**:
  - Ensure HC-05 sends valid data:
    - Key mode: Integers (1–88, e.g., `1\n`).
    - Frequency mode: Floats (20–20,000 Hz, e.g., `440.0\n`).
  - Verify `media` folder contains `p1.mp3` to `p88.mp3` for key-based playback.
- **MIDI/WAV Conversion Errors**:
  - Ensure valid input files and paths.
  - Check `mido` backend (install `python-rtmidi` for additional MIDI support):
    ```bash
    pip install python-rtmidi
    ```

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please include:
- Detailed description of changes.
- Tests for new features (e.g., serial data simulation, MIDI/WAV validation).
- Updates to this README if necessary.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For issues, feature requests, or questions, please open an issue on the [GitHub repository](https://github.com/<your-username>/Euphony-Studio/issues).
