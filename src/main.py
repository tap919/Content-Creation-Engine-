"""
Agentic Content Factory - Main Entry Point

This module serves as the main entry point for the content creation engine,
orchestrating the three core layers: Sentinel, Hive, and Evolution.
"""

import asyncio
import argparse
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

from src.sentinel import SentinelLayer
from src.hive import ProductionHive
from src.evolution import EvolutionaryLoop
from src.api import create_app
from src.utils.config import load_config, Config

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class AgenticContentFactory:
    """
    The Bio-Digital Creative Reflex - Main orchestrator for the content factory.
    
    This class coordinates the three layers:
    1. Sentinel Layer (Perception) - Trend detection and brief generation
    2. Production Hive (Creation) - Multi-agent content generation
    3. Evolutionary Loop (Optimization) - Engagement-based adaptation
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.sentinel = SentinelLayer(config)
        self.hive = ProductionHive(config)
        self.evolution = EvolutionaryLoop(config)
        self._running = False
        
    async def initialize(self) -> None:
        """Initialize all layers and connections."""
        logger.info("Initializing Agentic Content Factory")
        await self.sentinel.initialize()
        await self.hive.initialize()
        await self.evolution.initialize()
        logger.info("All layers initialized successfully")
        
    async def run_cycle(self) -> dict:
        """
        Execute one complete content creation cycle.
        
        Returns:
            dict: Results from the cycle including generated content metadata
        """
        logger.info("Starting content creation cycle")
        
        # Step 1: Sentinel detects trends and generates brief
        trend_data = await self.sentinel.detect_trends()
        
        if not trend_data.is_high_signal:
            logger.info("No high-signal event detected, skipping cycle")
            return {"status": "skipped", "reason": "no_high_signal_event"}
        
        brief = await self.sentinel.generate_brief(trend_data)
        logger.info("Brief generated", topic=brief.topic)
        
        # Step 2: Production Hive creates content
        content = await self.hive.produce(brief)
        logger.info("Content produced", content_id=content.id)
        
        # Step 3: Deploy content (placeholder for social media posting)
        deployment_result = await self._deploy_content(content)
        
        # Step 4: Schedule evolution check
        await self.evolution.schedule_fitness_check(content.id)
        
        return {
            "status": "success",
            "content_id": content.id,
            "topic": brief.topic,
            "deployment": deployment_result
        }
    
    async def _deploy_content(self, content) -> dict:
        """
        Deploy content to configured platforms.

        Note:
            This method is currently a stub and does not perform real deployment.
            The return value explicitly indicates that deployment has not occurred.
        """
        # Placeholder for actual deployment logic
        logger.warning(
            "Deployment not implemented; content not actually deployed",
            content_id=content.id,
        )
        return {
            "deployed": False,
            "reason": "deployment_not_implemented",
            "platforms": getattr(self.config, "deployment_platforms", []),
        }
    
    async def start(self) -> None:
        """Start the continuous content factory loop."""
        self._running = True
        logger.info("Starting continuous content factory")
        
        while self._running:
            try:
                result = await self.run_cycle()
                logger.info("Cycle completed", result=result)
            except Exception as e:
                logger.error("Error in content cycle", error=str(e))
            
            # Wait for next cycle (configurable interval)
            await asyncio.sleep(self.config.cycle_interval_seconds)
    
    async def stop(self) -> None:
        """Stop the content factory gracefully."""
        logger.info("Stopping content factory")
        self._running = False
        await self.sentinel.cleanup()
        await self.hive.cleanup()
        await self.evolution.cleanup()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Agentic Content Factory - AI-powered content creation engine"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["api", "worker", "single"],
        default="api",
        help="Run mode: api (HTTP server), worker (background), single (one cycle)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port"
    )
    return parser.parse_args()


async def run_api_server(config: Config, host: str, port: int):
    """Run the FastAPI server."""
    import uvicorn
    
    app = create_app(config)
    server_config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(server_config)
    await server.serve()


async def run_worker(config: Config):
    """Run as background worker."""
    factory = AgenticContentFactory(config)
    await factory.initialize()
    await factory.start()


async def run_single_cycle(config: Config):
    """Run a single content creation cycle."""
    factory = AgenticContentFactory(config)
    await factory.initialize()
    result = await factory.run_cycle()
    print(f"Cycle result: {result}")
    await factory.stop()


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    args = parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if config_path.exists():
        config = load_config(config_path)
    else:
        logger.warning("Config file not found, using defaults", path=str(config_path))
        config = Config()
    
    logger.info("Starting Agentic Content Factory", mode=args.mode)
    
    # Run based on mode
    if args.mode == "api":
        asyncio.run(run_api_server(config, args.host, args.port))
    elif args.mode == "worker":
        asyncio.run(run_worker(config))
    elif args.mode == "single":
        asyncio.run(run_single_cycle(config))
    else:
        logger.error("Unknown mode", mode=args.mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
