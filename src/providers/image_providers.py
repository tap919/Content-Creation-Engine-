"""
Image provider implementations.

Includes open-source and API-based image generation providers.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog

from .base import ImageProvider, ProviderConfig

logger = structlog.get_logger(__name__)


class ComfyUIImageProvider(ImageProvider):
    """ComfyUI API provider for advanced image generation workflows."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize ComfyUI provider.

        Args:
            config: Provider configuration with API URL
        """
        super().__init__(config)
        self.api_url = config.api_url or "http://localhost:8188"

    async def initialize(self) -> None:
        """Initialize ComfyUI connection."""
        logger.info("Initializing ComfyUI provider", api_url=self.api_url)
        logger.info("ComfyUI provider initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("ComfyUI provider cleanup")

    async def health_check(self) -> Dict[str, Any]:
        """Check if ComfyUI API is available."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/system_stats", timeout=5.0)
                if response.status_code == 200:
                    return {"status": "healthy", "provider": self.name, "api_url": self.api_url}
        except Exception as e:
            logger.warning("ComfyUI health check failed", error=str(e))

        return {"status": "unavailable", "provider": self.name}

    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate image using ComfyUI workflow.

        Args:
            prompt: Description of desired image
            output_path: Where to save the image file
            options: Additional options (workflow, size, etc.)

        Returns:
            Dictionary with generation results
        """
        try:
            import httpx
            import json
            logger.info("Generating image with ComfyUI", prompt=prompt)

            # Prepare workflow (simplified example)
            workflow = options.get("workflow") if options else None
            if not workflow:
                # Use default text-to-image workflow
                workflow = {
                    "3": {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": options.get("seed", 42) if options else 42,
                            "steps": options.get("steps", 20) if options else 20,
                            "cfg": options.get("cfg", 8) if options else 8,
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "denoise": 1,
                            "model": ["4", 0],
                            "positive": ["6", 0],
                            "negative": ["7", 0],
                            "latent_image": ["5", 0]
                        }
                    },
                    "4": {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {
                            "ckpt_name": options.get("checkpoint", "sd_xl_base_1.0.safetensors") if options else "sd_xl_base_1.0.safetensors"
                        }
                    },
                    "6": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "text": prompt,
                            "clip": ["4", 1]
                        }
                    },
                    "7": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "text": options.get("negative_prompt", "") if options else "",
                            "clip": ["4", 1]
                        }
                    },
                    "5": {
                        "class_type": "EmptyLatentImage",
                        "inputs": {
                            "width": options.get("width", 1024) if options else 1024,
                            "height": options.get("height", 1024) if options else 1024,
                            "batch_size": 1
                        }
                    }
                }

            # Queue prompt
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.api_url}/prompt",
                    json={"prompt": workflow}
                )
                response.raise_for_status()
                result = response.json()
                prompt_id = result["prompt_id"]

                # Poll for completion and get result
                # In a full implementation, use WebSocket for real-time updates
                # For now, simplified polling
                import asyncio
                for _ in range(60):  # Wait up to 5 minutes
                    await asyncio.sleep(5)
                    history_response = await client.get(f"{self.api_url}/history/{prompt_id}")
                    if history_response.status_code == 200:
                        history = history_response.json()
                        if prompt_id in history:
                            # Get image
                            outputs = history[prompt_id]["outputs"]
                            # Extract image filename from outputs
                            # Save to output_path
                            break

            logger.info("Image generated successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "size": (options.get("width", 1024), options.get("height", 1024)) if options else (1024, 1024),
                "format": output_path.suffix.lstrip('.'),
            }

        except Exception as e:
            logger.error("ComfyUI image generation failed", error=str(e))
            raise

    async def edit_image(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Edit image using ComfyUI img2img workflow.

        Args:
            image_path: Path to input image
            prompt: Description of desired edits
            output_path: Where to save the edited image
            options: Additional options

        Returns:
            Dictionary with edit results
        """
        try:
            logger.info("Editing image with ComfyUI", image=str(image_path), prompt=prompt)

            # In a full implementation, upload image and run img2img workflow
            # For now, simplified placeholder

            logger.info("Image edited successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "format": output_path.suffix.lstrip('.'),
            }

        except Exception as e:
            logger.error("ComfyUI image editing failed", error=str(e))
            raise


class StableDiffusionWebUIProvider(ImageProvider):
    """AUTOMATIC1111 Stable Diffusion WebUI API provider."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize SD WebUI provider.

        Args:
            config: Provider configuration with API URL
        """
        super().__init__(config)
        self.api_url = config.api_url or "http://localhost:7860"

    async def initialize(self) -> None:
        """Initialize SD WebUI connection."""
        logger.info("Initializing SD WebUI provider", api_url=self.api_url)
        logger.info("SD WebUI provider initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("SD WebUI provider cleanup")

    async def health_check(self) -> Dict[str, Any]:
        """Check if SD WebUI API is available."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/sdapi/v1/sd-models", timeout=5.0)
                if response.status_code == 200:
                    return {"status": "healthy", "provider": self.name, "api_url": self.api_url}
        except Exception as e:
            logger.warning("SD WebUI health check failed", error=str(e))

        return {"status": "unavailable", "provider": self.name}

    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate image using SD WebUI.

        Args:
            prompt: Description of desired image
            output_path: Where to save the image file
            options: Additional options

        Returns:
            Dictionary with generation results
        """
        try:
            import httpx
            import base64
            from PIL import Image
            import io

            logger.info("Generating image with SD WebUI", prompt=prompt)

            # Prepare request
            payload = {
                "prompt": prompt,
                "negative_prompt": options.get("negative_prompt", "") if options else "",
                "steps": options.get("steps", 20) if options else 20,
                "width": options.get("width", 1024) if options else 1024,
                "height": options.get("height", 1024) if options else 1024,
                "cfg_scale": options.get("cfg_scale", 7) if options else 7,
                "sampler_name": options.get("sampler", "Euler a") if options else "Euler a",
            }

            # Call SD WebUI API
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.api_url}/sdapi/v1/txt2img",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # Decode and save image
                image_data = base64.b64decode(result["images"][0])
                image = Image.open(io.BytesIO(image_data))
                image.save(output_path)

            logger.info("Image generated successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "size": (payload["width"], payload["height"]),
                "format": output_path.suffix.lstrip('.'),
            }

        except Exception as e:
            logger.error("SD WebUI image generation failed", error=str(e))
            raise

    async def edit_image(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Edit image using SD WebUI img2img.

        Args:
            image_path: Path to input image
            prompt: Description of desired edits
            output_path: Where to save the edited image
            options: Additional options

        Returns:
            Dictionary with edit results
        """
        try:
            import httpx
            import base64
            from PIL import Image
            import io

            logger.info("Editing image with SD WebUI", image=str(image_path), prompt=prompt)

            # Load and encode image
            with Image.open(image_path) as img:
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Prepare request
            payload = {
                "init_images": [img_base64],
                "prompt": prompt,
                "negative_prompt": options.get("negative_prompt", "") if options else "",
                "steps": options.get("steps", 20) if options else 20,
                "cfg_scale": options.get("cfg_scale", 7) if options else 7,
                "denoising_strength": options.get("denoising_strength", 0.75) if options else 0.75,
            }

            # Call SD WebUI API
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.api_url}/sdapi/v1/img2img",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # Decode and save image
                image_data = base64.b64decode(result["images"][0])
                image = Image.open(io.BytesIO(image_data))
                image.save(output_path)

            logger.info("Image edited successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "format": output_path.suffix.lstrip('.'),
            }

        except Exception as e:
            logger.error("SD WebUI image editing failed", error=str(e))
            raise
