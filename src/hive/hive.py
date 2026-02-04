"""
Production Hive - Multi-Agent Content Production Orchestrator

The Production Hive coordinates multiple specialized agents to produce
content from creative briefs. It implements the multi-agent system (MAS)
described in the specification.
"""

import asyncio
import uuid
import time
from typing import Optional

import structlog

from src.sentinel.models import CreativeBrief
from src.utils.config import Config
from .models import GeneratedContent, AgentRole, HiveReward, ImageVariation, AudioTrack
from .agents import VisualistAgent, CriticAgent, EditorAgent, AudioAgent

logger = structlog.get_logger(__name__)


class ProductionHive:
    """
    Production Hive Orchestrator
    
    Coordinates the multi-agent system for content production:
    1. Visualist generates image variations
    2. Critic selects best image
    3. Audio agent generates background music
    4. Editor assembles final video
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize agents
        self.visualist = VisualistAgent(config, num_variations=5)
        self.critic = CriticAgent(config)
        self.audio = AudioAgent(config)
        self.editor = EditorAgent(config)
        
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all agents in parallel."""
        logger.info("Initializing Production Hive")
        
        await asyncio.gather(
            self.visualist.initialize(),
            self.critic.initialize(),
            self.audio.initialize(),
            self.editor.initialize(),
        )
        
        self._initialized = True
        logger.info("Production Hive initialized")
        
    async def cleanup(self) -> None:
        """Cleanup all agent resources."""
        logger.info("Cleaning up Production Hive")
        
        await asyncio.gather(
            self.visualist.cleanup(),
            self.critic.cleanup(),
            self.audio.cleanup(),
            self.editor.cleanup(),
        )
        
    async def produce(self, brief: CreativeBrief) -> GeneratedContent:
        """
        Produce content from creative brief.
        
        Implements the full production pipeline:
        v_t = H(G_V(b_t, θ_music; z), G_T(b_t, θ_text), a_t^text)
        
        Args:
            brief: Creative brief from Sentinel layer
            
        Returns:
            GeneratedContent with all production artifacts
        """
        if not self._initialized:
            raise RuntimeError("Production Hive not initialized")
        
        start_time = time.time()
        content_id = str(uuid.uuid4())
        
        logger.info("Starting content production", content_id=content_id, brief_id=brief.id)
        
        # Step 1 & 2: Run Visualist and Audio in parallel
        visualist_result, audio_result = await asyncio.gather(
            self.visualist.execute(brief),
            self.audio.execute(brief),
        )
        
        # Extract variations from visualist result
        variations = self._extract_variations(visualist_result)
        
        # Extract audio track from audio result
        audio_track = self._extract_audio_track(audio_result)
        
        # Step 3: Critic evaluates and selects best image
        critic_result = await self.critic.execute(brief, variations=variations)
        
        # Get selected image
        selected_image = self._get_selected_image(variations, critic_result)
        
        # Step 4: Editor assembles final video
        editor_result = await self.editor.execute(
            brief,
            selected_image=selected_image,
            audio_track=audio_track,
        )
        
        # Calculate total processing time
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Assemble final content
        content = GeneratedContent(
            id=content_id,
            brief_id=brief.id,
            video_path=editor_result.output_path,
            thumbnail_path=editor_result.output_paths[1] if len(editor_result.output_paths) > 1 else None,
            images=variations,
            audio=audio_track,
            text_overlays=[],  # Populated by editor
            agent_results={
                AgentRole.VISUALIST.value: visualist_result,
                AgentRole.CRITIC.value: critic_result,
                AgentRole.AUDIO.value: audio_result,
                AgentRole.EDITOR.value: editor_result,
            },
            overall_quality_score=self._calculate_quality_score(
                visualist_result, critic_result, audio_result, editor_result
            ),
            brand_alignment_score=critic_result.quality_score,
            total_processing_time_ms=total_time_ms,
        )
        
        # Calculate hive reward
        reward = self._calculate_hive_reward(content, brief)
        
        logger.info(
            "Content production complete",
            content_id=content_id,
            quality_score=content.overall_quality_score,
            hive_reward=reward.total_reward,
            processing_time_ms=total_time_ms,
        )
        
        return content
    
    def _extract_variations(self, visualist_result) -> list[ImageVariation]:
        """Extract image variations from visualist result."""
        variations_data = visualist_result.metadata.get("variations", [])
        variations = []
        
        for v_data in variations_data:
            try:
                # Handle Path serialization
                if "path" in v_data and isinstance(v_data["path"], str):
                    from pathlib import Path
                    v_data["path"] = Path(v_data["path"])
                variations.append(ImageVariation(**v_data))
            except Exception as e:
                logger.warning("Failed to parse variation", error=str(e))
                
        return variations
    
    def _extract_audio_track(self, audio_result) -> Optional[AudioTrack]:
        """Extract audio track from audio agent result."""
        if not audio_result.success:
            return None
            
        track_data = audio_result.metadata.get("audio_track")
        if not track_data:
            return None
            
        try:
            if "path" in track_data and isinstance(track_data["path"], str):
                from pathlib import Path
                track_data["path"] = Path(track_data["path"])
            return AudioTrack(**track_data)
        except Exception as e:
            logger.warning("Failed to parse audio track", error=str(e))
            return None
    
    def _get_selected_image(
        self, 
        variations: list[ImageVariation],
        critic_result
    ) -> Optional[ImageVariation]:
        """Get the image selected by the critic."""
        selected_id = critic_result.metadata.get("selected_variation_id")
        
        for variation in variations:
            if variation.id == selected_id:
                return variation
                
        # Fallback to first variation
        return variations[0] if variations else None
    
    def _calculate_quality_score(
        self,
        visualist_result,
        critic_result, 
        audio_result,
        editor_result
    ) -> float:
        """Calculate overall quality score from agent results."""
        scores = []
        weights = []
        
        if visualist_result.success:
            scores.append(visualist_result.quality_score)
            weights.append(0.25)
            
        if critic_result.success:
            scores.append(critic_result.quality_score)
            weights.append(0.35)
            
        if audio_result.success:
            scores.append(audio_result.quality_score)
            weights.append(0.2)
            
        if editor_result.success:
            scores.append(editor_result.quality_score)
            weights.append(0.2)
        
        if not scores:
            return 0.0
            
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        return sum(s * w for s, w in zip(scores, normalized_weights))
    
    def _calculate_hive_reward(
        self, 
        content: GeneratedContent,
        brief: CreativeBrief
    ) -> HiveReward:
        """
        Calculate hive reward proxy (pre-engagement).
        
        r_t^hive = E[CLIPSim(v_t, θ_brand_aesthetic)] - λ||δ^music||_1 - μ||δ^text||_1
        """
        # CLIP similarity (using brand alignment as proxy)
        clip_sim = content.brand_alignment_score
        
        # Music perturbation penalty (deviation from default params)
        music_penalty = (
            abs(brief.music_tempo - 90.0) / 90.0 +
            abs(brief.music_energy - 0.4) +
            abs(brief.music_danceability - 0.3)
        )
        
        # Text perturbation penalty
        text_penalty = abs(brief.jargon_level - 0.3)
        
        return HiveReward(
            content_id=content.id,
            clip_similarity=clip_sim,
            music_perturbation_penalty=music_penalty,
            text_perturbation_penalty=text_penalty,
        )
