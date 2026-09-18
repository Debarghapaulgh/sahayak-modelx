"""
SahayakAI Part 1 SFT Dataset Pilot Generator.
Executes pilot generation and validation across WBBPE, WBBSE, and WBCHSE.
"""

import os
import json
from synthetictutor.core.schemas_part1 import (
    Part1SFTRecord, CurriculumMetadata, SourceMetadata,
    LocalContextMetadata, QAMetadata, LessonPlanMetadata,
    QuizMetadata
)
from synthetictutor.knowledge.curriculum_manifest import CurriculumManifest
from synthetictutor.pipeline.part1_pipeline import Part1Pipeline

def run_pilot():
    pipeline = Part1Pipeline(output_dir="datasets/textbook_sft_part1")

    pilot_candidates = [
        # 1. WBBPE Class 4 HPE - Nirmal Vidyalaya (QA)
        Part1SFTRecord(
            id="part1_pilot_001",
            task_type="QA",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumManifest.resolve_curriculum(4, "Health and Physical Education", "নির্মল বিদ্যালয়"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbpe_cl4_hpe_ch2_chunk_08"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="GENERIC_WB", scenario_type="HYPOTHETICAL"),
            qa_metadata=QAMetadata(subtype="EXPLAIN", difficulty="EASY", cognitive_level="UNDERSTAND"),
            user_prompt="চতুর্থ শ্রেণির শিক্ষার্থীদের জন্য 'নির্মল বিদ্যালয়' অভিযানের মূল উদ্দেশ্য এবং স্বাস্থ্যবিধির গুরুত্ব সহজ ভাষায় বুঝিয়ে দিন।",
            assistant_response="""নির্মল বিদ্যালয় অভিযানের মূল উদ্দেশ্য হলো আমাদের বিদ্যালয় প্রাঙ্গণ ও পরিবেশকে সবসময় পরিষ্কার-পরিচ্ছন্ন, স্বাস্থ্যকর ও সুন্দর রাখা।

এর প্রধান বিষয়গুলি হলো:
১. **ব্যক্তিগত পরিচ্ছন্নতা:** খাবার খাওয়ার আগে ও শৌচাগার ব্যবহারের পরে সাবান দিয়ে ভালো করে হাত ধোয়া।
২. **শ্রেণিকক্ষের পরিচ্ছন্নতা:** শ্রেণিকক্ষের মেঝে, বেঞ্চ ও ব্ল্যাকবোর্ড পরিচ্ছন্ন রাখা এবং যেখানে-সেখানে কাগজের টুকরো বা আবর্জনা না ফেলা।
৩. **নির্দিষ্ট ডাস্টবিনের ব্যবহার:** সমস্ত অপ্রয়োজনীয় আবর্জনা নির্দিষ্ট পাত্র বা ডাস্টবিনে ফেলা।
৪. **বিশুদ্ধ পানীয় জল:** পানীয় জলের জায়গা সবসময় শুকনো ও পরিষ্কার রাখা।

পরিচ্ছন্ন বিদ্যালয় পরিবেশ আমাদের শরীর ও মন উভয়কেই সুস্থ রাখে এবং আনন্দ সহকারে পড়াশোনা করতে সাহায্য করে।"""
        ),

        # 2. WBBPE Class 4 HPE - Nirmal Vidyalaya (Lesson Plan)
        Part1SFTRecord(
            id="part1_pilot_002",
            task_type="LESSON_PLAN",
            requester_role="TEACHER",
            instructional_target="TEACHER",
            curriculum=CurriculumManifest.resolve_curriculum(4, "Health and Physical Education", "নির্মল বিদ্যালয়"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbpe_cl4_hpe_ch2_chunk_08"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            lesson_plan_metadata=LessonPlanMetadata(
                lesson_duration_minutes=40,
                pedagogical_model="ACTIVITY_BASED",
                grade_tier="III_V",
                teaching_aids=["সাবান", "পরিষ্কার জল", "ডাস্টবিন", "হাত ধোয়ার পোস্টার"]
            ),
            user_prompt="চতুর্থ শ্রেণির 'স্বাস্থ্যবিধান ও পরিবেশ সচেতনতা' অধ্যায়ের 'নির্মল বিদ্যালয়' পাঠটির উপর ৪০ মিনিটের একটি সক্রিয়তা-ভিত্তিক পাঠপরিকল্পনা (Lesson Plan) তৈরি করে দিন।",
            assistant_response="""### পাঠপরিকল্পনা: স্বাস্থ্যবিধান ও পরিবেশ সচেতনতা (নির্মল বিদ্যালয়)

**শ্রেণি:** চতুর্থ শ্রেণি | **বিষয়:** স্বাস্থ্য ও শারীরশিক্ষা | **সময়:** ৪০ মিনিট | **পদ্ধতি:** সক্রিয়তা-ভিত্তিক শিখন

---

#### ১. শিখন উদ্দেশ্য ও শিখনফল (Learning Outcomes):
- শিক্ষার্থীরা নির্মল বিদ্যালয় অভিযানের মূল গুরুত্ব বুঝতে পারবে।
- সাবান দিয়ে সঠিক নিয়মে হাত ধোয়ার অভ্যাস আয়ত্ত করতে পারবে।
- বিদ্যালয়ের শ্রেণিকক্ষ ও মাঠ পরিষ্কার রাখার দায়িত্বশীলতা প্রদর্শন করবে।

#### ২. প্রয়োজনীয় উপকরণ (Teaching Aids):
- সাবান, পরিষ্কার জলের বালতি/মগ, দুটি রঙের ডাস্টবিন (পচনশীল ও অপচনশীল বর্জ্যের জন্য) এবং স্বাস্থ্যবিধির চার্ট।

#### ৩. পাঠ উপস্থাপন ও শিক্ষাদান পর্যায় (Teaching Sequence):
- **ভূমিকা ও প্রাক-অভিজ্ঞতা যাচাই (৭ মিনিট):** 
  শিক্ষক শিক্ষার্থীদের কাছে প্রশ্ন করবেন—"আজ সকালে স্কুলে আসার পর তোমরা কে কে হাত ধুয়েছ?" এবং আলোচনা শুরু করবেন।
- **উপস্থাপন ও সক্রিয়তা (১৫ মিনিট):** 
  শিক্ষক হাত ধোয়ার ৬টি ধাপ (পদ্ধতি) সরাসরি প্রদর্শন করবেন এবং শিক্ষার্থীদের দিয়ে তা অনুশীলন করাবেন।
- **দলগত কাজ (১০ মিনিট):** 
  শিক্ষার্থীদের দুটি দলে ভাগ করে শ্রেণিকক্ষ পরিচ্ছন্নতার নিয়মাবলি চার্টে চিহ্নিত করতে দেওয়া হবে।
- **মূল্যায়ন ও পর্যবেক্ষণ (৫ মিনিট):** 
  শিক্ষার্থীদের মৌখিক প্রশ্ন ও হাত ধোয়ার ধাপ পর্যবেক্ষণের মাধ্যমে ধারণা যাচাই।
- **বাড়ির কাজ / সম্প্রসারিত কাজ (৩ মিনিট):** 
  নিজের বাড়ি ও পড়ার জায়গা পরিষ্কার রাখার একটি তালিকা খাতায় লিখে নিয়ে আসা।"""
        ),

        # 3. WBBSE Class 6 Mathematics - Recurring Decimals (QA)
        Part1SFTRecord(
            id="part1_pilot_003",
            task_type="QA",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumManifest.resolve_curriculum(6, "Mathematics", "আবৃত্ত দশমিক সংখ্যা"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbse_cl6_math_ch10_chunk_03"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            qa_metadata=QAMetadata(subtype="SOLVE", difficulty="MODERATE", cognitive_level="APPLY", step_by_step=True),
            user_prompt="ষষ্ঠ শ্রেণির গণিতের বিশুদ্ধ আবৃত্ত দশমিক সংখ্যা ০.৫৭৫৭৫৭... (বা ০.৫̇৭̇)-কে সামান্য ভগ্নাংশে রূপান্তরের নিয়মটি ধাপে ধাপে বুঝিয়ে দিন।",
            assistant_response="""বিশুদ্ধ আবৃত্ত দশমিক সংখ্যাকে সামান্য ভগ্নাংশে রূপান্তর করার নিয়মটি নিচে ধাপে ধাপে দেখানো হলো:

**সমস্যা:** $0.\dot{5}\dot{7}$ (বা $0.575757...$)-কে সামান্য ভগ্নাংশে প্রকাশ করো।

**ধাপ ১: লব গঠন করা**
- দশমিক বিন্দু এবং পৌনঃপুনিক বিন্দু তুলে দিয়ে আবৃত্ত অংশের সম্পূর্ণ সংখ্যাটি লবে লিখি।
- এখানে লব = $57$।

**ধাপ ২: হর গঠন করা**
- পৌনঃপুনিক অংশের মধ্যে যতগুলি অঙ্ক আছে, ঠিক ততগুলি ৯ (নয়) হরে লিখতে হবে।
- এখানে পৌনঃপুনিক বিন্দুর নিচে দুটি অঙ্ক ($5$ ও $7$) আছে, তাই হরে দুটি ৯ অর্থাৎ $99$ হবে।
- সুতরাং ভগ্নাংশটি হলো = $\\frac{57}{99}$।

**ধাপ ৩: লঘিষ্ঠ আকারে প্রকাশ করা**
- লব ও হর উভয়কেই ৩ দিয়ে ভাগ করি:
  $$\\frac{57 \\div 3}{99 \\div 3} = \\frac{19}{33}$$

**উত্তর:** নির্ণেয় সামান্য ভগ্নাংশটি হলো $\\frac{19}{33}$।"""
        ),

        # 4. WBBSE Class 7 Mathematics - Double Bar Graphs (Quiz)
        Part1SFTRecord(
            id="part1_pilot_004",
            task_type="QUIZ",
            requester_role="TEACHER",
            instructional_target="TEACHER",
            curriculum=CurriculumManifest.resolve_curriculum(7, "Mathematics", "দ্বি-স্তম্ভ লেখ"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbse_cl7_math_ch16_chunk_14"],
                visual_dependency="SUPPORTIVE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            quiz_metadata=QuizMetadata(
                quiz_scope="SINGLE_TOPIC",
                question_count=4,
                total_marks=15,
                difficulty="MODERATE",
                answer_mode="QUIZ_WITH_SEPARATE_ANSWER_KEY"
            ),
            user_prompt="সপ্তম শ্রেণির গণিত বইয়ের 'অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ' অধ্যায়টির উপর শিক্ষার্থীদের মূল্যায়নের জন্য ১৫ নম্বরের একটি কুইজ ও উত্তর নির্দেশিকা তৈরি করে দিন।",
            assistant_response="""### সপ্তম শ্রেণি: গণিত — অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ (মূল্যায়ন কুইজ)

**পূর্ণমান:** ১৫ | **সময়:** ৩০ মিনিট

---

#### কুইজ প্রশ্নপত্র

১. দ্বি-স্তম্ভ লেখ (Double Bar Graph) কাকে বলে? এটি একক স্তম্ভলেখের চেয়ে কোন ক্ষেত্রে বেশি উপযোগী? (৩ নম্বর)

২. দ্বি-স্তম্ভ লেখ অঙ্কনের সময় আনুভূমিক অক্ষ ($x$-অক্ষ) এবং উল্লম্ব অক্ষ ($y$-অক্ষ) বরাবর সাধারণত কী কী তথ্য দেখানো হয়? স্কেল নির্বাচনের গুরুত্ব কী? (৩ নম্বর)

৩. নিচে একটি বিদ্যালয়ের সপ্তম শ্রেণির দুটি বিভাগ (বিভাগ 'ক' ও বিভাগ 'খ')-এর বার্ষিক পরীক্ষায় গণিত ও বিজ্ঞানের গড় নম্বর দেওয়া হলো:

| বিষয় | বিভাগ 'ক' (গড় নম্বর) | বিভাগ 'খ' (গড় নম্বর) |
| :--- | :---: | :---: |
| গণিত | ৮০ | ৭৫ |
| বিজ্ঞান | ৭০ | ৮৫ |

(ক) গণিতে কোন বিভাগ বেশি গড় নম্বর পেয়েছে এবং কত বেশি? (১ নম্বর)  
(খ) বিজ্ঞানে কোন বিভাগ এগিয়ে রয়েছে? (১ নম্বর)  
(গ) বিভাগ 'ক'-এর দুটি বিষয়ের মোট গড় নম্বর কত? (১ নম্বর)  
(ঘ) এই তথ্যের দ্বি-স্তম্ভ লেখ আঁকলে উল্লম্ব অক্ষে ১ একক সমান কত নম্বর ধরা যুক্তিযুক্ত? (১ নম্বর)  
(ঙ) বিভাগ 'খ'-এর গণিত ও বিজ্ঞান বিষয়ের নম্বরের পার্থক্য কত? (১ নম্বর)  
(চ) দুটি স্তম্ভের প্রস্থ ও তাদের মধ্যবর্তী ব্যবধান সম্পর্কে কী নিয়ম প্রযোজ্য? (১ নম্বর)

৪. বিদ্যালয়ের ষষ্ঠ ও সপ্তম শ্রেণির শিক্ষার্থীদের প্রিয় খেলার তালিকা ব্যবহার করে একটি দ্বি-স্তম্ভলেখের খসড়া চিত্র (অক্ষ ও স্কেল নির্দেশ সহ) অঙ্কন করো। (৩ নম্বর)

---

### উত্তর নির্দেশিকা ও নম্বর বিভাজন (Answer Key & Marking Scheme)

১. **উত্তর:** দুটি সম্পর্কিত তথ্যকে পাশাপাশি দুটি স্তম্ভের মাধ্যমে প্রকাশ করার লেখচিত্রকে দ্বি-স্তম্ভ লেখ বলে। দুটি দলের তথ্যের সরাসরি তুলনামূলক বিশ্লেষণের জন্য এটি একক স্তম্ভলেখের চেয়ে বেশি উপযোগী। (সংজ্ঞা: ২ নম্বর, উপযোগিতা: ১ নম্বর)

২. **উত্তর:** সাধারণত $x$-অক্ষে গুণবাচক তথ্য (যেমন বিষয়/বছর) এবং $y$-অক্ষে পরিমাণবাচক তথ্য (সংখ্যা/নম্বর) দেখানো হয়। তথ্যের বিস্তারের উপর নির্ভর করে সঠিক স্কেল নির্বাচন করলে স্তম্ভলেখের দৃশ্যমান নির্ভুলতা বজায় থাকে। (অক্ষ বর্ণনা: ২ নম্বর, স্কেল: ১ নম্বর)

৩. **উত্তর:**  
(ক) বিভাগ 'ক' বেশি পেয়েছে, $৮০ - ৭৫ = ৫$ নম্বর বেশি। (১ নম্বর)  
(খ) বিভাগ 'খ' বিজ্ঞানে এগিয়ে ($৮৫ > ৭০$)। (১ নম্বর)  
(গ) বিভাগ 'ক'-এর মোট গড় = $৮০ + ৭০ = ১৫০$। (১ নম্বর)  
(ঘ) ১ একক = ১০ নম্বর ধরা যুক্তিযুক্ত। (১ নম্বর)  
(ঙ) পার্থক্য = $৮৫ - ৭৫ = ১০$ নম্বর। (১ নম্বর)  
(চ) প্রতিটি স্তম্ভের প্রস্থ সমান হবে এবং জোড়া স্তম্ভের মধ্যবর্তী দূরত্ব সমান থাকবে। (১ নম্বর)

৪. **উত্তর:** সঠিক অক্ষ চিহ্নিতকরণ (১ নম্বর), উপযুক্ত স্কেল নির্দেশ (১ নম্বর) এবং স্তম্ভদ্বয়ের স্পষ্ট পার্থক্য সূচক চিহ্ন/রঙের ব্যবহার (১ নম্বর)।"""
        ),

        # 5. WBBSE Class 8 Mathematics - Percentages (QA)
        Part1SFTRecord(
            id="part1_pilot_005",
            task_type="QA",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumManifest.resolve_curriculum(8, "Mathematics", "শতকরা"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbse_cl8_math_ch11_chunk_05"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            qa_metadata=QAMetadata(subtype="STEP_BY_STEP", difficulty="MODERATE", cognitive_level="APPLY", step_by_step=True),
            user_prompt="অষ্টম শ্রেণির শিক্ষার্থীদের জন্য চিনির দাম শতকরা ২০% বৃদ্ধি পাওয়ার পর চিনির মাসিক খরচ অপরিবর্তিত রাখতে ব্যবহার শতকরা কত কমাতে হবে তা বুঝিয়ে দিন।",
            assistant_response="""চিনির মূল্যবৃদ্ধির পর খরচ অপরিবর্তিত রাখার সমস্যাটি নিচে সহজ ও ধাপে ধাপে সমাধান করে বোঝানো হলো:

**ধাপ ১: প্রাথমিক পরিমাণ ও মূল্য ধরে নেওয়া**
- মনে করি, পূর্বে ১০০ টাকায় পাওয়া যেত ১০০ একক চিনি।

**ধাপ ২: বর্তমান মূল্য নির্ধারণ**
- চিনির দাম ২০% বৃদ্ধি পেয়েছে।
- অর্থাৎ, পূর্বে যে পরিমাণ চিনি ১০০ টাকায় পাওয়া যেত, এখন তার দাম = $(১০০ + ২০) = ১২০$ টাকা।

**ধাপ ৩: ঐকিক নিয়মে বর্তমান ব্যবহার হিসাব করা**
- এখন ১২০ টাকায় পাওয়া যায় ১০০ একক চিনি।
- অতএব, ১ টাকায় পাওয়া যায় $\\frac{১০০}{১২০}$ একক চিনি।
- খরচ অপরিবর্তিত রাখতে ১০০ টাকায় পাওয়া যাবে:
  $$\\frac{১০০ \\times ১০০}{১২০} = \\frac{১০০০}{১২} = \\frac{২৫০}{৩} = ৮৩\\frac{১}{৩} \\text{ একক চিনি।}$$

**ধাপ ৪: ব্যবহার হ্রাসের শতকরা হার নির্ণয়**
- চিনির ব্যবহার কমাতে হবে = $১০০ - ৮৩\\frac{১}{৩} = \\frac{৩০০ - ২৫০}{৩} = \\frac{৫০}{৩} = ১৬\\frac{২}{৩}\\%$।

**উত্তর:** চিনির খরচ অপরিবর্তিত রাখতে চিনির মাসিক ব্যবহার $১৬\\frac{২}{৩}\\%$ কমাতে হবে।"""
        ),

        # 6. WBBSE Class 8 Bengali - Grammar (QA)
        Part1SFTRecord(
            id="part1_pilot_006",
            task_type="QA",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumManifest.resolve_curriculum(8, "Bengali", "দল ও ধ্বনি পরিবর্তন"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbbse_cl8_bengali_gram_chunk_02"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            qa_metadata=QAMetadata(subtype="EXPLAIN", difficulty="MODERATE", cognitive_level="UNDERSTAND"),
            user_prompt="অষ্টম শ্রেণির ভাষা পাঠ বইয়ের 'ধ্বনি পরিবর্তন' অধ্যায় থেকে 'আদি-স্বরলোপ' ও 'মধ্য-স্বরলোপ'-এর পার্থক্য উদাহরণসহ বুঝিয়ে দিন।",
            assistant_response="""বাংলা ব্যাকরণে শব্দের উচ্চারণের সুবিধার জন্য স্বরধ্বনির লোপ পাওয়ার দুটি গুরুত্বপূর্ণ নিয়ম হলো **আদি-স্বরলোপ** এবং **মধ্য-স্বরলোপ**। এদের পার্থক্য নিচে আলোচনা করা হলো:

---

### ১. আদি-স্বরলোপ (Procope):
- **সংজ্ঞা:** শব্দের শুরুতে থাকা স্বরধ্বনি যখন উচ্চারণের দ্রুততা বা সুবিধার কারণে লোপ পায়, তখন তাকে আদি-স্বরলোপ বলে।
- **পাঠ্যবইয়ের উদাহরণ:**
  - অলাবু > লাবু > **লাউ** (এখানে শব্দের শুরুতে থাকা 'অ' ধ্বনিটি লোপ পেয়েছে)
  - উদ্ধার > উধার > **ধার** (শব্দের আদি স্বরধ্বনি 'উ' লোপ পেয়েছে)

---

### ২. মধ্য-স্বরলোপ বা সমাক্ষরলোপ (Syncope):
- **সংজ্ঞা:** শব্দের মাঝখানে থাকা কোনো স্বরধ্বনি যখন লোপ পায়, তখন তাকে মধ্য-স্বরলোপ বলে।
- **পাঠ্যবইয়ের উদাহরণ:**
  - গামুছা > **গামছা** ('মু'-এর অন্তর্গত মধ্যবর্তী 'উ' স্বরধ্বনিটি লোপ পেয়েছে)
  - জানালা > **জানলা** ('না'-এর অন্তর্গত মধ্যবর্তী 'আ' স্বরধ্বনিটি লোপ পেয়েছে)

---

**সংক্ষেপে পার্থক্য:** 
আদি-স্বরলোপে শব্দের **প্রথম স্বরধ্বনি** বিলুপ্ত হয়, কিন্তু মধ্য-স্বরলোপে শব্দের **মাঝখানের স্বরধ্বনি** বিলুপ্ত হয়।"""
        ),

        # 7. WBCHSE Class 11 General / History - Anthropological Stages (Quiz)
        Part1SFTRecord(
            id="part1_pilot_007",
            task_type="QUIZ",
            requester_role="TEACHER",
            instructional_target="TEACHER",
            curriculum=CurriculumManifest.resolve_curriculum(11, "General", "নৃতাত্ত্বিক পর্যায়"),
            source=SourceMetadata(
                source_mode="TEXTBOOK_GROUNDED",
                textbook_source_chunks=["wbchse_cl11_hist_sem1_chunk_04"],
                visual_dependency="NONE"
            ),
            local_context=LocalContextMetadata(mode="NONE"),
            quiz_metadata=QuizMetadata(
                quiz_scope="SINGLE_TOPIC",
                question_count=3,
                total_marks=10,
                difficulty="DIFFICULT",
                answer_mode="QUIZ_WITH_SEPARATE_ANSWER_KEY"
            ),
            user_prompt="একাদশ শ্রেণির 'নৃতাত্ত্বিক পর্যায় নিরূপণের উপায়' অধ্যায় থেকে শিক্ষার্থীদের মূল্যায়নের জন্য একটি ১০ নম্বরের কুইজ তৈরি করে দিন।",
            assistant_response="""### একাদশ শ্রেণি: প্রথম অধ্যায় — নৃতাত্ত্বিক পর্যায় নিরূপণের উপায় (কুইজ)

**পূর্ণমান:** ১০ | **সময়:** ২০ মিনিট

---

#### কুইজ প্রশ্নপত্র

১. মানব বিবর্তনের নৃতাত্ত্বিক পর্যায় নিরূপণে 'রেডিওকার্বন ডেটিং' ($C^{14}$) পদ্ধতির ভূমিকা সংক্ষেপে ব্যাখ্যা করো। (৩ নম্বর)

২. প্রত্নতাত্ত্বিক স্তরবিন্যাসবিদ্যা (Stratigraphy) কীভাবে প্রাচীন মানব সংস্কৃতির কালক্রম নির্ধারণে সহায়তা করে? (৩ নম্বর)

৩. নিম্নলিখিত প্রশ্নগুলির সংক্ষিপ্ত উত্তর দাও: (৪ × ১ = ৪ নম্বর)  
(ক) জীবাশ্মবিদ্যা (Palaeontology) কাকে বলে?  
(খ) হোমো ইরেক্টাস পর্যায়ের দুটি প্রধান শারীরিক বৈশিষ্ট্য উল্লেখ করো।  
(গ) আপেক্ষিক কালনির্ধারণ ও পরম কালনির্ধারণের একটি প্রধান পার্থক্য কী?  
(ঘ) প্রাচীন মানব কঙ্কালের ক্র্যানিয়াল ক্যাপাসিটি (মস্তিষ্কের ধারণক্ষমতা) পরিমাপের গুরুত্ব কী?

---

### উত্তর নির্দেশিকা ও নম্বর বিভাজন (Answer Key & Marking Scheme)

১. **উত্তর:** জীবিত প্রাণীর মৃত্যুর পর $C^{14}$ আইসোটোপের ক্ষয়িষ্ণুতার অর্ধায়ু ($5730$ বছর) গণনা করে ৫০,০০০ বছর পর্যন্ত প্রাচীন জৈব অবশিষ্টাংশের সঠিক সময়সীমা নির্ণয় করা সম্ভব হয়। (৩ নম্বর)

২. **উত্তর:** ভূগর্ভস্থ পলল স্তরের বিন্যাস অনুযায়ী নীচের স্তর প্রাচীনতর এবং উপরের স্তর সাম্প্রতিকতর—এই ভূতাত্ত্বিক নিয়মের ভিত্তিতে প্রত্নতাত্ত্বিক নমুনার আপেক্ষিক সময়কাল নির্ধারিত হয়। (৩ নম্বর)

৩. **উত্তর:**  
(ক) প্রাচীন জীবাশ্মের গঠন ও জীবন সংক্রান্ত বিজ্ঞানসম্মত অধ্যয়ন। (১ নম্বর)  
(খ) সোজা হয়ে দাঁড়ানোর ক্ষমতা ও সুনির্দিষ্ট চোয়ালের গঠন। (১ নম্বর)  
(গ) আপেক্ষিক পদ্ধতিতে আনুমানিক ক্রম বোঝা যায়, পরম পদ্ধতিতে সুনির্দিষ্ট বছর গণনা করা যায়। (১ নম্বর)  
(ঘ) মানব মস্তিষ্কের বিবর্তন ও বুদ্ধিবৃত্তিক অগ্রগতির স্তর নিরূপণে সাহায্য করে। (১ নম্বর)"""
        )
    ]

    print(f"Processing {len(pilot_candidates)} pilot candidate records...")
    for rec in pilot_candidates:
        processed = pipeline.process_and_validate_record(rec)
        print(f"Record {processed.id} ({processed.task_type}) -> Valid: {processed.validation.overall_passed}")

    artifacts = pipeline.export_dataset_artifacts()
    print("\nSuccessfully exported Part 1 pilot artifacts:")
    for k, v in artifacts.items():
        print(f" - {k}: {v}")

if __name__ == "__main__":
    run_pilot()