"""
Community Forums Service

Provides discussion forums for breeders to share knowledge.
Uses in-memory storage for demo purposes.
"""

from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4


class ForumsService:
    """In-memory forums service for demo."""
    
    def __init__(self):
        self.categories: dict = {}
        self.topics: dict = {}
        self.replies: dict = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize with demo categories and topics."""
        # Categories
        categories = [
            {"id": "cat-1", "name": "General Discussion", "description": "General breeding topics", "icon": "💬", "topic_count": 3},
            {"id": "cat-2", "name": "Breeding Techniques", "description": "Share and discuss breeding methods", "icon": "🌾", "topic_count": 2},
            {"id": "cat-3", "name": "Genomics & Markers", "description": "Molecular breeding discussions", "icon": "🧬", "topic_count": 2},
            {"id": "cat-4", "name": "Field Trials", "description": "Trial design and management", "icon": "🌱", "topic_count": 1},
            {"id": "cat-5", "name": "Data Analysis", "description": "Statistical methods and tools", "icon": "📊", "topic_count": 1},
            {"id": "cat-6", "name": "Software & Tools", "description": "Bijmantra tips and feature requests", "icon": "💻", "topic_count": 1},
        ]
        for cat in categories:
            self.categories[cat["id"]] = cat
        
        # Demo topics
        topics = [
            {
                "id": "topic-1",
                "category_id": "cat-1",
                "title": "Welcome to Bijmantra Community!",
                "content": "Welcome to the Bijmantra community forums! This is a place to share knowledge, ask questions, and connect with fellow plant breeders.\n\nFeel free to introduce yourself and share what crops you're working on!",
                "author": {"id": "user-1", "name": "Admin", "avatar": "🌱"},
                "created_at": "2025-12-01T10:00:00Z",
                "updated_at": "2025-12-01T10:00:00Z",
                "views": 156,
                "likes": 24,
                "reply_count": 5,
                "is_pinned": True,
                "is_closed": False,
                "tags": ["welcome", "introduction"],
            },
            {
                "id": "topic-2",
                "category_id": "cat-2",
                "title": "Best practices for backcross breeding?",
                "content": "I'm working on introgressing a disease resistance gene into an elite line. What's the optimal number of backcross generations? Should I use marker-assisted selection at each generation?\n\nCurrently planning BC3F2 but wondering if BC4 would be better for genome recovery.",
                "author": {"id": "user-2", "name": "Dr. Sarah Chen", "avatar": "👩‍🔬"},
                "created_at": "2025-12-05T14:30:00Z",
                "updated_at": "2025-12-06T09:15:00Z",
                "views": 89,
                "likes": 12,
                "reply_count": 8,
                "is_pinned": False,
                "is_closed": False,
                "tags": ["backcross", "MAS", "disease-resistance"],
            },
            {
                "id": "topic-3",
                "category_id": "cat-3",
                "title": "KASP vs SSR markers for MAS",
                "content": "We're setting up a new MAS program and debating between KASP and SSR markers. KASP seems more high-throughput but SSRs are more informative.\n\nWhat's your experience? Cost per data point is also a consideration.",
                "author": {"id": "user-3", "name": "Raj Patel", "avatar": "👨‍🔬"},
                "created_at": "2025-12-08T11:00:00Z",
                "updated_at": "2025-12-08T11:00:00Z",
                "views": 67,
                "likes": 8,
                "reply_count": 4,
                "is_pinned": False,
                "is_closed": False,
                "tags": ["markers", "KASP", "SSR", "genotyping"],
            },
            {
                "id": "topic-4",
                "category_id": "cat-4",
                "title": "Alpha-lattice vs RCBD for early generation trials",
                "content": "Running OYT with 500 entries. Should I use alpha-lattice or stick with RCBD? Field is relatively uniform but large.\n\nAlso, how many checks should I include?",
                "author": {"id": "user-4", "name": "Maria Santos", "avatar": "👩‍🌾"},
                "created_at": "2025-12-09T08:45:00Z",
                "updated_at": "2025-12-09T08:45:00Z",
                "views": 45,
                "likes": 6,
                "reply_count": 3,
                "is_pinned": False,
                "is_closed": False,
                "tags": ["trial-design", "alpha-lattice", "RCBD"],
            },
            {
                "id": "topic-5",
                "category_id": "cat-5",
                "title": "Heritability estimation methods comparison",
                "content": "I've been using ANOVA-based heritability but heard REML is better. Can someone explain the practical differences?\n\nAlso, how do you handle unbalanced data?",
                "author": {"id": "user-5", "name": "James Wilson", "avatar": "📊"},
                "created_at": "2025-12-10T07:30:00Z",
                "updated_at": "2025-12-10T07:30:00Z",
                "views": 32,
                "likes": 4,
                "reply_count": 2,
                "is_pinned": False,
                "is_closed": False,
                "tags": ["heritability", "REML", "statistics"],
            },
        ]
        for topic in topics:
            self.topics[topic["id"]] = topic
        
        # Demo replies
        replies = [
            {
                "id": "reply-1",
                "topic_id": "topic-2",
                "content": "For most traits, BC3 gives you about 93.75% recurrent parent genome recovery. BC4 gets you to 96.875%. If you're using markers for background selection, BC3 is usually sufficient.\n\nI'd recommend foreground selection at every generation and background selection at BC2 and BC3.",
                "author": {"id": "user-6", "name": "Dr. Michael Brown", "avatar": "🧬"},
                "created_at": "2025-12-05T16:00:00Z",
                "likes": 8,
            },
            {
                "id": "reply-2",
                "topic_id": "topic-2",
                "content": "Agree with Michael. Also consider the linkage drag around your target gene. If it's in a recombination-poor region, you might need more backcrosses or larger population sizes.",
                "author": {"id": "user-3", "name": "Raj Patel", "avatar": "👨‍🔬"},
                "created_at": "2025-12-05T17:30:00Z",
                "likes": 5,
            },
            {
                "id": "reply-3",
                "topic_id": "topic-3",
                "content": "We switched from SSRs to KASP last year. Cost per data point dropped from $2.50 to $0.80. Throughput increased 10x. For MAS where you just need presence/absence, KASP is the way to go.\n\nSSRs are still better for diversity studies where you need allele size information.",
                "author": {"id": "user-7", "name": "Lisa Zhang", "avatar": "🔬"},
                "created_at": "2025-12-08T14:00:00Z",
                "likes": 6,
            },
        ]
        for reply in replies:
            if reply["topic_id"] not in self.replies:
                self.replies[reply["topic_id"]] = []
            self.replies[reply["topic_id"]].append(reply)
    
    # Category methods
    def get_categories(self) -> list:
        """Get all categories."""
        return list(self.categories.values())
    
    def get_category(self, category_id: str) -> Optional[dict]:
        """Get a single category."""
        return self.categories.get(category_id)
    
    def create_category(self, name: str, description: str, icon: str = "💬") -> dict:
        """Create a new category."""
        category = {
            "id": f"cat-{uuid4().hex[:8]}",
            "name": name,
            "description": description,
            "icon": icon,
            "topic_count": 0,
        }
        self.categories[category["id"]] = category
        return category
    
    # Topic methods
    def get_topics(
        self,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> dict:
        """Get topics with filtering and pagination."""
        topics = list(self.topics.values())
        
        # Filter by category
        if category_id:
            topics = [t for t in topics if t["category_id"] == category_id]
        
        # Search
        if search:
            search_lower = search.lower()
            topics = [
                t for t in topics
                if search_lower in t["title"].lower() or search_lower in t["content"].lower()
            ]
        
        # Sort: pinned first, then by date
        topics.sort(key=lambda t: (not t["is_pinned"], t["created_at"]), reverse=True)
        
        # Paginate
        total = len(topics)
        start = page * page_size
        end = start + page_size
        topics = topics[start:end]
        
        return {
            "data": topics,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_topic(self, topic_id: str) -> Optional[dict]:
        """Get a single topic with replies."""
        topic = self.topics.get(topic_id)
        if not topic:
            return None
        
        # Increment views
        topic["views"] += 1
        
        # Get replies
        replies = self.replies.get(topic_id, [])
        
        return {
            **topic,
            "replies": replies,
        }
    
    def create_topic(
        self,
        category_id: str,
        title: str,
        content: str,
        author_id: str,
        author_name: str,
        tags: list[str] = None,
    ) -> dict:
        """Create a new topic."""
        now = datetime.now(UTC).isoformat() + "Z"
        topic = {
            "id": f"topic-{uuid4().hex[:8]}",
            "category_id": category_id,
            "title": title,
            "content": content,
            "author": {"id": author_id, "name": author_name, "avatar": "👤"},
            "created_at": now,
            "updated_at": now,
            "views": 0,
            "likes": 0,
            "reply_count": 0,
            "is_pinned": False,
            "is_closed": False,
            "tags": tags or [],
        }
        self.topics[topic["id"]] = topic
        
        # Update category count
        if category_id in self.categories:
            self.categories[category_id]["topic_count"] += 1
        
        return topic
    
    def update_topic(self, topic_id: str, **updates) -> Optional[dict]:
        """Update a topic."""
        topic = self.topics.get(topic_id)
        if not topic:
            return None
        
        allowed_fields = ["title", "content", "tags", "is_pinned", "is_closed"]
        for field in allowed_fields:
            if field in updates:
                topic[field] = updates[field]
        
        topic["updated_at"] = datetime.now(UTC).isoformat() + "Z"
        return topic
    
    def like_topic(self, topic_id: str) -> Optional[dict]:
        """Like a topic."""
        topic = self.topics.get(topic_id)
        if not topic:
            return None
        topic["likes"] += 1
        return topic
    
    # Reply methods
    def add_reply(
        self,
        topic_id: str,
        content: str,
        author_id: str,
        author_name: str,
    ) -> Optional[dict]:
        """Add a reply to a topic."""
        topic = self.topics.get(topic_id)
        if not topic or topic["is_closed"]:
            return None
        
        reply = {
            "id": f"reply-{uuid4().hex[:8]}",
            "topic_id": topic_id,
            "content": content,
            "author": {"id": author_id, "name": author_name, "avatar": "👤"},
            "created_at": datetime.now(UTC).isoformat() + "Z",
            "likes": 0,
        }
        
        if topic_id not in self.replies:
            self.replies[topic_id] = []
        self.replies[topic_id].append(reply)
        
        # Update topic
        topic["reply_count"] += 1
        topic["updated_at"] = reply["created_at"]
        
        return reply
    
    def like_reply(self, topic_id: str, reply_id: str) -> Optional[dict]:
        """Like a reply."""
        replies = self.replies.get(topic_id, [])
        for reply in replies:
            if reply["id"] == reply_id:
                reply["likes"] += 1
                return reply
        return None
    
    def get_stats(self) -> dict:
        """Get forum statistics."""
        total_topics = len(self.topics)
        total_replies = sum(len(r) for r in self.replies.values())
        total_views = sum(t["views"] for t in self.topics.values())
        
        return {
            "total_categories": len(self.categories),
            "total_topics": total_topics,
            "total_replies": total_replies,
            "total_views": total_views,
            "active_users": 7,  # Demo value
        }


# Singleton instance
_forums_service: Optional[ForumsService] = None


def get_forums_service() -> ForumsService:
    """Get or create the forums service singleton."""
    global _forums_service
    if _forums_service is None:
        _forums_service = ForumsService()
    return _forums_service
