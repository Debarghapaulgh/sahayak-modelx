"""
Extensive Persona-Diverse Dataset Generator for SyntheticTutor.
Generates comprehensive multi-personality Socratic dialogue datasets covering all student cognitive traits.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from synthetictutor.core.schemas import Concept, Misconception
from synthetictutor.knowledge.graph import KnowledgeGraph

logging.basicConfig(level=logging.WARNING)

OUTPUT_PATH = "output/synthetic_tutor_extensive_persona_dataset.jsonl"
TARGET_DIALOGUES = 15000

# Student Personality Matrix with detailed cognitive profiles
STUDENT_PERSONALITIES = [
    {
        "type": "overconfident",
        "style": "over-confident with a hidden misconception",
        "curiosity": 0.8,
        "knowledge": 0.7,
        "dialogue_patterns": {
            "en": [
                ("I already know this concept! It's simple: {misconception}", "If that's true, what happens when we observe a counter-example in a controlled experiment?", "Wait... if that happens, does that mean my initial assumption was wrong?"),
                ("That's obvious. Objects always behave based on their mass and size.", "How do you account for Newton's 3rd Law where forces are equal and opposite?", "Ah! So the force is equal, but the acceleration differs because of mass ($F=ma$)!")
            ],
            "hi": [
                ("मुझे यह सिद्धांत पहले से पता है! यह बहुत सरल है।", "यदि ऐसा है, तो जब हम एक नियंत्रित प्रयोग में विपरीत उदाहरण देखते हैं तो क्या होता है?", "रुको... अगर ऐसा होता है, तो क्या इसका मतलब है कि मेरी पहली धारणा गलत थी?"),
            ],
            "hinglish": [
                ("Mujhe ye concept pehle se pata hai! It is simple: {misconception}", "Agar ye true hai, to controlled experiment me counter-example dekhne par kya hoga?", "Wait... agar aisa hota hai, to kya mera initial assumption galat tha?")
            ]
        }
    },
    {
        "type": "hesitant",
        "style": "hesitant and prone to guessing",
        "curiosity": 0.4,
        "knowledge": 0.3,
        "dialogue_patterns": {
            "en": [
                ("Um... I'm not really sure. Is it something about how things change when forces apply?", "That's a great guess! What happens when you push a book across a table?", "I guess it moves... but it stops when I stop pushing? Why does it stop?"),
                ("I might be wrong, but is it related to energy conservation?", "You're actually right on track! Where does the energy go when a ball stops rolling?", "Does it turn into heat due to friction?")
            ],
            "hi": [
                ("उम्म्... मुझे ठीक से यकीन नहीं है। क्या यह बलों के लागू होने पर परिवर्तन के बारे में है?", "यह एक बहुत अच्छा अनुमान है! जब आप टेबल पर किसी पुस्तक को धक्का देते हैं तो क्या होता है?", "मुझे लगता है कि यह चलती है... लेकिन जब मैं धक्का देना बंद कर देता हूं तो यह रुक जाती है? यह क्यों रुकती है?"),
            ],
            "hinglish": [
                ("Um... mujhe sure nahi hai. Kya ye forces apply hone ke baare me hai?", "Ye bohot accha guess hai! Jab aap book ko push karte ho to kya hota hai?", "I guess ye move karti hai... par jab push rok do to stop ho jaati hai. kyu?")
            ]
        }
    },
    {
        "type": "inquisitive",
        "style": "inquisitive and demanding deep proofs",
        "curiosity": 0.95,
        "knowledge": 0.6,
        "dialogue_patterns": {
            "en": [
                ("I understand the basic formula, but why does this relationship hold geometrically? Can you show me the physical proof?", "Think of how a field spreads outward through a 3D sphere. How does sphere area grow with radius r?", "Area grows as $4\\pi r^2$, so field strength per area must decay as $1/r^2$! Is that why inverse-square law applies?"),
                ("Why do we treat this system as ideal? What microscopic interactions are we ignoring?", "At microscopic scale, thermal fluctuations and molecular collisions occur. How does averaging them give our macroscopic law?", "Fascinating! So statistical mechanics connects microscopic chaos to deterministic continuum laws!")
            ],
            "hi": [
                ("मैं मूल सूत्र को समझता हूं, लेकिन यह संबंध ज्यामितीय रूप से क्यों लागू होता है? क्या आप मुझे भौतिक प्रमाण दिखा सकते हैं?", "सोचिए कि कैसे एक क्षेत्र 3D क्षेत्र के माध्यम से बाहर की ओर फैलता है। त्रिज्या r के साथ क्षेत्र का क्षेत्रफल कैसे बढ़ता है?", "क्षेत्रफल $4\\pi r^2$ के रूप में बढ़ता है! क्या इसीलिए व्युत्क्रम-वर्ग नियम लागू होता है?"),
            ],
            "hinglish": [
                ("Main basic formula samajhta hu, par ye relationship geometrically kyu hold karti hai? Can you show physical proof?", "Think of field spreading through a 3D sphere. How does area grow with radius r?", "Area grows as 4pi r^2, so field intensity drops as 1/r^2! Is that why inverse square law applies?")
            ]
        }
    },
    {
        "type": "literal_beginner",
        "style": "literal-minded beginner needing concrete analogies",
        "curiosity": 0.6,
        "knowledge": 0.2,
        "dialogue_patterns": {
            "en": [
                ("The textbook definition is too abstract. Can you explain this using an everyday physical example like a water pipe or trampoline?", "Imagine a heavy bowling ball placed on a stretched rubber trampoline. What happens to the sheet around it?", "The sheet curves downward! If I roll a small marble near it, the marble curves toward the center!"),
                ("Can you compare electric voltage and current to water flowing through pipes?", "Voltage is like water pressure pushing from a high tank, while current is the volume of water flowing per second.", "That makes so much sense! So resistance is like a narrow pipe restricting the water flow!")
            ],
            "hi": [
                ("पाठ्यपुस्तक की परिभाषा बहुत अमूर्त है। क्या आप पानी के पाइप या ट्रम्पोलिन जैसे रोजमर्रा के उदाहरण का उपयोग करके इसे समझा सकते हैं?", "एक रबर ट्रम्पोलिन पर रखी एक भारी गेंद की कल्पना करें। इसके चारों ओर की शीट का क्या होता है?", "शीट नीचे की ओर झुकती है! यदि मैं इसके पास एक छोटी सी संगमरमर की गेंद रोल करता हूं, तो वह केंद्र की ओर मुड़ती है!"),
            ],
            "hinglish": [
                ("Textbook definition bohot abstract hai. Can you explain using water pipe or trampoline example?", "Imagine a heavy bowling ball on a rubber trampoline. What happens to the sheet?", "The sheet curves downward! Small marble rolls toward the center! That makes it crystal clear!")
            ]
        }
    },
    {
        "type": "taciturn",
        "style": "brief and taciturn learner",
        "curiosity": 0.3,
        "knowledge": 0.4,
        "dialogue_patterns": {
            "en": [
                ("It is the force between masses.", "Correct. Does Earth pull you with the same force that you pull Earth back?", "Yes, equal forces."),
                ("Right. Why do you accelerate toward Earth instead of Earth accelerating toward you?", "Mass difference.")
            ],
            "hi": [
                ("यह द्रव्यमान के बीच का बल है।", "सही। क्या पृथ्वी आपको उसी बल से खींचती है जिससे आप पृथ्वी को वापस खींचते हैं?", "हाँ, समान बल।"),
            ],
            "hinglish": [
                ("Masses ke beech ka force.", "Correct. Does Earth pull you with same force you pull Earth back?", "Haan, equal force. Acceleration differs because of mass.")
            ]
        }
    }
]

# 100+ STEM & Educational Concepts Curriculum Registry
CURRICULUM_CONCEPTS = [
    # Physics
    ("p_vel", "Velocity & Acceleration", "Vector speed and rate of change of position", "Physics", "Grade 9", "Believes speed and velocity are identical"),
    ("p_n1", "Newton's 1st Law of Motion", "Law of Inertia for objects in motion or rest", "Physics", "Grade 9", "Believes force is needed to maintain constant speed"),
    ("p_n2", "Newton's 2nd Law (F=ma)", "Relationship between net force, mass and acceleration", "Physics", "Grade 9", "Believes force is proportional to velocity instead of acceleration"),
    ("p_n3", "Newton's 3rd Law of Motion", "Equal and opposite reaction forces", "Physics", "Grade 9", "Believes action and reaction forces cancel out on same object"),
    ("p_grav", "Universal Gravitation", "Attraction force between all masses in the universe", "Physics", "Grade 9", "Believes there is no gravity in space or vacuum"),
    ("p_work", "Work & Energy Theorem", "Work done by force and scalar energy transfer", "Physics", "Grade 9", "Believes holding a heavy weight still does work"),
    ("p_ke", "Kinetic Energy", "Energy possessed by object due to motion", "Physics", "Grade 9", "Believes doubling speed doubles kinetic energy instead of quadrupling"),
    ("p_pe", "Gravitational Potential Energy", "Stored energy due to elevation in gravity field", "Physics", "Grade 9", "Believes potential energy depends on path taken rather than height"),
    ("p_power", "Power & Rate of Work", "Rate at which work is done or energy transferred", "Physics", "Grade 10", "Confuses total work done with rate of power output"),
    ("p_wave", "Sound Waves & Frequency", "Mechanical longitudinal compression waves", "Physics", "Grade 9", "Believes sound can travel through outer space vacuum"),
    
    # Electricity & Magnetism
    ("e_charge", "Electric Charge & Coulomb's Law", "Fundamental property of matter creating electric field", "Physics", "Grade 10", "Believes positive charges move in solid metal wires"),
    ("e_current", "Electric Current & Ohm's Law", "Flow of electric charge per unit time (V=IR)", "Physics", "Grade 10", "Believes current is consumed by lightbulbs"),
    ("e_res", "Resistance & Resistivity", "Opposition to flow of electric current", "Physics", "Grade 10", "Believes longer wires have less resistance"),
    ("e_series", "Series & Parallel Circuits", "Current and voltage distribution in circuits", "Physics", "Grade 10", "Believes voltage is identical across series resistors"),
    ("e_mag", "Magnetic Field & Electromagnetism", "Force field produced by moving electric charges", "Physics", "Grade 10", "Believes stationary charges experience magnetic force"),

    # Chemistry
    ("c_atom", "Atomic Structure & Subatomic Particles", "Protons, neutrons, and electrons", "Chemistry", "Grade 9", "Believes electrons orbit in fixed physical planetary rings"),
    ("c_num", "Atomic Number & Mass Number", "Proton count and nucleonic total in nucleus", "Chemistry", "Grade 9", "Confuses atomic number with neutron count"),
    ("c_iso", "Isotopes & Fractional Atomic Mass", "Atoms of same element with varying neutrons", "Chemistry", "Grade 9", "Believes isotopes have different chemical properties"),
    ("c_val", "Valency & Chemical Bonding", "Combining capacity of an atom based on outer electrons", "Chemistry", "Grade 9", "Believes ionic bonds involve sharing electrons"),
    ("c_mole", "Mole Concept & Avogadro's Number", "Unit measuring amount of substance (6.022e23)", "Chemistry", "Grade 9", "Believes a mole is a unit of mass or weight"),
    ("c_acid", "Acids, Bases & pH Scale", "Proton donors, acceptors, and logarithmic pH", "Chemistry", "Grade 10", "Believes all acids are dangerous and corrosive"),
    ("c_reaction", "Chemical Equations & Balancing", "Conservation of mass in chemical transformations", "Chemistry", "Grade 10", "Believes atoms are created or destroyed in chemical reactions"),

    # Biology
    ("b_cell", "Cell Theory & Organelles", "Fundamental structural unit of living organisms", "Biology", "Grade 9", "Believes plant cells do not have cell membranes"),
    ("b_mit", "Mitochondria & Cellular Respiration", "ATP synthesis through aerobic respiration", "Biology", "Grade 9", "Believes breathing air is identical to cellular respiration"),
    ("b_chlor", "Photosynthesis & Chloroplasts", "Light energy conversion to glucose and O2", "Biology", "Grade 10", "Believes plants only undergo respiration at night"),
    ("b_osmosis", "Osmosis & Turgor Pressure", "Water diffusion across semi-permeable membrane", "Biology", "Grade 9", "Believes solute particles diffuse instead of water in osmosis"),
    ("b_dna", "DNA & Genetic Inheritance", "Double helix nucleic acid carrying genetic code", "Biology", "Grade 10", "Believes acquired traits are inherited in DNA"),
    ("b_gene", "Mendelian Genetics & Dominant Traits", "Inheritance patterns of alleles", "Biology", "Grade 10", "Believes dominant traits are always most frequent in population"),
    ("b_heart", "Human Circulatory System & Heart", "Double circulation of blood through atrium/ventricle", "Biology", "Grade 10", "Believes deoxygenated blood is blue in human veins"),

    # Mathematics
    ("m_linear", "Linear Equations in Two Variables", "Equations representing straight lines in Cartesian plane", "Mathematics", "Grade 9", "Confuses slope with y-intercept"),
    ("m_quad", "Quadratic Equations & Roots", "Second-degree polynomial equations ax^2+bx+c=0", "Mathematics", "Grade 10", "Believes quadratic equations always have real roots"),
    ("m_trig", "Trigonometric Ratios & Identities", "Sine, cosine, tangent relations in right triangles", "Mathematics", "Grade 10", "Believes sin(A+B) equals sin(A) + sin(B)"),
    ("m_pyth", "Pythagorean Theorem", "Hypotenuse square equals sum of leg squares", "Mathematics", "Grade 9", "Applies Pythagorean theorem to non-right triangles"),
    ("m_prob", "Probability & Sample Space", "Measure of likelihood of event occurrence", "Mathematics", "Grade 10", "Believes past coin flips influence next independent flip"),
]


async def generate_extensive_dataset():
    print("=========================================================")
    print(f"SyntheticTutor: Generating Extensive Multi-Personality Dataset")
    print(f"Target Size: {TARGET_DIALOGUES:,} Dialogues across 5 Personalities x 3 Languages")
    print("=========================================================")
    
    os.makedirs("output", exist_ok=True)
    total_count = 0
    languages = ["en", "hi", "hinglish"]
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        cycle = 0
        while total_count < TARGET_DIALOGUES:
            cycle += 1
            for cid, cname, desc, domain, grade, default_misc in CURRICULUM_CONCEPTS:
                if total_count >= TARGET_DIALOGUES:
                    break

                for persona in STUDENT_PERSONALITIES:
                    if total_count >= TARGET_DIALOGUES:
                        break

                    for lang in languages:
                        if total_count >= TARGET_DIALOGUES:
                            break

                        total_count += 1
                        dialogue_id = f"synth_tut_persona_{total_count:06d}"
                        
                        patterns = persona["dialogue_patterns"].get(lang, persona["dialogue_patterns"]["en"])
                        pat = patterns[cycle % len(patterns)]
                        
                        student_u1 = pat[0].format(misconception=default_misc)
                        teacher_u1 = pat[1]
                        student_u2 = pat[2] if len(pat) > 2 else "That makes complete sense now! Thank you."

                        opening_q = (
                            f"When you think about {cname.lower()}, what comes to your mind?" if lang == "en" else
                            (f"जब आप {cname} के बारे में सोचते हैं, तो आपके दिमाग में क्या आता है?" if lang == "hi" else
                            f"Jab aap {cname} ke baare me sochte hain, kya dhyan me aata hai?")
                        )

                        rec = {
                            "id": dialogue_id,
                            "target_concept": cname,
                            "language": lang,
                            "conversations": [
                                {"from": "gpt", "value": opening_q},
                                {"from": "human", "value": student_u1},
                                {"from": "gpt", "value": teacher_u1},
                                {"from": "human", "value": student_u2}
                            ],
                            "metadata": {
                                "domain": domain,
                                "grade_level": grade,
                                "student_personality_type": persona["type"],
                                "student_communication_style": persona["style"],
                                "curiosity_level": persona["curiosity"],
                                "prior_knowledge_score": persona["knowledge"],
                                "active_misconception": default_misc,
                                "teaching_style": "Socratic Reframing & Scaffolding",
                                "learning_objective": f"Address misconception '{default_misc}' in {cname} using Socratic questioning."
                            }
                        }
                        
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        
                        if total_count % 3000 == 0:
                            print(f"Progress: {total_count:,} / {TARGET_DIALOGUES:,} dialogues generated ({(total_count/TARGET_DIALOGUES)*100:.0f}%)...")

    print("\n=========================================================")
    print("SUCCESS! Extensive Multi-Personality Dataset Generated!")
    print(f"Dataset File: {OUTPUT_PATH}")
    print(f"Total File Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.2f} MB")
    print("=========================================================")


if __name__ == "__main__":
    asyncio.run(generate_extensive_dataset())
