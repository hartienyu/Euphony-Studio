import os
import warnings
from magenta.models.shared import sequence_generator_bundle
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from note_seq.protobuf import generator_pb2
import tensorflow.compat.v1 as tf
import note_seq

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow INFO logs

tf.disable_v2_behavior()

def extend_midi(
    input_midi_path="media/input.mid",
    output_midi_path="media/output.mid",
    num_steps=128,
    temperature=1.0,
    bundle_path="model/basic_rnn.mag",
    config="basic_rnn"
):
    """
    Extend an input MIDI file using Magenta's MelodyRNN model.

    Args:
        input_midi_path (str): Path to input MIDI file (default: 'media/input.mid')
        output_midi_path (str): Path to output extended MIDI file (default: 'media/output.mid')
        num_steps (int): Number of steps to generate (controls extension length)
        temperature (float): Randomness of generation (0.1 to 2.0)
        bundle_path (str): Path to the .mag model file (default: 'model/basic_rnn.mag')
        config (str): Model config ('basic_rnn', 'mono_rnn', 'lookback_rnn', 'attention_rnn')

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Starting MIDI extension with config: {config}")
    print(f"Input MIDI: {input_midi_path}")
    print(f"Bundle path: {bundle_path}")

    try:
        # Validate inputs
        valid_configs = ["basic_rnn", "mono_rnn", "lookback_rnn", "attention_rnn"]
        if config not in valid_configs:
            raise ValueError(f"Invalid config: {config}. Must be one of {valid_configs}")
        input_midi_path = os.path.abspath(input_midi_path)
        bundle_path = os.path.abspath(bundle_path)
        if not os.path.exists(input_midi_path):
            raise FileNotFoundError(f"Input MIDI file not found at {input_midi_path}")
        if not os.path.exists(bundle_path):
            raise FileNotFoundError(f"Bundle file not found at {bundle_path}. Download from https://github.com/magenta/magenta/tree/main/magenta/models/melody_rnn")
        print("File paths verified")

        # Load model
        print("Loading model bundle...")
        from magenta.models.shared import sequence_generator_bundle
        bundle = sequence_generator_bundle.read_bundle_file(bundle_path)

        generator_map = melody_rnn_sequence_generator.get_generator_map()
        generator = generator_map[config](checkpoint=None, bundle=bundle)
        generator.initialize()
        print("Model initialized")

        # Load MIDI
        print("Loading input MIDI...")
        input_sequence = note_seq.midi_file_to_note_sequence(input_midi_path)
        print("MIDI loaded")

        # Generate sequence
        print("Generating sequence...")
        last_end_time = max(n.end_time for n in input_sequence.notes) if input_sequence.notes else 0
        qpm = input_sequence.tempos[0].qpm if input_sequence.tempos else 120
        seconds_per_step = 60.0 / qpm / generator.steps_per_quarter
        generation_length_seconds = num_steps * seconds_per_step
        generation_start_time = last_end_time

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = temperature
        generator_options.generate_sections.add(
            start_time=generation_start_time,
            end_time=generation_start_time + generation_length_seconds
        )

        generated_sequence = generator.generate(input_sequence, generator_options)
        print("Sequence generated")

        # Save output
        os.makedirs(os.path.dirname(output_midi_path), exist_ok=True)
        note_seq.sequence_proto_to_midi_file(generated_sequence, output_midi_path)
        print(f"Generated extended MIDI file at: {output_midi_path}")
        return True

    except Exception as e:
        print(f"Error during MIDI extension: {str(e)}")
        return False