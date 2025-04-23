# Subtitle Enhancement System

An intelligent subtitle processing system that improves media viewing experience through automated subtitle enhancement, positioning, and synchronization.

## Features

- Subtitle cleansing and error correction
- Language consistency maintenance
- Invalid character removal
- Extra line removal
- Grammar and spelling correction
- Subtitle positioning optimization
- Timing synchronization with spoken dialogue
- Font consistency enforcement
- Support for video and subtitle file processing
- Multiple interface options (CLI and Web)

## Tech Stack

- Python 3.8+
- AWS Services:
  - Amazon Transcribe for speech-to-text
  - Amazon Translate for language translation
  - Amazon Rekognition for text overlay detection
- FastAPI for web interface
- Click for CLI
- Vue.js for frontend

## Quick Start

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure AWS credentials
4. Run the application:
   - Web Interface: `python -m src.web.app`
   - CLI: `python -m src.cli.main process-subtitle <input-file>`

For detailed instructions, please refer to the documentation in the `docs` folder:
- [Architecture Overview](docs/Architecture.md)
- [Running Instructions](docs/Run.md)
- [Technical Stack Details](docs/Techstack.md)

## License

MIT License

## Contributing

Please read our contributing guidelines before submitting pull requests.
