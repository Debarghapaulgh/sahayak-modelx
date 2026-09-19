"""
Locale Retriever Engine for SahayakAI Grounding-First Pipeline.
Provides verified regional facts, district context, economic indicators, and cultural markers
from locale.json without allowing hallucination or forced irrelevant localization.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class LocaleSnippet:
    district: str
    category: str
    fact_key: str
    fact_value: Any
    source: str
    snippet_text: str
    relevance_score: float = 0.0


class LocaleRetriever:
    """First-class retriever for verified local context from locale.json."""

    DISTRICT_SYNONYMS = {
        'darjeeling': ['দার্জিলিং', 'দার্জিলিং জেলা', 'darjeeling', 'কার্শিয়াং', 'মিরিক'],
        'kalimpong': ['কালিম্পং', 'কালিম্পং জেলা', 'kalimpong', 'লাভাতে', 'প্যাদং'],
        'jalpaiguri': ['জলপাইগুড়ি', 'জলপাইগুড়ি', 'jalpaiguri', 'মালবাজার', 'ধূপগুড়ি', 'ময়নাগুড়ি', 'গরুমারা', 'চালসা'],
        'alipurduar': ['আলিপুরদুয়ার', 'আলিপুরদুয়ার', 'alipurduar', 'ফালাকাটা', 'মাদারিহাট', 'জয়গাঁ', 'বক্সা'],
        'coochbehar': ['কোচবিহার', 'coochbehar', 'cooch behar', 'দিনহাটা', 'মাথাভাঙা', 'তুফানগঞ্জ'],
        'malda': ['মালদা', 'মালদহ', 'malda', 'ইংরেজবাজার', 'পুরাতন মালদা', 'গাজোল', 'চাঁচল'],
        'uttardinajpur': ['উত্তর দিনাজপুর', 'uttar dinajpur', 'রায়গঞ্জ', 'ইসলামপুর', 'কালিয়াগঞ্জ'],
        'dakshindinajpur': ['দক্ষিণ দিনাজপুর', 'dakshin dinajpur', 'বালুরঘাট', 'গঙ্গারামপুর', 'বুনিয়াদপুর']
    }

    LOCALE_TRIGGERS = [
        re.compile(r'চা[\s\-]বাগান|চা পাতা|চা শ্রমিক|tea garden', re.IGNORECASE),
        re.compile(r'জলপাইগুড়ি|জলপাইগুড়ি|দার্জিলিং|কালিম্পং|আলিপুরদুয়ার|কোচবিহার|মালদা|দিনাজপুর', re.IGNORECASE),
        re.compile(r'ডুয়ার্স|ডুয়াস|তরাই|dooars|terai|তিস্তা|তোর্সা|জলঢাকা|মহানন্দা', re.IGNORECASE),
        re.compile(r'স্থানীয়\s+উদাহরণ|আঞ্চলিক\s+প্রেক্ষাপট|গ্রামের\s+উদাহরণ|লোকাল\s+উদাহরণ', re.IGNORECASE),
        re.compile(r'গরুমারা|জলদাপাড়া|বক্সা|হাতি|বুনো\s+হাতি|জঙ্গল', re.IGNORECASE),
        re.compile(r'বিঘা|কাঠা|ছটাক|সের|মণ|কুইন্টাল', re.IGNORECASE)
    ]

    def __init__(self, locale_path: str = "locale.json"):
        self.locale_path = Path(locale_path)
        self.locale_data: Dict[str, Any] = {}
        self._load_locale_data()

    def _load_locale_data(self):
        if not self.locale_path.exists():
            raise FileNotFoundError(f"Locale file not found at: {self.locale_path}")
        with open(self.locale_path, "r", encoding="utf-8") as f:
            self.locale_data = json.load(f)

    def is_localization_requested(self, query: str) -> bool:
        """Determines if the user prompt explicitly or implicitly requests verified regional context."""
        return any(pattern.search(query) for pattern in self.LOCALE_TRIGGERS)

    def detect_target_district(self, query: str) -> Optional[str]:
        """Detects mentioned district key if explicitly stated in query."""
        q_lower = query.lower()
        for dist_key, synonyms in self.DISTRICT_SYNONYMS.items():
            if any(syn in q_lower for syn in synonyms):
                return dist_key
        return None

    def retrieve_locale_facts(
        self,
        query: str,
        target_district: Optional[str] = None,
        max_facts: int = 3
    ) -> List[LocaleSnippet]:
        """
        Retrieves verified facts from locale.json relevant to the query and target district.
        """
        if not target_district:
            target_district = self.detect_target_district(query)

        snippets: List[LocaleSnippet] = []
        districts_data = self.locale_data.get("districts", {})
        region_summary = self.locale_data.get("region_summary", {})

        # 1. District-specific retrieval
        if target_district and target_district in districts_data:
            d_info = districts_data[target_district]
            dist_name = d_info.get("name", target_district.capitalize())

            # Terrain & setting
            if "চা" in query or "বাগান" in query or "বন" in query or "নদী" in query:
                snippets.append(LocaleSnippet(
                    district=dist_name,
                    category="setting_type",
                    fact_key="setting_type",
                    fact_value=d_info.get("setting_type"),
                    source="locale.json",
                    snippet_text=f"ভৌগোলিক ও সামাজিক পরিবেশ: {dist_name} অঞ্চলে {d_info.get('setting_type', '')}, ভূপ্রকৃতি: {d_info.get('terrain', '')}।",
                    relevance_score=1.0
                ))

            # Agriculture & Economy
            agri = d_info.get("agriculture_and_economy", {})
            if "ফসল" in query or "চা" in query or "পাট" in query or "কৃষি" in query or "অনুপাত" in query or "অঙ্ক" in query:
                crops = agri.get("major_crops", [])
                tea_info = agri.get("tea_economy_context", "")
                if tea_info and ("চা" in query or "বাগান" in query):
                    snippets.append(LocaleSnippet(
                        district=dist_name,
                        category="agriculture_and_economy",
                        fact_key="tea_economy_context",
                        fact_value=tea_info,
                        source="locale.json",
                        snippet_text=f"চা-বাগান অর্থনীতি: {tea_info}",
                        relevance_score=1.0
                    ))
                elif crops:
                    snippets.append(LocaleSnippet(
                        district=dist_name,
                        category="agriculture_and_economy",
                        fact_key="major_crops",
                        fact_value=crops,
                        source="locale.json",
                        snippet_text=f"প্রধান কৃষিজ ফসল: {', '.join(crops[:4])} (গড় জমির পরিমাণ: {agri.get('average_landholding_size_hectares', {}).get('value', '')} হেক্টর)।",
                        relevance_score=0.9
                    ))

            # Climate & Rainfall
            climate = d_info.get("climate", {})
            if "বৃষ্টি" in query or "আবহাওয়া" in query or "জলবায়ু" in query:
                rain = climate.get("average_annual_rainfall_mm", {})
                snippets.append(LocaleSnippet(
                    district=dist_name,
                    category="climate",
                    fact_key="average_annual_rainfall_mm",
                    fact_value=rain.get("value"),
                    source=rain.get("source", "IMD Normals"),
                    snippet_text=f"গড় বার্ষিক বৃষ্টিপাত: {rain.get('value')} মিমি (উৎস: {rain.get('source', '')})।",
                    relevance_score=0.95
                ))

            # Niche local knowledge (elephants, rivers, culture)
            niche = d_info.get("niche_local_knowledge", {})
            for n_key, n_val in niche.items():
                if any(w in query for w in ["হাতি", "বন", "বন্যা", "নদী", "সেতু"]):
                    snippets.append(LocaleSnippet(
                        district=dist_name,
                        category="niche_local_knowledge",
                        fact_key=n_key,
                        fact_value=n_val,
                        source="locale.json",
                        snippet_text=f"আঞ্চলিক বৈশিষ্ট্য ({n_key}): {n_val}",
                        relevance_score=0.85
                    ))
                    break

        # 2. General Region Summary (Local units, wages, currency)
        if any(w in query for w in ["বিঘা", "কাঠা", "মজুরি", "দাম", "টাকা", "বাজার"]):
            units = region_summary.get("local_units", {})
            wage = region_summary.get("government_mgnrega_daily_wage_inr", {})
            snippets.append(LocaleSnippet(
                district="North Bengal Region",
                category="region_summary",
                fact_key="regional_standards",
                fact_value=units,
                source="locale.json",
                snippet_text=f"স্থানীয় পরিমাপ ও অর্থনীতি: বিঘা-কাঠা জমি পরিমাপ, দৈনিক মনরেগা মজুরি ₹{wage.get('value', 237)} (উৎস: {wage.get('source', '')})।",
                relevance_score=0.8
            ))

        return snippets[:max_facts]
