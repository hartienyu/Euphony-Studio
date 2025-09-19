<img width="310" height="110" alt="Banner" src="https://github.com/user-attachments/assets/9ffc7ca7-d3bc-402a-8cec-844dfe4ce9e6" />

# Euphony-Studio

Euphony-Studio is an AI-powered soft piano application designed for musicians and developers, offering interactive music creation with expressive control and real-time sound customization. It supports real-time piano playback via Bluetooth (HC-05), provides tools for converting between piano key numbers, MIDI files, and WAV audio, and includes AI-driven music composition using Magenta's `melody_rnn` model. The application features a modular architecture, enabling seamless integration of serial communication, audio playback, file conversion, and AI composition.

## Features

- **Real-Time Piano Playback**: Receives piano key numbers (1–88) or frequency data (20–20,000 Hz) via Bluetooth (HC-05) and plays corresponding MP3 files or generated sine wave tones.
- **MIDI and WAV Conversion**: Converts piano key sequences to MIDI or WAV files and extracts key numbers from MIDI files for playback or further processing.
- **AI Music Composition**: Uses Magenta's `melody_rnn` model to generate and extend musical sequences based on user-recorded piano input, enabling creative music composition.
- **Expressive Control**: Supports dynamic tone generation with customizable frequency, duration, and amplitude for realistic piano sound synthesis.
- **Modular Architecture**: Separates serial communication (`com.py`), audio playback and GUI (`main.py`), file conversion (`converter.py`), and AI composition (`music_extender.py`) for easy maintenance and extensibility.
- **Cross-Platform Potential**: Designed for compatibility across platforms, with low-latency performance for real-time applications.
- **GUI Integration**: Includes a Pygame-based interface for visualizing piano keys, AI model selection, and real-time input feedback.

## Prerequisites

- **Hardware**:
  - HC-05 Bluetooth module configured on a serial port (default: `COM7`, 9600 baud).
  - Audio output device (speakers or headphones).
- **Software**:
  - Python 3.8.10 (tested environment).
  - Required Python packages: see [Dependencies](#dependencies).
  - Magenta 2.1.4 for AI composition (CPU-only, no GPU required).
- **Media Files**:
  - Place MP3 files (`p01.mp3` to `p88.mp3` for piano keys 1–88) in the `res/raw/` folder for key-based playback.
  - Place Magenta model files (e.g., `basic_rnn.mag`, `mono_rnn.mag`, `lookback_rnn.mag`, `attention_rnn.mag`) in the `model/` folder for AI composition.
- **Directories**:
  - The application automatically creates `media/` for MIDI/WAV output and `model/` for Magenta model files.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/hartienyu/Euphony-Studio.git
   cd Euphony-Studio
   ```

2. **Set Up Python Environment**:

   Create a Conda environment (recommended):

   ```bash
   conda create -n euphony_env python=3.8.10
   conda activate euphony_env
   ```

   Or use a virtual environment:

   ```bash
   python -m venv euphony_env
   source euphony_env/bin/activate  # Linux/macOS
   euphony_env\Scripts\activate    # Windows
   ```

3. **Install Dependencies**:

   Install core dependencies:

   ```bash
   conda install pyserial=3.5 pygame=2.6.1 numpy=1.21.6 mido=1.2.6 note_seq=0.0.3 magenta=2.1.4
   ```

   Or with pip:

   ```bash
   pip install pyserial==3.5 pygame==2.6.1 numpy==1.21.6 mido==1.2.6 note_seq==0.0.3 magenta==2.1.4
   ```

   Optional for advanced audio processing:

   ```bash
   pip install pydub==0.25.1
   ```

4. **Download Magenta Models**:
   - Download Magenta `melody_rnn` model bundles (e.g., `basic_rnn.mag`, `mono_rnn.mag`, `lookback_rnn.mag`, `attention_rnn.mag`) from the [Magenta GitHub](https://github.com/magenta/magenta) or official model repository.
   - Place them in the `model/` folder (e.g., `Euphony-Studio/model/`).

5. **Configure Media Folder**:
   - Place MP3 files (`p01.mp3` to `p88.mp3`) in `Euphony-Studio/res/raw/` for key-based playback.
   - Ensure `media/` and `model/` directories are writable for MIDI/WAV output and model loading.

6. **Verify HC-05 Bluetooth**:
   - Ensure the HC-05 module is paired and assigned to a serial port (e.g., `COM7` on Windows, `/dev/ttyS0` on Linux).
   - Check the port using:

   ```bash
   python -m serial.tools.miniterm
   ```

## Build

The build artifacts for **Euphony-Studio** can be found in `Releases`.

### Build Instructions

Euphony-Studio can be built using **PyInstaller** in two ways:

1. **One File** (Compact, slower startup)
   ```bash
   pyinstaller --onefile --add-data "model/*;model" --add-data "res/*;res" --add-data "media;media" --icon=res/logo.ico --hidden-import tensorflow_probability.python --hidden-import tensorflow_probability.python.experimental main.py
   ```

2. **One Directory** (More files, faster startup)
   ```bash
   pyinstaller --onedir --add-data "model/*;model" --add-data "res/*;res" --add-data "media;media" --icon=res/logo.png --hidden-import tensorflow_probability.python --hidden-import tensorflow_probability.python.experimental main.py
   ```

## Usage

1. **Prepare Audio and Model Files**:
   - For key-based playback, place MP3 files in `res/raw/` (e.g., `p01.mp3` for key 1).
   - For AI composition, place Magenta model files in `model/`.
   - For tone generation, no audio files are required.

2. **Run the Application**:
   - Start the GUI and real-time playback via HC-05:

   ```bash
   conda activate euphony_env
   cd Euphony-Studio
   python main.py
   ```

   - For MIDI/WAV conversion (example):

   ```bash
   python -c "from converter import Converter; Converter.numbers_to_midi_file([1, 3, 5], 'media/output.mid')"
   python -c "from converter import Converter; Converter.numbers_to_wav([1, 3, 5], 'media/output.wav')"
   python -c "from converter import Converter; Converter.midi_to_wav('media/input.mid', 'media/output.wav')"
   ```

3. **AI Composition**:
   - Enter AI Composition mode in the GUI.
   - Select a `melody_rnn` model (e.g., `basic_rnn`, `attention_rnn`) and start recording.
   - Play piano keys via HC-05 to record a sequence.
   - Stop recording to generate an extended MIDI file using the selected model.
   - The application saves the recorded and extended MIDI files in `media/` and plays the extended sequence.

4. **Expected Output**:
   - Lists available serial ports and connects to the HC-05.
   - Initializes Pygame mixer at 22,050 Hz.
   - Plays MP3s (for key numbers 1–88) or generates tones (for frequencies 20–20,000 Hz) based on HC-05 input.
   - Saves MIDI/WAV files for conversion tasks and AI-generated sequences.
   - Example log for playback:

   ```bash
   可用串口：
     - COM7: Bluetooth Device
   已连接到 COM7
   Pygame mixer 初始化成功
   已创建媒体文件夹: Euphony-Studio/media
   接收到琴键: 1, 3, 5
   ```

   - Example log for AI composition:

   ```bash
   Started recording
   Saved recording to media/recording_20250919_030123.mid
   Saved extended MIDI to media/extended_20250919_030123.mid
   ```

5. **Stop the Application**:
   - Press `Ctrl+C` or close the GUI to exit, closing the serial port and Pygame mixer.

## File Structure

```
Euphony-Studio/
├── com.py              # Serial communication with HC-05 Bluetooth module
├── main.py             # Audio playback, tone generation, and Pygame GUI
├── converter.py        # MIDI and WAV file conversion for piano keys
├── music_extender.py   # AI composition using Magenta's melody_rnn model
├── media/              # Folder for MIDI/WAV output (auto-created)
├── model/              # Folder for Magenta model files (e.g., *.mag)
├── res/                # Folder for resources
│   ├── logo.png        # Application icon
│   ├── Banner.png      # Splash screen banner
│   ├── raw/            # MP3 files for piano keys (p01.mp3 to p88.mp3)
└── README.md           # Project documentation
```

- **`com.py`**: Manages HC-05 connection and reading of piano key numbers.
- **`main.py`**: Handles Pygame initialization, tone generation, MP3 playback, and GUI for piano, practice, and AI modes.
- **`converter.py`**: Converts between piano key numbers (1–88), MIDI files, and WAV files.
- **`music_extender.py`**: Extends recorded MIDI sequences using Magenta's `melody_rnn` model.
- **`media/`**: Stores generated MIDI/WAV files.
- **`model/`**: Stores Magenta model files for AI composition.
- **`res/`**: Contains MP3 files and images for GUI.

## Audio Conversion

Use `converter.py` for MIDI/WAV processing:
- **Convert Piano Keys to MIDI**:

  ```python
  from converter import Converter
  Converter.numbers_to_midi_file([1, 3, 5, 10], "media/output.mid", note_duration=500, velocity=100, bpm=120)
  ```

- **Convert Piano Keys to WAV**:

  ```python
  from converter import Converter
  Converter.numbers_to_wav([1, 3, 5, 10], "media/output.wav", note_duration=0.5, sample_rate=22050)
  ```

- **Convert MIDI to WAV**:

  ```python
  from converter import Converter
  Converter.midi_to_wav("media/input.mid", "media/output.wav", note_duration=0.5, sample_rate=22050)
  ```

- **Extract Keys from MIDI**:

  ```python
  from converter import Converter
  numbers = Converter.midi_file_to_numbers("media/input.mid")
  print(numbers)
  ```

## AI Composition

Use the GUI or `music_extender.py` for AI-driven music generation:
- **Record and Extend MIDI**:
  - In the GUI, select an AI model (e.g., `basic_rnn`) and click "Start Recording".
  - Play piano keys via HC-05 to record a sequence.
  - Click "Stop Recording" to save the input MIDI and generate an extended MIDI using `melody_rnn`.
- **Programmatic Example**:

  ```python
  from music_extender import extend_midi
  extend_midi(
      input_midi_path="media/recording.mid",
      output_midi_path="media/extended.mid",
      num_steps=128,
      temperature=1.0,
      bundle_path="model/basic_rnn.mag",
      config="basic_rnn"
  )
  ```

## Dependencies

The project has been tested with Python 3.8.10 on Windows. Below are the core dependencies and their tested versions (no GPU required):

| Package       | Version  | Purpose                             |
|---------------|----------|-------------------------------------|
| pyserial      | 3.5      | Serial communication with HC-05     |
| pygame        | 2.6.1    | Audio playback and GUI rendering    |
| numpy         | 1.21.6   | Tone generation and array handling  |
| mido          | 1.2.6    | MIDI file processing                |
| note_seq      | 0.0.3    | MIDI sequence manipulation          |
| magenta       | 2.1.4    | AI composition with melody_rnn      |
| pydub         | 0.25.1   | Optional: WAV file manipulation     |

To install:

```bash
conda install pyserial=3.5 pygame=2.6.1 numpy=1.21.6 mido=1.2.6 note_seq=0.0.3 magenta=2.1.4
pip install pydub==0.25.1
```

Magenta dependencies (automatically installed with `magenta==2.1.4`):
- `tensorflow==2.9.1` (CPU-only)
- `librosa==0.7.2`
- `pretty-midi==0.2.9`
- `protobuf==3.19.6`

Verify installed packages:

```bash
conda list | grep "pyserial\|pygame\|numpy\|mido\|note_seq\|magenta\|pydub"
```

## Troubleshooting

- **ModuleNotFoundError**:
  - Ensure dependencies are installed in the active environment:

  ```bash
  conda install pyserial=3.5 pygame=2.6.1 numpy=1.21.6 mido=1.2.6 note_seq=0.0.3 magenta=2.1.4
  ```

  - Verify environment:

  ```bash
  conda list | grep "pyserial\|pygame\|numpy\|mido\|note_seq\|magenta"
  ```

- **Serial Port Errors**:
  - If `Cannot open serial port`, update `port='COM7'` in `main.py` to match your HC-05 port.
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
  - Verify `res/raw/` contains `p01.mp3` to `p88.mp3`.

- **MIDI/WAV Conversion Errors**:
  - Ensure valid input files and paths in `media/`.
  - Check `mido` backend:

  ```bash
  pip install python-rtmidi==1.1.2
  ```

- **AI Composition Errors**:
  - Ensure Magenta model files (e.g., `basic_rnn.mag`) are in `model/`.
  - Verify `magenta==2.1.4` and `tensorflow==2.9.1` are installed correctly.
  - If `extend_midi` fails, check model compatibility and file paths.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please include:
- Detailed description of changes.
- Tests for new features (e.g., serial data simulation, MIDI/WAV validation, AI model output).
- Updates to this README if necessary.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For issues, feature requests, or questions, please open an issue on the [GitHub repository](https://github.com/<your-username>/Euphony-Studio/issues).
