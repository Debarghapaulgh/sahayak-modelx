# Start Here: Understanding the Data Files

Read this before any other file. It explains, in plain terms, what our data files are and how to read one line. No prior knowledge needed.

---

## 1. What is a JSON object

JSON is just a way of writing down information as labelled boxes. Each box has a name and a value.

```json
{ "name": "Rina", "grade": 5, "subject": "Mathematics" }
```

Read it as: name is Rina, grade is 5, subject is Mathematics. Curly braces `{ }` wrap one object. Names are in quotes. A value can be text ("Rina"), a number (5), a list ([ ... ]), or another object.

A list uses square brackets:

```json
{ "student_names": ["Rina", "Bishal", "Sujan"] }
```

That is one box called student_names holding three names.

---

## 2. What is a JSONL file

JSONL means "JSON Lines". It is a text file where **each line is one complete JSON object**. Line 1 is one example, line 2 is another, and so on.

So a file with 2000 training examples has 2000 lines. Each line stands alone. That is all a JSONL file is: one example per line.

---

## 3. What one training example says

Every training line has three parts. This is the whole idea. Learn these three and you understand the dataset.

1. **system** — the situation and the rules. This is where the local context lives (place, board, language, local facts). It tells the model who it is helping and what facts it may use.
2. **user** — the teacher's request, in their own words.
3. **assistant** — the ideal answer a real local teacher would accept.

The model reads the system and the user, and learns to produce the assistant answer.

---

## 4. A real line, explained piece by piece

Here is one actual training line (open `samples/northbengal-sft-chat.jsonl` to see it in the file):

```json
{
  "messages": [
    { "role": "system",    "content": "You are SahayakAI ... CONTEXT ... local_facts: tea_garden_daily_wage=240 INR ... student_names: Rina, Bishal, Sujan" },
    { "role": "user",      "content": "ক্লাস ৫ এর জন্য ভগ্নাংশের ওয়ার্কশিট বানাও, ৫টা প্রশ্ন।" },
    { "role": "assistant", "content": "ভগ্নাংশ - অনুশীলন ... ৪. এক দিনের মজুরি ২৪০ টাকা ..." }
  ]
}
```

What each part is doing:

- **messages** is a list of the three turns.
- **system** sets the scene: WBBSE, Bengali, North Bengal, and the local facts. Notice the wage 240 is written here.
- **user** is the teacher asking for a fractions worksheet, in Bengali.
- **assistant** is the good answer. Notice it uses tea leaves and the 240 wage. It only uses facts that were given in the system part above. It does not invent new ones.

That last point is the most important rule. Every fact in the answer must already be in the system context. If the answer used a wage of 500 when the context said 240, that example is wrong.

---

## 5. The two shapes you will see

The content is always the same three parts. Only the wrapping differs by tool.

- **chat shape** (`samples/northbengal-sft-chat.jsonl`): roles are system, user, assistant. Used for Gemma and Sarvam.
- **gemini shape** (`samples/northbengal-sft-gemini.jsonl`): the same information, but the last role is called model instead of assistant, and text sits inside parts. Used for Vertex Gemini tuning.

Do not worry about which one to use yet. Just know they hold the same three parts.

---

## 6. How to open these files

- In VS Code, just click the file. Each line is one example. Long lines wrap; that is fine.
- To pretty-print one line so it is easy to read:

```bash
python3 -c "import json; print(json.dumps(json.loads(open('samples/northbengal-sft-chat.jsonl').readline()), ensure_ascii=False, indent=2))"
```

That prints the first example with nice spacing.

---

## 7. What to do after reading this

1. Open `samples/northbengal-sft-chat.jsonl` and read the three lines slowly. Match each to the three parts above.
2. Open `samples/northbengal-labeling.sample.jsonl`. This is the raw human-written form, before it becomes a training line.
3. Then read `DATASET_ONE_PAGER.md` for the plan.

That is enough to understand everything. The rest of the docs are detail for when you start building.
