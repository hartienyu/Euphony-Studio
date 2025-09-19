import mido
import serial
import time
import asyncio

class MidiToLedController:
    """A class to control WS2812B LED strip based on MIDI file input via Arduino serial communication."""
    
    def __init__(self, midi_file, serial_port=None, ser=None, baud_rate=115200, num_leds=142, 
                 min_midi_note=21, max_midi_note=108, play_function=None):
        """
        Initialize the MIDI to LED controller.
        
        Args:
            midi_file (str): Path to the MIDI file.
            serial_port (str): Arduino serial port (e.g., 'COM3').
            ser (serial.Serial): Existing serial connection (optional).
            baud_rate (int): Serial baud rate (default: 115200).
            num_leds (int): Number of LEDs in the strip (default: 142).
            min_midi_note (int): Minimum MIDI note (A0, default: 21).
            max_midi_note (int): Maximum MIDI note (C8, default: 108).
            play_function (callable): Function to call on note_on with piano key (default: None).
        """
        self.midi_file = midi_file
        self.serial_port = serial_port
        self.ser = ser
        self.own_ser = ser is None
        self.baud_rate = baud_rate
        self.num_leds = num_leds
        self.min_midi_note = min_midi_note
        self.max_midi_note = max_midi_note
        self.play_function = play_function

        # Key to LED mapping from func.md (key 1-88 to LED 2-142, excluding 144)
        self.key_to_led_map = {
            1: 2, 2: 4, 3: 6, 4: 8, 5: 10, 6: 12, 7: 14, 8: 16, 9: 17, 10: 19,
            11: 21, 12: 23, 13: 25, 14: 27, 15: 29, 16: 31, 17: 33, 18: 35, 19: 37, 20: 38,
            21: 40, 22: 42, 23: 44, 24: 46, 25: 48, 26: 50, 27: 52, 28: 54, 29: 56, 30: 58,
            31: 60, 32: 61, 33: 63, 34: 65, 35: 67, 36: 69, 37: 71, 38: 73, 39: 75, 40: 77,
            41: 79, 42: 81, 43: 83, 44: 84, 45: 86, 46: 88, 47: 90, 48: 92, 49: 94, 50: 96,
            51: 98, 52: 100, 53: 102, 54: 104, 55: 106, 56: 108, 57: 109, 58: 111, 59: 113, 60: 115,
            61: 117, 62: 119, 63: 121, 64: 123, 65: 125, 66: 127, 67: 129, 68: 131, 69: 132, 70: 134,
            71: 136, 72: 140, 73: 142  # Exclude 74: 144 as it exceeds 142 LEDs
        }
        
        # State tracking
        self.note_active = {i: [] for i in range(1, 89)}  # List of (start_time, duration) for each piano key
        self.led_states = [False] * self.num_leds        # Current state of each LED: False = off

    def midi_to_piano_key(self, midi_note):
        """Map MIDI note to piano key (1-88). Returns None if out of range."""
        if self.min_midi_note <= midi_note <= self.max_midi_note:
            return midi_note - self.min_midi_note + 1
        return None

    def piano_key_to_led(self, key):
        """Map piano key (1-88) to LED index (0-141). Returns None if invalid."""
        if key in self.key_to_led_map:
            led = self.key_to_led_map[key] - 2  # Map LED numbers (2-142) to 0-141
            if led < self.num_leds:
                return led
        return None

    async def update_led(self, led_index, current_time):
        """Update LED state based on active notes."""
        if led_index is None:
            return
        keys_for_led = [k for k, v in self.key_to_led_map.items() if v - 2 == led_index and v - 2 < self.num_leds]
        new_state = False
        for key in keys_for_led:
            self.note_active[key] = [(t, d) for t, d in self.note_active[key] if current_time < t + d]
            if self.note_active[key]:
                new_state = True
        
        if new_state != self.led_states[led_index]:
            self.led_states[led_index] = new_state
            command = f"{'ON' if new_state else 'OFF'} {led_index}\n"
            self.ser.write(command.encode())
            await asyncio.sleep(0.01)  # Small delay to prevent serial buffer overflow
            print(f"Sent: {command.strip()} at time {current_time:.3f}s")

    def initialize_serial(self):
        """Initialize serial connection to Arduino if not provided."""
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.serial_port, self.baud_rate)
                self.own_ser = True
                print(f"Connected to {self.serial_port}")
                time.sleep(2)  # Wait for Arduino to reset
            except serial.SerialException as e:
                print(f"Failed to connect to {self.serial_port}: {e}")
                raise

    def parse_midi_durations(self):
        """Parse MIDI file to collect note durations."""
        try:
            mid = mido.MidiFile(self.midi_file)
        except Exception as e:
            print(f"Failed to load MIDI file: {e}")
            raise
        
        note_starts = {}
        note_durations = {}
        current_time = 0

        print("Scanning MIDI file for note durations...")
        for msg in mid:
            current_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                key = self.midi_to_piano_key(msg.note)
                if key:
                    note_starts[key] = current_time
                    print(f"Note on: MIDI {msg.note}, Key {key}, Time {current_time:.3f}s")
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = self.midi_to_piano_key(msg.note)
                if key and key in note_starts:
                    duration = current_time - note_starts[key]
                    note_durations[key] = duration
                    print(f"Note off: MIDI {msg.note}, Key {key}, Duration {duration:.3f}s")
                    del note_starts[key]
        
        return note_durations

    async def play_midi(self):
        """Process MIDI file in real-time and control LEDs asynchronously."""
        if self.ser is None:
            self.initialize_serial()
        
        note_durations = self.parse_midi_durations()
        
        print("Playing MIDI file and controlling LEDs...")
        current_time = 0.0
        try:
            mid = mido.MidiFile(self.midi_file)
            for msg in mid:
                await asyncio.sleep(msg.time)
                current_time += msg.time
                if msg.type in ['note_on', 'note_off']:
                    key = self.midi_to_piano_key(msg.note)
                    if key is None:
                        continue
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        duration = note_durations.get(key, 0.1)  # Default 0.1s if not found
                        self.note_active[key].append((current_time, duration))
                        print(f"Active: Key {key}, LED {self.piano_key_to_led(key)}, Start {current_time:.3f}s, Duration {duration:.3f}s")
                        if self.play_function:
                            self.play_function(key)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self.note_active[key] = [(t, d) for t, d in self.note_active[key] if current_time < t + d]
                    
                    led_index = self.piano_key_to_led(key)
                    await self.update_led(led_index, current_time)
            
            # Wait for remaining notes to finish
            max_duration = max(note_durations.values(), default=0)
            end_time = current_time + max_duration
            print(f"Waiting for remaining notes, max duration: {max_duration:.3f}s")
            while current_time < end_time:
                await asyncio.sleep(0.05)
                current_time += 0.05
                for led_index in range(self.num_leds):
                    await self.update_led(led_index, current_time)
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Turn off all LEDs and close serial connection if owned."""
        if self.ser and self.ser.is_open:
            print("Turning off all LEDs...")
            for i in range(self.num_leds):
                if self.led_states[i]:
                    command = f"OFF {i}\n"
                    self.ser.write(command.encode())
                    await asyncio.sleep(0.01)
                    print(f"Sent: {command.strip()}")
            if self.own_ser:
                self.ser.close()
                self.ser = None

if __name__ == "__main__":
    # Example usage
    controller = MidiToLedController(
        midi_file='input1.mid',
        serial_port='COM3',
        baud_rate=115200,
        num_leds=142,
        min_midi_note=21,
        max_midi_note=108
    )
    try:
        asyncio.run(controller.play_midi())
    except Exception as e:
        print(f"Error during execution: {e}")
        asyncio.run(controller.cleanup())