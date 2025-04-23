from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import uvicorn
import tempfile
import os
import shutil
from typing import Optional

from ..core.subtitle_processor import SubtitleProcessor
from ..core.video_processor import VideoProcessor

app = FastAPI(title="Subtitle Enhancement System")

# Mount static files
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Initialize processors
subtitle_processor = SubtitleProcessor()
video_processor = VideoProcessor()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/process-subtitle")
async def process_subtitle(
    subtitle_file: UploadFile = File(...),
    video_file: Optional[UploadFile] = File(None)
):
    """Process a subtitle file with optional video analysis."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            subtitle_path = Path(temp_dir) / subtitle_file.filename
            with open(subtitle_path, "wb") as f:
                shutil.copyfileobj(subtitle_file.file, f)
            
            video_path = None
            if video_file:
                video_path = Path(temp_dir) / video_file.filename
                with open(video_path, "wb") as f:
                    shutil.copyfileobj(video_file.file, f)
            
            # Process video if provided
            if video_path:
                video_analysis = video_processor.process_video(str(video_path), str(subtitle_path))
                if not video_analysis:
                    raise HTTPException(status_code=400, detail="Video analysis failed")
            
            # Process subtitles
            output_path = Path(temp_dir) / f"enhanced_{subtitle_file.filename}"
            success = subtitle_processor.process_subtitle_file(str(subtitle_path), str(output_path))
            
            if not success:
                raise HTTPException(status_code=400, detail="Subtitle processing failed")
            
            return FileResponse(
                output_path,
                media_type="text/vtt",
                filename=f"enhanced_{subtitle_file.filename}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-subtitle")
async def generate_subtitle(
    video_file: UploadFile = File(...),
    language: str = "en-US"
):
    """Generate subtitles from a video file."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded video
            video_path = Path(temp_dir) / video_file.filename
            with open(video_path, "wb") as f:
                shutil.copyfileobj(video_file.file, f)
            
            # Process video
            video_analysis = video_processor.process_video(str(video_path))
            if not video_analysis:
                raise HTTPException(status_code=400, detail="Video analysis failed")
            
            if not video_analysis.get('speech_timestamps'):
                raise HTTPException(status_code=400, detail="No speech detected in video")
            
            # Generate subtitles
            output_path = Path(temp_dir) / f"{video_file.filename}.vtt"
            success = subtitle_processor.process_subtitle_file(
                video_analysis['speech_timestamps'],
                str(output_path)
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Subtitle generation failed")
            
            return FileResponse(
                output_path,
                media_type="text/vtt",
                filename=f"{Path(video_file.filename).stem}.vtt"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def run_server():
    """Run the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()
