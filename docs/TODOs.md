## Hardware Issues

### Camera Color Problem (URGENT)
- **Issue**: Camera shows purple/corrupted colors in both web stream and saved photos
- **Diagnosis**: Hardware fault - ribbon cable or camera module defective
- **Solution**:
  1. First try: Replace camera ribbon cable (~$5-10)
  2. If that fails: Replace camera module (~$15-30)
- **Files affected**: `v1.0/example/11.video_car.py`
- **Note**: Software fixes attempted (all color space conversions) - none worked, confirming hardware issue

## Software TODOs

### Command functions
- alsa mixer to max levels
- diagnostic