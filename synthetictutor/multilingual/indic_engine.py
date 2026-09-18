"""
Expanded Multilingual Indic Engine supporting 12 Major Indian Languages.
Supports English, Hindi, Hinglish, Tamil, Telugu, Bengali, Marathi, Kannada, Gujarati, Malayalam, Odia, and Punjabi.
"""

from typing import Dict, Any, List

INDIC_LANGUAGES = {
    "en": {"name": "English", "script": "Latin"},
    "hi": {"name": "Hindi", "script": "Devanagari"},
    "hinglish": {"name": "Hinglish", "script": "Roman/Code-Switching"},
    "ta": {"name": "Tamil", "script": "Tamil"},
    "te": {"name": "Telugu", "script": "Telugu"},
    "bn": {"name": "Bengali", "script": "Bengali"},
    "mr": {"name": "Marathi", "script": "Devanagari"},
    "kn": {"name": "Kannada", "script": "Kannada"},
    "gu": {"name": "Gujarati", "script": "Gujarati"},
    "ml": {"name": "Malayalam", "script": "Malayalam"},
    "or": {"name": "Odia", "script": "Odia"},
    "pa": {"name": "Punjabi", "script": "Gurmukhi"},
}

OPENING_QUESTIONS = {
    "en": "When you think about {concept}, what comes to your mind?",
    "hi": "जब आप {concept} के बारे में सोचते हैं, तो आपके दिमाग में क्या आता है?",
    "hinglish": "Jab aap {concept} ke baare me sochte hain, kya dhyan me aata hai?",
    "ta": "{concept} பற்றி யோசிக்கும்போது, உங்கள் நினைவுக்கு என்ன வருகிறது?",
    "te": "మీరు {concept} గురించి ఆలోచించినప్పుడు, మీ మనస్సులోకి ఏమి వస్తుంది?",
    "bn": "{concept} সম্পর্কে চিন্তা করলে আপনার মনে কী আসে?",
    "mr": "तुम्ही {concept} बद्दल विचार करता तेव्हा तुमच्या मनात काय येते?",
    "kn": "ನೀವು {concept} ಬಗ್ಗೆ ಯೋಚಿಸಿದಾಗ ನಿಮ್ಮ ಮನಸ್ಸಿಗೆ ಏನು ಬರುತ್ತದೆ?",
    "gu": "જ્યારે તમે {concept} વિશે વિચારો છો, ત્યારે તમારા મનમાં શું આવે છે?",
    "ml": "{concept}-നെ കുറിച്ച് ചിന്തിക്കുമ്പോൾ നിങ്ങളുടെ മനസ്സിൽ എന്ത് വരുന്നു?",
    "or": "{concept} ବିଷୟରେ ଚିନ୍ତା କଲାବେଳେ ଆପଣଙ୍କ ମନକୁ କ’ଣ ଆସେ?",
    "pa": "ਜਦੋਂ ਤੁਸੀਂ {concept} ਬਾਰੇ ਸੋਚਦੇ ਹੋ, ਤੁਹਾਡੇ ਮਨ ਵਿੱਚ ਕੀ ਆਉਂਦਾ ਹੈ?",
}


def get_indic_opening_question(lang: str, concept: str) -> str:
    template = OPENING_QUESTIONS.get(lang.lower(), OPENING_QUESTIONS["en"])
    return template.format(concept=concept)
