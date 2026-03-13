import re
from typing import List, Dict

class InsightExtractor:
    """
    Extracts key facts, entities, and data points from raw text context
    to build a 'Knowledge Moat' beyond simple LLM summaries.
    """
    
    def extract_facts(self, text: str) -> List[str]:
        # Extract potential facts: Dates, Percentages, Names (Simple Regex for speed/efficiency)
        facts = []
        
        # 1. Extract Dates
        dates = re.findall(r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b', text, re.I)
        dates += re.findall(r'\b(?:20|19)\d{2}\b', text)
        for date in list(set(dates))[:5]:
            facts.append(f"Significant Date: {date}")
            
        # 2. Extract Statistics/Numbers
        stats = re.findall(r'\b\d+(?:\.\d+)?%\b|\b\$\d+(?:\.\d+)?\b\s*(?:billion|million|trillion)?', text, re.I)
        for stat in list(set(stats))[:5]:
            facts.append(f"Data Point: {stat}")
            
        # 3. Extract Key Entities (Capitalized words or Acronyms)
        entities = re.findall(r'\b[A-Z][A-Za-z0-9]+\b', text)
        for ent in list(set(entities))[:8]:
            if len(ent) > 2 and ent.lower() not in ['source', 'this', 'that', 'from', 'with']:
                facts.append(f"Entity: {ent}")
                
        # 4. Tech-specific Context
        if "fold" in text.lower(): facts.append("Industry Context: Foldable Technology")
        if "ai" in text.lower(): facts.append("Core Tech: Artificial Intelligence")
                
        return facts

    def get_summary_metadata(self, context: str) -> Dict:
        """Summarizes extracted insights into a UI-friendly dictionary."""
        return {
            "insights": self.extract_facts(context),
            "word_count": len(context.split()),
            "source_density": context.count("Source [")
        }

insight_extractor = InsightExtractor()
