import boto3
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import os

class AWSServices:
    def __init__(self):
        """Initialize AWS service clients."""
        self.transcribe = boto3.client('transcribe')
        self.translate = boto3.client('translate')
        self.rekognition = boto3.client('rekognition')
        self.s3 = boto3.client('s3')
        
        # Configure S3 bucket (should be set via environment variable in production)
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'subtitle-processor-bucket')

    def transcribe_audio(self, audio_path: str, language_code: str = 'en-US') -> Dict:
        """
        Transcribe audio using Amazon Transcribe.
        
        Args:
            audio_path (str): Path to audio file
            language_code (str): Language code for transcription
            
        Returns:
            Dict: Transcription results
        """
        try:
            # Upload audio to S3
            file_name = Path(audio_path).name
            s3_path = f"audio/{file_name}"
            self.s3.upload_file(audio_path, self.bucket_name, s3_path)
            
            # Start transcription job
            job_name = f"transcribe_{int(time.time())}"
            self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f"s3://{self.bucket_name}/{s3_path}"},
                MediaFormat='wav',
                LanguageCode=language_code,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 10
                }
            )
            
            # Wait for completion
            while True:
                status = self.transcribe.get_transcription_job(TranscriptionJobName=job_name)
                if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break
                time.sleep(5)
            
            if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                return self._process_transcription_results(status['TranscriptionJob'])
            else:
                raise Exception("Transcription job failed")
                
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return None
        finally:
            # Cleanup S3
            try:
                self.s3.delete_object(Bucket=self.bucket_name, Key=s3_path)
            except:
                pass

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Amazon Translate.
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        try:
            response = self.translate.translate_text(
                Text=text,
                SourceLanguageCode=source_lang,
                TargetLanguageCode=target_lang
            )
            return response['TranslatedText']
        except Exception as e:
            print(f"Error in translation: {str(e)}")
            return None

    def detect_text_in_image(self, image_bytes: bytes) -> List[Dict]:
        """
        Detect text in image using Amazon Rekognition.
        
        Args:
            image_bytes (bytes): Image data
            
        Returns:
            List[Dict]: Detected text regions
        """
        try:
            response = self.rekognition.detect_text(
                Image={'Bytes': image_bytes}
            )
            
            return [
                {
                    'text': detection['DetectedText'],
                    'confidence': detection['Confidence'],
                    'bbox': detection['Geometry']['BoundingBox']
                }
                for detection in response['TextDetections']
                if detection['Type'] == 'LINE'
            ]
        except Exception as e:
            print(f"Error in text detection: {str(e)}")
            return None

    def _process_transcription_results(self, job: Dict) -> Dict:
        """
        Process transcription job results.
        
        Args:
            job (Dict): Transcription job data
            
        Returns:
            Dict: Processed transcription results
        """
        try:
            # Get transcription results
            import requests
            response = requests.get(job['Transcript']['TranscriptFileUri'])
            transcript = response.json()
            
            # Extract items with timestamps
            items = transcript['results']['items']
            
            # Process speaker labels if available
            speakers = {}
            if 'speaker_labels' in transcript['results']:
                for segment in transcript['results']['speaker_labels']['segments']:
                    speaker_id = segment['speaker_label']
                    for item in segment['items']:
                        speakers[item['start_time']] = speaker_id
            
            # Combine results
            segments = []
            current_segment = {
                'start_time': None,
                'end_time': None,
                'speaker': None,
                'text': []
            }
            
            for item in items:
                if item['type'] == 'pronunciation':
                    if current_segment['start_time'] is None:
                        current_segment['start_time'] = float(item['start_time'])
                        if item['start_time'] in speakers:
                            current_segment['speaker'] = speakers[item['start_time']]
                    
                    current_segment['end_time'] = float(item['end_time'])
                    current_segment['text'].append(item['alternatives'][0]['content'])
                
                elif item['type'] == 'punctuation':
                    current_segment['text'][-1] += item['alternatives'][0]['content']
                    
                    # End segment on sentence-ending punctuation
                    if item['alternatives'][0]['content'] in ['.', '!', '?']:
                        current_segment['text'] = ' '.join(current_segment['text'])
                        segments.append(current_segment)
                        current_segment = {
                            'start_time': None,
                            'end_time': None,
                            'speaker': None,
                            'text': []
                        }
            
            # Add last segment if not empty
            if current_segment['text']:
                current_segment['text'] = ' '.join(current_segment['text'])
                segments.append(current_segment)
            
            return {
                'segments': segments,
                'language_code': transcript['results']['language_code'],
                'duration': float(job['MediaFormat']['DurationInSeconds'])
            }
            
        except Exception as e:
            print(f"Error processing transcription results: {str(e)}")
            return None
