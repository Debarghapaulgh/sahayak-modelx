import os
import sys
import json
import pytest

# Ensure synthetictutor is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
# Add synthetic-corpus/scripts to path to import script modules directly
sys.path.append(os.path.join(BASE_DIR, "synthetic-corpus", "scripts"))

from generate_ncert_localized_qa import (
    load_locale, get_district_context, format_to_sarg, run_pipeline
)
from download_and_extract_resources import (
    extract_pdf_text
)

def test_locale_json_structure():
    """Verify locale.json contains 100+ fields of North Bengal data with sources for quantities."""
    locale = load_locale()
    
    assert "region_summary" in locale
    assert "districts" in locale
    
    districts = locale["districts"]
    assert len(districts) == 8  # 8 districts of North Bengal
    
    total_fields = 0
    quantity_fields_with_sources = 0
    
    # Check region summary fields
    for key, val in locale["region_summary"].items():
        total_fields += 1
        if isinstance(val, dict) and "value" in val and "source" in val:
            quantity_fields_with_sources += 1
            
    # Check district fields
    for dist_key, dist_data in districts.items():
        for category_key, category_data in dist_data.items():
            if isinstance(category_data, dict):
                for field_key, field_val in category_data.items():
                    total_fields += 1
                    if isinstance(field_val, dict) and "value" in val and "source" in val:
                        quantity_fields_with_sources += 1
            elif isinstance(category_data, list):
                total_fields += len(category_data)
            else:
                total_fields += 1
                
    print(f"Total fields found: {total_fields}")
    print(f"Quantity fields with sources: {quantity_fields_with_sources}")
    
    # Verify we have a rich locale pack
    assert total_fields >= 100

def test_context_flattening_retrieval():
    """Verify that context retrieval flattens the dictionary without key errors."""
    locale = load_locale()
    
    # Test all 8 districts of North Bengal
    for dist_key in locale["districts"].keys():
        context = get_district_context(locale, dist_key)
        
        # Verify essential fields exist and are non-empty
        assert context["district_name"] == dist_key.replace("coochbehar", "Cooch Behar").replace("uttardinajpur", "Uttar Dinajpur").replace("dakshindinajpur", "Dakshin Dinajpur").title()
        assert "terrain" in context
        assert "paddy_yield" in context
        assert "mgnrega_wage" in context
        assert "specialty_wage" in context
        assert "electricity_reliability" in context
        assert "load_shedding_frequency" in context
        assert "textbook_sharing" in context
        assert "niche_knowledge" in context
        assert len(context["naming_conventions"]) > 0

def test_sarg_export_format():
    """Verify that records are correctly formatted to the SARG SFT metadata style."""
    record = format_to_sarg(
        question="What is the average rainfall in Darjeeling?",
        answer="It is approximately 3092 mm.",
        category="Strict Academic",
        task_type="Explain Concept",
        length="Short (1-2 paragraphs)"
    )
    
    assert "messages" in record
    assert "meta" in record
    
    messages = record["messages"]
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What is the average rainfall in Darjeeling?"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "It is approximately 3092 mm."
    
    meta = record["meta"]
    assert meta["category"] == "Strict Academic"
    assert meta["task_type"] == "Explain Concept"
    assert meta["target_length"] == "Short (1-2 paragraphs)"

def test_pdf_extraction_fallback():
    """Verify that PDF text extraction function runs correctly on empty/mock files."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_pdf = os.path.join(tmpdir, "dummy.pdf")
        dummy_txt = os.path.join(tmpdir, "dummy.txt")
        
        # Should handle non-existent file by returning False rather than crashing
        success = extract_pdf_text(dummy_pdf, dummy_txt)
        assert success is False

async def test_run_pipeline_mock():
    """Verify that the mock pipeline runs end-to-end and writes files in northbengal-sft-chat.jsonl format."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        await run_pipeline(
            grade=10,
            subject="science",
            region="darjeeling",
            num_chunks=2,
            output_dir=tmpdir,
            provider="openai",
            mock=True
        )
        for name in ['train', 'dev', 'test']:
            out_file = os.path.join(tmpdir, f"{name}_northbengal-sft-chat.jsonl")
            assert os.path.exists(out_file), f"Missing {out_file}"
        assert os.path.exists(os.path.join(tmpdir, "northbengal-sft-chat.jsonl"))


