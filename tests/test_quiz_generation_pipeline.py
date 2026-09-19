import unittest
from synthetictutor.knowledge.topic_scope_lock import TopicScopeLock
from synthetictutor.evaluation.quiz_topic_validator import QuizTopicValidator

class TestQuizGenerationPipeline(unittest.TestCase):
    def test_topic_scope_lock_resolution(self):
        # 1. Percentages
        scope_p = TopicScopeLock.resolve_topic(8, "Mathematics", "শতকরা")
        self.assertEqual(scope_p.status, "VERIFIED")
        self.assertIn("শতকরা", scope_p.canonical_topic)
        self.assertIn("বর্গক্ষেত্র", scope_p.hard_negatives)

        # 2. Double Bar Graphs
        scope_g = TopicScopeLock.resolve_topic(7, "Mathematics", "অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ")
        self.assertEqual(scope_g.status, "VERIFIED")
        self.assertIn("দ্বি-স্তম্ভ লেখ", scope_g.canonical_topic)
        self.assertIn("বৃহৎ সংখ্যা", scope_g.hard_negatives)

        # 3. Recurring Decimals
        scope_d = TopicScopeLock.resolve_topic(6, "Mathematics", "আবৃত্ত দশমিক সংখ্যা")
        self.assertEqual(scope_d.status, "VERIFIED")
        self.assertIn("আবৃত্ত দশমিক", scope_d.canonical_topic)
        self.assertIn("প্যাটার্ন", scope_d.hard_negatives)

        # 4. Nirmal Vidyalaya
        scope_n = TopicScopeLock.resolve_topic(4, "Health and Physical Education", "নির্মল বিদ্যালয়")
        self.assertEqual(scope_n.status, "VERIFIED")
        self.assertIn("নির্মল বিদ্যালয়", scope_n.canonical_topic)

    def test_hard_negative_rejections(self):
        # Case 1: Percentage vs Squares
        scope_p = TopicScopeLock.resolve_topic(8, "Mathematics", "শতকরা")
        off_topic_p = "বর্গক্ষেত্র ও ঘনক: আকারের জগত কুইজ\nQ1. একটি বর্গক্ষেত্রের প্রত্যেকটি কোণের পরিমাপ কত?"
        rep_p = QuizTopicValidator.validate_quiz(off_topic_p, scope_p.requested_topic, scope_p.canonical_topic, scope_p.hard_negatives)
        self.assertFalse(rep_p.passed)
        self.assertFalse(rep_p.hard_negative_passed)

        # Case 2: Double-Bar Graph vs Large Numbers
        scope_g = TopicScopeLock.resolve_topic(7, "Mathematics", "দ্বি-স্তম্ভ লেখ")
        off_topic_g = "বৃহৎ সংখ্যা: আমাদের চারপাশের অঙ্ক কুইজ\nQ1. একটি শহরের জনসংখ্যা হল 7,34,56,892।"
        rep_g = QuizTopicValidator.validate_quiz(off_topic_g, scope_g.requested_topic, scope_g.canonical_topic, scope_g.hard_negatives)
        self.assertFalse(rep_g.passed)
        self.assertFalse(rep_g.hard_negative_passed)

        # Case 3: Recurring Decimals vs Patterns
        scope_d = TopicScopeLock.resolve_topic(6, "Mathematics", "আবৃত্ত দশমিক সংখ্যা")
        off_topic_d = "গাণিতিক নকশা ও প্যাটার্ন কুইজ\nQ1. নিচের কোনটি একটি গাণিতিক প্যাটার্ন অনুসরণ করে: 2, 4, 6, 8, __?"
        rep_d = QuizTopicValidator.validate_quiz(off_topic_d, scope_d.requested_topic, scope_d.canonical_topic, scope_d.hard_negatives)
        self.assertFalse(rep_d.passed)
        self.assertFalse(rep_d.hard_negative_passed)

    def test_sft_baselines_pass(self):
        # Case 1: Class 7 Double Bar Graphs SFT Baseline
        scope_g = TopicScopeLock.resolve_topic(7, "Mathematics", "অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ")
        sft_g = """
        সপ্তম শ্রেণি: গণিত - অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ
        পূর্ণমান: ১৫
        ১. দ্বি-স্তম্ভ লেখ কাকে বলে? (৩ নম্বর)
        ২. একটি দ্বি-স্তম্ভ লেখ অঙ্কন করার সময় কোন বিষয় খেয়াল রাখতে হয়? (৩ নম্বর)
        ৩. স্তম্ভলেখ থেকে উত্তর দিন... (৬ নম্বর)
        ৪. স্কেচ তৈরি করুন... (৩ নম্বর)
        """
        rep_g = QuizTopicValidator.validate_quiz(sft_g, scope_g.requested_topic, scope_g.canonical_topic, scope_g.hard_negatives, target_marks=15)
        self.assertTrue(rep_g.passed)

        # Case 2: Class 4 Nirmal Vidyalaya SFT Baseline
        scope_n = TopicScopeLock.resolve_topic(4, "Health and Physical Education", "নির্মল বিদ্যালয়")
        sft_n = """
        চতুর্থ শ্রেণি: স্বাস্থ্যবিধান ও পরিবেশ সচেতনতা — নির্মল বিদ্যালয়
        ১. বিদ্যালয় পরিচ্ছন্ন রাখার জন্য কী কী করা উচিত?
        ২. খাওয়ার আগে ও শৌচাগার ব্যবহারের পরে সাবান দিয়ে হাত ধোয়া কেন জরুরি?
        """
        rep_n = QuizTopicValidator.validate_quiz(sft_n, scope_n.requested_topic, scope_n.canonical_topic, scope_n.hard_negatives)
        self.assertTrue(rep_n.passed)

if __name__ == '__main__':
    unittest.main()