import pytest
import json
from pathlib import Path
import webvtt
from src.core.subtitle_processor import SubtitleProcessor
from src.core.video_processor import VideoProcessor
from src.core.aws_services import AWSServices

@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent.parent / "data"

@pytest.fixture
def video_metadata(test_data_dir):
    """Load video metadata for testing."""
    with open(test_data_dir / "test_videos" / "sample1.json") as f:
        return json.load(f)

@pytest.fixture
def multilingual_metadata(test_data_dir):
    """Load multilingual video metadata for testing."""
    with open(test_data_dir / "test_videos" / "sample2.json") as f:
        return json.load(f)

@pytest.fixture
def sample_subtitle(test_data_dir):
    """Get path to sample subtitle file."""
    return test_data_dir / "test_subtitles" / "sample1.vtt"

def test_subtitle_processing_pipeline(test_data_dir, sample_subtitle):
    """Test the complete subtitle processing pipeline."""
    # Initialize processors
    subtitle_processor = SubtitleProcessor()
    
    # Process subtitle file
    output_path = test_data_dir / "test_subtitles" / "output_test.vtt"
    success = subtitle_processor.process_subtitle_file(str(sample_subtitle), str(output_path))
    
    assert success
    assert output_path.exists()
    
    # Validate output
    subtitles = list(webvtt.read(str(output_path)))
    
    # Check basic structure
    assert len(subtitles) > 0
    for subtitle in subtitles:
        assert subtitle.start
        assert subtitle.end
        assert subtitle.text
        
        # Check text cleaning
        assert "​" not in subtitle.text  # No zero-width space
        assert not any(len(line.strip()) == 0 for line in subtitle.text.split("\n"))  # No empty lines
        
        # Check timing format
        assert ":" in subtitle.start
        assert "." in subtitle.start
        assert ":" in subtitle.end
        assert "." in subtitle.end

def test_video_analysis(video_metadata):
    """Test video analysis functionality."""
    video_processor = VideoProcessor()
    
    # Mock video analysis using metadata
    text_regions = []
    for scene in video_metadata["scenes"]:
        for overlay in scene["text_overlays"]:
            text_regions.append({
                "timestamp": scene["start_time"],
                "regions": [{
                    "text": overlay["text"],
                    "bbox": {
                        "Left": overlay["position"]["x"] / video_metadata["metadata"]["width"],
                        "Top": overlay["position"]["y"] / video_metadata["metadata"]["height"],
                        "Width": 0.2,
                        "Height": 0.1
                    }
                }]
            })
    
    # Get optimal positions
    positions = video_processor.get_optimal_subtitle_positions({"text_regions": text_regions})
    
    # Validate positions
    assert len(positions) > 0
    for position in positions:
        assert "timestamp" in position
        assert "position" in position
        assert 0 <= position["position"]["x"] <= 100
        assert 0 <= position["position"]["y"] <= 100

def test_multilingual_support(multilingual_metadata):
    """Test multilingual subtitle processing."""
    aws_services = AWSServices()
    
    # Test translation
    spanish_text = "Hola y bienvenidos a todos!"
    english_translation = aws_services.translate_text(spanish_text, "es", "en")
    
    assert english_translation
    assert english_translation.lower() != spanish_text.lower()
    
    # Test speech detection
    for scene in multilingual_metadata["scenes"]:
        for segment in scene["speech_segments"]:
            # Verify we can handle multiple languages
            assert "language" in segment
            assert "speaker" in segment
            assert "text" in segment

def test_font_consistency(sample_subtitle, test_data_dir):
    """Test font consistency enforcement."""
    subtitle_processor = SubtitleProcessor()
    output_path = test_data_dir / "test_subtitles" / "font_test.vtt"
    
    # Process subtitle
    success = subtitle_processor.process_subtitle_file(str(sample_subtitle), str(output_path))
    assert success
    
    # Check output
    with open(output_path) as f:
        content = f.read()
        
    # Verify no font tags or only consistent font
    assert 'font face="Arial"' not in content.lower()
    assert 'font face="times new roman"' not in content.lower()

def test_error_handling():
    """Test error handling in processors."""
    subtitle_processor = SubtitleProcessor()
    video_processor = VideoProcessor()
    
    # Test invalid file
    success = subtitle_processor.process_subtitle_file(
        "nonexistent.vtt",
        "output.vtt"
    )
    assert not success
    
    # Test invalid video
    analysis = video_processor.process_video("nonexistent.mp4")
    assert not analysis

if __name__ == "__main__":
    pytest.main([__file__])
