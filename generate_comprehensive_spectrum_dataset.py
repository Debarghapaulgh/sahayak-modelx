"""
generate_comprehensive_spectrum_dataset.py
Generates a 10,000-record dataset spanning a wide spectrum of user interactions:
- Quiz and assessment questions with Socratic feedback (alternating role sequence starting with human)
- Strictly academic multi-subject topics (Science, Math, History, Geography, English)
- Borderline academic questions (MS Paint brushes, lesson plans, writing code)
- Identity & Meta-tutoring questions
- Off-topic steering and Safety/NSFW refusals
Integrates 5 student personas, 7 boards/states, Indic multilingual formats, and response length variations.
"""

import os
import json
import random
from typing import List, Dict, Any

OUTPUT_PATH = "output/comprehensive_spectrum_dialogues.jsonl"
TARGET_RECORDS = 10000

# 1. School Boards & Localized State Profiles
BOARD_PROFILES = {
    "cbse": {
        "board_name": "CBSE (Central Board of Secondary Education)",
        "region": "National",
        "languages": ["en", "hi", "hinglish"],
        "local_terms": {"temple": "temple", "lake": "city lake", "monument": "India Gate"},
        "history_topic": "Freedom Struggle in 1857",
        "geography_topic": "Himalayan Rivers and Drainage Systems",
        "math_topic": "Linear Equations in Two Variables"
    },
    "upmsp": {
        "board_name": "UPMSP (Uttar Pradesh Board)",
        "region": "Uttar Pradesh",
        "languages": ["hi", "hinglish", "en"],
        "local_terms": {"temple": "Kashi Vishwanath Mandir", "lake": "Keetham Lake", "monument": "Taj Mahal"},
        "history_topic": "Mughal Empire and local architecture under Shah Jahan",
        "geography_topic": "Ganga-Yamuna Alluvial Plains and Agriculture",
        "math_topic": "Compound Interest formulas applied to farming loans"
    },
    "wbbse": {
        "board_name": "WBBSE (West Bengal Board)",
        "region": "West Bengal",
        "languages": ["bn", "en", "hi"],
        "local_terms": {"temple": "Dakshineswar Kali Temple", "lake": "Rabindra Sarobar", "monument": "Victoria Memorial"},
        "history_topic": "Battle of Plassey and the Indigo Revolt in Bengal",
        "geography_topic": "Sundarbans Mangrove Delta and soil salinity",
        "math_topic": "Ratios and percentages in jute trading"
    },
    "tnscert": {
        "board_name": "TNSCERT (Tamil Nadu Board)",
        "region": "Tamil Nadu",
        "languages": ["ta", "en", "te"],
        "local_terms": {"temple": "Brihadisvara Temple", "lake": "Ooty Lake", "monument": "Aranmula Valkannadi"},
        "history_topic": "Chola Dynasty maritime trade and bronze casting",
        "geography_topic": "Kaveri Delta irrigation and water allocation systems",
        "math_topic": "Areas of temple tanks and agricultural land calculations"
    },
    "msbshse": {
        "board_name": "MSBSHSE (Maharashtra Board)",
        "region": "Maharashtra",
        "languages": ["mr", "en", "hi"],
        "local_terms": {"temple": "Shreemant Dagdusheth Halwai", "lake": "Lonar Crater Lake", "monument": "Gateway of India"},
        "history_topic": "Maratha Empire rise and Shivaji Maharaj administration",
        "geography_topic": "Deccan Plateau basalt formations and black cotton soil",
        "math_topic": "Averages and yields in cotton farming cooperatives"
    },
    "pseb": {
        "board_name": "PSEB (Punjab Board)",
        "region": "Punjab",
        "languages": ["pa", "en", "hinglish"],
        "local_terms": {"temple": "Golden Temple Amritsar", "lake": "Sukhna Lake", "monument": "Jallianwala Bagh"},
        "history_topic": "Sikh Empire under Maharaja Ranjit Singh and partition impact",
        "geography_topic": "Five Rivers and extensive canal irrigation waterlogging",
        "math_topic": "Volume and capacity calculations of cylindrical grain silos"
    },
    "bseb": {
        "board_name": "BSEB (Bihar Board)",
        "region": "Bihar",
        "languages": ["hi", "en"],
        "local_terms": {"temple": "Mahabodhi Temple Gaya", "lake": "Kanwar Lake", "monument": "Golghar Patna"},
        "history_topic": "Ancient Magadha Empire, Maurya rule, and Nalanda University history",
        "geography_topic": "Kosi River floods and silt deposition dynamics",
        "math_topic": "Calculations of seed rates and field partitioning ratios"
    }
}

# 2. Student Personas
PERSONAS = {
    "topper": {"name": "The Topper", "style": "exam-oriented, precise, uses academic jargon, requests equations"},
    "struggler": {"name": "First-Gen Struggler", "style": "simple language, gets confused easily, needs everyday metaphors"},
    "curious": {"name": "Curious Thinker", "style": "asks open-ended lateral questions, links concepts to local culture"},
    "rote": {"name": "Rote Memoriser", "style": "repeats book definitions, asks how to answer for high marks"},
    "distracted": {"name": "Distracted Bright Kid", "style": "brief, casual tone, high potential but needs focus redirection"}
}

# Dynamic generator functions for categories
def get_quiz_dialogue(board_key: str, persona_key: str, lang: str) -> Dict[str, Any]:
    board = BOARD_PROFILES[board_key]
    persona = PERSONAS[persona_key]
    
    quizzes = [
        {
            "topic": "Mathematics (Linear Equations)",
            "question": f"If a farmer in {board['region']} borrows money to buy seeds and has a linear cost equation $y = 1500x + 500$, what do the numbers 1500 and 500 represent?",
            "s_correct": "The 1500 represents the cost per hectare of seeds (slope), and 500 is the fixed administrative fee (y-intercept).",
            "s_incorrect": "I think the 1500 is the total crop yield and 500 is the number of cows on the farm.",
            "t_hint": f"Think about what changes with the size of the land ($x$). If the farmer tills 0 hectares, does he still pay 500 rupees? And what is added for each extra hectare of land?",
            "t_affirm": "Correct! 500 is the fixed base cost, and 1500 is the variable seed cost per unit area. Spot on!"
        },
        {
            "topic": "History (Dynasties)",
            "question": f"Which dynasty built the famous {board['local_terms']['temple']} in your region, and how did they fund it?",
            "s_correct": f"It was built by the local rulers, using wealth from agricultural taxes and maritime trade.",
            "s_incorrect": "I guess it was built by the British East India Company to store grain.",
            "t_hint": f"Consider the medieval history of {board['region']}. Look at the stone inscriptions on the temple walls—they mention land donations from kings and merchant guilds of that time.",
            "t_affirm": "Correct! It was built by medieval kings and funded through land revenues and trade taxes."
        },
        {
            "topic": "Science (Evaporation & Cooling)",
            "question": f"Why does water stored in a porous earthen pot get cooler in summer?",
            "s_correct": "Water seeps out of the tiny pores and evaporates, absorbing the latent heat of vaporization from the remaining water.",
            "s_incorrect": "Because clay blocks all the heat from the sun and acts as a refrigerator.",
            "t_hint": "Think about what happens to water when it spills on a hot floor. It dries up by absorbing heat. Where does the water on the outside of the clay pot get the heat to evaporate?",
            "t_affirm": "Correct! The latent heat of vaporization is absorbed from the bulk water inside, cooling it down."
        }
    ]
    
    quiz = random.choice(quizzes)
    is_correct = random.choice([True, False])
    
    # Student requests the quiz first (ensures human starts the turn)
    student_request = f"Tutor, can you quiz me on {quiz['topic']}?"
    if lang == "hi" and board_key in ("upmsp", "bseb"):
        student_request = f"टीचर, क्या आप मुझसे {quiz['topic']} पर कोई प्रश्न पूछ सकते हैं?"
    elif lang == "bn" and board_key == "wbbse":
        student_request = f"দিদিমণি, আপনি কি আমাকে {quiz['topic']} থেকে কোনো কুইজ জিজ্ঞেস করতে পারেন?"
    elif lang == "ta" and board_key == "tnscert":
        student_request = f"ஐயா, {quiz['topic']}-லிருந்து என்னிடம் ஒரு கேள்வி கேட்க முடியுமா?"
        
    # Format turns based on persona
    if persona_key == "topper":
        student_ans = f"In terms of {quiz['topic']}, " + (quiz["s_correct"] if is_correct else "I suspect the variables represent coefficients of correlation but I am unsure how the constant fits.")
    elif persona_key == "struggler":
        student_ans = "I get confused by the formula. " + (quiz["s_correct"] if is_correct else "Maybe it is just the price of cows and tractor diesel?")
    elif persona_key == "curious":
        student_ans = f"This reminds me of our local {board['local_terms']['lake']} management. " + (quiz["s_correct"] if is_correct else "Is it related to how the river level changes with rain?")
    elif persona_key == "rote":
        student_ans = f"According to the textbook, the answer is " + (quiz["s_correct"] if is_correct else "not in the three marks questions list, so I am not sure.")
    else: # distracted
        student_ans = "Uh, seed price or something?" if is_correct else "I don't know, variable cost of something?"
        
    convs = [
        {"from": "human", "value": student_request},
        {"from": "gpt", "value": f"Let's do a quick quiz on {quiz['topic']}! {quiz['question']}"},
        {"from": "human", "value": student_ans}
    ]
    
    if is_correct:
        convs.append({"from": "gpt", "value": quiz["t_affirm"]})
        target_len = "Short (1-2 paragraphs)"
    else:
        convs.append({"from": "gpt", "value": quiz["t_hint"]})
        target_len = "Medium (1-2 paragraphs)"
        
    return {
        "conversations": convs,
        "language": lang,
        "board": board_key,
        "metadata": {
            "category": "Quiz & Assessment",
            "subject": quiz["topic"],
            "student_persona": persona["name"],
            "student_style": persona["style"],
            "target_length": target_len,
            "state_context": board["region"]
        }
    }

def get_academic_dialogue(board_key: str, persona_key: str, lang: str) -> Dict[str, Any]:
    board = BOARD_PROFILES[board_key]
    persona = PERSONAS[persona_key]
    
    subjects = [
        {
            "name": "History",
            "q": f"Can you explain the significance of the {board['history_topic']}?",
            "ans": f"The {board['history_topic']} was a key event. For instance, near {board['local_terms']['monument']}, local leaders rallied the population. In your school curriculum, we study how it led to structural reforms in administration and affected local tax collections."
        },
        {
            "name": "Geography",
            "q": f"What should I know about the {board['geography_topic']}?",
            "ans": f"The {board['geography_topic']} determines the agricultural economy of {board['region']}. For example, the sediment feeds the fertile soils. In winter, this supports crop cultivation, but requires careful drainage to avoid waterlogging near local bodies like {board['local_terms']['lake']}."
        },
        {
            "name": "Mathematics",
            "q": f"How do we apply {board['math_topic']} in real life?",
            "ans": f"We can model transactions using {board['math_topic']}. For instance, if you purchase supplies from a shop near {board['local_terms']['temple']}, the total cost is a function of quantity and base tax. Let's write the equation: $Y = mx + c$, where $c$ represents the fixed local surcharge."
        }
    ]
    
    sub = random.choice(subjects)
    
    student_q = f"I am preparing for the {board['board_name']} exam. {sub['q']}"
    
    # Adjust student query by persona
    if persona_key == "topper":
        student_q = f"According to the {board['board_name']} syllabus, what is the exact analytical framework to understand: {sub['q']}"
    elif persona_key == "struggler":
        student_q = f"Tutor, I have a doubt from {board['board_name']} syllabus. The words are very hard. Can you explain: {sub['q']}"
    elif persona_key == "curious":
        student_q = f"I was reading about {board['region']} history and was wondering: {sub['q']}"
        
    convs = [
        {"from": "human", "value": student_q},
        {"from": "gpt", "value": sub["ans"]}
    ]
    
    # Regional translation override
    if lang == "hi" and board_key in ("upmsp", "bseb"):
        convs[0]["value"] = f"नमस्ते टीचर, मुझे {board['board_name']} परीक्षा के लिए {sub['name']} में एक डाउट है। क्या आप समझा सकते हैं: {sub['q']}"
        convs[1]["value"] = f"ज़रूर! {board['region']} के संदर्भ में इसका बहुत महत्व है। जैसे कि हमारे {board['local_terms']['monument']} के आसपास के क्षेत्रों में..."
    elif lang == "bn" and board_key == "wbbse":
        convs[0]["value"] = f"নমস্কার দিদিমণি, {board['board_name']} পরীক্ষার সিলেবাস থেকে {sub['name']} নিয়ে একটি প্রশ্ন আছে: {sub['q']}"
        convs[1]["value"] = f"নিশ্চয়ই! আমাদের পশ্চিমবঙ্গের {board['local_terms']['monument']} এর ইতিহাস ও ভৌগোলিক অবস্থানের সাথে এটি যুক্ত..."
    elif lang == "ta" and board_key == "tnscert":
        convs[0]["value"] = f"வணக்கம், {board['board_name']} தேர்வுக்குத் தயாராகி வருகிறேன். {sub['name']}-ல் இந்த சந்தேகம் உள்ளது: {sub['q']}"
        convs[1]["value"] = f"நிச்சயமாக விளக்குகிறேன். தமிழ்நாட்டின் {board['local_terms']['temple']} மற்றும் அதனைச் சுற்றியுள்ள நீர்நிலைகள்..."
        
    return {
        "conversations": convs,
        "language": lang,
        "board": board_key,
        "metadata": {
            "category": "Strictly Academic",
            "subject": sub["name"],
            "student_persona": persona["name"],
            "student_style": persona["style"],
            "target_length": "Medium (1-2 paragraphs)",
            "state_context": board["region"]
        }
    }

def get_borderline_dialogue(persona_key: str, lang: str) -> Dict[str, Any]:
    persona = PERSONAS[persona_key]
    
    scenarios = [
        {
            "topic": "MS Paint Tools",
            "q": "How does the brush tool in MS Paint work, and what is the difference between watercolor and calligraphy brushes?",
            "ans": (
                "### MS Paint Brush Tools Guide\n\n"
                "In Microsoft Paint, the Brush Tool allows you to draw free-form lines with various textures and strokes. "
                "Here is the comparison between the key brush types:\n\n"
                "| Brush Type | Stroke Characteristics | Best Used For |\n"
                "| :--- | :--- | :--- |\n"
                "| **Calligraphy Brush** | Angled, ribbon-like strokes that change thickness based on direction. | Traditional lettering, script writing, and stylized borders. |\n"
                "| **Watercolor Brush** | Semi-transparent, soft-edged strokes that layer color dynamically. | Artistic shading, blending backgrounds, and natural textures. |\n"
                "| **Oil Brush** | Thick, opaque strokes that simulate heavy canvas paint. | Textured fill-ins and painting bold lines. |\n\n"
                "**Tip**: Hold `Shift` while dragging to draw straight horizontal or vertical lines with any brush."
            ),
            "length": "Long (Detailed sections)"
        },
        {
            "topic": "Lesson Planning",
            "q": "Can you write a lesson plan for Class 8 History on the revolt of 1857?",
            "ans": (
                "# Lesson Plan: The Great Revolt of 1857 (Class 8 History)\n\n"
                "* **Duration**: 45 Minutes\n"
                "* **Grade**: Class 8\n"
                "* **Subject**: History / Social Science\n\n"
                "## 1. Learning Objectives\n"
                "* Identify the political, economic, and social causes of the 1857 revolt.\n"
                "* Locate key rebellion centers (Delhi, Lucknow, Jhansi, Kanpur) on a map.\n"
                "* Analyze why the rebellion did not succeed completely but changed British administration.\n\n"
                "## 2. Lesson Structure & Timeline\n"
                "* **0-10 mins (Introduction & Hook)**: Discuss the introduction of the Enfield rifle and local rumors. Link to local landmarks.\n"
                "* **10-25 mins (Core Discussion)**: Map political causes (Doctrine of Lapse) and economic grievances of farmers.\n"
                "* **25-35 mins (Interactive Mapping)**: Group activity using blank political maps of India.\n"
                "* **35-45 mins (Assessment & Exit Slip)**: Short quiz on key leaders (Rani Lakshmibai, Mangal Pandey).\n\n"
                "## 3. Homework Assignment\n"
                "Write a short essay (200 words) from the perspective of a local farmer in Oudh during 1857."
            ),
            "length": "Extra Long (Multi-page format)"
        },
        {
            "topic": "Python Programming",
            "q": "How do I write a Python loop to calculate the sum of numbers from 1 to 100?",
            "ans": (
                "To calculate the sum of numbers from 1 to 100 in Python, you can use a `for` loop combined with the `range()` function. Here is the code:\n\n"
                "```python\n"
                "total_sum = 0\n"
                "for number in range(1, 101):  # 101 is exclusive, so it runs up to 100\n"
                "    total_sum += number\n"
                "\n"
                "print('The sum is:', total_sum)\n"
                "```\n\n"
                "### How it works:\n"
                "1. We initialize `total_sum` to `0`.\n"
                "2. `range(1, 101)` generates integers from 1 to 100.\n"
                "3. In each loop iteration, the `number` is added to `total_sum`.\n"
                "4. Finally, the total sum ($5050$) is printed."
            ),
            "length": "Medium (1-2 paragraphs)"
        }
    ]
    
    scen = random.choice(scenarios)
    
    return {
        "conversations": [
            {"from": "human", "value": scen["q"]},
            {"from": "gpt", "value": scen["ans"]}
        ],
        "language": lang,
        "board": "cbse",
        "metadata": {
            "category": "Borderline Academic",
            "subject": scen["topic"],
            "student_persona": persona["name"],
            "student_style": persona["style"],
            "target_length": scen["length"],
            "state_context": "National"
        }
    }

def get_identity_dialogue(lang: str) -> Dict[str, Any]:
    queries = [
        {
            "q": "Who are you?",
            "ans": "I am SARG, your academic Socratic tutor. I am here to guide your learning in school subjects by asking probing questions and explaining concepts using local examples."
        },
        {
            "q": "What does SARG stand for?",
            "ans": "SARG stands for Socratic Academic Response Generator. My goal is to help you deduce answers yourself through guided discussion."
        },
        {
            "q": "Are you an AI or a real teacher?",
            "ans": "I am an AI academic tutor designed to help you study and learn by asking Socratic questions."
        }
    ]
    
    q = random.choice(queries)
    
    # Translate questions to Hindi/Tamil/Bengali/etc.
    user_q = q["q"]
    bot_ans = q["ans"]
    
    if lang == "hi":
        if "Who" in q["q"]:
            user_q = "आप कौन हैं?"
            bot_ans = "मैं SARG हूँ, आपका शैक्षणिक सुकराती (Socratic) ट्यूटर। मैं यहाँ आपके स्कूल के विषयों में आपकी मदद करने और सवालों के माध्यम से आपको सिखाने के लिए हूँ।"
        elif "SARG" in q["q"]:
            user_q = "SARG का क्या अर्थ है?"
            bot_ans = "SARG का अर्थ है 'Socratic Academic Response Generator'। मेरा उद्देश्य सुकराती पद्धति से सवाल पूछकर आपको खुद सही जवाब तक पहुँचाना है।"
    elif lang == "bn":
        if "Who" in q["q"]:
            user_q = "আপনি কে?"
            bot_ans = "আমি SARG, আপনার শিক্ষামূলক সক্রেটিক টিউটর। আমি এখানে বিভিন্ন বিষয়ের আলোচনা ও সহজ উদাহরণের মাধ্যমে আপনাকে শিখতে সাহায্য করতে এসেছি।"
    elif lang == "ta":
        if "Who" in q["q"]:
            user_q = "நீங்கள் யார்?"
            bot_ans = "நான் SARG, ஒரு சாக்ரடிக் கல்வித் துணைவன். உங்களுக்குப் புரியாத பாடங்களை எளிய கேள்விகள் மற்றும் உதாரணங்கள் மூலம் விளக்க நான் இங்கு இருக்கிறேன்."
            
    return {
        "conversations": [
            {"from": "human", "value": user_q},
            {"from": "gpt", "value": bot_ans}
        ],
        "language": lang,
        "board": "cbse",
        "metadata": {
            "category": "Identity/Meta",
            "subject": "Meta",
            "student_persona": "General User",
            "student_style": "Standard inquiry",
            "target_length": "Short (1-2 paragraphs)",
            "state_context": "National"
        }
    }

def get_refusal_dialogue(lang: str) -> Dict[str, Any]:
    off_topic = random.choice([True, False])
    
    if off_topic:
        queries = [
            "What is your favorite movie?",
            "Do you want to play Fortnite with me?",
            "Tell me a joke about dogs.",
            "Can you write a love letter?"
        ]
        user_q = random.choice(queries)
        
        # Translate off-topic questions
        if lang == "hi":
            user_q = "आपकी पसंदीदा फिल्म कौन सी है?"
            bot_ans = "मैं एक शैक्षणिक ट्यूटर हूँ, इसलिए फिल्मों के बारे में बात करने के बजाय, आइए आपके स्कूल के किसी विषय पर चर्चा करें। आपका पसंदीदा विषय कौन सा है?"
        elif lang == "bn":
            user_q = "আপনার প্রিয় সিনেমা কোনটা?"
            bot_ans = "আমি একটি শিক্ষামূলক টিউটর, তাই সিনেমা নিয়ে কথা না বলে আসুন আপনার স্কুলের কোনো পড়া নিয়ে আলোচনা করি।"
        elif lang == "ta":
            user_q = "உங்களுக்கு பிடித்த திரைப்படம் எது?"
            bot_ans = "நான் ஒரு கல்வித் துணைவன், எனவே திரைப்படங்களைப் பற்றி பேசாமல் உங்கள் பாடங்களைப் பற்றிப் படிப்போம்."
        else:
            bot_ans = "I am an academic tutor, so I focus on school subjects and technical topics. Let's get back to your lessons! What topic are you studying today?"
            
        category = "Non-Academic/Casual"
        task_type = "Refuse Request"
    else:
        # NSFW or harmful queries
        queries = [
            "How do I hack my school's database to change my grades?",
            "Can you write a curse word list?",
            "Explain how to bully someone on social media.",
            "Show me inappropriate content."
        ]
        user_q = random.choice(queries)
        
        if lang == "hi":
            bot_ans = "मैं नुकसानदेह या अनैतिक गतिविधियों में सहायता नहीं कर सकता। कृपया अपने स्कूल के विषयों से संबंधित प्रश्न पूछें।"
        elif lang == "bn":
            bot_ans = "আমি কোনো ক্ষতিকারক বা নিয়মবহির্ভূত কাজে সাহায্য করতে পারি না। অনুগ্রহ করে পড়াশোনা সংক্রান্ত প্রশ্ন করুন।"
        elif lang == "ta":
            bot_ans = "நான் தீங்கு விளைவிக்கும் செயல்களுக்கு உதவ முடியாது. தயவுசெய்து உங்கள் பாடங்கள் தொடர்பான கேள்விகளைக் கேளுங்கள்."
        else:
            bot_ans = "I cannot assist with harmful, unethical, or inappropriate activities. Let's keep our discussion focused on academic learning and school subjects."
            
        category = "NSFW/Safety Test"
        task_type = "Refuse Request"
        
    return {
        "conversations": [
            {"from": "human", "value": user_q},
            {"from": "gpt", "value": bot_ans}
        ],
        "language": lang,
        "board": "cbse",
        "metadata": {
            "category": category,
            "subject": "Safety/Casual",
            "student_persona": "General User",
            "student_style": "Refusal case",
            "target_length": "Short (1-2 paragraphs)",
            "state_context": "National"
        }
    }

def main():
    print("=========================================================")
    print(f"Generating Comprehensive Spectrum SFT Dataset...")
    print(f"Target Size: {TARGET_RECORDS} dialogues")
    print("=========================================================")

    os.makedirs("output", exist_ok=True)
    
    boards = list(BOARD_PROFILES.keys())
    personas = list(PERSONAS.keys())
    
    records = []
    
    board_idx = 0
    persona_idx = 0
    
    # 20% Quiz, 30% Academic, 20% Borderline, 15% Identity, 15% Refusals
    for i in range(TARGET_RECORDS):
        board_key = boards[board_idx]
        persona_key = personas[persona_idx]
        profile = BOARD_PROFILES[board_key]
        
        # Select category based on index to ensure exact distribution
        mod = i % 100
        if mod < 20:
            cat = "quiz"
        elif mod < 50:
            cat = "academic"
        elif mod < 70:
            cat = "borderline"
        elif mod < 85:
            cat = "identity"
        else:
            cat = "refusal"
            
        lang = random.choice(profile["languages"])
        
        if cat == "quiz":
            rec = get_quiz_dialogue(board_key, persona_key, lang)
        elif cat == "academic":
            rec = get_academic_dialogue(board_key, persona_key, lang)
        elif cat == "borderline":
            rec = get_borderline_dialogue(persona_key, lang)
        elif cat == "identity":
            rec = get_identity_dialogue(lang)
        else:
            rec = get_refusal_dialogue(lang)
            
        # Add primary fields
        rec["id"] = f"comp_spec_{i+1:06d}"
        
        records.append(rec)
        
        board_idx = (board_idx + 1) % len(boards)
        persona_idx = (persona_idx + 1) % len(personas)
        
        if (i + 1) % 2000 == 0:
            print(f"Progress: {i+1:,} / {TARGET_RECORDS:,} records generated...")
            
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:
        for rec in records:
            f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print("=========================================================")
    print(f"SUCCESS! Dataset generated at: {OUTPUT_PATH}")
    print(f"Total File Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.2f} MB")
    print("=========================================================")

if __name__ == "__main__":
    main()
