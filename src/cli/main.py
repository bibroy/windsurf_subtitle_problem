import click
import os
from pathlib import Path
from ..core.subtitle_processor import SubtitleProcessor
from ..core.video_processor import VideoProcessor
from typing import Optional

@click.group()
def cli():
    """Subtitle Enhancement System CLI"""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--video', '-v', type=click.Path(exists=True), help='Associated video file for positioning')
def process_subtitle(input_file: str, output: Optional[str], video: Optional[str]):
    """Process a subtitle file for enhancement."""
    try:
        # Create processors
        subtitle_processor = SubtitleProcessor()
        video_processor = None if not video else VideoProcessor()
        
        # Determine output path
        if not output:
            input_path = Path(input_file)
            output = str(input_path.parent / f"{input_path.stem}_enhanced{input_path.suffix}")
        
        click.echo(f"Processing subtitle file: {input_file}")
        
        # Process video if provided
        if video:
            click.echo(f"Analyzing video file: {video}")
            video_analysis = video_processor.process_video(video, input_file)
            if not video_analysis:
                click.echo("Warning: Video analysis failed, proceeding with default positioning")
        
        # Process subtitles
        success = subtitle_processor.process_subtitle_file(input_file, output)
        
        if success:
            click.echo(f"Successfully processed subtitles. Output saved to: {output}")
        else:
            click.echo("Error: Failed to process subtitles", err=True)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('video_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output subtitle file path')
@click.option('--language', '-l', default='en-US', help='Language code for transcription')
def generate_subtitle(video_file: str, output: Optional[str], language: str):
    """Generate subtitles from a video file."""
    try:
        # Create processors
        video_processor = VideoProcessor()
        subtitle_processor = SubtitleProcessor()
        
        # Determine output path
        if not output:
            video_path = Path(video_file)
            output = str(video_path.parent / f"{video_path.stem}_subtitles.vtt")
        
        click.echo(f"Analyzing video file: {video_file}")
        
        # Process video
        video_analysis = video_processor.process_video(video_file)
        if not video_analysis:
            click.echo("Error: Video analysis failed", err=True)
            return
        
        # Generate subtitles
        if video_analysis.get('speech_timestamps'):
            click.echo("Generating subtitles...")
            success = subtitle_processor.process_subtitle_file(
                video_analysis['speech_timestamps'],
                output
            )
            
            if success:
                click.echo(f"Successfully generated subtitles. Output saved to: {output}")
            else:
                click.echo("Error: Failed to generate subtitles", err=True)
        else:
            click.echo("Error: No speech detected in video", err=True)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
