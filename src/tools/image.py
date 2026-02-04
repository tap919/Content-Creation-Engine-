"""
Image Processing Tools

Provides wrappers for:
- Pillow: Image manipulation
- OpenCV: Computer vision and image processing
- rembg: Background removal
"""

import uuid
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# Pillow import (should always be available)
try:
    from PIL import Image, ImageEnhance, ImageFilter

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not available. Install with: pip install Pillow")

# OpenCV import (optional)
try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")

# rembg import (optional)
try:
    from rembg import remove

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("rembg not available. Install with: pip install rembg")


class PillowTool:
    """
    Pillow wrapper for image manipulation.

    Provides methods for:
    - Resizing images
    - Cropping images
    - Applying filters and enhancements
    - Creating thumbnails
    - Format conversion
    """

    def __init__(self, output_dir: str = "./output/images"):
        """
        Initialize Pillow tool.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def available(self) -> bool:
        """Check if Pillow is available."""
        return PILLOW_AVAILABLE

    def resize(
        self,
        input_path: str,
        width: int,
        height: int,
        output_path: Optional[str] = None,
        maintain_aspect: bool = True,
    ) -> Optional[str]:
        """
        Resize image to specified dimensions.

        Args:
            input_path: Path to input image
            width: Target width
            height: Target height
            output_path: Path for output image
            maintain_aspect: Maintain aspect ratio (uses thumbnail method)

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)

            if maintain_aspect:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"resized_{uuid.uuid4().hex[:8]}{ext}"
                )

            img.save(output_path)
            logger.info("Image resized", input=input_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Image resize failed", error=str(e))
            return None

    def resize_for_avatar(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        size: int = 512,
    ) -> Optional[str]:
        """
        Resize image for avatar use (square format).

        Args:
            input_path: Path to input image
            output_path: Path for output image
            size: Avatar size (default 512x512)

        Returns:
            Path to output image or None if failed
        """
        return self.resize(
            input_path,
            size,
            size,
            output_path,
            maintain_aspect=False,
        )

    def crop(
        self,
        input_path: str,
        left: int,
        top: int,
        right: int,
        bottom: int,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Crop image to specified region.

        Args:
            input_path: Path to input image
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            cropped = img.crop((left, top, right, bottom))

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"cropped_{uuid.uuid4().hex[:8]}{ext}"
                )

            cropped.save(output_path)
            logger.info("Image cropped", input=input_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Image crop failed", error=str(e))
            return None

    def enhance_sharpness(
        self,
        input_path: str,
        factor: float = 2.0,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhance image sharpness.

        Args:
            input_path: Path to input image
            factor: Enhancement factor (1.0 = original, >1 = sharper)
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            enhancer = ImageEnhance.Sharpness(img)
            enhanced = enhancer.enhance(factor)

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"sharp_{uuid.uuid4().hex[:8]}{ext}"
                )

            enhanced.save(output_path)
            logger.info(
                "Sharpness enhanced", input=input_path, factor=factor, output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Sharpness enhancement failed", error=str(e))
            return None

    def enhance_contrast(
        self,
        input_path: str,
        factor: float = 1.5,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhance image contrast.

        Args:
            input_path: Path to input image
            factor: Enhancement factor (1.0 = original, >1 = more contrast)
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            enhancer = ImageEnhance.Contrast(img)
            enhanced = enhancer.enhance(factor)

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"contrast_{uuid.uuid4().hex[:8]}{ext}"
                )

            enhanced.save(output_path)
            logger.info(
                "Contrast enhanced", input=input_path, factor=factor, output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Contrast enhancement failed", error=str(e))
            return None

    def enhance_brightness(
        self,
        input_path: str,
        factor: float = 1.2,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhance image brightness.

        Args:
            input_path: Path to input image
            factor: Enhancement factor (1.0 = original, >1 = brighter)
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            enhancer = ImageEnhance.Brightness(img)
            enhanced = enhancer.enhance(factor)

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"bright_{uuid.uuid4().hex[:8]}{ext}"
                )

            enhanced.save(output_path)
            logger.info(
                "Brightness enhanced", input=input_path, factor=factor, output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Brightness enhancement failed", error=str(e))
            return None

    def apply_blur(
        self,
        input_path: str,
        radius: int = 2,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Apply blur filter to image.

        Args:
            input_path: Path to input image
            radius: Blur radius
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            blurred = img.filter(ImageFilter.GaussianBlur(radius))

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"blur_{uuid.uuid4().hex[:8]}{ext}"
                )

            blurred.save(output_path)
            logger.info("Blur applied", input=input_path, radius=radius, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Blur failed", error=str(e))
            return None

    def convert_format(
        self,
        input_path: str,
        output_format: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Convert image to different format.

        Args:
            input_path: Path to input image
            output_format: Target format (png, jpg, webp, etc.)
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)

            # Handle RGBA to RGB conversion for JPEG
            if output_format.lower() in ["jpg", "jpeg"] and img.mode == "RGBA":
                img = img.convert("RGB")

            if output_path is None:
                output_path = str(
                    self.output_dir / f"converted_{uuid.uuid4().hex[:8]}.{output_format}"
                )

            img.save(output_path, format=output_format.upper())
            logger.info(
                "Image converted", input=input_path, format=output_format, output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Image convert failed", error=str(e))
            return None

    def create_thumbnail(
        self,
        input_path: str,
        size: tuple[int, int] = (128, 128),
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create thumbnail from image.

        Args:
            input_path: Path to input image
            size: Thumbnail size (width, height)
            output_path: Path for output thumbnail

        Returns:
            Path to thumbnail or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            img = Image.open(input_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"thumb_{uuid.uuid4().hex[:8]}{ext}"
                )

            img.save(output_path)
            logger.info("Thumbnail created", input=input_path, size=size, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Thumbnail creation failed", error=str(e))
            return None

    def get_dimensions(self, image_path: str) -> Optional[tuple[int, int]]:
        """
        Get image dimensions.

        Args:
            image_path: Path to image

        Returns:
            Tuple of (width, height) or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None

        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error("Get dimensions failed", error=str(e))
            return None


class OpenCVTool:
    """
    OpenCV wrapper for computer vision tasks.

    Provides methods for:
    - Face detection
    - Background removal (simple)
    - Video frame extraction
    - Image preprocessing
    """

    def __init__(self, output_dir: str = "./output/images"):
        """
        Initialize OpenCV tool.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._face_cascade = None

    @property
    def available(self) -> bool:
        """Check if OpenCV is available."""
        return OPENCV_AVAILABLE

    def _get_face_cascade(self):
        """Lazy load face cascade classifier."""
        if self._face_cascade is None and OPENCV_AVAILABLE:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
        return self._face_cascade

    def detect_faces(
        self,
        image_path: str,
        scale_factor: float = 1.1,
        min_neighbors: int = 4,
    ) -> Optional[list[dict]]:
        """
        Detect faces in image.

        Args:
            image_path: Path to image
            scale_factor: Scale factor for detection
            min_neighbors: Minimum neighbors for detection

        Returns:
            List of face dicts with x, y, width, height or None if failed
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available")
            return None

        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            face_cascade = self._get_face_cascade()
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=scale_factor, minNeighbors=min_neighbors
            )

            results = []
            for x, y, w, h in faces:
                results.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                })

            logger.info("Faces detected", image=image_path, count=len(results))
            return results
        except Exception as e:
            logger.error("Face detection failed", error=str(e))
            return None

    def crop_to_face(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        padding: int = 20,
    ) -> Optional[str]:
        """
        Crop image to detected face.

        Args:
            image_path: Path to image
            output_path: Path for output image
            padding: Padding around face in pixels

        Returns:
            Path to cropped image or None if failed
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available")
            return None

        try:
            faces = self.detect_faces(image_path)
            if not faces:
                logger.warning("No faces detected")
                return None

            # Use the first (largest) face
            face = max(faces, key=lambda f: f["width"] * f["height"])

            img = cv2.imread(image_path)
            h, w = img.shape[:2]

            # Calculate crop region with padding
            x1 = max(0, face["x"] - padding)
            y1 = max(0, face["y"] - padding)
            x2 = min(w, face["x"] + face["width"] + padding)
            y2 = min(h, face["y"] + face["height"] + padding)

            cropped = img[y1:y2, x1:x2]

            if output_path is None:
                ext = Path(image_path).suffix
                output_path = str(
                    self.output_dir / f"face_crop_{uuid.uuid4().hex[:8]}{ext}"
                )

            cv2.imwrite(output_path, cropped)
            logger.info("Face cropped", input=image_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Face crop failed", error=str(e))
            return None

    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        interval: int = 1,
        max_frames: Optional[int] = None,
    ) -> Optional[list[str]]:
        """
        Extract frames from video.

        Args:
            video_path: Path to video file
            output_dir: Directory for output frames
            interval: Extract every Nth frame
            max_frames: Maximum number of frames to extract

        Returns:
            List of frame paths or None if failed
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available")
            return None

        try:
            if output_dir is None:
                output_dir = str(self.output_dir / f"frames_{uuid.uuid4().hex[:8]}")
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            cap = cv2.VideoCapture(video_path)
            frame_paths = []
            frame_count = 0
            extracted_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % interval == 0:
                    frame_path = str(Path(output_dir) / f"frame_{extracted_count:05d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    extracted_count += 1

                    if max_frames and extracted_count >= max_frames:
                        break

                frame_count += 1

            cap.release()
            logger.info(
                "Frames extracted", video=video_path, count=len(frame_paths)
            )
            return frame_paths
        except Exception as e:
            logger.error("Frame extraction failed", error=str(e))
            return None

    def apply_grayscale(
        self,
        image_path: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Convert image to grayscale.

        Args:
            image_path: Path to image
            output_path: Path for output image

        Returns:
            Path to grayscale image or None if failed
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available")
            return None

        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if output_path is None:
                ext = Path(image_path).suffix
                output_path = str(
                    self.output_dir / f"gray_{uuid.uuid4().hex[:8]}{ext}"
                )

            cv2.imwrite(output_path, gray)
            logger.info("Grayscale applied", input=image_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Grayscale conversion failed", error=str(e))
            return None


class RembgTool:
    """
    rembg wrapper for background removal.

    Provides methods for:
    - Removing image backgrounds
    - Creating transparent PNGs
    """

    def __init__(self, output_dir: str = "./output/images"):
        """
        Initialize rembg tool.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def available(self) -> bool:
        """Check if rembg is available."""
        return REMBG_AVAILABLE

    def remove_background(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Remove background from image.

        Args:
            input_path: Path to input image
            output_path: Path for output image (PNG with transparency)

        Returns:
            Path to output image or None if failed
        """
        if not REMBG_AVAILABLE:
            logger.error("rembg not available")
            return None

        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available (required for rembg)")
            return None

        try:
            input_img = Image.open(input_path)
            output_img = remove(input_img)

            if output_path is None:
                output_path = str(
                    self.output_dir / f"no_bg_{uuid.uuid4().hex[:8]}.png"
                )

            output_img.save(output_path, "PNG")
            logger.info("Background removed", input=input_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Background removal failed", error=str(e))
            return None

    def replace_background(
        self,
        input_path: str,
        background_color: tuple[int, int, int] = (255, 255, 255),
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Remove background and replace with solid color.

        Args:
            input_path: Path to input image
            background_color: RGB tuple for new background
            output_path: Path for output image

        Returns:
            Path to output image or None if failed
        """
        if not REMBG_AVAILABLE or not PILLOW_AVAILABLE:
            logger.error("rembg or Pillow not available")
            return None

        try:
            input_img = Image.open(input_path)
            output_img = remove(input_img)

            # Create new image with solid background
            background = Image.new("RGB", output_img.size, background_color)
            background.paste(output_img, mask=output_img.split()[3])  # Use alpha as mask

            if output_path is None:
                output_path = str(
                    self.output_dir / f"new_bg_{uuid.uuid4().hex[:8]}.jpg"
                )

            background.save(output_path)
            logger.info(
                "Background replaced",
                input=input_path,
                color=background_color,
                output=output_path,
            )
            return output_path
        except Exception as e:
            logger.error("Background replacement failed", error=str(e))
            return None
