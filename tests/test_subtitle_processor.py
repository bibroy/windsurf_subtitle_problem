import pytest
from pathlib import Path
import tempfile
from src.core.subtitle_processor import SubtitleProcessor

@pytest.fixture
def subtitle_processor():
    """Create a SubtitleProcessor instance for testing."""
    return SubtitleProcessor()

@pytest.fixture
def sample_vtt_content():
    """Create a sample VTT file content."""
    return """WEBVTT

1
00:00:01.000 --> 00:00:04.000
This is a test subtitle
with multiple lines

2
00:00:05.000 --> 00:00:08.000
Another test subtitle"""

def test_clean_text(subtitle_processor):
    """Test text cleaning functionality."""
    # Test removing invalid characters
    text = "Hello\u0000World"
    cleaned = subtitle_processor._clean_text(text)
    assert cleaned == "HelloWorld"
    
    # Test removing extra lines
    text = "Line 1\n\n\nLine 2"
    cleaned = subtitle_processor._clean_text(text)
    assert cleaned == "Line 1\nLine 2"

def test_fix_grammar(subtitle_processor):
    """Test grammar correction functionality."""
    # Test basic grammar correction
    text = "They is going home"
    corrected = subtitle_processor._fix_grammar(text)
    assert corrected == "They are going home"

def test_optimize_position(subtitle_processor):
    """Test subtitle positioning functionality."""
    # Test default positioning
    position = subtitle_processor._optimize_position("Test subtitle")
    assert position == {'x': 50, 'y': 90}

def test_process_subtitle_file(subtitle_processor, sample_vtt_content):
    """Test complete subtitle processing workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create input file
        input_path = Path(temp_dir) / "input.vtt"
        with open(input_path, "w") as f:
            f.write(sample_vtt_content)
        
        # Process subtitle
        output_path = Path(temp_dir) / "output.vtt"
        success = subtitle_processor.process_subtitle_file(str(input_path), str(output_path))
        
        # Verify processing
        assert success
        assert output_path.exists()
        
        # Verify content
        with open(output_path) as f:
            content = f.read()
            assert "WEBVTT" in content
            assert "position:" in content  # Check if positioning was added
