"""
generate_localised_context_dataset.py
Generates a culturally-adaptive, topic-aligned localized Socratic dialogue dataset (5,000 records)
spanning 10 STEM topics, 7 school boards, 5 personalities, and 12 Indic languages.
"""

import os
import json
import random
from typing import List, Dict, Any

OUTPUT_PATH = "output/localised_sarg_dialogues.jsonl"
TARGET_DIALOGUES = 5000

# 1. Regional Board Profiles & Cultural Markers
REGIONAL_PROFILES = {
    "cbse": {
        "board_name": "CBSE (Central Board of Secondary Education)",
        "region": "National (Urban/Semi-Urban)",
        "languages": ["en", "hi", "hinglish"],
        "soils": ["standard garden soil", "potting soil"],
        "crops": ["wheat", "paddy"],
        "festivals": ["Diwali", "Holi"],
        "cultural_objects": ["guitars", "fairy lights", "cars", "ovens"],
        "local_terms": {"soil": "soil", "pond": "park pond", "fertiliser": "fertiliser", "crop": "crop"}
    },
    "upboard": {
        "board_name": "UPMSP (Uttar Pradesh Board)",
        "region": "Uttar Pradesh",
        "languages": ["hi", "hinglish", "en"],
        "soils": ["domat mitti (alluvial loam)", "kachhar mitti (sandy loam)"],
        "crops": ["ganna (sugarcane)", "gehun (wheat)", "sarson (mustard)"],
        "festivals": ["Dussehra", "Holi", "Makar Sankranti"],
        "cultural_objects": ["tubewell", "chulha (stove)", "bailgadi (bullock cart)", "ghirni (pulley)"],
        "local_terms": {"soil": "domat mitti", "pond": "khet-pond", "fertiliser": "gobar khaad", "crop": "ganna"}
    },
    "wbboard": {
        "board_name": "WBBSE (West Bengal Board)",
        "region": "West Bengal",
        "languages": ["bn", "en", "hi"],
        "soils": ["clayey-loam deltaic soil", "kumartuli clay"],
        "crops": ["aman dhan (monsoon rice)", "boro dhan (winter rice)", "pat (jute)"],
        "festivals": ["Durga Puja", "Kali Puja"],
        "cultural_objects": ["pukur (pond)", "nouka (country boat)", "charkha (spinning wheel)", "clay pots"],
        "local_terms": {"soil": "ente mati", "pond": "pukur", "fertiliser": "gobar saar", "crop": "dhan"}
    },
    "tnboard": {
        "board_name": "TNSCERT (Tamil Nadu Board)",
        "region": "Tamil Nadu",
        "languages": ["ta", "en", "te"],
        "soils": ["chemman (red soil)", "karisal man (black soil)"],
        "crops": ["nel (paddy)", "thennai (coconut)", "vazhai (banana)"],
        "festivals": ["Pongal", "Karthigai Deepam"],
        "cultural_objects": ["kulam (temple tank)", "mridangam", "pullanguzhal (flute)", "kamatchi vilakku (bronze lamp)"],
        "local_terms": {"soil": "chemman", "pond": "kulam", "fertiliser": "saanam (manure)", "crop": "nel"}
    },
    "mahboard": {
        "board_name": "MSBSHSE (Maharashtra Board)",
        "region": "Maharashtra",
        "languages": ["mr", "en", "hi"],
        "soils": ["regur (black cotton soil)", "tambadi mati (red soil)"],
        "crops": ["kapas (cotton)", "soybean", "jowar"],
        "festivals": ["Ganesh Chaturthi", "Gudi Padwa"],
        "cultural_objects": ["lost-wax bronze molds", "matka (earthen pot)", "shet (farm)", "drip lines"],
        "local_terms": {"soil": "regur mati", "pond": "shet-tale (farm pond)", "fertiliser": "khat", "crop": "kapas"}
    },
    "punboard": {
        "board_name": "PSEB (Punjab Board)",
        "region": "Punjab",
        "languages": ["pa", "en", "hinglish"],
        "soils": ["dakar (heavy clayey soil)", "rohi (loamy soil)"],
        "crops": ["kanak (wheat)", "chona (paddy)", "sarson"],
        "festivals": ["Baisakhi", "Lohri"],
        "cultural_objects": ["nahar (canal)", "dhol drum", "tubewell", "phulkari looms"],
        "local_terms": {"soil": "rohi mitti", "pond": "toba (village pond)", "fertiliser": "khaad", "crop": "kanak"}
    },
    "bihboard": {
        "board_name": "BSEB (Bihar Board)",
        "region": "Bihar",
        "languages": ["hi", "en"],
        "soils": ["sandy alluvial soil", "baluahi mitti"],
        "crops": ["makai (maize)", "litchi", "sugarcane"],
        "festivals": ["Chhath Puja", "Sama Chakeva"],
        "cultural_objects": ["chaur (wetlands)", "sil-batta", "bullock cart", "madhubani canvases"],
        "local_terms": {"soil": "baluahi mitti", "pond": "pokhra (pond)", "fertiliser": "gobar khaad", "crop": "makai"}
    }
}

# 2. 10 STEM Topics & Mappings
TOPICS = {
    "c_light": {
        "name": "Light, Shadows & Reflections",
        "cbse_concept": "Reflection, transparent vs opaque objects, pinhole cameras",
        "localisations": {
            "cbse": "standard mirror reflections and flashlight beams.",
            "upboard": "shadows cast during Dussehra Ramlila effigy burnings.",
            "wbboard": "shadow puppetry screens and transparent clay glasswork.",
            "tnboard": "reflection of Kamatchi vilakku bronze lamps and Tholu Bommalata shadow puppetry.",
            "mahboard": "reflection properties in polished metal utensils used during Gudi Padwa.",
            "punboard": "reflections in glass panels of traditional phulkari embroidery.",
            "bihboard": "mirror reflection alignments used in traditional village melas."
        }
    },
    "c_sound": {
        "name": "Sound & Vibrations",
        "cbse_concept": "Vibration frequency, amplitude, string and air column resonance",
        "localisations": {
            "cbse": "vibrations of guitar strings and tuning forks.",
            "upboard": "sound pitch of classical brass bells and chiming dholaks.",
            "wbboard": "resonance of traditional ektara strings and baul drums.",
            "tnboard": "pitch alterations in mridangam head tension and pullanguzhal (flute) air columns.",
            "mahboard": "sound frequencies of large dhol-tasha during Ganesh Chaturthi processions.",
            "punboard": "frequency changes in dhol drumheads when struck in the center vs the rim.",
            "bihboard": "sound transmission through village metal plates (thalis) during celebrations."
        }
    },
    "c_acids": {
        "name": "Acids, Bases & Salts",
        "cbse_concept": "pH indicators, neutralization reactions, acidic soil treatment",
        "localisations": {
            "cbse": "litmus tests and laboratory acid-base neutralization.",
            "upboard": "washing yellow haldi (turmeric) stains with basic soap vs neutralizing with lemon juice.",
            "wbboard": "using sour imli (tamarind containing tartaric acid) to clean copper puja utensils.",
            "tnboard": "household cleaning of copper lamps using lemon juice and tamarind paste.",
            "mahboard": "testing agricultural soil pH and treating acidic soils using quicklime.",
            "punboard": "neutralizing basic soil using gypsum in canal-irrigated districts.",
            "bihboard": "using sour vinegar (containing acetic acid) to clean household metal vessels."
        }
    },
    "c_micro": {
        "name": "Microorganisms & Preservation",
        "cbse_concept": "Fermentation, yeast, lactobacillus, pickling osmosis",
        "localisations": {
            "cbse": "yeast rising in bakery bread and setting curd in a kitchen.",
            "upboard": "lactic acid fermentation to set dahi (curd) in clay pots.",
            "wbboard": "setting sweet misti doi using lactobacillus culture under warm conditions.",
            "tnboard": "overnight fermentation of idli and dosa batter under tropical coastal heat.",
            "mahboard": "fermenting jalebi batter using yeast and setting fresh buttermilk.",
            "punboard": "preserving traditional pickles (achar) with mustard oil and salt to prevent osmosis.",
            "bihboard": "fermenting native food items like handia and preserving litchis using sugar syrup."
        }
    },
    "c_force": {
        "name": "Force, Friction & Motion",
        "cbse_concept": "Newton's laws, static vs sliding friction, momentum, pulleys",
        "localisations": {
            "cbse": "cars sliding on wet roads and children on playground slides.",
            "upboard": "pulleys (ghirni) to lift water from wells and friction on ropes.",
            "wbboard": "movement of country boats (nouka) in muddy water against drag.",
            "tnboard": "friction and momentum during Kabaddi raids and sliding heavy temple carts.",
            "mahboard": "sliding heavy grain sacks across stone flooring in a local godown.",
            "punboard": "kite flying dynamics, including manjha string tension and wind drag.",
            "bihboard": "sliding a heavy pestle on a traditional grinding stone (sil-batta)."
        }
    },
    "c_metals": {
        "name": "Metals & Alloying",
        "cbse_concept": "Properties of metals, alloying (melting point/hardness), corrosion",
        "localisations": {
            "cbse": "steel bridges, aluminum sheets, and gold plating.",
            "upboard": "alloying of brass for utensils and traditional copper bell casting.",
            "wbboard": "traditional Dhokra metal casting using copper and tin alloys.",
            "tnboard": "casting Panchaloha bronze idols and standard 22-karat gold durability.",
            "mahboard": "corrosion resistance of brass lamps and bronze casting molds.",
            "punboard": "durability of traditional iron tawa pans and steel farm equipment.",
            "bihboard": "alloying metals for traditional farm sickles and copper ornaments."
        }
    },
    "c_reaction": {
        "name": "Chemical Reactions & Equations",
        "cbse_concept": "Combustion, acid rain, oxidation, rancidity",
        "localisations": {
            "cbse": "laboratory oxidation, candle combustion, and iron rusting.",
            "upboard": "combustion of wood in traditional chulha stoves and iron rusting.",
            "wbboard": "acid rain damage to historical monuments and rusting of iron fish-pans.",
            "tnboard": "monument weathering (Taj Mahal acid rain model) and oil rancidity in sweets.",
            "mahboard": "rancidity of oils/ghee in stored snacks and basic rusting of metal farm tools.",
            "punboard": "combustion reactions and particulate releases during stubble (parali) burning.",
            "bihboard": "chemical weathering of river structures and rust formation on iron vessels."
        }
    },
    "c_thermo": {
        "name": "Thermodynamics & States of Matter",
        "cbse_concept": "Evaporative cooling, pressure cooker boiling points, latent heat",
        "localisations": {
            "cbse": "evaporation of sweat and commercial cooling systems.",
            "upboard": "evaporative cooling of water stored in porous earthen surahis.",
            "wbboard": "latent heat of vaporization in traditional clay cups (bhar).",
            "tnboard": "pressure cooker physics and water boiling point elevations in home kitchens.",
            "mahboard": "evaporative cooling in earthen matkas during hot summer dry spells.",
            "punboard": "boiling points of water in open boilers vs sealed boilers on farms.",
            "bihboard": "latent heat absorption in boiling sugarcane juice to make jaggery (gur)."
        }
    },
    "c_ecology": {
        "name": "Ecology & Biodiversity",
        "cbse_concept": "Ecosystem services, local species adaptations, conservation",
        "localisations": {
            "cbse": "forest ecosystems, food chains, and urban environmental balance.",
            "upboard": "aquatic life adaptations in the Ganga river basin.",
            "wbboard": "pneumatophore root adaptations in the Sundarbans mangrove ecosystem.",
            "tnboard": "traditional temple forest conservation and tank ecosystem biodiversity.",
            "mahboard": "endemic biodiversity and species protection in Western Ghats sacred groves (devrai).",
            "punboard": "impact of heavy pesticide runoffs on local canal water ecosystems.",
            "bihboard": "wetland ecosystem dynamics and migratory birds in Bihar's chaur areas."
        }
    },
    "c_crops": {
        "name": "Crop Production & Management",
        "cbse_concept": "Kharif vs Rabi crops, soil aeration, water logging",
        "localisations": {
            "cbse": "general agricultural crop seasons and garden soil aeration.",
            "upboard": "sugarcane water requirements and tilling of alluvial clay soil.",
            "wbboard": "monsoon aman paddy sowing vs winter boro paddy harvesting in Bengal delta.",
            "tnboard": "kuruvai (short-term) rice cycle and water drainage in Kaveri basin.",
            "mahboard": "black soil water retention and cotton/soybean tilling requirements.",
            "punboard": "wheat (kanak) and paddy (chona) rotation and canal water-logging.",
            "bihboard": "rotation of makai (maize) and pulses in flood-prone river regions."
        }
    }
}

# 3. Dialogue Patterns by Persona (incorporating regional/cultural keys)
PERSONA_PATTERNS = {
    "topper": {
        "name": "The Topper",
        "ability": "high",
        "traits": "precise, academic, exam-oriented"
    },
    "struggler": {
        "name": "First-Gen Struggler",
        "ability": "low_moderate",
        "traits": "simple language, terms conflated, anxious but intuitive"
    },
    "curious": {
        "name": "Curious Lateral Thinker",
        "ability": "average",
        "traits": "verbose, examples-rich, lateral connections, slightly off-topic"
    },
    "rote": {
        "name": "Rote Memoriser",
        "ability": "moderate_high_recall_weak_application",
        "traits": "high recall of book definitions, breaks on application"
    },
    "distracted": {
        "name": "Distracted Bright Kid",
        "ability": "high_potential_low_effort",
        "traits": "short answers, casual tone, high potential but careless"
    }
}

# 4. Topic-Specific Dialogue Patterns mapped by [Topic] × [Persona] (escaped LaTeX curly braces)
TOPIC_PERSONA_TURNS = {
    "c_light": {
        "topper": {
            "s1": "In geometrical optics, mirror reflections follow the law of reflection ($i=r$). For our local curved {local_object}, how do we calculate the focal length?",
            "t1": "Excellent! For curved reflective surfaces like a bronze {local_object}, the focal length $f = R/2$, where $R$ is the radius of curvature. How does this curvature affect the magnification of the image?",
            "s2": "Since the focal length depends on curvature, a smaller radius of curvature will create a more warped image. I will draw this ray diagram for my exam.",
            "t2": "Spot on! Curved ray optics is highly consistent. Great structured approach!"
        },
        "struggler": {
            "s1": "Teacher, when I look at the polished {local_object} during {festival}, I see my reflection, but on a normal wall I see nothing. Why does light bounce off metal but not the wall?",
            "t1": "That's a very good question! Think of rolling a ball on a smooth cement floor vs a gravel path. On cement, it rolls straight; on gravel, it bounces randomly. Polished metal is smooth, so light bounces in order. How does that explain mirrors?",
            "s2": "Oh! So light bounces off smooth {local_object} in one direction (regular reflection), but on the rough wall it scatters everywhere (diffuse reflection)!",
            "t2": "Exactly! You've got it. Science just explains what you see around you every day."
        },
        "curious": {
            "s1": "During {festival}, I saw shadow puppets in our region. The shadow gets huge when the puppet is close to the lamp, but small when far. Why does shadow size change with distance?",
            "t1": "Fantastic question! Light travels in straight lines. When a puppet is closer to the lamp, it blocks a wider angle of light rays. What happens to the blocked region on the screen as the puppet moves away?",
            "s2": "As it moves away, it blocks a smaller angle of light, so the shadow shrinks! That explains the shadow scale. It is pure geometry!",
            "t2": "Precisely! It's the geometry of rectilinear propagation of light. Keep exploring!"
        },
        "rote": {
            "s1": "The book says: Light travels in straight lines and forms shadows when blocked by an opaque object. I have memorised this. But how does our local {local_object} relate to this?",
            "t1": "You have the definition down perfectly, Meera! Think of our local {local_object}. If light did not travel in straight lines, could it form a clear image or shadow when blocked?",
            "s2": "If light bent around it, there would be no dark shadow behind it. So shadows prove light travels in straight lines.",
            "t2": "Exactly! You've successfully linked the textbook definition to real-world observations."
        },
        "distracted": {
            "s1": "Shadows are just blocked light, right? Like when we block the lamps during {festival}.",
            "t1": "Yes, it is that simple. But why is the center of the shadow darker (umbra) while the edges are lighter (penumbra)? What is causing the split?",
            "s2": "Because the light source isn't a single point; light from different parts of the bulb overlaps at the edges. Umbra gets zero light, penumbra gets partial.",
            "t2": "Spot on! That's the difference between point and extended light sources."
        }
    },
    "c_sound": {
        "topper": {
            "s1": "In acoustics, string pitch is determined by tension and length. For our local {local_object}, how does tightening the pegs mathematically alter the frequency?",
            "t1": "Excellent! The fundamental frequency is $f = \\frac{{1}}{{2L}}\\sqrt{{\\frac{{T}}{{\\mu}}}}$, where $T$ is tension. If we increase tension, how does frequency respond?",
            "s2": "Frequency is proportional to the square root of tension, so tightening the pegs increases the frequency and pitch. I will state this formula.",
            "t2": "Perfect! Your mathematical grasp of wave mechanics is very solid."
        },
        "struggler": {
            "s1": "Teacher, when I hit the local {local_object} during {festival}, it makes a loud sound. But if I touch the drum membrane, it stops. Why does touching it make it quiet?",
            "t1": "A great observation! Sound is created by vibrations. When you strike the drum, the membrane vibrates. What happens to the vibration when you press your hand against it?",
            "s2": "My hand stops the vibration! So if there's no vibration, there is no sound wave traveling in the air.",
            "t2": "Exactly! Sound requires mechanical vibration. You explained it beautifully."
        },
        "curious": {
            "s1": "I was thinking, when we play our local {local_object} on the farm, the sound travel is clear. If we played it in outer space vacuum, could we hear it?",
            "t1": "Fascinating question! Sound is a mechanical longitudinal wave that requires a material medium (air, water, solid) to compress and propagate. In a space vacuum, what medium is there to vibrate?",
            "s2": "There are no air molecules in space to push, so sound cannot travel at all! So space battles in movies must be silent.",
            "t2": "Exactly! In space, no one can hear you play. Great scientific deduction!"
        },
        "rote": {
            "s1": "Sound is a mechanical wave that requires a medium to travel. It cannot travel in vacuum. I have memorised this. How do we show this in the {board} exam using our local {local_object}?",
            "t1": "You have the facts right, Meera. If we put a ringing buzzer inside a glass jar and pump out all the air, the sound disappears. How does this prove the definition?",
            "s2": "Because when the air medium is removed, the sound waves have nothing to travel through, showing a medium is necessary.",
            "t2": "Perfect. You have linked the exam experiment to the core definition."
        },
        "distracted": {
            "s1": "Pitch is just about how high or low the note is, like when playing the {local_object}.",
            "t1": "Yes, but what physical property of the sound wave determines the pitch? What makes the notes different?",
            "s2": "It's the frequency of the wave. High frequency means high pitch, low frequency means low pitch.",
            "t2": "Correct. Amplitude determines loudness, frequency determines pitch. Simple and true."
        }
    },
    "c_acids": {
        "topper": {
            "s1": "Neutralisation involves hydrogen ions reacting with hydroxide ions ($H^+ + OH^- \\rightarrow H_2O$). When we clean tarnished brass using acid in tamarind, what is the exact chemical reaction?",
            "t1": "Excellent! Copper tarnishes to form basic copper carbonate ($CuCO_3\\cdot Cu(OH)_2$), which is basic. The tartaric acid in tamarind neutralizes it. What products are formed?",
            "s2": "The reaction produces soluble copper tartrate salt, carbon dioxide, and water, washing away the green tarnish. I will write this reaction.",
            "t2": "Brilliant! You have mapped organic acid properties to coordination chemistry perfectly."
        },
        "struggler": {
            "s1": "Teacher, why does my mother use sour tamarind paste to clean our brass {local_object} in the temple? It becomes shiny again.",
            "t1": "That's a very practical observation! The green tarnish on brass is basic. Tamarind is sour because it contains acid. When acid meets a base, they neutralize each other. How does this explain the shine?",
            "s2": "Oh! The acid in tamarind reacts with the basic green layer and washes it away, leaving the clean metal shiny!",
            "t2": "Yes! You've just explained neutralization in everyday life. Excellent!"
        },
        "curious": {
            "s1": "If we spill turmeric water during {festival} on my shirt, it turns yellow. But when we rub basic soap on it, it turns red! Why does it change color?",
            "t1": "What a neat observation! Turmeric (*haldi*) contains curcumin, which acts as a natural pH indicator. It changes color from yellow to reddish-brown in basic solutions. What happens if you pour sour lemon juice (acid) on the red stain?",
            "s2": "Since lemon juice is acidic, it should neutralize the base, turning the stain yellow again! I must try this!",
            "t2": "Exactly! It reverses the pH state. Try it out—it's a real-world chemical titration!"
        },
        "rote": {
            "s1": "Acids are sour and turn blue litmus red. Bases are bitter, soapy, and turn red litmus blue. I have memorised this. But why does soap turn turmeric stains red?",
            "t1": "You have memorized the indicators perfectly, Meera. Turmeric is a natural indicator. It remains yellow in acid but turns red in base. Since soap turns it red, what does that tell you about soap?",
            "s2": "Since it turns red, soap must be basic in nature. So soap has a pH greater than 7.",
            "t2": "Exactly! You've used the definition to classify soap as a base."
        },
        "distracted": {
            "s1": "Acids are just chemical liquids that burn skin, right? Like sulfuric acid.",
            "t1": "Strong acids do, but what about weak organic acids? Do we eat acids in our daily food?",
            "s2": "Yeah, citric acid is in lemons, lactic acid is in curd/buttermilk, tartaric is in tamarind. We eat them all the time.",
            "t2": "Exactly. Not all acids are hazardous; organic acids are essential to our diet."
        }
    },
    "c_micro": {
        "topper": {
            "s1": "Fermentation is anaerobic respiration where yeast converts glucose into ethanol and $CO_2$. In our local fermentation of idli batter, what biological pathways are active?",
            "t1": "Precise query! In idli batter, wild yeasts and lactic acid bacteria (like Leuconostoc) undergo lactic acid and carbon dioxide fermentation. Why does the batter rise?",
            "s2": "The carbon dioxide gas gets trapped in the gluten/starch matrix, causing the batter to rise and become spongy. I will document this pathway.",
            "t2": "Splendid! You have integrated microbial biochemistry with food science flawlessly."
        },
        "struggler": {
            "s1": "Teacher, in winter our dosa batter does not rise, but in summer it rises quickly and gets sour. Why does temperature change the batter?",
            "t1": "A very common kitchen problem! The rising and souring are caused by tiny micro-organisms (bacteria and yeast) growing in the batter. Like us, they are active when it is warm. What happens to their activity when it is cold?",
            "s2": "They go to sleep or grow very slowly in the cold! So they don't produce the gas needed to make the batter rise.",
            "t2": "Exactly! Temperature affects the rate of microbial growth and fermentation. Well reasoned!"
        },
        "curious": {
            "s1": "When we make pickles at home, we put lots of salt and oil. Why does salt prevent the pickles from rotting or growing fungus?",
            "t1": "Brilliant question! Fungi and bacteria need water to live. When you put excess salt, the water inside the microbial cells is drawn out because the environment is saltier. What is this cellular water-drawing process called?",
            "s2": "It is osmosis! Water moves from inside the cell to the saltier outside, shrinking the microbial cells and killing them. So salt acts as a preservative!",
            "t2": "Spot on! That is plasmolysis due to hypertonic osmosis. You've mapped the cell biology perfectly!"
        },
        "rote": {
            "s1": "Preservatives prevent food spoilage by inhibiting microbial growth. Examples are sodium benzoate, oil, and salt. I have memorised this. How does oil act as a preservative?",
            "t1": "Good recall, Meera. Think about oil floating on water. How does a thick layer of oil on top of a pickle jar affect the oxygen supply to microbes?",
            "s2": "The oil layer blocks air (oxygen) from entering, preventing aerobic bacteria and molds from growing on the food.",
            "t2": "Perfect. You have explained the physical barrier mechanism of preservation."
        },
        "distracted": {
            "s1": "Curd is just milk with lactobacillus bacteria added, right?",
            "t1": "Yes. But why does boiling the milk first and then cooling it to lukewarm before adding the inoculum matter? Why not put it in boiling milk?",
            "s2": "Boiling milk would kill the bacteria in the inoculum. It needs to be lukewarm so the lactobacillus can survive and multiply.",
            "t2": "Exactly. Temperature control is key in fermentation. Good job."
        }
    },
    "c_force": {
        "topper": {
            "s1": "Newton's 3rd Law states $F_1 = -F_2$. When we pull water using a well {local_object}, why does the tension in the rope not cancel out the applied force?",
            "t1": "Excellent! Action and reaction forces are equal and opposite, but they act on *different* bodies. What are the two bodies in this system?",
            "s2": "The rope acts on the bucket, and the bucket acts on the rope. Since the forces act on different objects, they do not cancel out. I will draw this free-body diagram.",
            "t2": "Exactly! Action-reaction pairs never act on the same body. Keep up the high-level mechanics!"
        },
        "struggler": {
            "s1": "Teacher, when I grind spices on the local {local_object}, it is very hard to start sliding the heavy stone. But once it starts sliding, it becomes easier. Why?",
            "t1": "A classic friction observation! Before the stone slides, the interlocking microscopic bumps between the stones are locked tight; this is static friction. Once it slides, they ride over each other; this is kinetic friction. Which force is stronger?",
            "s2": "Static friction is stronger! So it takes more force to break the interlocking at first, but less force (kinetic friction) to keep it moving.",
            "t2": "Perfect! You've just deduced why static friction is greater than sliding friction. Well done!"
        },
        "curious": {
            "s1": "When flying kites during {festival}, we coat the thread with glass (*manjha*). Why does the manjha cut the other kite string? Is it about pressure or friction?",
            "t1": "What a great connection! The glass particles on the manjha are sharp, meaning they have a tiny surface area. When the strings rub, this small area concentrates force, creating high pressure. How does this high pressure combined with friction help cut the other string?",
            "s2": "Small area means huge pressure ($P=F/A$). So even a small pull creates enough pressure and friction to cut through the other string! That makes sense!",
            "t2": "Precisely! You've combined the concepts of pressure (force per unit area) and friction perfectly."
        },
        "rote": {
            "s1": "Newton's First Law: An object remains in a state of rest or uniform motion unless acted upon by an external force. I have memorised this. But why does a rolling ball eventually stop on the ground?",
            "t1": "Good recall, Meera. If the ball stops, there must be an external force acting on it according to the law. What invisible force is acting between the ball and the ground?",
            "s2": "The rolling ball stops because of the force of friction between the ball's surface and the ground, which opposes its motion.",
            "t2": "Exactly! Friction is the external force. You've applied the law correctly."
        },
        "distracted": {
            "s1": "Pulleys like the local {local_object} just make lifting water easier. It's standard mechanical stuff.",
            "t1": "Yes, but how? Does a single fixed pulley reduce the actual force needed, or does it just change the direction of force?",
            "s2": "It doesn't reduce force; it just changes direction so you can pull down (using your body weight) instead of lifting up. Change of direction makes it easier.",
            "t2": "Exactly! It's a change of direction, not a force multiplier. Excellent distinction."
        }
    },
    "c_metals": {
        "topper": {
            "s1": "Alloying alters electrical conductivity and mechanical properties by disrupting crystal lattice symmetry. In Panchaloha bronze idols, how does the alloy composition affect structural strength?",
            "t1": "Outstanding query! Pure metals have organized layers that slide past each other easily. Adding copper, tin, and zinc introduces atoms of different sizes, locking the layers in place. How does this affect hardness?",
            "s2": "The different atomic sizes prevent layers from sliding, which increases hardness and tensile strength while lowering the melting point. I will diagram this lattice.",
            "t2": "Superb! You have explained interstitial and substitutional alloy strengthening perfectly."
        },
        "struggler": {
            "s1": "Teacher, pure copper is very soft and bends easily, but when we make our temple {local_object} using bronze (copper mixed with tin), it becomes very hard. Why does mixing make it stronger?",
            "t1": "A very important metal craft concept! Imagine a stack of identical smooth coins sliding easily. If you insert a few larger coins in the stack, they block the sliding. The tin atoms are larger than copper atoms. How does this stop the metal from bending?",
            "s2": "The larger tin atoms block the copper layers from sliding past each other! So the metal mixture becomes hard and does not bend easily.",
            "t2": "Exactly! That is how alloying works to make metals stronger. Excellent intuition!"
        },
        "curious": {
            "s1": "When we buy gold ornaments in our family, they say 24-karat gold is too soft and we must buy 22-karat gold. Why can't we make ornaments out of pure gold?",
            "t1": "Great practical question! Pure 24K gold is extremely soft and malleable, meaning it scratch and bend out of shape easily. To make it durable, we mix 22 parts gold with 2 parts copper or silver. How does this addition help?",
            "s2": "The copper/silver atoms harden the gold lattice, making the ornament strong enough to hold its shape and resist scratches! So 22K is an alloy!",
            "t2": "Precisely! 22-karat gold is an alloy designed for durability. Excellent connection!"
        },
        "rote": {
            "s1": "An alloy is a homogeneous mixture of two or more metals, or a metal and a non-metal. Examples are steel, brass, and bronze. I have memorised this. Why is steel preferred over pure iron?",
            "t1": "Good definition, Meera. Pure iron is soft and rusts easily. When we mix it with carbon to make steel, what properties are improved?",
            "s2": "Adding carbon makes the iron hard and strong, and if we add chromium/nickel (stainless steel), it prevents rusting.",
            "t2": "Perfect. You have explained how alloying alters both strength and corrosion resistance."
        },
        "distracted": {
            "s1": "Metals conduct electricity because they have free electrons. It's why we use copper wires.",
            "t1": "Yes. But why don't we use silver wires since silver is actually a better conductor than copper?",
            "s2": "Because silver is too expensive. Copper is cheap and abundant, making it commercially practical for wiring.",
            "t2": "Exactly. Engineering decisions balance physical properties with economic cost. Good point."
        }
    },
    "c_reaction": {
        "topper": {
            "s1": "Acid rain damage to monuments involves calcium carbonate reacting with sulfuric acid ($CaCO_3 + H_2SO_4 \\rightarrow CaSO_4 + H_2O + CO_2$). What thermodynamic factors drive this weathering?",
            "t1": "Precise query! The reaction is driven by the formation of gypsum ($CaSO_4\\cdot 2H_2O$), which has a larger volume than marble, causing mechanical cracking. Is this reaction exothermic?",
            "s2": "Yes, it is exothermic and increases entropy via $CO_2$ gas release, driving the weathering reaction forward. I will write this equation.",
            "t2": "Magnificent! You have mapped chemical kinetics and thermodynamics onto ecological weathering perfectly."
        },
        "struggler": {
            "s1": "Teacher, why is the white marble of the Taj Mahal turning yellow? They say it is because of chemical reactions in the air.",
            "t1": "A very sad but important chemical reaction! Factories release sulfur dioxide gas, which reacts with rain water to form acid rain. Marble is calcium carbonate. What happens when acid rain falls on the basic marble monument?",
            "s2": "The acid reacts with the marble (neutralization), eating away at the stone and forming a yellowish layer! So the air pollution is corroding the marble.",
            "t2": "Yes! You have explained acid-rain corrosion of carbonate rocks perfectly. Great job!"
        },
        "curious": {
            "s1": "When we store fried snacks (*pakoras*) in our kitchen for many days, they start smelling and tasting bad. Why does food spoil like this? Is it a chemical reaction?",
            "t1": "What a common and important observation! The fats and oils in the food react with oxygen in the air over time. This chemical reaction is called oxidation. How does oxidation change the structure of the oils, and how can we prevent it?",
            "s2": "The oxygen breaks down the oil molecules into smelly compounds (rancidity). We can prevent it by storing food in airtight containers or flushing them with nitrogen gas!",
            "t2": "Exactly! That is rancidity. Flushing potato chip packets with inert nitrogen gas prevents oxygen from reacting with the oils."
        },
        "rote": {
            "s1": "Rancidity is the oxidation of fats and oils in food, leading to bad smell and taste. It is prevented by antioxidants or nitrogen gas. I have memorised this. Why does nitrogen prevent rancidity?",
            "t1": "Good recall, Meera. Think about nitrogen's triple bond ($N\\equiv N$). How reactive is nitrogen gas compared to oxygen gas in the air?",
            "s2": "Nitrogen is inert and non-reactive because of its triple bond. It displaces oxygen, preventing oxidation of the food.",
            "t2": "Perfect. You have linked chemical bonding stability to food preservation."
        },
        "distracted": {
            "s1": "Rusting is just iron oxidation. Like when our farm tools get red flakes after rains.",
            "t1": "Yes. But does iron rust in dry air, or does it require both oxygen and water to occur? What is the trigger?",
            "s2": "It needs both. Water acts as the medium for electron transfer, and oxygen oxidizes the iron. Dry air won't cause rust.",
            "t2": "Correct. Rusting is an electrochemical process requiring both moisture and oxygen."
        }
    },
    "c_thermo": {
        "topper": {
            "s1": "Evaporative cooling is driven by latent heat of vaporization ($L_v$). For our local clay {local_object}, how does humidity affect the rate of bulk temperature reduction?",
            "t1": "Excellent! The rate of evaporation depends on the vapor pressure gradient between the wet clay surface and the air. If the ambient humidity is high, what happens to this gradient?",
            "s2": "High humidity decreases the vapor pressure gradient, slowing down evaporation and reducing the cooling rate of the {local_object}. I will state this relation.",
            "t2": "Brilliant! You have mapped mass transfer and thermodynamic boundary layers perfectly."
        },
        "struggler": {
            "s1": "Teacher, why does water inside our clay {local_object} remain cool in hot summers, but water in a plastic bottle stays warm?",
            "t1": "An excellent cooling question! Clay pots have thousands of microscopic holes (pores). Water seeps through these pores and evaporates off the outside surface. To evaporate, water absorbs heat. Where does it take this heat from?",
            "s2": "It absorbs heat from the bulk water inside the pot! So the water inside loses heat and becomes cold. Plastic has no pores, so it cannot evaporate.",
            "t2": "Exactly! That is cooling by evaporation. You explained it beautifully!"
        },
        "curious": {
            "s1": "In our kitchen, when we boil water in an open pot, it takes a long time. But in a pressure cooker, it cooks in minutes. Why does high pressure speed up the cooking?",
            "t1": "What a great kitchen physics query! Boiling point is the temperature where vapor pressure equals external pressure. In a sealed pressure cooker, steam increases the internal pressure. What does this do to the boiling point of water?",
            "s2": "Higher pressure raises the boiling point of water (above $100^\\circ\\text{{C}}$). So the water gets much hotter before boiling, transferring more heat to the food quickly!",
            "t2": "Exactly! The high-temperature liquid water transfers heat much faster than steam, cooking the food in minutes."
        },
        "rote": {
            "s1": "Latent heat of vaporization is the heat required to convert a unit mass of liquid into vapor without a change in temperature. I have memorised this. Why does steam cause more severe burns than boiling water at the same temperature?",
            "t1": "Good recall, Meera. Think about the latent heat stored in steam. When steam hits the skin, what phase change occurs, and what happens to that stored heat?",
            "s2": "Steam condenses back into liquid water on the skin, releasing its extra latent heat of vaporization, causing a deeper burn.",
            "t2": "Perfect. You have linked the phase transition energy release directly to the definition."
        },
        "distracted": {
            "s1": "Earthen pots cool water because of evaporation. Simple thermal balance.",
            "t1": "Yes, but why does a hot wind blowing over the pot accelerate the cooling rate? What is the wind doing to the boundary layer?",
            "s2": "The wind sweeps away the evaporated water vapor, preventing saturation near the pot. This keeps the evaporation rate high.",
            "t2": "Correct. Wind maintains a steep concentration gradient, accelerating mass transfer."
        }
    },
    "c_ecology": {
        "topper": {
            "s1": "Pneumatophores are specialized root adaptations for gas exchange in anaerobic soils. In the Sundarbans mangrove ecosystem, how does this relate to cellular respiration?",
            "t1": "Outstanding! Water-logged clay soil has zero oxygen pore space, preventing aerobic root respiration. Pneumatophores grow upwards against gravity to fetch oxygen. What cellular pathway is protected?",
            "s2": "They ensure oxygen supply for aerobic oxidative phosphorylation, preventing anaerobic root decay and cell death. I will diagram this gas exchange.",
            "t2": "Excellent! You have linked anatomical adaptation to mitochondrial biochemistry flawlessly."
        },
        "struggler": {
            "s1": "Teacher, in the Sundarbans delta, the tree roots grow upwards out of the muddy soil instead of going down. Why do roots grow towards the air?",
            "t1": "A very unique root adaptation! The delta mud is heavily waterlogged and clayey, meaning it has no air or oxygen trapped inside. Roots are living cells and need to breathe oxygen. How does growing upwards help them?",
            "s2": "They grow upwards out of the mud to get oxygen directly from the air! So they don't suffocate in the wet clay.",
            "t2": "Yes! Those are breathing roots called pneumatophores. You've explained root respiration adaptations perfectly!"
        },
        "curious": {
            "s1": "In our village, during {festival}, we discuss the local sacred groves (*devrai*). Why are these groves protected by local traditions? Is there an ecological benefit?",
            "t1": "What a wonderful cultural connection! Sacred groves act as traditional community-conserved forest reserves. They preserve rare flora, maintain local water tables, and prevent soil erosion. How do they act as seed banks for the surrounding area?",
            "s2": "Because they are protected from grazing and logging, they preserve parent plants that scatter seeds, helping regenerate the local ecosystem naturally!",
            "t2": "Exactly! They are crucial gene banks and biodiversity hotspots preserved by ancient local culture."
        },
        "rote": {
            "s1": "Ecosystem services are the direct and indirect contributions of ecosystems to human well-being. Examples include pollination, soil erosion control, and carbon sequestration. I have memorised this. How do trees prevent soil erosion?",
            "t1": "Good recall, Meera. Think about tree roots holding soil particles together. When heavy monsoon rains fall, what happens to soil held by roots compared to bare soil?",
            "s2": "The roots bind the soil, preventing water from washing the fertile topsoil away. So forests act as soil stabilizers.",
            "t2": "Perfect. You have linked physical soil binding to the ecosystem service of erosion control."
        },
        "distracted": {
            "s1": "Stubble burning just pollutes the air. It's simple combustion releasing ash.",
            "t1": "Yes, but how does burning crop residue affect the chemical and biological composition of the topsoil? What gets destroyed?",
            "s2": "The heat kills beneficial soil microbes and earthworms, and burns up organic matter (humus), reducing soil fertility in the long run.",
            "t2": "Exactly. It damages the biological topsoil web, not just the air quality. Good observation."
        }
    },
    "c_crops": {
        "topper": {
            "s1": "Symbiotic nitrogen fixation by Rhizobium in legumes increases soil nitrates. In crop rotation, how does sowing gram after wheat restore soil fertility?",
            "t1": "Excellent! Wheat is a nitrogen depleter, while gram (a legume) hosts Rhizobium which fixes atmospheric nitrogen. How does this cycle affect our NPK fertilizer needs?",
            "s2": "Gram nodules replenish nitrogen levels biologically, reducing the need for synthetic chemical fertilizers. I will draft this nitrogen cycle diagram.",
            "t2": "Splendid! You have mapped agricultural biology onto soil chemistry perfectly."
        },
        "struggler": {
            "s1": "Teacher, in our village we sow wheat in the winter cold (rabi) but paddy in the hot monsoon rain (kharif). Why can't we grow rice in winter?",
            "t1": "A very important farm cycle! Paddy (rice) requires constant warm temperatures and huge amounts of water to grow. In winter, temperatures are low and there is little rainfall. What would happen to the rice seeds in winter?",
            "s2": "The cold and dry winter weather would kill the rice plants, or they wouldn't get enough water to grow! So they need the monsoon.",
            "t2": "Exactly! That's why crops are classified into Kharif (monsoon) and Rabi (winter) seasons based on climate. Well reasoned!"
        },
        "curious": {
            "s1": "If we irrigate our fields in Punjab too much, water stays logged in the soil. Why does standing water harm the wheat crop? Doesn't more water help them grow?",
            "t1": "Great practical irrigation question! Plant roots need oxygen from air pockets in the soil to breathe. When water logging occurs, standing water fills all the air pockets. What happens to root respiration under water?",
            "s2": "The roots cannot get air and suffocate! Without respiration, the roots decay and the plant dies. So too much water can drown a crop!",
            "t2": "Spot on! That is root asphyxiation due to anaerobic waterlogging. Excellent scientific deduction!"
        },
        "rote": {
            "s1": "Kharif crops are sown in June/July and harvested in September/October. Rabi crops are sown in October/November and harvested in March/April. I have memorised this. Give an example of each.",
            "t1": "Good recall, Meera. Think about your local crops. What is sown at the start of the monsoon rain, and what is sown in the winter dry season?",
            "s2": "Paddy (rice) and maize are Kharif crops. Wheat and mustard are Rabi crops.",
            "t2": "Perfect. You have mapped the examples directly to their seasonal definitions."
        },
        "distracted": {
            "s1": "Tilling is just turning the soil. Like when we plow the fields before sowing.",
            "t1": "Yes, but why? What physical change does tilling make to the soil structure that helps the newly sown seeds?",
            "s2": "It loosens the soil so roots can penetrate easily and breathe. It also brings nutrient-rich soil from the bottom to the top.",
            "t2": "Correct. Soil aeration and nutrient mixing are the core reasons. Good point."
        }
    }
}

# 6. Generate Dialogues
def generate_dataset():
    print("=========================================================")
    print("Generating Localised & Culturally-Adaptive SFT Dataset...")
    print(f"Target Size: {TARGET_DIALOGUES} Dialogues")
    print(f"Scope: 10 STEM Topics, 7 Boards, 5 Personas")
    print("=========================================================")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    boards = list(REGIONAL_PROFILES.keys())
    topics = list(TOPICS.keys())
    personas = list(PERSONA_PATTERNS.keys())
    
    records = []
    
    board_idx = 0
    topic_idx = 0
    persona_idx = 0
    
    while len(records) < TARGET_DIALOGUES:
        board_key = boards[board_idx]
        topic_key = topics[topic_idx]
        persona_key = personas[persona_idx]
        
        profile = REGIONAL_PROFILES[board_key]
        topic_info = TOPICS[topic_key]
        persona_info = PERSONA_PATTERNS[persona_key]
        
        lang = random.choice(profile["languages"])
        
        concept_name = topic_info["name"]
        cbse_concept = topic_info["cbse_concept"]
        localization_desc = topic_info["localisations"][board_key]
        
        local_object = random.choice(profile["cultural_objects"])
        local_soil = random.choice(profile["soils"])
        local_fertiliser = profile["local_terms"]["fertiliser"]
        festival = random.choice(profile["festivals"])
        
        p_dict = {
            "concept": concept_name,
            "cbse_concept": cbse_concept,
            "board": profile["board_name"],
            "local_object": local_object,
            "local_soil": local_soil,
            "local_fertiliser": local_fertiliser,
            "festival": festival
        }
        
        # Load topic-persona specific turns
        turns_dict = TOPIC_PERSONA_TURNS[topic_key][persona_key]
        
        # Format turns
        student_u1 = turns_dict["s1"].format(**p_dict)
        teacher_u1 = turns_dict["t1"].format(**p_dict)
        student_u2 = turns_dict["s2"].format(**p_dict)
        teacher_u2 = turns_dict["t2"].format(**p_dict)
        
        dialogue_id = f"localised_sarg_{len(records) + 1:06d}"
        
        # Language overrides for regional mediums
        if lang == "hi" and board_key in ("upboard", "bihboard"):
            if topic_key == "c_acids":
                student_u1 = f"नमस्ते टीचर। पीएच (pH) मान तो मैं समझती हूँ। पर हमारी रसोई में ताँबे के बरतनों को चमकाने के लिए इमली (acid) का उपयोग क्यों होता है?"
                teacher_u1 = "बहुत बढ़िया! ताँबे के बर्तनों पर एक क्षारीय (basic) कॉपर कार्बोनेट की परत जम जाती है। इमली में टार्टरिक अम्ल (acid) होता है जो उसे उदासीन (neutralize) कर देता है। इससे क्या बनेगा?"
                student_u2 = "अच्छा! तो अम्ल और क्षार मिलकर उदासीन अभिक्रिया करते हैं, और वह हरी परत घुलकर बह जाती है। बर्तन चमकने लगता है!"
                teacher_u2 = "बिल्कुल सही! हमारे घरों में रोज़ाना ऐसी कई रासायनिक अभिक्रियाएँ होती हैं। शाबाश!"
            elif topic_key == "c_crops":
                student_u1 = f"टीचर, हमारे यहाँ खेतों में {profile['crops'][0]} की फसल केवल सर्दियों (rabi) में ही क्यों बोई जाती है? मानसून में क्यों नहीं?"
                teacher_u1 = f"बहुत अच्छा प्रश्न! {profile['crops'][0]} को बढ़ने के लिए कम तापमान और कम पानी चाहिए। मानसून में तापमान और वर्षा बहुत अधिक होती है। यदि हम इसे मानसून में बोएँगे तो क्या होगा?"
                student_u2 = f"अधिक पानी और गर्मी से फसल के पौधे सड़ जाएँगे! इसलिए इसे सर्दियों के शुष्क मौसम में ही बोया जाता है। समझ गया!"
                teacher_u2 = "बिल्कुल सही! यही कारण है कि फसलों को रबी और खरीफ ऋतुओं में उनकी जल-आवश्यकता के अनुसार बाँटा गया है।"
            else:
                student_u1 = f"नमस्ते टीचर। मैं {profile['board_name']} से हूँ। मुझे {concept_name} का सिद्धांत समझ आता है पर हमारे यहाँ {local_object} में यह कैसे काम करता है?"
                teacher_u1 = f"बहुत अच्छा प्रश्न! {local_object} में {concept_name} का सिद्धांत इस प्रकार काम करता है: {localization_desc}. इसे ऐसे समझो..."
                student_u2 = f"अच्छा! तो इसका मतलब है कि {local_soil} और {local_object} दोनों भौतिक नियमों के अनुसार ही काम करते हैं। समझ गई!"
                teacher_u2 = "बिल्कुल सही! हमारे आस-पास का वातावरण और खेती-बाड़ी सब विज्ञान के सिद्धांतों से ही जुड़ी हुई है।"
        elif lang == "bn" and board_key == "wbboard":
            if topic_key == "c_acids":
                student_u1 = f"নমস্কার দিদিমণি। পরীক্ষার জন্য তো অ্যাসিড ও ক্ষারের সংজ্ঞা মুখস্থ করেছি। কিন্তু আমাদের পুজো ঘরে তামার প্রদীপ পরিষ্কার করতে তেঁতুল ব্যবহার করা হয় কেন?"
                teacher_u1 = "দারুণ প্রশ্ন! তামার ওপর ক্ষারীয় কপার কার্বনেটের একটি সবুজ আস্তরণ পড়ে। তেঁতুলে থাকা টারটারিক অ্যাসিড সেটিকে প্রশমিত (neutralize) করে দেয়। এর ফলে কী ঘটে বলতো?"
                student_u2 = "অ্যাসিড আর ক্ষার বিক্রিয়া করে লবণ ও জল তৈরি করে, ফলে ওই সবুজ আস্তরণটি ধুয়ে যায় এবং তামার প্রদীপটি আবার চকচকে হয়ে ওঠে!"
                teacher_u2 = "একদম ঠিক! বিজ্ঞানের এই তত্ত্বগুলো আমাদের দৈনন্দিন জীবনে এভাবেই লুকিয়ে আছে। খুব ভালো!"
            else:
                student_u1 = f"নমস্কার দিদিমণি/শিক্ষক মহাশয়। {concept_name} সম্পর্কে বইতে পড়েছি, কিন্তু আমাদের ওখানকার {local_object} এর সাথে এর কী সম্পর্ক?"
                teacher_u1 = f"দারুণ প্রশ্ন! আসলে আমাদের ওখানকার {local_object} এর ক্ষেত্রে {concept_name} নীতিটি এইভাবে কাজ করে: {localization_desc}. বিষয়টি সহজভাবে বুঝিয়ে বলছি..."
                student_u2 = f"বাহ! তাহলে তো বোঝা যাচ্ছে যে {local_soil} এবং {local_object} এর ওপর এই নীতিগুলোই খাটছে। এবার ধারণাটি পরিষ্কার হলো।"
                teacher_u2 = "একদম ঠিক! নিজের চারপাশের পরিবেশ ও ঐতিহ্যের সাথে বিজ্ঞানকে মেলাতে পারলে পড়া আরও সহজ ও আনন্দদায়ক হয়।"
        elif lang == "ta" and board_key == "tnboard":
            if topic_key == "c_acids":
                student_u1 = f"வணக்கம் ஐயா. அமிலங்கள் மற்றும் காரங்கள் நடுநிலையாக்கல் வினையை உருவாக்குகிறது என்று படித்தேன். ஆனால் நம் பூஜை அறையில் உள்ள காமாட்சி விளக்கை புளி போட்டு துலக்கினால் ஏன் பளபளக்கிறது?"
                teacher_u1 = "சிறப்பான கேள்வி! காமாட்சி விளக்கின் மேல் காரத்தன்மை கொண்ட காப்பர் கார்பனேட் படிகிறது. புளியில் உள்ள டார்டாரிக் அமிலம் அதனை நடுநிலையாக்குகிறது (neutralize). இதனால் என்ன உருவாகிறது?"
                student_u2 = "அமிலமும் காரமும் வினைபுரிந்து நீரில் கரையக்கூடிய உப்பை உருவாக்குகிறது, இதனால் அந்த பச்சை நிறப் படிவு நீங்கி விளக்கு பளபளக்கிறது!"
                teacher_u2 = "மிகச் சரி! நம் வீட்டு பூஜை அறையில் கூட வேதியியல் நடுநிலையாக்கல் வினை எவ்வாறு செயல்படுகிறது என்பதைப் புரிந்து கொண்டாய். நன்று!"
            else:
                student_u1 = f"வணக்கம் ஐயா/அம்மா. {concept_name} என்ற தலைப்பை புத்தகத்தில் படித்தேன், ஆனால் நம் ஊர் {local_object} உடன் இது எவ்வாறு தொடர்பு கொள்கிறது?"
                teacher_u1 = f"சிறப்பான கேள்வி! நம் பகுதியில் உள்ள {local_object}-ல் {concept_name} கொள்கை எவ்வாறு தான் செயல்படுகிறது: {localization_desc}. இதைப் புரிந்து கொள்ள எளிய உதாரணம்..."
                student_u2 = f"புரிகிறது! அப்படியானால் {local_soil} மற்றும் {local_object} இரண்டுமே அறிவியல் விதிகளுக்கு உட்பட்டவை தான். இப்போது தெளிவாகப் புரிகிறது."
                teacher_u2 = "மிகச் சரி! நம் மண்ணையும் பண்பாட்டையும் அறிவியலோடு இணைத்துப் பார்க்கும்போது தான் கற்றல் முழுமையடைகிறது."
        elif lang == "mr" and board_key == "mahboard":
            student_u1 = f"नमस्कार सर. पुस्तकात {concept_name} ची व्याख्या वाचली, पण आपल्या भागातील {local_object} च्या संदर्भात हे कसे घडते?"
            teacher_u1 = f"खूपच छान प्रश्न! आपल्याकडील {local_object} च्या बाबतीत {concept_name} चा सिद्धांत या प्रकारे काम करतो: {localization_desc}. सोप्या भाषेत सांगायचे तर..."
            student_u2 = f"हो, आता समजले! म्हणजेच {local_soil} आणि {local_object} दोन्हीवरही हेच वैज्ञानिक नियम लागू होतात. माझी संकल्पना स्पष्ट झाली."
            teacher_u2 = "नक्कीच! आजूबाजूच्या शेत-परिसराला आणि संस्कृतीला विज्ञानाशी जोडल्यास शिक्षण अधिक सोपे आणि मजेशीर होते."
        elif lang == "pa" and board_key == "punboard":
            student_u1 = f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ। ਮੈਨੂੰ {concept_name} ਦਾ ਸਿਧਾਂਤ ਸਮਝ ਆਉਂਦਾ ਹੈ, ਪਰ ਸਾਡੇ ਇਲਾਕੇ ਦੇ {local_object} ਨਾਲ ਇਹਦਾ ਕੀ ਸਬੰਧ ਹੈ?"
            teacher_u1 = f"ਬਹੁਤ ਵਧੀਆ ਸਵਾਲ! ਸਾਡੇ ਇਲਾਕੇ ਵਿੱਚ {local_object} ਉੱਤੇ {concept_name} ਦਾ ਨਿਯਮ ਇਸ ਤਰ੍ਹਾਂ ਲਾਗੂ ਹੁੰਦਾ ਹੈ: {localization_desc}. ਇਹਨੂੰ ਸੌਖੇ ਤਰੀਕੇ ਨਾਲ ਸਮਝਾਉਂਦਾ ਹਾਂ..."
            student_u2 = f"ਅੱਛਾ! ਹੁਣ ਸਮਝ ਆਇਆ ਕਿ ਸਾਡੀ {local_soil} ਅਤੇ {local_object} ਦੋਵੇਂ ਵਿਗਿਆਨਕ ਨਿਯਮਾਂ ਮੁਤਾਬਕ ਹੀ ਕੰਮ ਕਰਦੇ ਹਨ।"
            teacher_u2 = "ਬਿਲਕੁਲ ਠੀਕ! ਆਪਣੇ ਆਲੇ-ਦੁਆਲੇ ਅਤੇ ਸੱਭਿਆਚਾਰ ਨੂੰ ਵਿਗਿਆਨ ਨਾਲ ਜੋੜ ਕੇ ਦੇਖਣਾ ਹੀ ਅਸਲ ਪੜ੍ਹਾਈ ਹੈ।"
            
        rec = {
            "id": dialogue_id,
            "target_concept": concept_name,
            "board": board_key,
            "language": lang,
            "conversations": [
                {"from": "human", "value": student_u1},
                {"from": "gpt", "value": teacher_u1},
                {"from": "human", "value": student_u2},
                {"from": "gpt", "value": teacher_u2}
            ],
            "metadata": {
                "board_name": profile["board_name"],
                "region": profile["region"],
                "student_personality": persona_info["name"],
                "student_ability": persona_info["ability"],
                "student_traits": persona_info["traits"],
                "topic": concept_name,
                "soil_context": local_soil,
                "crop_context": profile["crops"],
                "festival_context": festival,
                "cultural_object": local_object,
                "is_culturally_adaptive": True
            }
        }
        
        records.append(rec)
        
        board_idx = (board_idx + 1) % len(boards)
        topic_idx = (topic_idx + 1) % len(topics)
        persona_idx = (persona_idx + 1) % len(personas)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:
        for rec in records:
            f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(records)} localized dialogues at {OUTPUT_PATH}")
    print(f"Total File Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.2f} MB")
    print("=========================================================")

if __name__ == "__main__":
    generate_dataset()
