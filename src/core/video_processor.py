import cv2
import boto3
import numpy as np
from typing import Dict, List, Tuple
import ffmpeg
import json
from pathlib import Path

class VideoProcessor:
    def __init__(self):
        """Initialize the video processor with AWS Rekognition client."""
        self.rekognition = boto3.client('rekognition')
        self.transcribe = boto3.client('transcribe')

    def process_video(self, video_path: str, subtitle_path: str = None) -> Dict:
        """
        Process video file to extract information for subtitle positioning and timing.
        
        Args:
            video_path (str): Path to input video file
            subtitle_path (str): Optional path to existing subtitle file
            
        Returns:
            Dict: Video analysis results
        """
        try:
            # Extract video metadata
            metadata = self._extract_metadata(video_path)
            
            # Analyze video frames for text regions
            text_regions = self._analyze_text_regions(video_path)
            
            # Generate speech timestamps if no subtitle file
            if not subtitle_path:
                speech_timestamps = self._generate_speech_timestamps(video_path)
            else:
                speech_timestamps = None

            return {
                'metadata': metadata,
                'text_regions': text_regions,
                'speech_timestamps': speech_timestamps
            }
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            return None

    def _extract_metadata(self, video_path: str) -> Dict:
        """
        Extract video metadata using ffmpeg.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            Dict: Video metadata
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            return {
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'duration': float(probe['format']['duration']),
                'fps': eval(video_info['r_frame_rate'])
            }
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
            return None

    def _analyze_text_regions(self, video_path: str) -> List[Dict]:
        """
        Analyze video frames to detect text regions using AWS Rekognition.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            List[Dict]: List of detected text regions with timestamps
        """
        text_regions = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Convert frame to bytes
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                # Detect text in frame using Rekognition
                response = self.rekognition.detect_text(Image={'Bytes': frame_bytes})
                
                if response['TextDetections']:
                    text_regions.append({
                        'timestamp': timestamp,
                        'regions': [
                            {
                                'text': detection['DetectedText'],
                                'confidence': detection['Confidence'],
                                'bbox': detection['Geometry']['BoundingBox']
                            }
                            for detection in response['TextDetections']
                            if detection['Type'] == 'LINE'
                        ]
                    })

        finally:
            cap.release()

        return text_regions

    def _generate_speech_timestamps(self, video_path: str) -> List[Dict]:
        """
        Generate speech timestamps using AWS Transcribe.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            List[Dict]: List of speech segments with timestamps
        """
        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            
            # Upload audio to S3 (assuming S3 bucket is configured)
            # Note: In production, implement S3 upload logic here
            
            # Start transcription job
            job_name = f"transcribe_{Path(video_path).stem}"
            # Note: In production, implement full Transcribe job workflow
            
            return []  # Placeholder for actual timestamps
            
        except Exception as e:
            print(f"Error generating speech timestamps: {str(e)}")
            return None

    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Path to extracted audio file
        """
        audio_path = str(Path(video_path).with_suffix('.wav'))
        
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, overwrite_output=True)
            
            return audio_path
        except Exception as e:
            print(f"Error extracting audio: {str(e)}")
            return None

    def get_optimal_subtitle_positions(self, video_analysis: Dict) -> List[Dict]:
        """
        Calculate optimal subtitle positions based on video analysis.
        
        Args:
            video_analysis (Dict): Video analysis results
            
        Returns:
            List[Dict]: List of optimal positions with timestamps
        """
        positions = []
        
        for region in video_analysis['text_regions']:
            # Find safe areas for subtitles (avoiding text regions)
            safe_areas = self._find_safe_areas(
                region['regions'],
                video_analysis['metadata']['width'],
                video_analysis['metadata']['height']
            )
            
            positions.append({
                'timestamp': region['timestamp'],
                'position': safe_areas[0] if safe_areas else {'x': 50, 'y': 90}  # Default to bottom center
            })
        
        return positions

    def _find_safe_areas(self, text_regions: List[Dict], width: int, height: int) -> List[Dict]:
        """
        Find safe areas for subtitle placement that don't overlap with existing text.
        
        Args:
            text_regions (List[Dict]): List of detected text regions
            width (int): Video width
            height (int): Video height
            
        Returns:
            List[Dict]: List of safe positions
        """
        # Simple implementation: return bottom center if no conflicts
        # In production, implement more sophisticated position calculation
        return [{'x': 50, 'y': 90}]
