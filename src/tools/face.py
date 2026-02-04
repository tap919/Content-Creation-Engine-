"""
Face Analysis Tools

Provides wrappers for:
- DeepFace: Face recognition and analysis
"""

from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# DeepFace import (optional)
try:
    from deepface import DeepFace

    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("DeepFace not available. Install with: pip install deepface")


class DeepFaceTool:
    """
    DeepFace wrapper for face analysis.

    Provides methods for:
    - Face verification (compare faces)
    - Face analysis (age, gender, emotion, race)
    - Face quality assessment
    """

    def __init__(self):
        """Initialize DeepFace tool."""
        pass

    @property
    def available(self) -> bool:
        """Check if DeepFace is available."""
        return DEEPFACE_AVAILABLE

    def analyze_face(
        self,
        image_path: str,
        actions: Optional[list[str]] = None,
    ) -> Optional[list[dict]]:
        """
        Analyze face in image.

        Args:
            image_path: Path to image containing face
            actions: List of analysis actions (age, gender, emotion, race)
                    Default: all actions

        Returns:
            List of face analysis results or None if failed
        """
        if not DEEPFACE_AVAILABLE:
            logger.error("DeepFace not available")
            return None

        try:
            if actions is None:
                actions = ["age", "gender", "emotion", "race"]

            results = DeepFace.analyze(
                img_path=image_path,
                actions=actions,
                enforce_detection=False,
            )

            # Ensure results is a list
            if not isinstance(results, list):
                results = [results]

            logger.info(
                "Face analyzed",
                image=image_path,
                faces_found=len(results),
                actions=actions,
            )
            return results
        except Exception as e:
            logger.error("Face analysis failed", error=str(e))
            return None

    def detect_emotion(self, image_path: str) -> Optional[dict]:
        """
        Detect dominant emotion in face.

        Args:
            image_path: Path to image containing face

        Returns:
            Dict with emotion data or None if failed
        """
        results = self.analyze_face(image_path, actions=["emotion"])
        if not results:
            return None

        result = results[0]
        return {
            "dominant_emotion": result.get("dominant_emotion"),
            "emotion_scores": result.get("emotion", {}),
        }

    def estimate_age_gender(self, image_path: str) -> Optional[dict]:
        """
        Estimate age and gender from face.

        Args:
            image_path: Path to image containing face

        Returns:
            Dict with age and gender data or None if failed
        """
        results = self.analyze_face(image_path, actions=["age", "gender"])
        if not results:
            return None

        result = results[0]
        return {
            "age": result.get("age"),
            "gender": result.get("dominant_gender"),
            "gender_confidence": result.get("gender", {}).get(
                result.get("dominant_gender"), 0
            ),
        }

    def verify_faces(
        self,
        image1_path: str,
        image2_path: str,
        model_name: str = "VGG-Face",
    ) -> Optional[dict]:
        """
        Verify if two images contain the same person.

        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            model_name: Face recognition model to use

        Returns:
            Verification result dict or None if failed
        """
        if not DEEPFACE_AVAILABLE:
            logger.error("DeepFace not available")
            return None

        try:
            result = DeepFace.verify(
                img1_path=image1_path,
                img2_path=image2_path,
                model_name=model_name,
                enforce_detection=False,
            )

            logger.info(
                "Faces verified",
                image1=image1_path,
                image2=image2_path,
                verified=result.get("verified"),
            )
            return result
        except Exception as e:
            logger.error("Face verification failed", error=str(e))
            return None

    def assess_face_quality(self, image_path: str) -> Optional[dict]:
        """
        Assess face quality for avatar creation.

        Args:
            image_path: Path to image containing face

        Returns:
            Quality assessment dict or None if failed
        """
        if not DEEPFACE_AVAILABLE:
            logger.error("DeepFace not available")
            return None

        try:
            results = DeepFace.analyze(
                img_path=image_path,
                actions=["emotion"],
                enforce_detection=True,
            )

            if not results:
                return {"suitable_for_avatar": False, "reason": "No face detected"}

            result = results[0] if isinstance(results, list) else results

            # Check face region
            face_region = result.get("region", {})
            face_width = face_region.get("w", 0)
            face_height = face_region.get("h", 0)

            # Quality checks
            face_confidence = result.get("face_confidence", 0)
            is_size_sufficient = face_width >= 128 and face_height >= 128
            is_confidence_high = face_confidence > 0.9 if face_confidence else True

            suitable = is_size_sufficient and is_confidence_high

            quality = {
                "suitable_for_avatar": suitable,
                "face_width": face_width,
                "face_height": face_height,
                "face_confidence": face_confidence,
                "dominant_emotion": result.get("dominant_emotion"),
                "recommendations": [],
            }

            if not is_size_sufficient:
                quality["recommendations"].append(
                    "Face too small - use higher resolution image"
                )
            if not is_confidence_high:
                quality["recommendations"].append(
                    "Low face detection confidence - use clearer image"
                )

            logger.info(
                "Face quality assessed",
                image=image_path,
                suitable=suitable,
            )
            return quality
        except Exception as e:
            logger.error("Face quality assessment failed", error=str(e))
            return {
                "suitable_for_avatar": False,
                "reason": f"Analysis failed: {str(e)}",
            }

    def find_face_in_database(
        self,
        image_path: str,
        database_path: str,
        model_name: str = "VGG-Face",
    ) -> Optional[list[dict]]:
        """
        Find matching faces in a database directory.

        Args:
            image_path: Path to query image
            database_path: Path to directory containing face images
            model_name: Face recognition model to use

        Returns:
            List of matching faces or None if failed
        """
        if not DEEPFACE_AVAILABLE:
            logger.error("DeepFace not available")
            return None

        try:
            if not Path(database_path).is_dir():
                logger.error("Database path is not a directory")
                return None

            results = DeepFace.find(
                img_path=image_path,
                db_path=database_path,
                model_name=model_name,
                enforce_detection=False,
            )

            # Convert DataFrame results to list of dicts
            matches = []
            for df in results:
                if not df.empty:
                    matches.extend(df.to_dict(orient="records"))

            logger.info(
                "Face search completed",
                image=image_path,
                matches_found=len(matches),
            )
            return matches
        except Exception as e:
            logger.error("Face search failed", error=str(e))
            return None
