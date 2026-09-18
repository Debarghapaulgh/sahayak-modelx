import os
import sys
import json
import random
import click
import asyncio
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Ensure synthetictutor is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)
sys.path.append(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))))

from synthetictutor.llm.openai_client import OpenAICompatibleClient

# Define Pydantic models for structured output validation
class MCQResponse(BaseModel):
    question: str = Field(description="The multiple-choice question text.")
    options: Dict[str, str] = Field(description="Dictionary containing options A, B, C, and D.")
    answer: str = Field(description="The correct option letter (A, B, C, or D).")
    explanation: str = Field(description="Brief explanation of why the option is correct.")

class OpenEndedResponse(BaseModel):
    question: str = Field(description="The open-ended question text.")
    answer: str = Field(description="Detailed answer or calculation steps.")

class GeneratedQA(BaseModel):
    mcq: MCQResponse = Field(description="The generated MCQ.")
    open_ended: OpenEndedResponse = Field(description="The generated Open-Ended question.")

class EvaluationScores(BaseModel):
    pedagogical_alignment: float = Field(description="Score (1-10) for pedagogical alignment.")
    local_realism: float = Field(description="Score (1-10) for local realism.")
    structural_clarity: float = Field(description="Score (1-10) for structural clarity.")
    linguistic_accessibility: float = Field(description="Score (1-10) for linguistic accessibility.")
    error_free_execution: float = Field(description="Score (1-10) for error-free execution.")

def load_locale() -> Dict[str, Any]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, "locale.json"),
        os.path.join(os.path.dirname(current_dir), "locale.json"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "locale.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "locale.json")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    # Default fallback
    locale_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "locale.json")
    with open(locale_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_district_context(locale_data: Dict[str, Any], district_key: Optional[str] = None) -> Dict[str, Any]:
    if not district_key:
        district_key = random.choice(list(locale_data["districts"].keys()))
    
    district = locale_data["districts"][district_key]
    region = locale_data["region_summary"]
    
    # Flatten the structures for easy retrieval and prompt grounding
    context = {
        "region_name": region["name"],
        "state": region["state"],
        "board": region["default_board"],
        "medium": region["default_medium"],
        "setting": region["setting"],
        "mgnrega_wage": f"INR {region['government_mgnrega_daily_wage_inr']['value']} per day (Source: {region['government_mgnrega_daily_wage_inr']['source']})",
        "urea_price": f"INR {region['urea_subsidized_price_inr_per_45kg_bag']['value']} per 45kg bag (Source: {region['urea_subsidized_price_inr_per_45kg_bag']['source']})",
        "household_size": region["avg_household_size_rural"]["value"],
        "notebook_price": region["notebook_market_price_inr"]["value"],
        "pen_price": region["pen_market_price_inr"]["value"],
        "school_bag_price": region["school_bag_market_price_inr"]["value"],
        
        "district_name": district["name"],
        "terrain": district["terrain"],
        "headquarters": district["hq"],
        "setting_type": district["setting_type"],
        "literacy_rate": f"{district['demographics']['literacy_rate_percentage']['value']}% (Source: {district['demographics']['literacy_rate_percentage']['source']})",
        "major_ethnic_groups": ", ".join(district["demographics"]["major_ethnic_groups"]),
        "annual_rainfall": f"{district['climate']['average_annual_rainfall_mm']['value']} mm (Source: {district['climate']['average_annual_rainfall_mm']['source']})",
        "soil_type": district["climate"]["typical_soil_type"],
        "soil_ph": f"{district['climate']['soil_ph_range']['min']} - {district['climate']['soil_ph_range']['max']} (Source: {district['climate']['soil_ph_range']['source']})",
        "organic_carbon": f"{district['climate']['average_organic_carbon_percentage']['value']}% (Source: {district['climate']['average_organic_carbon_percentage']['source']})",
        "solar_insulation": f"{district['climate']['solar_insulation_kwh_per_sqm_per_day']['value']} kWh/m2/day (Source: {district['climate']['solar_insulation_kwh_per_sqm_per_day']['source']})",
        
        "electricity_reliability": f"{district['infrastructure']['electricity_reliability_hours_per_day']['value']} hours/day (Source: {district['infrastructure']['electricity_reliability_hours_per_day']['source']})",
        "load_shedding_frequency": f"{district['infrastructure']['load_shedding_frequency_per_week']['value']} times/week (Source: {district['infrastructure']['load_shedding_frequency_per_week']['source']})",
        "school_projectors": f"{district['infrastructure']['school_projector_availability_rate_percentage']['value']}% (Source: {district['infrastructure']['school_projector_availability_rate_percentage']['source']})",
        "smartboards": f"{district['infrastructure']['smartboard_equipped_classrooms_ratio']['value']} ratio (Source: {district['infrastructure']['smartboard_equipped_classrooms_ratio']['source']})",
        "internet_connectivity": district["infrastructure"]["internet_connectivity_status"],
        "textbook_sharing": district["infrastructure"]["textbook_sharing_ratio"],
        
        "landholding_size": f"{district['agriculture_and_economy']['average_landholding_size_hectares']['value']} hectares (Source: {district['agriculture_and_economy']['average_landholding_size_hectares']['source']})",
        "major_crops": ", ".join(district["agriculture_and_economy"]["major_crops"]),
        "paddy_yield": f"{district['agriculture_and_economy']['paddy_yield_kg_per_hectare']['value']} kg/ha (Source: {district['agriculture_and_economy']['paddy_yield_kg_per_hectare']['source']})",
        "specialty_livelihood": district["agriculture_and_economy"]["specialty_livelihood"],
        "specialty_wage": f"INR {district['agriculture_and_economy']['daily_wage_specialty_inr']['value']} per day (Source: {district['agriculture_and_economy']['daily_wage_specialty_inr']['source']})",
        
        "land_measurement": region["local_units"]["land_measurement"],
        "naming_conventions": district["cultural_markers"]["naming_conventions"],
        "flora": ", ".join(district["cultural_markers"]["flora"]),
        "fauna": ", ".join(district["cultural_markers"]["fauna"]),
        "major_rivers": ", ".join(district["cultural_markers"]["major_rivers"]),
        "geographic_features": ", ".join(district["cultural_markers"]["geographic_features"]),
        "regional_food": ", ".join(district["cultural_markers"]["regional_food"]),
        "festivals": ", ".join(district["cultural_markers"]["festivals"]),
        "cultural_objects": ", ".join(district["cultural_markers"]["cultural_objects"]),
        
        # Niche local knowledge
        "niche_knowledge": "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in district["niche_local_knowledge"].items()])
    }
    
    # Add specialty metrics for specific districts if they exist
    if "tea_leaf_yield_kg_per_hectare" in district["agriculture_and_economy"]:
        context["tea_leaf_yield"] = f"{district['agriculture_and_economy']['tea_leaf_yield_kg_per_hectare']['value']} kg/ha (Source: {district['agriculture_and_economy']['tea_leaf_yield_kg_per_hectare']['source']})"
    else:
        context["tea_leaf_yield"] = "N/A"
        
    return context

def generate_mock_qa(chunk_text: str, context: Dict[str, Any]) -> GeneratedQA:
    student_name = random.choice(context["naming_conventions"])
    dist_name = context["district_name"]
    wage = float(re.search(r'\d+', context["specialty_wage"]).group())
    
    mcq = MCQResponse(
        question=f"In a rural school of {dist_name} district, {student_name}'s family owns an agricultural field. If the daily labor rate for their specialty livelihood is {context['specialty_wage'].split('(')[0].strip()}, how much would {student_name}'s family pay a worker for 5 days of work?",
        options={
            "A": f"INR {int(wage * 5)}",
            "B": f"INR {int(wage * 4)}",
            "C": f"INR {int(wage * 6)}",
            "D": f"INR {int(wage * 3)}"
        },
        answer="A",
        explanation=f"Based on the local economics of {dist_name}, the worker earns {context['specialty_wage'].split('(')[0].strip()}. For 5 days of work, the total payment is {wage} * 5 = INR {int(wage * 5)}."
    )
    
    open_ended = OpenEndedResponse(
        question=f"In the context of the geography and climate of {dist_name}, the average annual rainfall is recorded as {context['annual_rainfall'].split('(')[0].strip()}. Based on the concepts of water cycles and rain shadow zones in your science curriculum, explain how this high rainfall supports the growth of local vegetation like {context['flora']}.",
        answer=f"The high rainfall of {context['annual_rainfall'].split('(')[0].strip()} in {dist_name} provides continuous moisture in the soil, which has an acidic pH of {context['soil_ph'].split('(')[0].strip()}. This environment is highly conducive to native plants such as {context['flora']}, which thrive under wet sub-Himalayan forest or Terai conditions. The water cycle ensures that constant evaporation and local topography cause precipitation, fueling this rich ecosystem."
    )
    
    return GeneratedQA(mcq=mcq, open_ended=open_ended)

async def generate_pair(client: OpenAICompatibleClient, chunk_text: str, context: Dict[str, Any], grade: int, mock: bool = False) -> Optional[GeneratedQA]:
    if mock:
        return generate_mock_qa(chunk_text, context)
        
    student_name = random.choice(context["naming_conventions"])
    
    gen_prompt = f"""You are tasked with generating a high-quality educational QA pair based on a curriculum topic chunk.
You must localize the QA pair to a rural or semi-rural setting in North Bengal, India using the local context provided below.

[NCERT Textbook Excerpt]:
{chunk_text}

[Local Context Profile (Rural/Semi-Rural North Bengal)]:
- District: {context["district_name"]}
- Terrain: {context["terrain"]}
- Setting type: {context["setting_type"]}
- Key Crops & Yields: {context["major_crops"]} (Paddy yield: {context["paddy_yield"]})
- Daily Wages: {context["specialty_livelihood"]} average wage is {context["specialty_wage"]}, MGNREGA wage is {context["mgnrega_wage"]}
- Infrastructure Challenges: Electricity reliability: {context["electricity_reliability"]}; Load shedding frequency: {context["load_shedding_frequency"]}; Internet connectivity: {context["internet_connectivity"]}; Textbook sharing: {context["textbook_sharing"]}
- Local units: {context["land_measurement"]}
- Niche Local Knowledge:
{context["niche_knowledge"]}
- Flora & Fauna: {context["flora"]}, {context["fauna"]}
- Local Rivers & Geographic Features: {context["major_rivers"]}, {context["geographic_features"]}
- Local Food: {context["regional_food"]}
- Local Festivals: {context["festivals"]}
- Cultural Objects: {context["cultural_objects"]}

[Instruction]:
Generate exactly two questions and their corresponding answers:
1. One Multiple-Choice Question (MCQ) with 4 options (A, B, C, D) and the correct answer indicated.
2. One Open-Ended Question that requires a detailed explanation or step-by-step calculation.

Rules:
- The questions must be pedagogically aligned to the concepts discussed in the textbook excerpt.
- Ground the question's scenario, names, and parameters using the local context (e.g., use the local student name '{student_name}', local crops, wages, or local geographical/infrastructural realities of {context["district_name"]}).
- For calculations (e.g. math or science problems), construct realistic math word problems based on the daily wages, landholding sizes in Bighas, rainfall, or crop yields specified in the local context. Make sure to use the exact values from the local context.
- Keep the language accessible for Grade {grade} students but maintain academic rigor.
- Do NOT mention NCERT or "the textbook excerpt" in the question itself. Ground it as a natural real-world problem a tutor or student in {context["district_name"]} would discuss.
"""
    
    system_instruction = (
        "You are Sahayak AI, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    
    try:
        qa_data = await client.generate_structured(
            prompt=gen_prompt,
            response_schema=GeneratedQA,
            system_instruction=system_instruction,
            temperature=0.7
        )
        return qa_data
    except Exception as e:
        print(f"Error during structured QA generation: {e}")
        return None

async def evaluate_pair(
    client: OpenAICompatibleClient, 
    chunk_text: str, 
    context: Dict[str, Any], 
    qa_pair: GeneratedQA, 
    grade: int,
    mock: bool = False
) -> Optional[EvaluationScores]:
    if mock:
        return EvaluationScores(
            pedagogical_alignment=9.5,
            local_realism=9.0,
            structural_clarity=10.0,
            linguistic_accessibility=9.5,
            error_free_execution=10.0
        )
        
    eval_prompt = f"""You are an expert academic evaluator. Evaluate the following generated QA pair on 5 dimensions.

[NCERT Textbook Excerpt]:
{chunk_text}

[Local Context Profile]:
- District: {context["district_name"]}
- Terrain: {context["terrain"]}
- Key Crops: {context["major_crops"]} (Paddy yield: {context["paddy_yield"]})
- Specialty Livelihood: {context["specialty_livelihood"]} ({context["specialty_wage"]})
- Infrastructure: {context["electricity_reliability"]}, Load shedding: {context["load_shedding_frequency"]}
- Local Units: {context["land_measurement"]}
- Niche Knowledge: {context["niche_knowledge"]}

[Generated MCQ]:
Question: {qa_pair.mcq.question}
Options:
A: {qa_pair.mcq.options.get('A', '')}
B: {qa_pair.mcq.options.get('B', '')}
C: {qa_pair.mcq.options.get('C', '')}
D: {qa_pair.mcq.options.get('D', '')}
Answer: {qa_pair.mcq.answer}
Explanation: {qa_pair.mcq.explanation}

[Generated Open-Ended Question]:
Question: {qa_pair.open_ended.question}
Answer: {qa_pair.open_ended.answer}

[Dimensions for Evaluation]:
1. Pedagogical Alignment (1-10): Is the question testing concepts present in the textbook excerpt?
2. Local Realism (1-10): Are the names, crops, geography, and infrastructure constraints authentic to North Bengal's rural setting? Do calculations use the exact values from the local context?
3. Structural Clarity (1-10): Is the question free of ambiguity, grammatically correct, and formatted properly?
4. Linguistic Accessibility (1-10): Is the tone and language grade-appropriate (Grade {grade})?
5. Error-Free Execution (1-10): Is the correct option actually correct? Are calculations mathematically accurate?
"""
    
    try:
        scores = await client.generate_structured(
            prompt=eval_prompt,
            response_schema=EvaluationScores,
            temperature=0.2
        )
        return scores
    except Exception as e:
        print(f"Error during structured evaluation: {e}")
        return None

def format_to_sarg(question: str, answer: str, category: str, task_type: str, length: str) -> Dict[str, Any]:
    system_prompt = (
        "You are Sahayak AI, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ],
        "meta": {
            "category": category,
            "task_type": task_type,
            "target_length": length
        }
    }

@click.command()
@click.option('--grade', default=10, help='NCERT Class grade (6-12)')
@click.option('--subject', default='science', help='Curriculum subject (e.g. science, physics, geography)')
@click.option('--region', default=None, help='District name in North Bengal (optional)')
@click.option('--num_chunks', default=5, help='Number of chunks to process')
@click.option('--output_dir', default='synthetic-corpus/output', help='Directory to export the JSONL files')
@click.option('--provider', default='openai', help='LLM client provider name')
@click.option('--mock', is_flag=True, help='Run in mock generation mode (no active LLM needed)')
def generate_pipeline(grade: int, subject: str, region: Optional[str], num_chunks: int, output_dir: str, provider: str, mock: bool):
    asyncio.run(run_pipeline(grade, subject, region, num_chunks, output_dir, provider, mock))

async def run_pipeline(grade: int, subject: str, region: Optional[str], num_chunks: int, output_dir: str, provider: str, mock: bool):
    print(f"Starting NCERT Localized QA Pipeline for Class {grade} {subject} (Mock={mock})...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load locale data
    locale_data = load_locale()
    
    # 2. Load all available text resources for the given grade/subject
    sub_clean = re.sub(r'[^a-zA-Z0-9_]', '_', subject).lower()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_raw_dirs = [
        os.path.join(current_dir, "raw-textbooks"),
        os.path.join(os.path.dirname(current_dir), "raw-textbooks"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "raw-textbooks"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "raw-textbooks")
    ]
    raw_dir = None
    for d in possible_raw_dirs:
        if os.path.exists(d):
            raw_dir = d
            break
    if not raw_dir:
        raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'raw-textbooks')
    
    paths_to_try = [
        os.path.join(raw_dir, 'ncert', f"class_{grade}", f"{sub_clean}_textbook.txt"),
        os.path.join(raw_dir, 'cbse', f"class_{grade}", f"{sub_clean}_sqp.txt"),
        os.path.join(raw_dir, 'cbse', f"class_{grade}", f"{sub_clean}_pyqs.txt")
    ]
    
    merged_content = []
    for p in paths_to_try:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                merged_content.append(f.read())
                
    if not merged_content:
        print(f"Error: No source text files found for Class {grade} {subject}.")
        print("Checked paths:")
        for p in paths_to_try:
            print(f"  {p}")
        sys.exit(1)
        
    # Combine content using clean separation
    content = "\n\n==================================================\n\n".join(merged_content)
        
    chunks = [c.strip() for c in content.split("==================================================") if c.strip()]
    if not chunks:
        # If no delimiter, chunk by paragraphs or block sizes
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0
        for p in paragraphs:
            current_chunk.append(p)
            current_len += len(p.split())
            if current_len >= 500:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
    print(f"Loaded {len(chunks)} textbook and PYQ/SQP chunks.")
    
    # Restrict to requested chunks count
    chunks_to_process = chunks[:num_chunks]
    
    # 3. Initialize LLM Client
    client = OpenAICompatibleClient() if not mock else None
    
    all_sarg_records = []
    
    for idx, chunk in enumerate(chunks_to_process):
        print(f"\n[{idx+1}/{len(chunks_to_process)}] Processing chunk...")
        # Get district context
        context = get_district_context(locale_data, region)
        print(f"Grounding in District: {context['district_name']} ({context['terrain']})")
        
        # Stage 2: Generate candidate QA pair
        qa_pair = await generate_pair(client, chunk, context, grade, mock)
        if not qa_pair:
            print("Skipping due to generation failure.")
            continue
            
        # Stage 3: Quality self-reflection filter
        scores = await evaluate_pair(client, chunk, context, qa_pair, grade, mock)
        if not scores:
            print("Skipping due to evaluation failure.")
            continue
            
        print(f"Scores -> Alignment: {scores.pedagogical_alignment}, Realism: {scores.local_realism}, Clarity: {scores.structural_clarity}, Access: {scores.linguistic_accessibility}, Accuracy: {scores.error_free_execution}")
        
        # Check threshold (each score >= 8.0)
        passed = (
            scores.pedagogical_alignment >= 8.0 and
            scores.local_realism >= 8.0 and
            scores.structural_clarity >= 8.0 and
            scores.linguistic_accessibility >= 8.0 and
            scores.error_free_execution >= 8.0
        )
        
        if not passed:
            print("Failed self-reflection filter. Retrying once...")
            # Retry once
            qa_pair = await generate_pair(client, chunk, context, grade, mock)
            if not qa_pair:
                continue
            scores = await evaluate_pair(client, chunk, context, qa_pair, grade, mock)
            if not scores:
                continue
            passed = (
                scores.pedagogical_alignment >= 8.0 and
                scores.local_realism >= 8.0 and
                scores.structural_clarity >= 8.0 and
                scores.linguistic_accessibility >= 8.0 and
                scores.error_free_execution >= 8.0
            )
            if not passed:
                print("Failed retry. Discarding QA pair.")
                continue
                
        print("Passed quality checks!")
        
        # Format MCQ
        mcq_str = f"Question: {qa_pair.mcq.question}\n"
        for opt, val in sorted(qa_pair.mcq.options.items()):
            mcq_str += f"{opt}. {val}\n"
            
        mcq_ans = f"Correct Answer: {qa_pair.mcq.answer}\n\nExplanation: {qa_pair.mcq.explanation}"
        
        # Format OE
        oe_str = qa_pair.open_ended.question
        oe_ans = qa_pair.open_ended.answer
        
        # Resolve SARG metadata
        meta_category = "Borderline Applied" if grade <= 8 else "Strict Academic"
        
        mcq_record = format_to_sarg(
            question=mcq_str.strip(),
            answer=mcq_ans.strip(),
            category=meta_category,
            task_type="Solve Question",
            length="Short (1-2 paragraphs)"
        )
        
        oe_task = "Solve Question" if any(x in oe_str.lower() for x in ["calculate", "find", "determine", "math", "yield", "wage"]) else "Explain Concept"
        oe_len = "Long (Detailed sections)" if len(oe_ans.split()) > 100 else "Short (1-2 paragraphs)"
        
        oe_record = format_to_sarg(
            question=oe_str.strip(),
            answer=oe_ans.strip(),
            category=meta_category,
            task_type=oe_task,
            length=oe_len
        )
        
        all_sarg_records.append(mcq_record)
        all_sarg_records.append(oe_record)

    # 4. Partition and Export (60/20/20 train/dev/test)
    random.shuffle(all_sarg_records)
    total = len(all_sarg_records)
    print(f"\nGenerated {total} total SARG-formatted QA records.")
    
    if total > 0:
        n_train = int(total * 0.6)
        n_dev = int(total * 0.2)
        
        train_records = all_sarg_records[:n_train]
        dev_records = all_sarg_records[n_train:n_train+n_dev]
        test_records = all_sarg_records[n_train+n_dev:]
        
        # Export files
        for name, records in [('train', train_records), ('dev', dev_records), ('test', test_records)]:
            out_file = os.path.join(output_dir, f"{name}_northbengal-sft-chat.jsonl")
            with open(out_file, 'w', encoding='utf-8') as f:
                for r in records:
                    f.write(json.dumps(r) + '\n')
            print(f"Exported {len(records)} records to {out_file}")
            
        # Export a full, consolidated file
        full_out_file = os.path.join(output_dir, "northbengal-sft-chat.jsonl")
        with open(full_out_file, 'w', encoding='utf-8') as f:
            for r in all_sarg_records:
                f.write(json.dumps(r) + '\n')
        print(f"Exported all {len(all_sarg_records)} records to {full_out_file}")
            
    print("NCERT Localized QA dataset generation complete!")

if __name__ == '__main__':
    generate_pipeline()
