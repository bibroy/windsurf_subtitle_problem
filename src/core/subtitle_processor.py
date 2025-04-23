import webvtt
import boto3
import language_tool_python
from typing import List, Dict, Optional
import json
import os
from pathlib import Path

class SubtitleProcessor:
    def __init__(self):
        """Initialize the subtitle processor with necessary AWS clients and language tool."""
        self.transcribe = boto3.client('transcribe')
        self.translate = boto3.client('translate')
        self.rekognition = boto3.client('rekognition')
        self.language_tool = language_tool_python.LanguageTool('en-US')

    def process_subtitle_file(self, input_path: str, output_path: str) -> bool:
        """
        Process a VTT subtitle file and generate enhanced output.
        
        Args:
            input_path (str): Path to input VTT file
            output_path (str): Path to save enhanced VTT file
            
        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            # Read VTT file
            subtitles = webvtt.read(input_path)
            enhanced_subtitles = []

            for caption in subtitles:
                # Clean and enhance each caption
                enhanced_caption = self._enhance_caption(caption)
                enhanced_subtitles.append(enhanced_caption)

            # Write enhanced subtitles
            self._write_enhanced_subtitles(enhanced_subtitles, output_path)
            return True
        except Exception as e:
            print(f"Error processing subtitle file: {str(e)}")
            return False

    def _enhance_caption(self, caption) -> Dict:
        """
        Enhance a single caption by applying various improvements.
        
        Args:
            caption: WebVTT caption object
            
        Returns:
            Dict: Enhanced caption data
        """
        # Clean text
        text = self._clean_text(caption.text)
        
        # Fix grammar and spelling
        text = self._fix_grammar(text)
        
        # Optimize positioning
        position = self._optimize_position(text)
        
        return {
            'start': caption.start,
            'end': caption.end,
            'text': text,
            'position': position
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing invalid characters and extra lines.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        # Remove invalid characters
        text = ''.join(char for char in text if ord(char) < 65535)
        
        # Remove extra lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def _fix_grammar(self, text: str) -> str:
        """
        Fix grammar and spelling issues in the text.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Corrected text
        """
        matches = self.language_tool.check(text)
        return language_tool_python.utils.correct(text, matches)

    def _optimize_position(self, text: str) -> Dict[str, int]:
        """
        Calculate optimal position for subtitle text.
        
        Args:
            text (str): Subtitle text
            
        Returns:
            Dict[str, int]: Position coordinates
        """
        # Default position (bottom center)
        return {'x': 50, 'y': 90}

    def _write_enhanced_subtitles(self, subtitles: List[Dict], output_path: str):
        """
        Write enhanced subtitles to VTT file.
        
        Args:
            subtitles (List[Dict]): List of enhanced subtitles
            output_path (str): Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n\n')
            
            for i, subtitle in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{subtitle['start']} --> {subtitle['end']}")
                f.write(f" position:{subtitle['position']['x']}%,{subtitle['position']['y']}%\n")
                f.write(f"{subtitle['text']}\n\n")
