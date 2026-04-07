"""
Campaign management service with enhanced workflow support.
"""

import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from src.models.campaign import (
    Campaign,
    ContentPiece,
    ContentAsset,
    CampaignStatus,
    ContentStatus,
    WorkflowStage,
    ContentCalendarEntry,
    AssetLibraryEntry,
)

logger = structlog.get_logger(__name__)


class CampaignManager:
    """
    Manages campaigns with full workflow support.

    Features:
    - Multi-stage workflow management
    - Content calendar and scheduling
    - Asset library with version control
    - Budget and cost tracking
    - Performance analytics
    """

    def __init__(self, config, storage_path: Path):
        """
        Initialize Campaign Manager.

        Args:
            config: Application configuration
            storage_path: Path for campaign data storage
        """
        self.config = config
        self.storage_path = storage_path
        self.campaigns: Dict[str, Campaign] = {}
        self.calendar: List[ContentCalendarEntry] = []
        self.asset_library: Dict[str, AssetLibraryEntry] = {}

        # Create storage directories
        self.campaigns_dir = storage_path / "campaigns"
        self.assets_dir = storage_path / "assets"
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Campaign Manager initialized", storage=str(storage_path))

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """
        Create a new campaign.

        Args:
            campaign_data: Campaign configuration

        Returns:
            Created Campaign object
        """
        campaign = Campaign.from_dict(campaign_data)
        campaign.updated_at = datetime.utcnow()

        # Save to storage
        await self._save_campaign(campaign)

        # Cache in memory
        self.campaigns[campaign.id] = campaign

        logger.info("Campaign created", campaign_id=campaign.id, name=campaign.name)

        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign object or None
        """
        # Check cache first
        if campaign_id in self.campaigns:
            return self.campaigns[campaign_id]

        # Load from storage
        campaign = await self._load_campaign(campaign_id)
        if campaign:
            self.campaigns[campaign_id] = campaign

        return campaign

    async def update_campaign(
        self,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Campaign:
        """
        Update campaign.

        Args:
            campaign_id: Campaign ID
            updates: Fields to update

        Returns:
            Updated Campaign object
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Apply updates
        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        campaign.updated_at = datetime.utcnow()

        # Save
        await self._save_campaign(campaign)

        logger.info("Campaign updated", campaign_id=campaign_id)

        return campaign

    async def add_content_piece(
        self,
        campaign_id: str,
        content_data: Dict[str, Any]
    ) -> ContentPiece:
        """
        Add content piece to campaign.

        Args:
            campaign_id: Campaign ID
            content_data: Content configuration

        Returns:
            Created ContentPiece object
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        content = ContentPiece(**content_data)
        content.campaign_id = campaign_id
        content.updated_at = datetime.utcnow()

        campaign.content_pieces.append(content)
        campaign.updated_at = datetime.utcnow()

        await self._save_campaign(campaign)

        logger.info(
            "Content piece added",
            campaign_id=campaign_id,
            content_id=content.id
        )

        return content

    async def update_content_status(
        self,
        campaign_id: str,
        content_id: str,
        new_status: ContentStatus,
        new_stage: Optional[WorkflowStage] = None
    ) -> ContentPiece:
        """
        Update content piece status and stage.

        Args:
            campaign_id: Campaign ID
            content_id: Content piece ID
            new_status: New status
            new_stage: Optional new workflow stage

        Returns:
            Updated ContentPiece
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        content = None
        for cp in campaign.content_pieces:
            if cp.id == content_id:
                content = cp
                break

        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Update status
        old_status = content.status
        content.status = new_status

        if new_stage:
            content.current_stage = new_stage

        # Add to workflow history
        content.workflow_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_status": old_status.value,
            "to_status": new_status.value,
            "stage": new_stage.value if new_stage else content.current_stage.value,
        })

        content.updated_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()

        await self._save_campaign(campaign)

        logger.info(
            "Content status updated",
            content_id=content_id,
            old_status=old_status.value,
            new_status=new_status.value
        )

        return content

    async def schedule_content(
        self,
        campaign_id: str,
        content_id: str,
        platform: str,
        scheduled_time: datetime
    ) -> ContentCalendarEntry:
        """
        Schedule content for publishing.

        Args:
            campaign_id: Campaign ID
            content_id: Content piece ID
            platform: Target platform
            scheduled_time: When to publish

        Returns:
            ContentCalendarEntry
        """
        entry = ContentCalendarEntry(
            campaign_id=campaign_id,
            content_id=content_id,
            platform=platform,
            scheduled_time=scheduled_time,
            status="scheduled",
        )

        self.calendar.append(entry)
        await self._save_calendar()

        # Update content status
        await self.update_content_status(
            campaign_id,
            content_id,
            ContentStatus.SCHEDULED,
            WorkflowStage.SCHEDULING
        )

        logger.info(
            "Content scheduled",
            content_id=content_id,
            platform=platform,
            time=scheduled_time.isoformat()
        )

        return entry

    async def get_calendar_entries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        campaign_id: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[ContentCalendarEntry]:
        """
        Get calendar entries with optional filters.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            campaign_id: Filter by campaign
            platform: Filter by platform

        Returns:
            List of calendar entries
        """
        entries = self.calendar

        if start_date:
            entries = [e for e in entries if e.scheduled_time >= start_date]

        if end_date:
            entries = [e for e in entries if e.scheduled_time <= end_date]

        if campaign_id:
            entries = [e for e in entries if e.campaign_id == campaign_id]

        if platform:
            entries = [e for e in entries if e.platform == platform]

        return sorted(entries, key=lambda e: e.scheduled_time)

    async def add_asset(
        self,
        asset: ContentAsset,
        file_path: Path,
        campaign_ids: Optional[List[str]] = None
    ) -> AssetLibraryEntry:
        """
        Add asset to library.

        Args:
            asset: Asset object
            file_path: Path to asset file
            campaign_ids: Optional associated campaigns

        Returns:
            AssetLibraryEntry
        """
        # Get file size
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Copy to assets directory
        storage_path = self.assets_dir / f"{asset.id}{file_path.suffix}"
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, storage_path)

        entry = AssetLibraryEntry(
            asset=asset,
            campaign_ids=campaign_ids or [],
            file_size=file_size,
            storage_path=str(storage_path),
            tags=asset.tags,
        )

        self.asset_library[asset.id] = entry
        await self._save_asset_library()

        logger.info("Asset added to library", asset_id=asset.id, type=asset.type)

        return entry

    async def track_api_cost(
        self,
        campaign_id: str,
        provider: str,
        cost: float,
        operation: str
    ) -> None:
        """
        Track API usage cost for a campaign.

        Args:
            campaign_id: Campaign ID
            provider: Provider name (e.g., "openai", "elevenlabs")
            cost: Cost in dollars
            operation: Operation type (e.g., "tts", "image_gen")
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return

        # Update campaign costs
        if provider not in campaign.api_costs:
            campaign.api_costs[provider] = 0.0

        campaign.api_costs[provider] += cost
        campaign.budget_spent += cost
        campaign.updated_at = datetime.utcnow()

        await self._save_campaign(campaign)

        logger.info(
            "API cost tracked",
            campaign_id=campaign_id,
            provider=provider,
            cost=cost,
            total_spent=campaign.budget_spent
        )

    async def generate_campaign_calendar(
        self,
        campaign_id: str
    ) -> List[ContentCalendarEntry]:
        """
        Auto-generate publishing calendar for campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            List of generated calendar entries
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if not campaign.start_date or not campaign.end_date:
            raise ValueError("Campaign must have start and end dates")

        entries = []
        current_date = campaign.start_date

        # Determine posting frequency
        if campaign.frequency == "daily":
            delta = timedelta(days=1)
        elif campaign.frequency == "every-other-day":
            delta = timedelta(days=2)
        elif campaign.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            delta = timedelta(days=2)  # Default

        # Generate schedule
        content_index = 0
        while current_date <= campaign.end_date and content_index < len(campaign.content_pieces):
            content = campaign.content_pieces[content_index]

            # Schedule for each platform
            for platform in content.platforms:
                entry = await self.schedule_content(
                    campaign_id,
                    content.id,
                    platform,
                    current_date
                )
                entries.append(entry)

            current_date += delta
            content_index += 1

        logger.info(
            "Campaign calendar generated",
            campaign_id=campaign_id,
            entries_count=len(entries)
        )

        return entries

    async def _save_campaign(self, campaign: Campaign) -> None:
        """Save campaign to storage."""
        file_path = self.campaigns_dir / f"{campaign.id}.json"
        with open(file_path, "w") as f:
            json.dump(campaign.to_dict(), f, indent=2)

    async def _load_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Load campaign from storage."""
        file_path = self.campaigns_dir / f"{campaign_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return Campaign.from_dict(data)
        except Exception as e:
            logger.error("Failed to load campaign", campaign_id=campaign_id, error=str(e))
            return None

    async def _save_calendar(self) -> None:
        """Save calendar to storage."""
        file_path = self.campaigns_dir / "calendar.json"
        data = [
            {
                "id": e.id,
                "campaign_id": e.campaign_id,
                "content_id": e.content_id,
                "platform": e.platform,
                "scheduled_time": e.scheduled_time.isoformat(),
                "status": e.status,
                "published_time": e.published_time.isoformat() if e.published_time else None,
                "publish_result": e.publish_result,
            }
            for e in self.calendar
        ]
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    async def _save_asset_library(self) -> None:
        """Save asset library to storage."""
        file_path = self.assets_dir / "library.json"
        data = {
            asset_id: {
                "asset": entry.asset.__dict__,
                "campaign_ids": entry.campaign_ids,
                "usage_count": entry.usage_count,
                "file_size": entry.file_size,
                "storage_path": entry.storage_path,
                "tags": entry.tags,
                "search_keywords": entry.search_keywords,
            }
            for asset_id, entry in self.asset_library.items()
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
