"""
AI-Powered Content Moderation & Classification
Machine learning-based text analysis and content filtering
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from pydantic import BaseModel
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS & ENUMS
# ============================================================================

class ContentSeverity(str, Enum):
    """Content severity levels"""
    CLEAN = "clean"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentCategory(str, Enum):
    """Content categories"""
    SPAM = "spam"
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    MISINFORMATION = "misinformation"
    ADULT_CONTENT = "adult_content"
    VIOLENCE = "violence"
    PHISHING = "phishing"
    CLEAN = "clean"


class ModerationResult(BaseModel):
    """Result of content moderation"""
    message_id: int
    user_id: int
    group_id: int
    content: str
    severity: ContentSeverity
    categories: List[ContentCategory]
    confidence: float
    detected_keywords: List[str]
    suggested_action: str
    flagged: bool
    hash: str  # For deduplication


class UserBehaviorProfile(BaseModel):
    """User behavior analysis profile"""
    user_id: int
    group_id: int
    message_count: int
    average_message_length: float
    spam_score: float
    profanity_score: float
    toxicity_score: float
    last_moderation_action: Optional[str] = None
    risk_level: str  # "safe", "medium", "high", "critical"
    is_bot: bool = False


# ============================================================================
# CONTENT MODERATION ENGINE
# ============================================================================

class ModerationEngine:
    """AI-like content moderation and analysis"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Content filters
        self.spam_keywords = self._load_spam_keywords()
        self.profanity_keywords = self._load_profanity_keywords()
        self.toxic_patterns = self._load_toxic_patterns()
        self.phishing_patterns = self._load_phishing_patterns()
        
        # User behavior cache
        self.user_profiles: Dict[int, UserBehaviorProfile] = {}
    
    async def analyze_message(
        self,
        message_id: int,
        user_id: int,
        group_id: int,
        content: str
    ) -> ModerationResult:
        """
        Comprehensive message analysis
        Returns moderation result with severity and recommended action
        """
        
        # Preprocess content
        processed_content = self._preprocess_text(content)
        
        # Check for various categories
        categories = []
        scores = {}
        
        # Spam detection
        spam_score = self._detect_spam(processed_content)
        scores["spam"] = spam_score
        if spam_score > 0.6:
            categories.append(ContentCategory.SPAM)
        
        # Profanity detection
        profanity_score, profanity_keywords = self._detect_profanity(processed_content)
        scores["profanity"] = profanity_score
        if profanity_score > 0.5:
            categories.append(ContentCategory.PROFANITY)
        
        # Hate speech detection
        hate_score = self._detect_hate_speech(processed_content)
        scores["hate_speech"] = hate_score
        if hate_score > 0.7:
            categories.append(ContentCategory.HATE_SPEECH)
        
        # Harassment detection
        harassment_score = self._detect_harassment(processed_content)
        scores["harassment"] = harassment_score
        if harassment_score > 0.6:
            categories.append(ContentCategory.HARASSMENT)
        
        # Phishing detection
        phishing_score = self._detect_phishing(content)
        scores["phishing"] = phishing_score
        if phishing_score > 0.8:
            categories.append(ContentCategory.PHISHING)
        
        # Adult content detection
        adult_score = self._detect_adult_content(processed_content)
        scores["adult"] = adult_score
        if adult_score > 0.7:
            categories.append(ContentCategory.ADULT_CONTENT)
        
        # Determine severity
        max_score = max(scores.values()) if scores else 0
        severity = self._calculate_severity(max_score, categories)
        
        # Determine suggested action
        suggested_action = self._get_suggested_action(severity, categories)
        
        # Create result
        result = ModerationResult(
            message_id=message_id,
            user_id=user_id,
            group_id=group_id,
            content=content[:100],  # Truncate for storage
            severity=severity,
            categories=categories,
            confidence=max_score,
            detected_keywords=profanity_keywords,
            suggested_action=suggested_action,
            flagged=severity in [ContentSeverity.HIGH, ContentSeverity.CRITICAL],
            hash=hashlib.md5(content.encode()).hexdigest()
        )
        
        # Update user profile
        await self._update_user_profile(user_id, group_id, result)
        
        # Log to database
        await self.db.db[self.db.db_name]["moderation_results"].insert_one(
            result.dict()
        )
        
        return result
    
    async def analyze_user_behavior(
        self,
        user_id: int,
        group_id: int
    ) -> UserBehaviorProfile:
        """Analyze user behavior patterns"""
        
        # Get recent messages
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "group_id": group_id,
                    "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "message_count": {"$sum": 1},
                    "avg_length": {"$avg": {"$strLenCP": "$content"}},
                    "spam_count": {
                        "$sum": {"$cond": [
                            {"$eq": ["$content_category", "spam"]}, 1, 0
                        ]}
                    },
                    "profanity_count": {
                        "$sum": {"$cond": [
                            {"$eq": ["$content_category", "profanity"]}, 1, 0
                        ]}
                    }
                }
            }
        ]
        
        try:
            result = await self.db.aggregate_actions(pipeline)
            data = result[0] if result else {}
        except:
            data = {}
        
        message_count = data.get("message_count", 0)
        avg_length = data.get("avg_length", 0)
        spam_count = data.get("spam_count", 0)
        profanity_count = data.get("profanity_count", 0)
        
        # Calculate scores
        spam_score = (spam_count / max(message_count, 1)) * 100
        profanity_score = (profanity_count / max(message_count, 1)) * 100
        toxicity_score = (spam_score + profanity_score) / 2
        
        # Determine risk level
        if toxicity_score > 50:
            risk_level = "critical"
        elif toxicity_score > 30:
            risk_level = "high"
        elif toxicity_score > 10:
            risk_level = "medium"
        else:
            risk_level = "safe"
        
        # Detect bot-like behavior (e.g., many short messages in short time)
        is_bot = self._detect_bot_behavior(message_count, avg_length)
        
        profile = UserBehaviorProfile(
            user_id=user_id,
            group_id=group_id,
            message_count=message_count,
            average_message_length=avg_length,
            spam_score=spam_score,
            profanity_score=profanity_score,
            toxicity_score=toxicity_score,
            risk_level=risk_level,
            is_bot=is_bot
        )
        
        self.user_profiles[user_id] = profile
        return profile
    
    async def detect_duplicate_content(
        self,
        group_id: int,
        content_hash: str
    ) -> Dict[str, Any]:
        """Detect duplicate/spam messages"""
        
        # Look for recent messages with same hash
        recent_messages = await self.db.db[self.db.db_name]["moderation_results"].find(
            {
                "group_id": group_id,
                "hash": content_hash,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            }
        ).to_list(None)
        
        return {
            "is_duplicate": len(recent_messages) > 0,
            "duplicate_count": len(recent_messages),
            "spam_score": min(len(recent_messages) * 0.3, 1.0)
        }
    
    def get_moderation_stats(self, group_id: int) -> Dict[str, Any]:
        """Get moderation statistics"""
        return {
            "total_analyzed": 0,  # Would query database
            "flagged": 0,
            "by_category": {},
            "by_severity": {},
            "user_profiles_tracked": len(self.user_profiles)
        }
    
    # ========================================================================
    # DETECTION METHODS
    # ========================================================================
    
    def _detect_spam(self, content: str) -> float:
        """Detect spam content (0.0 - 1.0)"""
        score = 0.0
        
        # Check for spam keywords
        spam_count = sum(1 for keyword in self.spam_keywords if keyword in content)
        score += min(spam_count * 0.1, 0.5)
        
        # Check for excessive links
        links = len(re.findall(r'http[s]?://\S+', content))
        if links > 2:
            score += 0.3
        
        # Check for excessive uppercase
        if len(content) > 5:
            uppercase_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if uppercase_ratio > 0.7:
                score += 0.2
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', content):
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_profanity(self, content: str) -> Tuple[float, List[str]]:
        """Detect profanity (0.0 - 1.0) and return detected words"""
        detected = []
        score = 0.0
        
        for keyword in self.profanity_keywords:
            if keyword in content:
                detected.append(keyword)
                score += 0.2
        
        return min(score, 1.0), detected
    
    def _detect_hate_speech(self, content: str) -> float:
        """Detect hate speech (0.0 - 1.0)"""
        score = 0.0
        
        # Check for offensive patterns
        offensive_patterns = [
            r'\b(bad|terrible|awful)\s+(people|group|nation|race)\b',
            r'(all|every)\s+(group|nation|race)\s+(is|are)',
        ]
        
        for pattern in offensive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.3
        
        return min(score, 1.0)
    
    def _detect_harassment(self, content: str) -> float:
        """Detect harassment (0.0 - 1.0)"""
        score = 0.0
        
        # Check for threatening language
        threats = [
            r'(will|gonna|should|should)\s+(beat|hit|kill|hurt)',
            r'go\s+(die|kill)\s+yourself',
            r'you\s+(are|is)\s+(stupid|dumb|idiot)',
        ]
        
        for threat in threats:
            if re.search(threat, content, re.IGNORECASE):
                score += 0.4
        
        return min(score, 1.0)
    
    def _detect_phishing(self, content: str) -> float:
        """Detect phishing attempts (0.0 - 1.0)"""
        score = 0.0
        
        # Check for phishing patterns
        phishing_patterns = [
            r'(verify|confirm|update).*account',
            r'click.*link.*(urgent|immediately)',
            r'(password|credit card|bank).*required',
        ]
        
        for pattern in phishing_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.3
        
        # Check for suspicious URLs
        suspicious_domains = ['bit.ly', 'tinyurl', 'short.link']
        for domain in suspicious_domains:
            if domain in content:
                score += 0.2
        
        return min(score, 1.0)
    
    def _detect_adult_content(self, content: str) -> float:
        """Detect adult content (0.0 - 1.0)"""
        # Simplified implementation
        adult_keywords = ['xxx', 'porn', '18+', 'nude']
        score = sum(0.25 for keyword in adult_keywords if keyword in content)
        return min(score, 1.0)
    
    def _detect_bot_behavior(self, message_count: int, avg_length: float) -> bool:
        """Detect bot-like behavior"""
        # Very high message count with very short messages
        return message_count > 50 and avg_length < 10
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove mentions and hashtags for some checks
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        return text
    
    def _calculate_severity(
        self,
        max_score: float,
        categories: List[ContentCategory]
    ) -> ContentSeverity:
        """Calculate overall severity"""
        
        # Critical categories override score
        if ContentCategory.PHISHING in categories:
            return ContentSeverity.CRITICAL
        
        if ContentCategory.HATE_SPEECH in categories and max_score > 0.7:
            return ContentSeverity.CRITICAL
        
        if max_score > 0.8:
            return ContentSeverity.CRITICAL
        elif max_score > 0.6:
            return ContentSeverity.HIGH
        elif max_score > 0.4:
            return ContentSeverity.MEDIUM
        elif max_score > 0.2:
            return ContentSeverity.LOW
        else:
            return ContentSeverity.CLEAN
    
    def _get_suggested_action(
        self,
        severity: ContentSeverity,
        categories: List[ContentCategory]
    ) -> str:
        """Get suggested moderation action"""
        
        if severity == ContentSeverity.CRITICAL:
            if ContentCategory.PHISHING in categories:
                return "ban_user"
            return "ban_user"
        
        elif severity == ContentSeverity.HIGH:
            if ContentCategory.HATE_SPEECH in categories:
                return "mute_24h"
            return "warn"
        
        elif severity == ContentSeverity.MEDIUM:
            return "delete_message"
        
        elif severity == ContentSeverity.LOW:
            return "review_later"
        
        else:
            return "no_action"
    
    def _load_spam_keywords(self) -> List[str]:
        """Load spam detection keywords"""
        return [
            "click here", "buy now", "limited offer", "act now",
            "free money", "bitcoin", "crypto", "forex", "casino"
        ]
    
    def _load_profanity_keywords(self) -> List[str]:
        """Load profanity keywords"""
        return [
            "damn", "hell", "crap"
            # Add more as needed
        ]
    
    def _load_toxic_patterns(self) -> List[str]:
        """Load toxic communication patterns"""
        return [
            r'you (are|r) (stupid|dumb)',
            r'(go|fuck)\s+yourself',
            r'kill\s+yourself'
        ]
    
    def _load_phishing_patterns(self) -> List[str]:
        """Load phishing detection patterns"""
        return [
            "verify your account",
            "click to confirm",
            "update payment information"
        ]
    
    async def _update_user_profile(
        self,
        user_id: int,
        group_id: int,
        result: ModerationResult
    ):
        """Update user behavior profile based on moderation result"""
        
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.message_count += 1
            
            if result.severity in [ContentSeverity.HIGH, ContentSeverity.CRITICAL]:
                profile.toxicity_score = min(profile.toxicity_score + 10, 100)
        
        # Store in database
        await self.db.db[self.db.db_name]["user_profiles"].update_one(
            {"user_id": user_id, "group_id": group_id},
            {"$inc": {"message_count": 1}},
            upsert=True
        )


# Import datetime at module level
from datetime import datetime, timedelta
