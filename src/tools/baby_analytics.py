"""
Baby Analytics - Simple self-hosted analytics (Google Analytics alternative)

Provides basic analytics tracking using SQLite:
- Page view tracking
- Event tracking
- Traffic source analysis
- Basic reporting
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class BabyAnalytics:
    """
    Simple self-hosted analytics system.
    
    Provides:
    - Event tracking
    - Page view counting
    - Traffic source analysis
    - User session tracking
    - Basic reporting
    """
    
    def __init__(self, db_path: str = "./analytics.db"):
        """
        Initialize Baby Analytics.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                page_url TEXT,
                user_agent TEXT,
                referrer TEXT,
                session_id TEXT,
                user_id TEXT,
                properties TEXT,
                ip_address TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                page_views INTEGER DEFAULT 0,
                events INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_events_timestamp 
            ON events(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_events_type 
            ON events(event_type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_events_page 
            ON events(page_url)
        ''')
        
        self.conn.commit()
    
    def track_event(
        self,
        event_type: str,
        page_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event (pageview, click, signup, etc.)
            page_url: Page URL
            user_agent: User agent string
            referrer: Referrer URL
            session_id: Session identifier
            user_id: User identifier
            properties: Additional event properties as dict
            ip_address: User IP address
            
        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Convert properties to JSON string
            import json
            properties_json = json.dumps(properties) if properties else None
            
            cursor.execute('''
                INSERT INTO events (
                    timestamp, event_type, page_url, user_agent,
                    referrer, session_id, user_id, properties, ip_address
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                event_type,
                page_url,
                user_agent,
                referrer,
                session_id,
                user_id,
                properties_json,
                ip_address
            ))
            
            # Update or create session
            is_pageview = (event_type == 'pageview')
            self._update_session(session_id, user_id, is_pageview)
            
            self.conn.commit()
            
            logger.debug("Event tracked", event_type=event_type, session=session_id)
            return True
            
        except Exception as e:
            logger.error("Track event failed", error=str(e))
            return False
    
    def _update_session(self, session_id: str, user_id: Optional[str] = None, is_pageview: bool = False):
        """Update or create session record."""
        cursor = self.conn.cursor()
        
        # Increment page_views if this is a pageview event
        pageview_increment = 1 if is_pageview else 0
        
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id, start_time, last_activity, page_views, events)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(session_id) DO UPDATE SET
                last_activity = ?,
                page_views = page_views + ?,
                events = events + 1
        ''', (session_id, user_id, datetime.now(), datetime.now(), pageview_increment, datetime.now(), pageview_increment))
    
    def track_pageview(
        self,
        page_url: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track a page view (convenience method).
        
        Args:
            page_url: Page URL
            session_id: Session identifier
            user_id: User identifier
            referrer: Referrer URL
            user_agent: User agent
            
        Returns:
            True if successful
        """
        return self.track_event(
            'pageview',
            page_url=page_url,
            session_id=session_id,
            user_id=user_id,
            referrer=referrer,
            user_agent=user_agent
        )
    
    def get_page_views(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get page view statistics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of page view stats
        """
        try:
            cursor = self.conn.cursor()
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            cursor.execute('''
                SELECT 
                    page_url,
                    COUNT(*) as views,
                    COUNT(DISTINCT session_id) as unique_views
                FROM events
                WHERE event_type = 'pageview'
                    AND timestamp BETWEEN ? AND ?
                GROUP BY page_url
                ORDER BY views DESC
                LIMIT ?
            ''', (start_date, end_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error("Get page views failed", error=str(e))
            return []
    
    def get_traffic_sources(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Analyze traffic sources.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of traffic source stats
        """
        try:
            cursor = self.conn.cursor()
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            cursor.execute('''
                SELECT 
                    COALESCE(referrer, 'Direct') as source,
                    COUNT(*) as visits,
                    COUNT(DISTINCT session_id) as unique_visitors
                FROM events
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY referrer
                ORDER BY visits DESC
                LIMIT ?
            ''', (start_date, end_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error("Get traffic sources failed", error=str(e))
            return []
    
    def get_events_by_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get events of specific type.
        
        Args:
            event_type: Event type to filter
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of events
        """
        try:
            cursor = self.conn.cursor()
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            cursor.execute('''
                SELECT *
                FROM events
                WHERE event_type = ?
                    AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (event_type, start_date, end_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error("Get events by type failed", error=str(e))
            return []
    
    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for date range.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Summary statistics dict
        """
        try:
            cursor = self.conn.cursor()
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Total events
            cursor.execute('''
                SELECT COUNT(*) as total_events
                FROM events
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_date, end_date))
            total_events = cursor.fetchone()['total_events']
            
            # Total page views
            cursor.execute('''
                SELECT COUNT(*) as pageviews
                FROM events
                WHERE event_type = 'pageview'
                    AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date))
            pageviews = cursor.fetchone()['pageviews']
            
            # Unique sessions
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) as unique_sessions
                FROM events
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_date, end_date))
            unique_sessions = cursor.fetchone()['unique_sessions']
            
            # Unique users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as unique_users
                FROM events
                WHERE user_id IS NOT NULL
                    AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date))
            unique_users = cursor.fetchone()['unique_users']
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_events': total_events,
                'pageviews': pageviews,
                'unique_sessions': unique_sessions,
                'unique_users': unique_users,
                'avg_events_per_session': total_events / unique_sessions if unique_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error("Get summary failed", error=str(e))
            return {}
    
    def get_popular_pages(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get most popular pages.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of popular pages
        """
        return self.get_page_views(start_date, end_date, limit)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
