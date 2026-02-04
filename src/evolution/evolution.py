"""
Evolutionary Loop - Engagement-Based Parameter Optimization

The Evolutionary Loop tracks engagement metrics and adapts brand parameters
to optimize for audience response. It implements the evolutionary algorithm
described in the mathematical specification.
"""

import uuid
from datetime import datetime, timezone

import structlog
import numpy as np

from src.utils.config import Config
from .models import (
    EngagementMetrics, FitnessScore, BrandParameters, EvolutionConfig
)

logger = structlog.get_logger(__name__)


class EvolutionaryLoop:
    """
    Evolutionary Loop for brand parameter optimization.
    
    Implements the evolutionary algorithm:
    1. Sample perturbations {η_i ~ N(0,I)}_{i=1}^N
    2. Fitness-rank θ_t^(i) = θ_t + α*η_i
    3. Select top-k, crossover, mutate:
       θ_{t+1} = (1-β)*θ_elite + β*M(θ_elite, η)
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.evo_config = EvolutionConfig()
        
        # Current brand parameters
        self.current_params = BrandParameters(
            id=str(uuid.uuid4()),
            generation=0,
        )
        
        # Fitness tracking
        self.fitness_history: list[FitnessScore] = []
        self.pending_content: dict[str, datetime] = {}
        
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the evolutionary loop."""
        logger.info("Initializing Evolutionary Loop")
        self._initialized = True
        
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up Evolutionary Loop")
        
    async def schedule_fitness_check(self, content_id: str) -> None:
        """
        Schedule a fitness check for deployed content.
        
        The check will be performed after sufficient engagement data
        has been collected (typically 24-48 hours).
        """
        self.pending_content[content_id] = datetime.now(timezone.utc)
        logger.info("Fitness check scheduled", content_id=content_id)
        
    async def collect_engagement(self, content_id: str, platform: str) -> EngagementMetrics:
        """
        Collect engagement metrics for content.
        
        In production, this would query social media APIs.
        """
        logger.info("Collecting engagement", content_id=content_id, platform=platform)
        
        # Placeholder: Generate synthetic engagement data
        return EngagementMetrics(
            content_id=content_id,
            platform=platform,
            views=np.random.randint(100, 10000),
            likes=np.random.randint(10, 1000),
            shares=np.random.randint(5, 200),
            comments=np.random.randint(1, 100),
            watch_time_percent=np.random.uniform(0.3, 0.9),
        )
        
    async def evaluate_fitness(self, content_id: str) -> FitnessScore:
        """
        Evaluate fitness for a piece of content.
        
        Implements:
        f_t(θ_t) = 0.4*(likes/views) + 0.3*(shares/views) + 0.3*watch% - 0.1*cost(t)
        """
        # Collect engagement from all platforms
        platforms = self.config.deployment_platforms
        all_metrics = []
        
        for platform in platforms:
            metrics = await self.collect_engagement(content_id, platform)
            all_metrics.append(metrics)
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics(content_id, all_metrics)
        
        # Calculate historical average
        hist_avg = self._get_historical_average()
        
        # Create fitness score
        fitness = FitnessScore.from_engagement(
            content_id=content_id,
            metrics=aggregated,
            cost=self._estimate_cost(content_id),
            historical_avg=hist_avg,
        )
        
        # Track fitness
        self.fitness_history.append(fitness)
        self.current_params.fitness_history.append(fitness.total_fitness)
        
        logger.info(
            "Fitness evaluated",
            content_id=content_id,
            fitness=fitness.total_fitness,
            triggers_evolution=fitness.triggers_evolution,
        )
        
        return fitness
    
    def _aggregate_metrics(
        self,
        content_id: str,
        metrics_list: list[EngagementMetrics]
    ) -> EngagementMetrics:
        """Aggregate engagement metrics across platforms."""
        total_views = sum(m.views for m in metrics_list)
        total_likes = sum(m.likes for m in metrics_list)
        total_shares = sum(m.shares for m in metrics_list)
        total_comments = sum(m.comments for m in metrics_list)
        
        # Weighted average watch time by views to reflect platform volume
        if total_views > 0:
            avg_watch_time = sum(
                m.watch_time_percent * m.views for m in metrics_list
            ) / total_views
        else:
            avg_watch_time = 0.0
        
        return EngagementMetrics(
            content_id=content_id,
            platform="aggregated",
            views=total_views,
            likes=total_likes,
            shares=total_shares,
            comments=total_comments,
            watch_time_percent=avg_watch_time,
        )
    
    def _get_historical_average(self) -> float:
        """Get historical average fitness."""
        if not self.fitness_history:
            return 0.0
        return np.mean([f.total_fitness for f in self.fitness_history])
    
    def _estimate_cost(self, content_id: str) -> float:
        """Estimate production cost (API calls, compute, etc.)."""
        # Placeholder: Fixed cost per content
        return 0.1
    
    async def evolve_parameters(self, fitness: FitnessScore) -> BrandParameters:
        """
        Evolve brand parameters based on fitness.
        
        Implements the evolutionary step:
        1. Sample perturbations {η_i ~ N(0,I)}_{i=1}^N
        2. Fitness-rank θ_t^(i) = θ_t + α*η_i
        3. Select top-k, crossover, mutate:
           θ_{t+1} = (1-β)*θ_elite + β*M(θ_elite, η)
        """
        if not fitness.triggers_evolution:
            logger.info("Fitness below threshold, no evolution")
            return self.current_params
        
        logger.info(
            "Evolving parameters",
            current_generation=self.current_params.generation,
            fitness=fitness.total_fitness,
        )
        
        # Convert current params to vector
        current_vector = self.current_params.to_vector()
        dim = len(current_vector)
        
        # Step 1: Sample perturbations
        perturbations = np.random.randn(self.evo_config.population_size, dim)
        
        # Step 2: Create candidate population and rank by simulated fitness
        candidates = []
        for i in range(self.evo_config.population_size):
            perturbed = current_vector + self.evo_config.alpha * perturbations[i]
            candidate_params = BrandParameters.from_vector(perturbed, self.current_params)
            
            # Simulate fitness (in production, this would use the hive reward proxy)
            simulated_fitness = self._simulate_fitness(candidate_params)
            candidates.append((candidate_params, simulated_fitness))
        
        # Sort by fitness (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Step 3: Select elite, crossover, mutate
        elite = [c[0] for c in candidates[:self.evo_config.elite_count]]
        
        # Average elite vectors
        elite_vectors = np.array([e.to_vector() for e in elite])
        elite_mean = np.mean(elite_vectors, axis=0)
        
        # Mutation
        mutation_noise = np.random.randn(dim)
        new_vector = (
            (1 - self.evo_config.beta) * elite_mean +
            self.evo_config.beta * (elite_mean + self.evo_config.alpha * mutation_noise)
        )
        
        # Create new parameters
        new_params = BrandParameters.from_vector(new_vector, self.current_params)
        
        # Update current parameters
        self.current_params = new_params
        
        logger.info(
            "Parameters evolved",
            new_generation=new_params.generation,
            elite_fitness=candidates[0][1],
        )
        
        return new_params
    
    def _simulate_fitness(self, params: BrandParameters) -> float:
        """
        Simulate fitness for parameter candidate.
        
        Uses the hive reward proxy for pre-engagement fitness estimation.
        """
        # Placeholder: Simple heuristic based on parameter values
        # In production, this would use the actual CLIP similarity model
        
        vector = params.to_vector()
        
        # Prefer moderate values (penalize extremes)
        moderation_score = 1.0 - np.mean(np.abs(vector - 0.5))
        
        # Add some randomness
        noise = np.random.uniform(0.9, 1.1)
        
        return moderation_score * noise
    
    def get_current_parameters(self) -> BrandParameters:
        """Get current evolved brand parameters."""
        return self.current_params
    
    async def run_evolution_cycle(self, content_ids: list[str]) -> BrandParameters:
        """
        Run a complete evolution cycle for multiple content pieces.
        
        Collects engagement for all content, evaluates fitness,
        and evolves parameters based on aggregate performance.
        """
        logger.info("Running evolution cycle", content_count=len(content_ids))
        
        # Evaluate fitness for all content
        fitness_scores = []
        for content_id in content_ids:
            fitness = await self.evaluate_fitness(content_id)
            fitness_scores.append(fitness)
        
        # Use best fitness for evolution decision
        best_fitness = max(fitness_scores, key=lambda f: f.total_fitness)
        
        # Evolve parameters
        new_params = await self.evolve_parameters(best_fitness)
        
        return new_params
