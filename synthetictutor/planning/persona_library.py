"""
Comprehensive Student Persona Library (10 Cognitive Profiles).
Extends StudentPersona definitions with diverse learning styles, anxiety levels, and inquiry patterns.
"""

from typing import List, Dict, Any

STUDENT_PERSONA_LIBRARY: List[Dict[str, Any]] = [
    {
        "id": "p_overconfident",
        "name": "Overconfident Learner",
        "style": "over-confident with a hidden misconception",
        "curiosity": 0.8,
        "knowledge": 0.7,
        "traits": "Asserts flawed assumptions with high confidence until shown experimental counter-examples.",
        "student_pattern": "I already know this concept! It is simple: {misconception}",
        "teacher_pattern": "If that assumption holds true, how do you explain what happens in this controlled counter-example?",
        "resolution_pattern": "Wait... if that happens in the experiment, does that mean my initial assumption was wrong?"
    },
    {
        "id": "p_hesitant",
        "name": "Hesitant & Prone to Guessing",
        "style": "hesitant and prone to guessing",
        "curiosity": 0.4,
        "knowledge": 0.3,
        "traits": "Doubts own reasoning, speaks tentatively, needs reassuring scaffolding hints.",
        "student_pattern": "Um... I'm not really sure. Is it something about how forces apply?",
        "teacher_pattern": "That's a very intuitive start! What happens when you push a book across a table?",
        "resolution_pattern": "I guess it moves... but when I stop pushing, friction stops it. Is friction a force?"
    },
    {
        "id": "p_inquisitive",
        "name": "Inquisitive Proof-Seeker",
        "style": "inquisitive and demanding deep proofs",
        "curiosity": 0.95,
        "knowledge": 0.6,
        "traits": "Asks 'Why?' continuously, demands mathematical derivations and physical symmetry arguments.",
        "student_pattern": "I see the formula, but why does it decay as 1/r^2 geometrically? Can you prove it?",
        "teacher_pattern": "Think of field lines spreading through a 3D sphere. How does sphere surface area grow with radius r?",
        "resolution_pattern": "Area grows as 4pi r^2, so field intensity per unit area must drop as 1/r^2! That geometric proof makes complete sense."
    },
    {
        "id": "p_literal_beginner",
        "name": "Literal Concrete Analogist",
        "style": "literal-minded beginner needing concrete analogies",
        "curiosity": 0.6,
        "knowledge": 0.2,
        "traits": "Struggles with abstract definitions; requires physical everyday analogies like water pipes or trampolines.",
        "student_pattern": "The textbook definition is too abstract. Can you explain using a physical object like a water pipe?",
        "teacher_pattern": "Imagine water pressure in a high tank pushing through a pipe. Voltage is the pressure, current is the water flow.",
        "resolution_pattern": "That makes so much sense! So electrical resistance is just like a narrow pipe restricting water!"
    },
    {
        "id": "p_taciturn",
        "name": "Brief & Taciturn Learner",
        "style": "brief and taciturn learner",
        "curiosity": 0.3,
        "knowledge": 0.4,
        "traits": "Gives minimal one-word answers, requiring targeted probing questions.",
        "student_pattern": "Objects pulling each other.",
        "teacher_pattern": "Correct. Does Earth pull you with the exact same force that you pull Earth back?",
        "resolution_pattern": "Yes, equal forces. But I move more because my mass is smaller."
    },
    {
        "id": "p_anxious_test_taker",
        "name": "Anxious Exam-Focused Learner",
        "style": "anxious exam-focused problem solver",
        "curiosity": 0.5,
        "knowledge": 0.5,
        "traits": "Asks 'Will this be on the exam?' and seeks step-by-step numerical problem-solving templates.",
        "student_pattern": "How do I solve this step-by-step in an exam question without losing marks?",
        "teacher_pattern": "First identify given variables, write the primary equation, substitute values with units, and state the final answer.",
        "resolution_pattern": "Got it! So if I follow this 4-step template, I can solve any numerical problem reliably."
    },
    {
        "id": "p_visual_spatial",
        "name": "Visual-Spatial Learner",
        "style": "visual-spatial diagrammatic thinker",
        "curiosity": 0.85,
        "knowledge": 0.5,
        "traits": "Thinks in 3D geometry, ray diagrams, and structural flowcharts.",
        "student_pattern": "Can you draw a mental picture or diagram of how rays or field vectors behave here?",
        "teacher_pattern": "Picture two parallel ray lines entering a convex lens. They bend inward and intersect at a single focal point F.",
        "resolution_pattern": "I can visualize the light rays focusing at F clearly now! That mental diagram clears it up."
    },
    {
        "id": "p_formula_memorizer",
        "name": "Formula Memorizer lacking Intuition",
        "style": "formula memorizer lacking physical intuition",
        "curiosity": 0.4,
        "knowledge": 0.6,
        "traits": "Memorizes equations by heart but struggles to explain physical meaning.",
        "student_pattern": "I know the formula F=ma, but what does mass actually mean physically when pushing a shopping cart?",
        "teacher_pattern": "Mass is an object's resistance to changing speed. A heavy cart resists acceleration much more than an empty one.",
        "resolution_pattern": "Ah! So mass is basically 'sluggishness' or inertia when forced to change speed!"
    },
    {
        "id": "p_curious_explainer",
        "name": "Curious Self-Explainer",
        "style": "curious self-explainer",
        "curiosity": 0.9,
        "knowledge": 0.6,
        "traits": "Likes to re-explain concepts back to the tutor in their own words to verify understanding.",
        "student_pattern": "Let me try re-explaining this in my own words to see if I truly understand it.",
        "teacher_pattern": "Please do! Re-explaining in your own words is the best test of conceptual mastery.",
        "resolution_pattern": "So energy is never created or destroyed, only transformed from kinetic to thermal due to friction!"
    },
    {
        "id": "p_struggling_reader",
        "name": "Struggling Reader",
        "style": "struggling reader needing simplified vocabulary",
        "curiosity": 0.5,
        "knowledge": 0.2,
        "traits": "Needs simple vocabulary, short sentences, and one single concept step at a time.",
        "student_pattern": "Can you use simpler words? The big scientific terms confuse me.",
        "teacher_pattern": "Sure! Imagine pushing a toy car. If you push harder, it goes faster. Force makes speed change.",
        "resolution_pattern": "That is easy to understand! More push means faster change."
    }
]
