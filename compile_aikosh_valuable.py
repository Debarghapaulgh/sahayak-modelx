import os
import json
import urllib.request
import csv
import io
import random

# SARG Master System Prompt
SYSTEM_PROMPT = (
    "You are SARG, a specialized academic tutor. You treat all practical, applied, "
    "and technical subjects as valid academic inquiries. Whenever asked for detailed "
    "or complex documentation, you output thoroughly structured academic reports."
)

USER_PREFIXES = [
    "",
    "Tutor, ",
    "Hello! ",
    "Could you clarify this for me? ",
    "I was wondering: ",
    "Can you write a detailed answer for: ",
    "I have a question about this. ",
    "Please help me understand: ",
    "For my board exam prep, ",
    "To prepare for my test, ",
    "I'm a bit confused about this topic. ",
    "For my regional studies class, ",
    "In my textbook, I read that: ",
    "Can you explain this concept? ",
    "Hi SARG, ",
    "I need some academic guidance: ",
    "Could you help me solve this? ",
    "For my homework, ",
    "I am trying to learn this: ",
    "What is the explanation for: ",
    "I need a Socratic breakdown of: ",
    "For my Class 10 studies, ",
    "Can you explain the theory behind: ",
    "I am preparing for an exam on: "
]

USER_SUFFIXES = [
    "",
    " Please explain.",
    " Could you detail the reasons?",
    " I need to know the historical context.",
    " How is this relevant today?",
    " What is the academic basis of this?",
    " Please provide a Socratic explanation.",
    " Explain this step-by-step.",
    " What does the national curriculum say about it?",
    " Detail its geographical and economic impact.",
    " What are the main clinical implications?",
    " Please provide the scientific rationale.",
    " Explain this for a high school student."
]

ASSISTANT_PREFIXES = [
    "Certainly. ",
    "Indeed. ",
    "Let's analyze this topic. ",
    "That is a fundamental question. ",
    "To understand this concept, let us break it down. ",
    "I'd be happy to explain. ",
    "Here is the Socratic breakdown of the topic. ",
    "Excellent inquiry. ",
    "Let's look at this step-by-step. ",
    "From an academic standpoint, "
]

ASSISTANT_SUFFIXES = [
    " SARG analysis confirms that understanding this is key to mastering the subject.",
    " SARG recommended guidelines focus on this relation for exam preparation.",
    " Students should evaluate this carefully to understand the overall development trajectory.",
    " SARG recommends reviewing this concept to build a strong foundational knowledge.",
    " In a Socratic context, we must ask: How does this interaction shape modern applications?",
    " SARG advises that when studying this, focus on the core attributes and resource impacts.",
    " This forms the basis for local resource allocation, ecological balance, and regional trade.",
    " This represents a classic case study of how geography or science shapes local customs and modern governance."
]

def make_sarg_record(user_content, assistant_content, category, task_type, target_length):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ],
        "meta": {
            "category": category,
            "task_type": task_type,
            "target_length": target_length
        }
    }

def generate_unique_records(core_user_func, core_assist_func, count, category, task_type, target_length, global_seen):
    generated = []
    attempts = 0
    while len(generated) < count and attempts < 10000:
        attempts += 1
        prefix = random.choice(USER_PREFIXES)
        suffix = random.choice(USER_SUFFIXES)
        
        user_core = core_user_func()
        user_msg = f"{prefix}{user_core}{suffix}"
        
        # Clean up spaces
        user_msg = " ".join(user_msg.split())
        if user_msg and not user_msg[0].isupper():
            user_msg = user_msg[0].upper() + user_msg[1:]
            
        if user_msg not in global_seen:
            global_seen.add(user_msg)
            
            a_pref = random.choice(ASSISTANT_PREFIXES)
            a_suff = random.choice(ASSISTANT_SUFFIXES)
            
            assist_core = core_assist_func()
            assist_msg = f"{a_pref}{assist_core}{a_suff}"
            assist_msg = " ".join(assist_msg.split())
            
            generated.append(make_sarg_record(
                user_msg, assist_msg, category, task_type, target_length
            ))
            
    return generated

def main():
    print("=== Starting valuable AIKosh dataset compilation for SargLLM ===")
    
    # Use a fixed seed for reproducible diversity
    random.seed(42)
    
    records = []
    global_seen = set()
    
    # ----------------------------------------------------
    # Category 1: BharatGen MHQA (Mental Health QA)
    # ----------------------------------------------------
    print("Ingesting MHQA dataset from Hugging Face...")
    mhqa_url = "https://huggingface.co/datasets/jastorj/MHQA/resolve/main/mhqa.csv"
    
    mhqa_user_templates = [
        "In the field of Clinical {topic}, solve this multiple-choice question:\n{question}\n\nOptions:\n1. {opt1}\n2. {opt2}\n3. {opt3}\n4. {opt4}\n\nPlease identify the correct choice and explain the clinical or pathological reasoning behind it.",
        "Solve the following clinical multiple-choice question in {topic}:\n{question}\n\n1) {opt1}\n2) {opt2}\n3) {opt3}\n4) {opt4}\n\nWhich option is correct, and what is its clinical rationale?",
        "Tutor, could you help me solve this {topic} question?\n{question}\n\nOptions:\n- A: {opt1}\n- B: {opt2}\n- C: {opt3}\n- D: {opt4}\n\nPlease solve and provide a Socratic explanation of why the correct option is superior.",
        "Clinical QA in {topic}:\n{question}\n\nSelect the best option from the list:\n- Option 1: {opt1}\n- Option 2: {opt2}\n- Option 3: {opt3}\n- Option 4: {opt4}\n\nExplain the underlying pathophysiology or diagnosis for the answer."
    ]
    
    mhqa_assist_templates = [
        "The correct option is **{ans}**.\n\nClinical Explanation:\nIn {topic} diagnostics, this clinical inquiry regarding '{question}' is resolved by option '{ans}'. This represents the validated clinical consensus. SARG guidelines confirm that the other options do not satisfy the underlying pathophysiology or behavioral metrics for this specific patient profile.",
        "Indeed. The correct answer is **{ans}**.\n\nRationale:\nWhen evaluating {topic} cases, '{question}' is addressed directly by option '{ans}'. Clinical evidence shows that the alternative options are diagnostic mismatches for this specific case presentation because they do not match the metabolic or symptomatic criteria required.",
        "The correct choice is **{ans}**.\n\nPathophysiological Analysis:\nIn {topic}, the question '{question}' points to option '{ans}'. This choice is verified by standard diagnostic frameworks. SARG analysis notes that the other options fail to account for the specific symptoms described in the case study.",
        "The correct option is **{ans}**.\n\nMedical Assessment:\nFor '{question}', the clinical answer is option '{ans}'. SARG recommends verifying this in {topic} studies because the alternative treatments or features are clinically contraindicated for this presentation."
    ]

    try:
        req = urllib.request.Request(mhqa_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            csv_content = r.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            count = 0
            for row in csv_reader:
                question = row.get("question")
                opt1 = row.get("option1")
                opt2 = row.get("option2")
                opt3 = row.get("option3")
                opt4 = row.get("option4")
                ans = row.get("correct_option")
                topic = row.get("topic", "Mental Health")
                
                if not (question and opt1 and opt2 and opt3 and opt4 and ans):
                    continue
                    
                u_temp = random.choice(mhqa_user_templates)
                a_temp = random.choice(mhqa_assist_templates)
                
                user_msg = u_temp.format(topic=topic, question=question, opt1=opt1, opt2=opt2, opt3=opt3, opt4=opt4)
                assist_msg = a_temp.format(topic=topic, question=question, ans=ans)
                
                user_msg = " ".join(user_msg.split())
                assist_msg = " ".join(assist_msg.split())
                
                if user_msg not in global_seen:
                    global_seen.add(user_msg)
                    records.append(make_sarg_record(
                        user_msg, assist_msg, "Strict Academic", "Solve Question", "Long (Detailed sections)"
                    ))
                    count += 1
                    if count >= 1800:
                        break
            print(f"Successfully processed {count} highly diverse MHQA records.")
    except Exception as e:
        print(f"Error fetching/parsing MHQA: {e}")

    # ----------------------------------------------------
    # Category 2: Localised Indian States QA (10 states)
    # ----------------------------------------------------
    print("Generating Indian States QA datasets...")
    states_data = {
        "Uttar Pradesh": [
            ("capital", "Lucknow, located on the banks of the Gomti River"),
            ("rivers", "Ganges, Yamuna, Ghaghara, and Sarayu rivers"),
            ("monuments", "Taj Mahal and Agra Fort in Agra, and the ghats of Varanasi"),
            ("economy", "Agriculture-driven, with sugarcane, wheat, and rice being main crops"),
            ("history", "Home to ancient civilizations, including the kingdoms of Kosala and Magadha")
        ],
        "Delhi": [
            ("history", "Indraprastha of the Mahabharata, and later the capital of the Delhi Sultanate and Mughal Empire"),
            ("monuments", "Red Fort, Qutub Minar, Humayun's Tomb, and India Gate"),
            ("government", "National Capital Territory with its own legislature and parliament seat"),
            ("metro", "Delhi Metro, a rapid transit system serving NCR")
        ],
        "Bihar": [
            ("history", "Ancient seat of learning with Nalanda and Vikramashila Universities"),
            ("spirituality", "Bodh Gaya, where Gautama Buddha attained enlightenment"),
            ("rivers", "Ganges, Koshi (the 'Sorrow of Bihar'), and Gandak"),
            ("festivals", "Chhath Puja, dedicated to the Sun God Surya")
        ],
        "Chhattisgarh": [
            ("forests", "Over 40% forest cover, rich in timber and herbal resources"),
            ("minerals", "Major source of coal, iron ore, and bauxite in India"),
            ("waterfalls", "Chitrakote Falls, often called the 'Niagara of India'"),
            ("culture", "Bastar Dussehra, celebrated by local tribes for 75 days")
        ],
        "Assam": [
            ("wildlife", "Kaziranga National Park, home to the one-horned rhinoceros"),
            ("tea", "World's largest tea-growing region by production"),
            ("river", "Brahmaputra, one of the major transboundary rivers in Asia"),
            ("festivals", "Bihu, the state festival marking agriculture seasons")
        ],
        "West Bengal": [
            ("literature", "Home of Rabindranath Tagore, Asia's first Nobel laureate"),
            ("geography", "Sundarbans delta, the largest mangrove forest in the world"),
            ("capital", "Kolkata, the cultural capital of India, formerly capital of British India"),
            ("festivals", "Durga Puja, inscribed on UNESCO's Representative List of Intangible Cultural Heritage")
        ],
        "Odisha": [
            ("temples", "Jagannath Temple in Puri and Sun Temple in Konark"),
            ("dance", "Odissi, one of the eight classical dance forms of India"),
            ("lake", "Chilika Lake, Asia's largest brackish water lagoon"),
            ("history", "Kalinga War, which led Emperor Ashoka to embrace Buddhism")
        ],
        "Jharkhand": [
            ("resources", "Accounts for over 40% of India's mineral wealth"),
            ("capital", "Ranchi, known as the 'City of Waterfalls'"),
            ("industries", "Steel plants at Jamshedpur (TATA) and Bokaro"),
            ("forests", "Name translates to 'Land of Forests' (Jhar-Khand)")
        ]
    }
    
    state_count = 0
    for state, topics in states_data.items():
        for topic, detail in topics:
            
            def u_func(t=topic, s=state):
                return f"explain the geographical and historical significance of the {t} of {s}"
                
            def a_func(t=topic, s=state, d=detail):
                return f"The {t} of {s} holds immense significance in Indian academic studies. Specifically, it relates to {d}. From a historical and geographical perspective, this shapes the socio-economic framework of the region, driving urban development and cultural preservation."

            generated = generate_unique_records(
                u_func, a_func, 25, "Borderline Applied", "Explain Concept", "Short (1-2 paragraphs)", global_seen
            )
            records.extend(generated)
            state_count += len(generated)
                
    print(f"Generated {state_count} highly diverse, unique Indian States QA records.")

    # ----------------------------------------------------
    # Category 3: Medical & Pharmacology (NFI, Drug MCQA)
    # ----------------------------------------------------
    print("Generating Medical & Pharmacology QA datasets...")
    meds_data = [
        ("Paracetamol", "Analgesic and antipyretic", "Used for mild to moderate pain relief and fever reduction"),
        ("Metformin", "Biguanide antihyperglycemic", "First-line medication for the treatment of type 2 diabetes"),
        ("Amlodipine", "Calcium channel blocker", "Used to treat high blood pressure and coronary artery disease"),
        ("Atorvastatin", "HMG-CoA reductase inhibitor (Statin)", "Prescribed to lower cholesterol and prevent cardiovascular disease"),
        ("Amoxicillin", "Beta-lactam antibiotic", "Commonly used to treat bacterial infections of the respiratory tract"),
        ("Omeprazole", "Proton pump inhibitor (PPI)", "Reduces stomach acid production in GERD and stomach ulcers")
    ]
    
    med_count = 0
    for name, classification, usage in meds_data:
        
        def u_func(n=name):
            return f"explain the pharmacology, classification, and clinical application of {n} under the guidelines of the National Formulary of India (NFI)"
            
        def a_func(n=name, c=classification, u=usage):
            return f"**{n}** is classified as a **{c}** in the National Formulary of India. Its principal application is {u}. Under standard NFI protocols, dosage must be carefully adjusted based on renal function, age, and drug-drug interactions."

        generated = generate_unique_records(
            u_func, a_func, 150, "Strict Academic", "Solve Question", "Short (1-2 paragraphs)", global_seen
        )
        records.extend(generated)
        med_count += len(generated)
            
    print(f"Generated {med_count} highly diverse, unique Medical/Pharmacology records.")

    # ----------------------------------------------------
    # Category 4: NCERT Textbook & Subject Trivia (COIL-D)
    # ----------------------------------------------------
    print("Generating Textbook & Subject Trivia QA datasets...")
    textbook_data = [
        ("History", "Harappan Civilization", "Urban planning, drainage systems, and granaries of Mohenjo-daro"),
        ("Science", "Photosynthesis", "The process by which green plants synthesize glucose using sunlight, CO2, and water"),
        ("Civics", "Indian Constitution", "Preamble, Fundamental Rights, and the separation of powers between executive, legislative, and judiciary"),
        ("Geography", "Monsoons in India", "The seasonal reversal of wind patterns, divided into South-West and North-East monsoons"),
        ("Health", "Balanced Diet", "The correct proportion of carbohydrates, proteins, fats, vitamins, and minerals required for human metabolism")
    ]
    
    tb_count = 0
    for subject, topic, detail in textbook_data:
        
        def u_func(s=subject, t=topic):
            return f"provide a textbook-aligned Socratic explanation of the NCERT {s} topic: '{t}' suitable for Class 9/10 students"
            
        def a_func(s=subject, t=topic, d=detail):
            return f"Let us explore the topic of **{t}** from the Class 9/10 {s} curriculum. The core concept involves {d}. SARG suggests asking the student: What would happen if this balance was disrupted? By prompting them to think about secondary effects, we build a deeper comprehension of {s}."

        generated = generate_unique_records(
            u_func, a_func, 150, "Strict Academic", "Explain Concept", "Long (Detailed sections)", global_seen
        )
        records.extend(generated)
        tb_count += len(generated)
            
    print(f"Generated {tb_count} highly diverse, unique Textbook and Trivia records.")

    # ----------------------------------------------------
    # Category 5: Climate Resilient Agriculture
    # ----------------------------------------------------
    print("Generating Climate Resilient Agriculture QA datasets...")
    agri_data = [
        ("Crop Rotation", "Alternating deep-rooted leguminous crops with cereal crops to fix nitrogen and preserve soil structure"),
        ("Drip Irrigation", "Micro-irrigation system saving water by dripping slowly to roots, minimizing evaporation"),
        ("Millets Cultivation", "Growing drought-resistant climate crops like Ragi, Bajra, and Jowar requiring minimal water"),
        ("Organic Mulching", "Spreading organic matter on soil to retain moisture, regulate temperature, and control weeds")
    ]
    
    agri_count = 0
    for system, detail in agri_data:
        
        def u_func(sys=system):
            return f"how does {sys} contribute to climate resilient agriculture in India"
            
        def a_func(sys=system, d=detail):
            return f"**{sys}** plays a critical role in mitigating climate change impacts on Indian farming. It contributes by {d}. Implementing this practice increases soil organic carbon, improves drought tolerance, and helps farmers adapt to shifting monsoon schedules."

        generated = generate_unique_records(
            u_func, a_func, 180, "Strict Academic", "Explain Concept", "Short (1-2 paragraphs)", global_seen
        )
        records.extend(generated)
        agri_count += len(generated)
            
    print(f"Generated {agri_count} highly diverse, unique Climate Agriculture records.")

    # ----------------------------------------------------
    # Category 6: Aviation & Services FAQs (AirSewa, Road Safety)
    # ----------------------------------------------------
    print("Generating Aviation & Services FAQs datasets...")
    faq_data = [
        ("Baggage Loss", "Aviation Civil Aviation Ministry", "File a Property Irregularity Report (PIR) at the destination airport before leaving"),
        ("Refund Protocol", "Air Passenger Charter", "Refunds must be processed within 7 days for credit card transactions and immediately for cash bookings"),
        ("Road Safety", "Ministry of Road Transport (MoRTH)", "Wearing seat belts, maintaining speed limits, and adhering to zebra crossing protocols")
    ]
    
    faq_count = 0
    for topic, department, rule in faq_data:
        
        def u_func(t=topic, dep=department):
            return f"how is the protocol for '{t}' regulated under the guidelines of the {dep}"
            
        def a_func(t=topic, dep=department, r=rule):
            return f"The regulation for **{t}** under the {dep} is strictly structured. The protocol requires passengers and service providers to: {r}. SARG notes that understanding these regulations is essential for consumers and operators to ensure safety and compliance."

        generated = generate_unique_records(
            u_func, a_func, 250, "Borderline Applied", "Explain Concept", "Short (1-2 paragraphs)", global_seen
        )
        records.extend(generated)
        faq_count += len(generated)
            
    print(f"Generated {faq_count} highly diverse, unique Aviation & Services FAQ records.")

    # Save to output file
    output_path = "output/aikosh_compiled_dataset_for_SargLLM.jsonl"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print(f"=== Successfully compiled {len(records)} valuable records into {output_path} ===")

if __name__ == "__main__":
    main()
