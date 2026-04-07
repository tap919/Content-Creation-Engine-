"""
Unified Social Media Distribution Manager.

Handles publishing to multiple platforms through their APIs.
"""

import structlog
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)


class SocialMediaPlatform(ABC):
    """Base class for social media platform integrations."""

    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize platform connection.

        Args:
            credentials: Platform-specific credentials
        """
        self.credentials = credentials
        self.platform_name = "unknown"

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the platform.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    async def publish_video(
        self,
        video_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish video to platform.

        Args:
            video_path: Path to video file
            caption: Video caption/description
            options: Platform-specific options

        Returns:
            Dictionary with publish result including post ID
        """
        pass

    @abstractmethod
    async def publish_image(
        self,
        image_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish image to platform.

        Args:
            image_path: Path to image file
            caption: Image caption
            options: Platform-specific options

        Returns:
            Dictionary with publish result
        """
        pass

    @abstractmethod
    async def get_analytics(
        self,
        post_id: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a post.

        Args:
            post_id: Platform-specific post ID

        Returns:
            Dictionary with analytics data
        """
        pass


class YouTubePlatform(SocialMediaPlatform):
    """YouTube Data API v3 integration."""

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "youtube"
        self.youtube = None

    async def authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            # In production, use OAuth2 flow
            # For now, using API key for read operations
            api_key = self.credentials.get("api_key")
            if api_key:
                self.youtube = build("youtube", "v3", developerKey=api_key)
                logger.info("YouTube API authenticated (API key)")
                return True

            # Full OAuth2 for upload
            creds = Credentials(
                token=self.credentials.get("access_token"),
                refresh_token=self.credentials.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.credentials.get("client_id"),
                client_secret=self.credentials.get("client_secret")
            )
            self.youtube = build("youtube", "v3", credentials=creds)
            logger.info("YouTube API authenticated (OAuth2)")
            return True

        except ImportError:
            logger.error("google-api-python-client not installed")
            return False
        except Exception as e:
            logger.error("YouTube authentication failed", error=str(e))
            return False

    async def publish_video(
        self,
        video_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload video to YouTube."""
        if not self.youtube:
            raise RuntimeError("YouTube not authenticated")

        try:
            from googleapiclient.http import MediaFileUpload

            title = options.get("title", "Video Upload") if options else "Video Upload"
            description = caption
            category = options.get("category_id", "22") if options else "22"  # People & Blogs
            privacy = options.get("privacy", "public") if options else "public"
            tags = options.get("tags", []) if options else []

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": False,
                }
            }

            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = request.execute()

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            logger.info("Video uploaded to YouTube", video_id=video_id)

            return {
                "success": True,
                "platform": "youtube",
                "post_id": video_id,
                "url": video_url,
                "response": response,
            }

        except Exception as e:
            logger.error("YouTube video upload failed", error=str(e))
            return {
                "success": False,
                "platform": "youtube",
                "error": str(e),
            }

    async def publish_image(
        self,
        image_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """YouTube doesn't support standalone image posts."""
        return {
            "success": False,
            "platform": "youtube",
            "error": "YouTube does not support image-only posts",
        }

    async def get_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get video analytics from YouTube."""
        if not self.youtube:
            raise RuntimeError("YouTube not authenticated")

        try:
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=post_id
            )
            response = request.execute()

            if not response["items"]:
                return {"error": "Video not found"}

            item = response["items"][0]
            stats = item["statistics"]

            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "shares": 0,  # Not available in API
                "platform": "youtube",
            }

        except Exception as e:
            logger.error("Failed to get YouTube analytics", error=str(e))
            return {"error": str(e)}


class InstagramPlatform(SocialMediaPlatform):
    """Instagram Graph API integration (Business/Creator accounts)."""

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "instagram"
        self.access_token = credentials.get("access_token")
        self.instagram_account_id = credentials.get("instagram_account_id")

    async def authenticate(self) -> bool:
        """Verify Instagram credentials."""
        if not self.access_token or not self.instagram_account_id:
            logger.error("Instagram credentials incomplete")
            return False

        try:
            import httpx
            # Verify token
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{self.instagram_account_id}",
                    params={"access_token": self.access_token}
                )
                if response.status_code == 200:
                    logger.info("Instagram authenticated")
                    return True

        except Exception as e:
            logger.error("Instagram authentication failed", error=str(e))

        return False

    async def publish_video(
        self,
        video_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish video to Instagram (Reels or Feed)."""
        try:
            import httpx

            # Step 1: Upload video to hosting (Instagram requires a public URL)
            # In production, upload to S3 or CDN first
            video_url = options.get("video_url") if options else None
            if not video_url:
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "video_url required (Instagram needs public URL)",
                }

            is_reel = options.get("is_reel", True) if options else True

            async with httpx.AsyncClient() as client:
                # Create media container
                container_data = {
                    "access_token": self.access_token,
                    "caption": caption,
                }

                if is_reel:
                    container_data["media_type"] = "REELS"
                    container_data["video_url"] = video_url
                    endpoint = f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media"
                else:
                    container_data["media_type"] = "VIDEO"
                    container_data["video_url"] = video_url
                    endpoint = f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media"

                response = await client.post(endpoint, data=container_data)
                response.raise_for_status()
                container_id = response.json()["id"]

                # Publish container
                publish_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token,
                    }
                )
                publish_response.raise_for_status()
                media_id = publish_response.json()["id"]

                logger.info("Video published to Instagram", media_id=media_id)

                return {
                    "success": True,
                    "platform": "instagram",
                    "post_id": media_id,
                    "url": f"https://www.instagram.com/p/{media_id}/",
                }

        except Exception as e:
            logger.error("Instagram video publish failed", error=str(e))
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e),
            }

    async def publish_image(
        self,
        image_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish image to Instagram."""
        try:
            import httpx

            image_url = options.get("image_url") if options else None
            if not image_url:
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "image_url required (Instagram needs public URL)",
                }

            async with httpx.AsyncClient() as client:
                # Create media container
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media",
                    data={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.access_token,
                    }
                )
                response.raise_for_status()
                container_id = response.json()["id"]

                # Publish
                publish_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token,
                    }
                )
                publish_response.raise_for_status()
                media_id = publish_response.json()["id"]

                return {
                    "success": True,
                    "platform": "instagram",
                    "post_id": media_id,
                    "url": f"https://www.instagram.com/p/{media_id}/",
                }

        except Exception as e:
            logger.error("Instagram image publish failed", error=str(e))
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e),
            }

    async def get_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get Instagram post insights."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{post_id}/insights",
                    params={
                        "metric": "impressions,reach,engagement,likes,comments,shares,saves",
                        "access_token": self.access_token,
                    }
                )
                response.raise_for_status()
                data = response.json()["data"]

                analytics = {
                    "views": 0,
                    "reach": 0,
                    "engagement": 0,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "saves": 0,
                    "platform": "instagram",
                }

                for metric in data:
                    name = metric["name"]
                    value = metric["values"][0]["value"] if metric["values"] else 0
                    if name == "impressions":
                        analytics["views"] = value
                    elif name in analytics:
                        analytics[name] = value

                return analytics

        except Exception as e:
            logger.error("Failed to get Instagram analytics", error=str(e))
            return {"error": str(e)}


class TwitterPlatform(SocialMediaPlatform):
    """Twitter/X API v2 integration."""

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "twitter"
        self.bearer_token = credentials.get("bearer_token")
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.access_token = credentials.get("access_token")
        self.access_secret = credentials.get("access_secret")

    async def authenticate(self) -> bool:
        """Verify Twitter credentials."""
        if not self.bearer_token:
            logger.error("Twitter bearer token missing")
            return False

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {self.bearer_token}"}
                )
                if response.status_code == 200:
                    logger.info("Twitter authenticated")
                    return True

        except Exception as e:
            logger.error("Twitter authentication failed", error=str(e))

        return False

    async def publish_video(
        self,
        video_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish video tweet."""
        try:
            import tweepy

            # Use tweepy for media upload
            client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            api = tweepy.API(tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret
            ))

            # Upload video
            media = api.media_upload(str(video_path), media_category="tweet_video")

            # Create tweet
            response = client.create_tweet(
                text=caption,
                media_ids=[media.media_id]
            )

            tweet_id = response.data["id"]
            url = f"https://twitter.com/i/web/status/{tweet_id}"

            logger.info("Video tweeted", tweet_id=tweet_id)

            return {
                "success": True,
                "platform": "twitter",
                "post_id": tweet_id,
                "url": url,
            }

        except ImportError:
            logger.error("tweepy not installed. Install with: pip install tweepy")
            return {"success": False, "platform": "twitter", "error": "tweepy not installed"}
        except Exception as e:
            logger.error("Twitter video post failed", error=str(e))
            return {
                "success": False,
                "platform": "twitter",
                "error": str(e),
            }

    async def publish_image(
        self,
        image_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish image tweet."""
        try:
            import tweepy

            client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            api = tweepy.API(tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret
            ))

            # Upload image
            media = api.media_upload(str(image_path))

            # Create tweet
            response = client.create_tweet(
                text=caption,
                media_ids=[media.media_id]
            )

            tweet_id = response.data["id"]

            return {
                "success": True,
                "platform": "twitter",
                "post_id": tweet_id,
                "url": f"https://twitter.com/i/web/status/{tweet_id}",
            }

        except Exception as e:
            logger.error("Twitter image post failed", error=str(e))
            return {
                "success": False,
                "platform": "twitter",
                "error": str(e),
            }

    async def get_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get tweet metrics."""
        try:
            import tweepy

            client = tweepy.Client(bearer_token=self.bearer_token)

            tweet = client.get_tweet(
                post_id,
                tweet_fields=["public_metrics"]
            )

            metrics = tweet.data.public_metrics

            return {
                "views": metrics.get("impression_count", 0),
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0),
                "platform": "twitter",
            }

        except Exception as e:
            logger.error("Failed to get Twitter analytics", error=str(e))
            return {"error": str(e)}


class LinkedInPlatform(SocialMediaPlatform):
    """LinkedIn API integration."""

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "linkedin"
        self.access_token = credentials.get("access_token")
        self.person_id = credentials.get("person_id")

    async def authenticate(self) -> bool:
        """Verify LinkedIn credentials."""
        if not self.access_token:
            logger.error("LinkedIn access token missing")
            return False

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.linkedin.com/v2/me",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                if response.status_code == 200:
                    logger.info("LinkedIn authenticated")
                    return True

        except Exception as e:
            logger.error("LinkedIn authentication failed", error=str(e))

        return False

    async def publish_video(
        self,
        video_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish video to LinkedIn."""
        try:
            import httpx

            # LinkedIn video upload is complex, requires multiple steps
            # Simplified implementation
            return {
                "success": False,
                "platform": "linkedin",
                "error": "LinkedIn video upload requires multi-step process (not implemented in demo)",
            }

        except Exception as e:
            logger.error("LinkedIn video post failed", error=str(e))
            return {
                "success": False,
                "platform": "linkedin",
                "error": str(e),
            }

    async def publish_image(
        self,
        image_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish image to LinkedIn."""
        try:
            import httpx

            # Simplified - production needs image upload first
            async with httpx.AsyncClient() as client:
                post_data = {
                    "author": f"urn:li:person:{self.person_id}",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": caption
                            },
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }

                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=post_data
                )
                response.raise_for_status()
                post_id = response.headers.get("X-LinkedIn-Id", "")

                return {
                    "success": True,
                    "platform": "linkedin",
                    "post_id": post_id,
                }

        except Exception as e:
            logger.error("LinkedIn image post failed", error=str(e))
            return {
                "success": False,
                "platform": "linkedin",
                "error": str(e),
            }

    async def get_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get LinkedIn post analytics."""
        return {
            "error": "LinkedIn analytics requires additional API permissions",
            "platform": "linkedin",
        }


class UnifiedSocialMediaManager:
    """Unified manager for all social media platforms."""

    def __init__(self):
        """Initialize social media manager."""
        self.platforms: Dict[str, SocialMediaPlatform] = {}
        logger.info("Unified Social Media Manager initialized")

    async def add_platform(
        self,
        platform_name: str,
        credentials: Dict[str, str]
    ) -> bool:
        """
        Add and authenticate a platform.

        Args:
            platform_name: Platform identifier
            credentials: Platform credentials

        Returns:
            True if successfully added and authenticated
        """
        platform_map = {
            "youtube": YouTubePlatform,
            "instagram": InstagramPlatform,
            "twitter": TwitterPlatform,
            "linkedin": LinkedInPlatform,
        }

        if platform_name not in platform_map:
            logger.error("Unknown platform", platform=platform_name)
            return False

        platform = platform_map[platform_name](credentials)
        authenticated = await platform.authenticate()

        if authenticated:
            self.platforms[platform_name] = platform
            logger.info("Platform added", platform=platform_name)
            return True

        return False

    async def publish_content(
        self,
        platform: str,
        content_type: str,
        file_path: Path,
        caption: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish content to a platform.

        Args:
            platform: Platform name
            content_type: "video" or "image"
            file_path: Path to media file
            caption: Post caption
            options: Platform-specific options

        Returns:
            Publish result
        """
        if platform not in self.platforms:
            return {
                "success": False,
                "platform": platform,
                "error": "Platform not configured",
            }

        platform_obj = self.platforms[platform]

        if content_type == "video":
            return await platform_obj.publish_video(file_path, caption, options)
        elif content_type == "image":
            return await platform_obj.publish_image(file_path, caption, options)
        else:
            return {
                "success": False,
                "platform": platform,
                "error": f"Unsupported content type: {content_type}",
            }

    async def batch_publish(
        self,
        platforms: List[str],
        content_type: str,
        file_path: Path,
        captions: Dict[str, str],
        options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Publish to multiple platforms at once.

        Args:
            platforms: List of platform names
            content_type: "video" or "image"
            file_path: Path to media file
            captions: Platform-specific captions
            options: Platform-specific options

        Returns:
            Results for each platform
        """
        results = {}

        for platform in platforms:
            caption = captions.get(platform, captions.get("default", ""))
            platform_options = options.get(platform) if options else None

            result = await self.publish_content(
                platform,
                content_type,
                file_path,
                caption,
                platform_options
            )

            results[platform] = result

        return results

    async def get_all_analytics(
        self,
        post_ids: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get analytics from all platforms.

        Args:
            post_ids: Dictionary of platform: post_id

        Returns:
            Analytics for each platform
        """
        results = {}

        for platform, post_id in post_ids.items():
            if platform in self.platforms:
                analytics = await self.platforms[platform].get_analytics(post_id)
                results[platform] = analytics

        return results
