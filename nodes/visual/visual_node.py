"""
Visual Node for Nevil v3.0

Handles camera operations and image capture on demand.
Subscribes to snap_pic topic and publishes images to ai_cognitive node.
"""

import os
import time
import base64
from io import BytesIO
from nevil_framework.base_node import NevilNode

# Camera availability will be checked at runtime
PICAMERA_AVAILABLE = None
CV2_AVAILABLE = None


class VisualNode(NevilNode):
    """
    Visual Node for camera capture and image processing.

    Features:
    - On-demand image capture via snap_pic topic
    - Support for PiCamera2 and OpenCV fallback
    - Base64 encoded image publishing
    - Configurable image quality and resolution
    """

    def __init__(self):
        super().__init__("visual")

        # Camera configuration
        config = self.config.get('configuration', {})
        self.camera_config = config.get('camera', {})

        # Image settings
        self.image_width = self.camera_config.get('width', 640)
        self.image_height = self.camera_config.get('height', 480)
        self.image_quality = self.camera_config.get('quality', 85)
        self.image_format = self.camera_config.get('format', 'JPEG')

        # Camera state
        self.camera = None
        self.camera_type = None
        self.capture_count = 0

        # Processing state
        self.last_capture_time = 0
        self.min_capture_interval = self.camera_config.get('min_interval', 1.0)  # Minimum seconds between captures

    def initialize(self):
        """Initialize camera and visual processing"""
        self.logger.info("Initializing Visual Node...")

        # Check camera availability at runtime
        self._check_camera_availability()

        # Log available camera libraries
        self.logger.info(f"PiCamera2 available: {PICAMERA_AVAILABLE}")
        self.logger.info(f"OpenCV available: {CV2_AVAILABLE}")

        # Try to initialize camera
        if self._init_camera():
            self.logger.info(f"Camera initialized successfully using {self.camera_type}")
            camera_status = "camera_ready"
        else:
            self.logger.warning("No camera available - running in stub mode")
            self.camera_type = "stub"
            camera_status = "camera_unavailable"

        # Log configuration
        self.logger.info("Visual Node Configuration:")
        self.logger.info(f"  Camera type: {self.camera_type}")
        self.logger.info(f"  Resolution: {self.image_width}x{self.image_height}")
        self.logger.info(f"  Quality: {self.image_quality}")
        self.logger.info(f"  Format: {self.image_format}")
        self.logger.info(f"  Min capture interval: {self.min_capture_interval}s")

        # Start in idle mode
        self._set_system_mode("idle", camera_status)

        self.logger.info("Visual Node initialization complete")
        return True

    def _check_camera_availability(self):
        """Check camera library availability at runtime"""
        global PICAMERA_AVAILABLE, CV2_AVAILABLE

        if PICAMERA_AVAILABLE is None:
            try:
                import picamera2
                PICAMERA_AVAILABLE = True
                self.logger.info("PiCamera2 library available")
            except ImportError as e:
                PICAMERA_AVAILABLE = False
                self.logger.info(f"PiCamera2 not available: {e}")
            except Exception as e:
                PICAMERA_AVAILABLE = False
                self.logger.info(f"PiCamera2 import error: {e}")

        if CV2_AVAILABLE is None:
            try:
                import cv2
                CV2_AVAILABLE = True
                self.logger.info("OpenCV library available")
            except ImportError as e:
                self.logger.warning(f"OpenCV not available: {e}")
                CV2_AVAILABLE = False
            except Exception as e:
                self.logger.warning(f"OpenCV import error: {e}")
                CV2_AVAILABLE = False

    def _init_camera(self):
        """Initialize camera using available libraries"""
        try:
            # Try PiCamera2 first (preferred for Raspberry Pi)
            if PICAMERA_AVAILABLE:
                from picamera2 import Picamera2
                self.camera = Picamera2()

                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={"size": (self.image_width, self.image_height)}
                )
                self.camera.configure(camera_config)
                self.camera.start()

                # Give camera time to warm up
                time.sleep(2)

                self.camera_type = "PiCamera2"
                return True

        except Exception as e:
            self.logger.warning(f"Failed to initialize PiCamera2: {e}")

        try:
            # Try rpicam-still (modern Raspberry Pi camera)
            import subprocess
            result = subprocess.run(['rpicam-still', '--help'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                self.camera_type = "rpicam-still"
                self.camera = True  # Just a placeholder - rpicam-still doesn't need persistent connection
                return True
            else:
                self.logger.warning("rpicam-still not available")

        except Exception as e:
            self.logger.warning(f"Failed to initialize rpicam-still: {e}")

        return False

    def main_loop(self):
        """Main processing loop - minimal for event-driven operation"""
        time.sleep(0.1)

    def on_snap_pic(self, message):
        """
        Handle picture capture requests

        This is the main callback for the snap_pic topic.
        Captures image and publishes to ai_cognitive node.
        """
        try:
            self.logger.info(f"📷 Visual node received snap_pic request from {message.data.get('requested_by', 'unknown')}")

            # Check rate limiting
            current_time = time.time()
            if current_time - self.last_capture_time < self.min_capture_interval:
                self.logger.warning(f"Rate limited: {current_time - self.last_capture_time:.1f}s since last capture")
                return

            self.logger.info("📸 Capturing image...")
            self._set_system_mode("capturing", "snap_pic_requested")

            # Capture image
            image_data = self._capture_image()

            if image_data:
                # Prepare image message
                image_message_data = {
                    "image_data": image_data,
                    "format": self.image_format,
                    "width": self.image_width,
                    "height": self.image_height,
                    "timestamp": current_time,
                    "capture_id": f"snap_{self.capture_count}_{int(current_time)}"
                }

                # Publish to ai_cognitive node
                if self.publish("visual_data", image_message_data):
                    self.logger.info(f"✅ Image captured and published to visual_data topic (ID: {image_message_data['capture_id']})")
                    self.logger.info(f"📊 Image size: {len(image_data)} bytes (base64)")
                    self.capture_count += 1
                    self.last_capture_time = current_time
                    self._set_system_mode("idle", "image_published")
                else:
                    self.logger.error("❌ Failed to publish image data to visual_data topic")
                    self._set_system_mode("error", "publish_failed")
            else:
                self.logger.error("Failed to capture image")
                self._set_system_mode("error", "capture_failed")

        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            self._set_system_mode("error", f"capture_error: {e}")

    def _capture_image(self):
        """Capture image using available camera"""
        try:
            if self.camera_type == "PiCamera2":
                return self._capture_picamera2()
            elif self.camera_type == "rpicam-still":
                return self._capture_opencv()  # Renamed but now uses rpicam-still
            elif self.camera_type == "stub":
                return self._capture_stub()
            else:
                self.logger.error(f"Unknown camera type: {self.camera_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error in _capture_image: {e}")
            return None

    def _capture_picamera2(self):
        """Capture image using PiCamera2"""
        try:
            # Capture to BytesIO buffer
            buffer = BytesIO()
            self.camera.capture_file(buffer, format=self.image_format.lower())

            # Get image data and encode as base64
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            self.logger.debug(f"Captured image: {len(image_bytes)} bytes")
            return image_base64

        except Exception as e:
            self.logger.error(f"PiCamera2 capture failed: {e}")
            return None

    def _capture_opencv(self):
        """Capture image using rpicam-still (modern Raspberry Pi camera)"""
        try:
            import subprocess
            import tempfile
            import os

            # Create temporary file for capture
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Use rpicam-still to capture image
                cmd = [
                    'rpicam-still',
                    '--timeout', '1000',  # 1 second timeout
                    '--width', str(self.image_width),
                    '--height', str(self.image_height),
                    '--quality', str(self.image_quality),
                    '--nopreview',  # No preview window
                    '-o', temp_path
                ]

                # Capture image
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

                if result.returncode != 0:
                    self.logger.error(f"rpicam-still failed: {result.stderr}")
                    return None

                # Read and encode image
                with open(temp_path, 'rb') as f:
                    image_bytes = f.read()

                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

                self.logger.debug(f"Captured image with rpicam-still: {len(image_bytes)} bytes")
                return image_base64

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            self.logger.error(f"rpicam-still capture failed: {e}")
            return None

    def _capture_stub(self):
        """Generate a stub image when no camera is available"""
        try:
            # Create a minimal valid JPEG using PIL
            from PIL import Image
            import base64
            from io import BytesIO

            # Create a simple 100x100 red image
            width, height = 100, 100
            image = Image.new('RGB', (width, height), color='red')

            # Save as JPEG to BytesIO
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Convert to base64
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            self.logger.debug(f"Generated stub image data (JPEG format, {len(image_bytes)} bytes)")
            return image_base64

        except ImportError:
            self.logger.warning("PIL not available, creating minimal BMP stub")
            try:
                # Fallback: create a minimal valid BMP file
                import base64

                # Minimal 2x2 BMP header + pixel data (54 bytes header + 12 bytes pixels)
                # This is a valid 2x2 red BMP image
                bmp_data = bytearray([
                    # BMP Header (14 bytes)
                    0x42, 0x4D,  # "BM" signature
                    0x42, 0x00, 0x00, 0x00,  # File size (66 bytes)
                    0x00, 0x00, 0x00, 0x00,  # Reserved
                    0x36, 0x00, 0x00, 0x00,  # Offset to pixel data (54 bytes)

                    # DIB Header (40 bytes)
                    0x28, 0x00, 0x00, 0x00,  # Header size (40 bytes)
                    0x02, 0x00, 0x00, 0x00,  # Width (2 pixels)
                    0x02, 0x00, 0x00, 0x00,  # Height (2 pixels)
                    0x01, 0x00,              # Planes (1)
                    0x18, 0x00,              # Bits per pixel (24)
                    0x00, 0x00, 0x00, 0x00,  # Compression (none)
                    0x0C, 0x00, 0x00, 0x00,  # Image size (12 bytes)
                    0x00, 0x00, 0x00, 0x00,  # X pixels per meter
                    0x00, 0x00, 0x00, 0x00,  # Y pixels per meter
                    0x00, 0x00, 0x00, 0x00,  # Colors used
                    0x00, 0x00, 0x00, 0x00,  # Important colors

                    # Pixel data (12 bytes) - 2x2 red pixels, padded rows
                    0x00, 0x00, 0xFF, 0x00, 0x00, 0xFF, 0x00, 0x00,  # Row 1: red, red + padding
                    0x00, 0x00, 0xFF, 0x00, 0x00, 0xFF, 0x00, 0x00   # Row 2: red, red + padding
                ])

                image_base64 = base64.b64encode(bmp_data).decode('utf-8')
                self.logger.debug(f"Generated stub BMP image data ({len(bmp_data)} bytes)")
                return image_base64

            except Exception as e:
                self.logger.error(f"BMP stub creation failed: {e}")
                return None

        except Exception as e:
            self.logger.error(f"Stub capture failed: {e}")
            return None

    def _set_system_mode(self, mode, reason):
        """Set system mode and publish change"""
        mode_data = {
            "mode": mode,
            "reason": reason,
            "timestamp": time.time(),
            "node": "visual"
        }

        self.publish("system_mode", mode_data)
        self.logger.debug(f"Set system mode: {mode} ({reason})")

    def cleanup(self):
        """Cleanup camera resources"""
        self.logger.info("Cleaning up Visual Node...")

        # Set system to idle
        self._set_system_mode("idle", "shutting_down")

        # Release camera
        if self.camera:
            try:
                if self.camera_type == "PiCamera2":
                    self.camera.stop()
                    self.camera.close()
                elif self.camera_type == "rpicam-still":
                    # rpicam-still doesn't need cleanup
                    pass

                self.logger.info("Camera released")
            except Exception as e:
                self.logger.warning(f"Error releasing camera: {e}")

        self.camera = None

        self.logger.info(f"Visual Node stopped after {self.capture_count} captures")

    def get_visual_stats(self):
        """Get visual node statistics"""
        return {
            "camera_type": self.camera_type,
            "camera_available": self.camera is not None,
            "capture_count": self.capture_count,
            "last_capture_time": self.last_capture_time,
            "image_settings": {
                "width": self.image_width,
                "height": self.image_height,
                "quality": self.image_quality,
                "format": self.image_format
            }
        }