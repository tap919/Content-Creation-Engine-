"""
Natural Language Processing Tools

Provides wrappers for:
- spaCy: NLP for text processing and hashtag extraction
"""

from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# spaCy import (optional)
try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy")


class SpacyTool:
    """
    spaCy wrapper for NLP tasks.

    Provides methods for:
    - Keyword extraction for hashtags
    - Named entity recognition
    - Text summarization (extractive)
    - Part-of-speech tagging
    """

    # Valid spaCy model name pattern (e.g., en_core_web_sm, en_core_web_md, etc.)
    VALID_MODEL_PATTERN = r"^[a-z]{2}_[a-z]+_[a-z]+_[a-z]{2,}$"

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize spaCy tool.

        Args:
            model_name: spaCy model to use (default: en_core_web_sm)

        Raises:
            ValueError: If model_name doesn't match expected spaCy model naming pattern
        """
        import re

        if not re.match(self.VALID_MODEL_PATTERN, model_name):
            raise ValueError(
                f"Invalid spaCy model name: {model_name}. "
                "Expected format like 'en_core_web_sm', 'en_core_web_md', etc."
            )
        self.model_name = model_name
        self._nlp = None

    @property
    def available(self) -> bool:
        """Check if spaCy is available."""
        return SPACY_AVAILABLE

    def _load_model(self):
        """Lazy load the spaCy model."""
        if self._nlp is None and SPACY_AVAILABLE:
            try:
                logger.info("Loading spaCy model", model=self.model_name)
                self._nlp = spacy.load(self.model_name)
            except OSError:
                logger.warning(
                    "spaCy model not found, attempting download",
                    model=self.model_name,
                )
                try:
                    import subprocess

                    subprocess.run(
                        ["python", "-m", "spacy", "download", self.model_name],
                        check=True,
                        timeout=300,
                    )
                    self._nlp = spacy.load(self.model_name)
                except Exception as e:
                    logger.error("Failed to download spaCy model", error=str(e))
                    return None
        return self._nlp

    def extract_keywords(
        self,
        text: str,
        top_n: int = 10,
        include_verbs: bool = False,
    ) -> Optional[list[str]]:
        """
        Extract keywords from text for hashtag generation.

        Args:
            text: Input text
            top_n: Number of top keywords to return
            include_verbs: Include verbs in keywords

        Returns:
            List of keywords or None if failed
        """
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return None

        try:
            nlp = self._load_model()
            if nlp is None:
                return None

            doc = nlp(text)

            # POS tags to include
            pos_tags = ["NOUN", "PROPN"]
            if include_verbs:
                pos_tags.append("VERB")

            # Extract and count keywords
            keyword_counts: dict[str, int] = {}
            for token in doc:
                if token.pos_ in pos_tags and not token.is_stop and len(token.text) > 2:
                    word = token.lemma_.lower()
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Sort by frequency and return top N
            sorted_keywords = sorted(
                keyword_counts.items(), key=lambda x: x[1], reverse=True
            )
            keywords = [word for word, _ in sorted_keywords[:top_n]]

            logger.info("Keywords extracted", text_length=len(text), count=len(keywords))
            return keywords
        except Exception as e:
            logger.error("Keyword extraction failed", error=str(e))
            return None

    def generate_hashtags(
        self,
        text: str,
        max_hashtags: int = 5,
        prefix: str = "#",
    ) -> Optional[list[str]]:
        """
        Generate hashtags from text.

        Args:
            text: Input text
            max_hashtags: Maximum number of hashtags
            prefix: Hashtag prefix (default: #)

        Returns:
            List of hashtags or None if failed
        """
        keywords = self.extract_keywords(text, top_n=max_hashtags)
        if keywords is None:
            return None

        # Convert keywords to hashtags
        hashtags = []
        for keyword in keywords:
            # Remove spaces and special characters, capitalize
            hashtag = keyword.replace(" ", "").replace("-", "")
            hashtag = prefix + hashtag
            hashtags.append(hashtag)

        logger.info("Hashtags generated", count=len(hashtags))
        return hashtags

    def extract_entities(self, text: str) -> Optional[list[dict]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of entity dicts with 'text', 'label', 'start', 'end' or None if failed
        """
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return None

        try:
            nlp = self._load_model()
            if nlp is None:
                return None

            doc = nlp(text)
            entities = []

            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })

            logger.info("Entities extracted", text_length=len(text), count=len(entities))
            return entities
        except Exception as e:
            logger.error("Entity extraction failed", error=str(e))
            return None

    def extractive_summary(
        self,
        text: str,
        num_sentences: int = 3,
    ) -> Optional[str]:
        """
        Create extractive summary of text.

        Args:
            text: Input text
            num_sentences: Number of sentences in summary

        Returns:
            Summary text or None if failed
        """
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return None

        try:
            nlp = self._load_model()
            if nlp is None:
                return None

            doc = nlp(text)

            # Score sentences based on keyword density
            sentences = list(doc.sents)
            if len(sentences) <= num_sentences:
                return text

            # Get keyword frequencies
            keyword_counts: dict[str, int] = {}
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN", "VERB"] and not token.is_stop:
                    word = token.lemma_.lower()
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Score sentences
            sentence_scores = []
            for sent in sentences:
                score = 0
                for token in sent:
                    if token.lemma_.lower() in keyword_counts:
                        score += keyword_counts[token.lemma_.lower()]
                sentence_scores.append((sent, score))

            # Get top sentences by score, maintaining order
            sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
            top_sentences = sorted_sentences[:num_sentences]

            # Sort by original position
            top_sentences.sort(key=lambda x: x[0].start)
            summary = " ".join([sent.text for sent, _ in top_sentences])

            logger.info(
                "Summary created",
                original_length=len(text),
                summary_length=len(summary),
            )
            return summary
        except Exception as e:
            logger.error("Summarization failed", error=str(e))
            return None

    def analyze_sentiment_basic(self, text: str) -> Optional[dict]:
        """
        Basic sentiment analysis using lexical features.

        WARNING: This is a placeholder implementation using a simple word-matching
        approach with a very limited vocabulary. It is NOT suitable for production
        use and will produce unreliable results. For accurate sentiment analysis,
        use a dedicated sentiment model such as:
        - TextBlob
        - VADER (Valence Aware Dictionary and sEntiment Reasoner)
        - Hugging Face transformers (e.g., distilbert-base-uncased-finetuned-sst-2-english)
        - spaCy's textcat component with a trained model

        Args:
            text: Input text

        Returns:
            Dict with basic text statistics and a rough sentiment indicator,
            or None if failed. The sentiment_score is a very rough approximation
            and should not be relied upon for any critical decisions.
        """
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return None

        try:
            nlp = self._load_model()
            if nlp is None:
                return None

            doc = nlp(text)

            # Count positive/negative words (basic approach)
            # WARNING: This is a very limited word list and should NOT be used
            # for production sentiment analysis. Use a proper sentiment model instead.
            positive_words = {
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "fantastic",
                "love",
                "best",
                "happy",
                "positive",
                "success",
                "win",
                "beautiful",
            }
            negative_words = {
                "bad",
                "terrible",
                "awful",
                "horrible",
                "hate",
                "worst",
                "sad",
                "negative",
                "fail",
                "lose",
                "ugly",
                "poor",
                "wrong",
            }

            positive_count = 0
            negative_count = 0

            for token in doc:
                word = token.lemma_.lower()
                if word in positive_words:
                    positive_count += 1
                elif word in negative_words:
                    negative_count += 1

            total = positive_count + negative_count
            if total == 0:
                sentiment_score = 0.0
            else:
                sentiment_score = (positive_count - negative_count) / total

            analysis = {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "sentiment_score": sentiment_score,  # -1 to 1 (UNRELIABLE - see docstring)
                "word_count": len(doc),
                "sentence_count": len(list(doc.sents)),
                "_warning": "This is a basic placeholder. Use a proper sentiment model for production.",
            }

            logger.info("Sentiment analyzed", text_length=len(text))
            return analysis
        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e))
            return None

    def get_pos_tags(self, text: str) -> Optional[list[dict]]:
        """
        Get part-of-speech tags for text.

        Args:
            text: Input text

        Returns:
            List of token dicts with 'text', 'pos', 'tag', 'lemma' or None if failed
        """
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return None

        try:
            nlp = self._load_model()
            if nlp is None:
                return None

            doc = nlp(text)
            tokens = []

            for token in doc:
                tokens.append({
                    "text": token.text,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "lemma": token.lemma_,
                })

            logger.info("POS tags extracted", text_length=len(text), token_count=len(tokens))
            return tokens
        except Exception as e:
            logger.error("POS tagging failed", error=str(e))
            return None
