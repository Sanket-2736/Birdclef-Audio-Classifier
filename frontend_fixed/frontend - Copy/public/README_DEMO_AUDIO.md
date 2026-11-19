# Demo Audio File

The `demo.ogg` file should be placed in this directory for the How-It-Works demo to work with real audio.

## Steps to add demo audio:

1. **Obtain a 60-second bird audio recording** (OGG Vorbis format recommended)
   - Can be sourced from: BirdCLEF dataset, Xeno-canto, or local recordings
   - Must be 60 seconds long (matching the demoResult.json windowing)

2. **Convert to OGG format** (if needed):
   ```bash
   ffmpeg -i input.wav -c:a libvorbis -q:a 6 demo.ogg
   ```

3. **Place in this directory**: `frontend/public/demo.ogg`

4. **The frontend will automatically load this file** when users visit the How-It-Works page

## Example sources:

- **BirdCLEF Dataset**: https://www.kaggle.com/competitions/birdclef-2024
- **Xeno-canto**: https://www.xeno-canto.org/ (large repository of bird recordings)
- **Local recordings**: Record your own 60-second bird audio

## Specifications:

- Duration: 60 seconds (12 windows × 5 seconds)
- Format: OGG Vorbis (.ogg)
- Sample rate: 32 kHz or higher (will be resampled if needed)
- Channels: Mono (recommended) or stereo
- File size: ~200-500 KB typical

Once added, the waveform visualization in How-It-Works will display the actual audio peaks!
