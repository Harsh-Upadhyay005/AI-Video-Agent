"""
Global Video Analysis - Extract topics, concepts, and structure from entire transcript.
Uses map-reduce approach for long transcripts.
"""

import os
from typing import List, Dict, Tuple
from datetime import datetime

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    ChatMistralAI = None
    ChatPromptTemplate = None
    StrOutputParser = None
    RecursiveCharacterTextSplitter = None

from core.global_metadata import VideoMetadata, VideoSection


class GlobalVideoAnalyzer:
    """
    Analyzes entire video transcript to extract global information.
    Uses hierarchical map-reduce for long transcripts.
    """
    
    def __init__(self):
        """Initialize analyzer with LLM."""
        self.llm = None
        if ChatMistralAI is not None:
            try:
                self.llm = ChatMistralAI(
                    model="mistral-small-latest",
                    mistral_api_key=os.getenv("MISTRAL_API_KEY"),
                    temperature=0.3
                )
            except Exception as e:
                print(f"[GlobalAnalyzer] Warning: Could not initialize LLM: {e}")
    
    def analyze_video(
        self,
        video_id: str,
        source: str,
        source_type: str,
        transcript: str,
        title: str = "Untitled",
        duration: float = None
    ) -> VideoMetadata:
        """
        Analyze entire video transcript and extract global information.
        
        Args:
            video_id: Unique identifier for the video
            source: Source URL or filename
            source_type: youtube, mp3, mp4
            transcript: Complete transcript text
            title: Video title
            duration: Duration in seconds
            
        Returns:
            VideoMetadata with global information
        """
        print(f"[GlobalAnalyzer] Analyzing video: {video_id}")
        
        if not transcript or not transcript.strip():
            # Return minimal metadata for empty transcript
            return VideoMetadata(
                video_id=video_id,
                source=source,
                source_type=source_type,
                duration=duration,
                title=title,
                summary="No transcript available",
                topics=[],
                key_concepts=[],
                sections=[],
                created_at=datetime.now().isoformat(),
                transcript_length=0,
                chunk_count=0
            )
        
        # Split transcript into manageable chunks for analysis
        chunks = self._split_transcript(transcript)
        print(f"[GlobalAnalyzer] Split transcript into {len(chunks)} chunks")
        
        # Extract topics and concepts (map-reduce)
        if len(chunks) <= 3:
            # Short transcript: analyze directly
            topics, concepts = self._extract_topics_and_concepts_direct(transcript)
        else:
            # Long transcript: use map-reduce
            topics, concepts = self._extract_topics_and_concepts_mapreduce(chunks)
        
        # Generate overall summary
        summary = self._generate_summary(transcript[:8000])  # Use first part for summary
        
        # Identify sections (optional, for future enhancement)
        sections = []
        
        metadata = VideoMetadata(
            video_id=video_id,
            source=source,
            source_type=source_type,
            duration=duration,
            title=title,
            summary=summary,
            topics=topics,
            key_concepts=concepts,
            sections=sections,
            created_at=datetime.now().isoformat(),
            transcript_length=len(transcript),
            chunk_count=len(chunks)
        )
        
        print(f"[GlobalAnalyzer] Extracted {len(topics)} topics and {len(concepts)} concepts")
        return metadata
    
    def _split_transcript(self, transcript: str, chunk_size: int = 3000) -> List[str]:
        """Split transcript into chunks for processing."""
        if RecursiveCharacterTextSplitter is None:
            # Fallback: simple splitting
            words = transcript.split()
            chunks = []
            for i in range(0, len(words), 500):
                chunks.append(" ".join(words[i:i+500]))
            return chunks
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200
        )
        return splitter.split_text(transcript)
    
    def _extract_topics_and_concepts_direct(self, transcript: str) -> Tuple[List[str], List[str]]:
        """
        Extract topics and concepts from transcript directly (for short transcripts).
        
        Args:
            transcript: Full transcript text
            
        Returns:
            Tuple of (topics, concepts)
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return [], []
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing a video/audio transcript. Extract the main topics and key concepts discussed.

Topics: Broad subjects or themes discussed (e.g., "Machine Learning", "Data Processing", "Team Management")
Concepts: Specific ideas, techniques, or terms explained (e.g., "RAG", "Embeddings", "Vector Databases")

Respond in this exact format:
TOPICS:
- Topic 1
- Topic 2
- Topic 3

CONCEPTS:
- Concept 1
- Concept 2
- Concept 3

Only include topics/concepts that are actually discussed with some depth. Do not invent topics not present in the transcript."""),
            ("human", "Transcript:\n{transcript}")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"transcript": transcript[:6000]})  # Limit to avoid token limits
            
            return self._parse_topics_concepts(result)
        except Exception as e:
            print(f"[GlobalAnalyzer] Error extracting topics/concepts: {e}")
            return [], []
    
    def _extract_topics_and_concepts_mapreduce(self, chunks: List[str]) -> Tuple[List[str], List[str]]:
        """
        Extract topics and concepts using map-reduce for long transcripts.
        
        Args:
            chunks: List of transcript chunks
            
        Returns:
            Tuple of (topics, concepts)
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return [], []
        
        # MAP phase: Extract from each chunk
        map_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract the main topics and concepts from this transcript section.

Respond in this exact format:
TOPICS:
- Topic 1
- Topic 2

CONCEPTS:
- Concept 1
- Concept 2

Be concise. Only include topics/concepts clearly discussed in this section."""),
            ("human", "Transcript section:\n{chunk}")
        ])
        
        all_topics = []
        all_concepts = []
        
        # Process chunks in batches to avoid overloading
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            for chunk in batch[:10]:  # Limit to 10 chunks per batch
                try:
                    chain = map_prompt | self.llm | StrOutputParser()
                    result = chain.invoke({"chunk": chunk[:2000]})
                    topics, concepts = self._parse_topics_concepts(result)
                    all_topics.extend(topics)
                    all_concepts.extend(concepts)
                except Exception as e:
                    print(f"[GlobalAnalyzer] Error processing chunk: {e}")
                    continue
        
        # REDUCE phase: Deduplicate and consolidate
        topics = self._deduplicate_and_consolidate(all_topics)
        concepts = self._deduplicate_and_consolidate(all_concepts)
        
        # If we have too many, reduce further with LLM
        if len(topics) > 15 or len(concepts) > 15:
            topics, concepts = self._reduce_topics_concepts(topics, concepts)
        
        return topics, concepts
    
    def _parse_topics_concepts(self, llm_output: str) -> Tuple[List[str], List[str]]:
        """Parse LLM output to extract topics and concepts lists."""
        topics = []
        concepts = []
        
        lines = llm_output.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('TOPICS:'):
                current_section = 'topics'
                continue
            elif line.upper().startswith('CONCEPTS:'):
                current_section = 'concepts'
                continue
            
            if line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if item and current_section == 'topics':
                    topics.append(item)
                elif item and current_section == 'concepts':
                    concepts.append(item)
            elif line and current_section:  # Handle items without bullet points
                if current_section == 'topics' and len(line) < 100:
                    topics.append(line)
                elif current_section == 'concepts' and len(line) < 100:
                    concepts.append(line)
        
        return topics, concepts
    
    def _deduplicate_and_consolidate(self, items: List[str]) -> List[str]:
        """Remove duplicates and similar items."""
        # Simple deduplication: case-insensitive
        seen = set()
        result = []
        
        for item in items:
            item_lower = item.lower().strip()
            if item_lower and item_lower not in seen:
                seen.add(item_lower)
                result.append(item.strip())
        
        return result
    
    def _reduce_topics_concepts(self, topics: List[str], concepts: List[str]) -> Tuple[List[str], List[str]]:
        """
        Use LLM to reduce and consolidate topics/concepts list.
        
        Args:
            topics: List of topics
            concepts: List of concepts
            
        Returns:
            Tuple of (reduced_topics, reduced_concepts)
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return topics[:10], concepts[:10]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are consolidating a list of topics and concepts from a video.

Merge similar/duplicate items and keep only the most important and distinct ones.
Aim for 7-10 topics and 7-10 concepts.

Respond in this exact format:
TOPICS:
- Topic 1
- Topic 2

CONCEPTS:
- Concept 1
- Concept 2"""),
            ("human", "TOPICS:\n{topics}\n\nCONCEPTS:\n{concepts}")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "topics": "\n".join(f"- {t}" for t in topics),
                "concepts": "\n".join(f"- {c}" for c in concepts)
            })
            
            return self._parse_topics_concepts(result)
        except Exception as e:
            print(f"[GlobalAnalyzer] Error reducing topics/concepts: {e}")
            return topics[:10], concepts[:10]
    
    def _generate_summary(self, transcript_sample: str) -> str:
        """
        Generate brief overall summary.
        
        Args:
            transcript_sample: First part of transcript
            
        Returns:
            Summary text
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return "No summary available"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Provide a brief 2-3 sentence summary of what this video/audio is about based on the transcript."),
            ("human", "Transcript:\n{transcript}")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            summary = chain.invoke({"transcript": transcript_sample})
            return summary.strip()
        except Exception as e:
            print(f"[GlobalAnalyzer] Error generating summary: {e}")
            return "Summary generation failed"


# Global instance
_global_analyzer = None


def get_global_analyzer() -> GlobalVideoAnalyzer:
    """Get singleton global analyzer instance."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = GlobalVideoAnalyzer()
    return _global_analyzer


def analyze_video_global(
    video_id: str,
    source: str,
    source_type: str,
    transcript: str,
    title: str = "Untitled",
    duration: float = None
) -> VideoMetadata:
    """Convenience function to analyze video."""
    analyzer = get_global_analyzer()
    return analyzer.analyze_video(video_id, source, source_type, transcript, title, duration)
