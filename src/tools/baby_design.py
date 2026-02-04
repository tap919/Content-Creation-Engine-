"""
Baby Design Tools - Open-source alternatives to Canva and Adobe CC

Provides simple, effective design tools using:
- Pillow for image manipulation and template creation
- Pre-built templates for social media
"""

import uuid
from pathlib import Path
from typing import Optional, Tuple, List
import structlog

logger = structlog.get_logger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not available. Install with: pip install Pillow")


class BabyCanva:
    """
    Simple Canva alternative using Pillow.
    
    Provides:
    - Social media post templates (Instagram, Facebook, Twitter)
    - Text overlay on images
    - Simple filters and effects
    - Thumbnail generation
    """
    
    # Social media dimensions
    DIMENSIONS = {
        'instagram_post': (1080, 1080),
        'instagram_story': (1080, 1920),
        'facebook_post': (1200, 630),
        'twitter_post': (1200, 675),
        'youtube_thumbnail': (1280, 720),
        'linkedin_post': (1200, 627),
        'tiktok': (1080, 1920),
    }
    
    def __init__(self, output_dir: str = "./output/designs"):
        """
        Initialize Baby Canva tool.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not available - tool will be disabled")
    
    @property
    def available(self) -> bool:
        """Check if tool is available."""
        return PILLOW_AVAILABLE
    
    def create_social_post(
        self,
        platform: str,
        text: str,
        background_color: Tuple[int, int, int] = (33, 150, 243),
        text_color: str = 'white',
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a simple social media post with text.
        
        Args:
            platform: Platform name (instagram_post, facebook_post, etc.)
            text: Text to display
            background_color: RGB tuple for background
            text_color: Text color
            output_path: Output file path (auto-generated if None)
            
        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None
        
        try:
            dimensions = self.DIMENSIONS.get(platform, (1080, 1080))
            img = Image.new('RGB', dimensions, color=background_color)
            draw = ImageDraw.Draw(img)
            
            # Try to load a nice font, fallback to default
            font_size = dimensions[0] // 15
            try:
                font = ImageFont.truetype('Arial.ttf', font_size)
            except OSError:
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
                except OSError:
                    font = ImageFont.load_default()
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            position = (
                (dimensions[0] - text_width) // 2,
                (dimensions[1] - text_height) // 2
            )
            
            # Draw text with shadow for better readability
            shadow_offset = 3
            draw.text(
                (position[0] + shadow_offset, position[1] + shadow_offset),
                text,
                font=font,
                fill='black'
            )
            draw.text(position, text, font=font, fill=text_color)
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"{platform}_{uuid.uuid4().hex[:8]}.png"
                )
            
            img.save(output_path)
            logger.info("Social post created", platform=platform, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Create social post failed", error=str(e))
            return None
    
    def add_text_to_image(
        self,
        image_path: str,
        text: str,
        position: str = 'center',
        font_size: int = 60,
        text_color: str = 'white',
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add text overlay to an existing image.
        
        Args:
            image_path: Path to input image
            text: Text to add
            position: Position ('top', 'center', 'bottom')
            font_size: Font size
            text_color: Text color
            output_path: Output path
            
        Returns:
            Path to output image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None
        
        try:
            with Image.open(image_path) as img:
                # Create a copy to work with
                img_copy = img.copy()
            
            draw = ImageDraw.Draw(img_copy)
            
            # Load font
            try:
                font = ImageFont.truetype('Arial.ttf', font_size)
            except OSError:
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
                except OSError:
                    font = ImageFont.load_default()
            
            # Calculate position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img_copy.width - text_width) // 2
            
            if position == 'top':
                y = img_copy.height // 10
            elif position == 'bottom':
                y = img_copy.height - text_height - img_copy.height // 10
            else:  # center
                y = (img_copy.height - text_height) // 2
            
            # Draw text with shadow
            shadow_offset = 2
            draw.text(
                (x + shadow_offset, y + shadow_offset),
                text,
                font=font,
                fill='black'
            )
            draw.text((x, y), text, font=font, fill=text_color)
            
            if output_path is None:
                ext = Path(image_path).suffix
                output_path = str(
                    self.output_dir / f"text_overlay_{uuid.uuid4().hex[:8]}{ext}"
                )
            
            img_copy.save(output_path)
            logger.info("Text added to image", input=image_path, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Add text to image failed", error=str(e))
            return None
    
    def create_thumbnail(
        self,
        title: str,
        background_image: Optional[str] = None,
        background_color: Tuple[int, int, int] = (33, 33, 33),
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a YouTube-style thumbnail.
        
        Args:
            title: Video title text
            background_image: Optional background image path
            background_color: Background color if no image
            output_path: Output path
            
        Returns:
            Path to thumbnail or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None
        
        try:
            dimensions = self.DIMENSIONS['youtube_thumbnail']
            
            if background_image:
                with Image.open(background_image) as bg_img:
                    img = bg_img.resize(dimensions, Image.Resampling.LANCZOS)
                    # Darken for better text readability
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(0.6)
            else:
                img = Image.new('RGB', dimensions, color=background_color)
            
            draw = ImageDraw.Draw(img)
            
            # Large, bold text for thumbnail
            font_size = 80
            try:
                font = ImageFont.truetype('Arial.ttf', font_size)
            except OSError:
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
                except OSError:
                    font = ImageFont.load_default()
            
            # Word wrap text
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] < dimensions[0] - 100:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw text lines
            y_offset = (dimensions[1] - len(lines) * (font_size + 10)) // 2
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (dimensions[0] - text_width) // 2
                y = y_offset + i * (font_size + 10)
                
                # Shadow
                draw.text((x + 4, y + 4), line, font=font, fill='black')
                # Text
                draw.text((x, y), line, font=font, fill='yellow')
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"thumbnail_{uuid.uuid4().hex[:8]}.png"
                )
            
            img.save(output_path)
            logger.info("Thumbnail created", output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Thumbnail creation failed", error=str(e))
            return None
    
    def apply_filter(
        self,
        image_path: str,
        filter_type: str = 'enhance',
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Apply Instagram-style filter to image.
        
        Args:
            image_path: Input image path
            filter_type: Filter type ('enhance', 'warm', 'cool', 'vintage', 'bw')
            output_path: Output path
            
        Returns:
            Path to filtered image or None if failed
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return None
        
        try:
            with Image.open(image_path) as source_img:
                img = source_img.copy()
            
            if filter_type == 'enhance':
                # Enhance colors and sharpness
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.3)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
                
            elif filter_type == 'warm':
                # Warm tones
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)
                
            elif filter_type == 'cool':
                # Cool tones
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.9)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
                
            elif filter_type == 'vintage':
                # Vintage look
                img = img.filter(ImageFilter.SMOOTH)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(0.8)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.7)
                
            elif filter_type == 'bw':
                # Black and white
                img = img.convert('L').convert('RGB')
            
            if output_path is None:
                ext = Path(image_path).suffix
                output_path = str(
                    self.output_dir / f"filtered_{filter_type}_{uuid.uuid4().hex[:8]}{ext}"
                )
            
            img.save(output_path)
            logger.info("Filter applied", filter=filter_type, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Apply filter failed", error=str(e))
            return None
    
    def batch_resize(
        self,
        image_paths: List[str],
        platform: str,
        output_dir: Optional[str] = None,
    ) -> List[str]:
        """
        Batch resize images for a specific platform.
        
        Args:
            image_paths: List of image paths
            platform: Target platform
            output_dir: Output directory
            
        Returns:
            List of output paths
        """
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available")
            return []
        
        if output_dir is None:
            output_dir = str(self.output_dir / f"batch_{platform}")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        dimensions = self.DIMENSIONS.get(platform, (1080, 1080))
        results = []
        
        for img_path in image_paths:
            try:
                with Image.open(img_path) as source_img:
                    img = source_img.copy()
                    
                    # Resize maintaining aspect ratio
                    img.thumbnail(dimensions, Image.Resampling.LANCZOS)
                    
                    # Create new image with exact dimensions and paste resized
                    final_img = Image.new('RGB', dimensions, (0, 0, 0))
                    offset = (
                        (dimensions[0] - img.width) // 2,
                        (dimensions[1] - img.height) // 2
                    )
                    final_img.paste(img, offset)
                    
                    filename = Path(img_path).stem
                    output_path = str(Path(output_dir) / f"{filename}_{platform}.jpg")
                    final_img.save(output_path)
                    results.append(output_path)
                
            except Exception as e:
                logger.error("Batch resize failed for image", image=img_path, error=str(e))
        
        logger.info("Batch resize completed", count=len(results), platform=platform)
        return results
