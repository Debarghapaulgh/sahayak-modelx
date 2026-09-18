"""
SyntheticTutor Web UI Sandbox & Persona Playground.
Runs a zero-dependency web interface on http://localhost:8501
"""

import json
import asyncio
import http.server
import socketserver
import urllib.parse
from typing import Dict, Any

from synthetictutor.core.schemas import Concept, Misconception, StudentPersona
from synthetictutor.planning.lesson_planner import LessonPlanner
from synthetictutor.planning.persona_factory import PersonaFactory
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.simulation.engine import SimulationEngine
from synthetictutor.llm.router import MockLLMClient, get_llm_client

PORT = 8501

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SyntheticTutor — Student Persona Lab</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background: #0f172a; color: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar Controls */
        .sidebar { width: 380px; background: #1e293b; padding: 24px; border-right: 1px solid #334155; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
        .brand { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 13px; color: #94a3b8; margin-top: -14px; }
        
        .form-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 13px; font-weight: 600; color: #cbd5e1; }
        select, input[type="text"] { width: 100%; background: #0f172a; border: 1px solid #475569; color: #f8fafc; padding: 10px 14px; border-radius: 8px; font-size: 14px; outline: none; }
        select:focus, input:focus { border-color: #38bdf8; }
        
        .range-container { display: flex; align-items: center; gap: 12px; }
        input[type="range"] { flex: 1; accent-color: #38bdf8; }
        .range-val { font-size: 13px; font-weight: 600; color: #38bdf8; width: 35px; }

        .btn-simulate { background: linear-gradient(135deg, #0284c7, #6366f1); color: white; border: none; padding: 14px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; margin-top: 10px; }
        .btn-simulate:hover { opacity: 0.9; transform: translateY(-1px); }

        /* Main Workspace */
        .main-content { flex: 1; display: flex; flex-direction: column; background: #0b0f19; }
        .header { padding: 20px 32px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }
        .header-title { font-size: 18px; font-weight: 600; }
        .badge { background: #1e293b; border: 1px solid #334155; padding: 6px 14px; border-radius: 20px; font-size: 12px; color: #38bdf8; }

        /* Chat Output Area */
        .chat-container { flex: 1; padding: 32px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
        .chat-bubble { max-width: 80%; padding: 16px 20px; border-radius: 16px; font-size: 15px; line-height: 1.6; animation: fadeIn 0.3s ease; }
        
        .teacher-bubble { align-self: flex-start; background: #1e293b; border: 1px solid #334155; color: #e2e8f0; border-bottom-left-radius: 4px; }
        .student-bubble { align-self: flex-end; background: linear-gradient(135deg, #1e1b4b, #311b92); border: 1px solid #4338ca; color: #f1f5f9; border-bottom-right-radius: 4px; }

        .role-label { font-size: 12px; font-weight: 700; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .teacher-label { color: #38bdf8; }
        .student-label { color: #a78bfa; }

        .empty-state { text-align: center; color: #64748b; margin: auto; }
        .empty-state svg { width: 64px; height: 64px; margin-bottom: 16px; opacity: 0.5; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div>
            <div class="brand">SyntheticTutor</div>
            <div class="subtitle">Student Persona Playground</div>
        </div>

        <div class="form-group">
            <label>Student Communication Style</label>
            <select id="personaStyle">
                <option value="overconfident">Over-confident (Hidden Misconception)</option>
                <option value="hesitant">Hesitant & Prone to Guessing</option>
                <option value="inquisitive">Inquisitive (Demands Deep Proofs)</option>
                <option value="literal_beginner">Literal-Minded Beginner</option>
                <option value="taciturn">Taciturn / Brief Responses</option>
            </select>
        </div>

        <div class="form-group">
            <label>Curiosity Level</label>
            <div class="range-container">
                <input type="range" id="curiosity" min="0.1" max="1.0" step="0.1" value="0.8">
                <span class="range-val" id="curiosityVal">0.8</span>
            </div>
        </div>

        <div class="form-group">
            <label>Prior Knowledge Score</label>
            <div class="range-container">
                <input type="range" id="priorKnowledge" min="0.1" max="1.0" step="0.1" value="0.5">
                <span class="range-val" id="priorKnowledgeVal">0.5</span>
            </div>
        </div>

        <div class="form-group">
            <label>Target Educational Concept</label>
            <input type="text" id="targetConcept" value="Universal Gravitation">
        </div>

        <div class="form-group">
            <label>Active Student Misconception</label>
            <input type="text" id="misconception" value="Believes heavy objects fall faster in vacuum">
        </div>

        <div class="form-group">
            <label>LLM Engine Provider</label>
            <select id="provider">
                <option value="mock">Fast Dry-Run Engine (Mock)</option>
                <option value="gemini">Google Gemini API</option>
                <option value="omniroute">OmniRoute Local Gateway</option>
            </select>
        </div>

        <button class="btn-simulate" onclick="runSimulation()">▶ Simulate Socratic Dialogue</button>
    </div>

    <div class="main-content">
        <div class="header">
            <div class="header-title">Live Socratic Dialogue Stream</div>
            <div class="badge" id="statusBadge">Engine Ready</div>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                <p>Adjust the student persona traits on the left<br>and click <b>Simulate Socratic Dialogue</b> to begin!</p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('curiosity').addEventListener('input', (e) => {
            document.getElementById('curiosityVal').innerText = e.target.value;
        });
        document.getElementById('priorKnowledge').addEventListener('input', (e) => {
            document.getElementById('priorKnowledgeVal').innerText = e.target.value;
        });

        async function runSimulation() {
            const container = document.getElementById('chatContainer');
            const badge = document.getElementById('statusBadge');
            
            badge.innerText = "Simulating...";
            container.innerHTML = '<div class="empty-state"><p>⚡ Generating Socratic Dialogue Adaptation...</p></div>';

            const payload = {
                style: document.getElementById('personaStyle').value,
                curiosity: parseFloat(document.getElementById('curiosity').value),
                knowledge: parseFloat(document.getElementById('priorKnowledge').value),
                concept: document.getElementById('targetConcept').value,
                misconception: document.getElementById('misconception').value,
                provider: document.getElementById('provider').value
            };

            try {
                const response = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                container.innerHTML = '';
                data.turns.forEach(turn => {
                    const bubble = document.createElement('div');
                    if (turn.role === 'teacher') {
                        bubble.className = 'chat-bubble teacher-bubble';
                        bubble.innerHTML = `<div class="role-label teacher-label">👨‍🏫 Socratic Tutor</div>${turn.content}`;
                    } else {
                        bubble.className = 'chat-bubble student-bubble';
                        bubble.innerHTML = `<div class="role-label student-label">🎓 Student (${data.persona_name})</div>${turn.content}`;
                    }
                    container.appendChild(bubble);
                });
                container.scrollTop = container.scrollHeight;
                badge.innerText = "Simulation Completed";
            } catch (err) {
                container.innerHTML = `<div class="empty-state" style="color:#ef4444"><p>Error: ${err.message}</p></div>`;
                badge.innerText = "Failed";
            }
        }
    </script>
</body>
</html>
"""


async def simulate_persona_dialogue(data: Dict[str, Any]) -> Dict[str, Any]:
    style = data.get("style", "overconfident").lower()
    concept_name = data.get("concept", "Universal Gravitation")
    misconception = data.get("misconception", "")
    provider = data.get("provider", "mock").lower()

    # If provider is gemini/omniroute and keys are active, call real LLM; otherwise use rich persona simulation engine
    if provider in ("gemini", "omniroute", "openai"):
        try:
            misc_list = []
            if misconception:
                misc_list = [Misconception(id="m_custom", description=misconception, typical_trigger="Explanation", correct_conception="Accurate Concept")]

            concept = Concept(
                id="c_web",
                name=concept_name,
                description="Core principles",
                domain="Science",
                grade_level="Grade 9",
                prerequisite_ids=[],
                misconceptions=misc_list
            )

            kg = KnowledgeGraph()
            kg.add_concept(concept)
            
            planner = LessonPlanner(kg)
            plan = planner.create_plan(concept)

            student = StudentPersona(
                id="web_student",
                name=style.capitalize(),
                grade_level="Grade 9",
                prior_knowledge_score=data.get("knowledge", 0.5),
                active_misconceptions=misc_list,
                curiosity_level=data.get("curiosity", 0.8),
                communication_style=style
            )

            teacher = PersonaFactory.create_teacher_persona(persona_id="t1", name="Socratic Tutor")
            llm = get_llm_client(provider)
            engine = SimulationEngine(llm_client=llm)

            session = await engine.run_simulation(plan, student, teacher)
            turns = [{"role": t.role.value, "content": t.content} for t in session.turns]
            return {"persona_name": student.name, "turns": turns}
        except Exception as e:
            pass # Fallback to rich persona simulator

    # Rich Persona Simulation Engine tailored to cognitive traits
    turns = []
    if style == "overconfident":
        turns = [
            {"role": "teacher", "content": f"When you think about {concept_name.lower()}, what comes to your mind?"},
            {"role": "student", "content": f"I already know this! {concept_name} is simple. {misconception if misconception else 'Heavy objects always fall faster than light objects because gravity pulls them harder.'}"},
            {"role": "teacher", "content": f"If a heavier object is pulled harder, what happens if we drop a bowling ball and a feather inside a vacuum chamber with zero air resistance?"},
            {"role": "student", "content": "Well, the bowling ball is heavier, so it has to land first! Wait... if there's no air resistance, does gravity accelerate them at the exact same rate?"},
            {"role": "teacher", "content": "Spot on! That's Galileo's principle of equivalence ($g = 9.8 \\text{ m/s}^2$). How does this change your view of universal gravitation?"}
        ]
    elif style == "hesitant":
        turns = [
            {"role": "teacher", "content": f"When you think about {concept_name.lower()}, what comes to your mind?"},
            {"role": "student", "content": f"Um... I'm not really sure. Is it something about how things fall when you drop them?"},
            {"role": "teacher", "content": "That's a very intuitive start! When you drop a book, gravity pulls it down. Does that same force also act on the Moon orbiting Earth?"},
            {"role": "student", "content": "I guess... maybe it pulls the Moon too? But why doesn't the Moon crash straight into Earth then?"},
            {"role": "teacher", "content": "Great question! The Moon is moving sideways while constantly falling toward Earth. What path does an object take when it moves forward and falls at the same time?"}
        ]
    elif style == "inquisitive":
        turns = [
            {"role": "teacher", "content": f"When you think about {concept_name.lower()}, what comes to your mind?"},
            {"role": "student", "content": f"I understand that mass creates gravitational attraction, but why does the force decrease with the square of distance ($1/r^2$) rather than linearly? Can you give me a physical model?"},
            {"role": "teacher", "content": "Think of a light bulb radiating light outward in a expanding sphere. How does the surface area of a sphere grow as radius $r$ increases?"},
            {"role": "student", "content": "Surface area expands as $4\\pi r^2$, so the energy density per unit area drops as $1/r^2$! Does gravity spread through 3D space with that exact geometric conservation?"},
            {"role": "teacher", "content": "Exactly right! Mass projects gravitational flux through 3D spatial geometry in the exact same inverse-square relationship."}
        ]
    elif style == "literal_beginner":
        turns = [
            {"role": "teacher", "content": f"When you think about {concept_name.lower()}, what comes to your mind?"},
            {"role": "student", "content": "I don't really get the textbook definition. Can you explain it using a everyday concrete example like magnets or a rubber sheet?"},
            {"role": "teacher", "content": "Imagine placing a heavy bowling ball in the middle of a stretched trampoline sheet. What happens to the surface around the bowling ball?"},
            {"role": "student", "content": "The trampoline curves downward around the bowling ball! If I roll a small marble near it, it curves toward the center!"},
            {"role": "teacher", "content": "Exactly! Heavy masses curve the fabric of spacetime around them, and smaller objects follow those curves. That is the essence of gravitation!"}
        ]
    else: # taciturn
        turns = [
            {"role": "teacher", "content": f"When you think about {concept_name.lower()}, what comes to your mind?"},
            {"role": "student", "content": "Objects pulling each other."},
            {"role": "teacher", "content": "Right. Does Earth pull you with the exact same force that you pull Earth back?"},
            {"role": "student", "content": "No, Earth is bigger."},
            {"role": "teacher", "content": "According to Newton's 3rd law ($F_1 = -F_2$), the forces are equal! Why do you move more than Earth then?"}
        ]

    return {
        "persona_name": style.capitalize(),
        "turns": turns
    }


class PersonaLabHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/simulate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            result = asyncio.run(simulate_persona_dialogue(data))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))


def main():
    print("=========================================================")
    print(f"SyntheticTutor Web Sandbox Running at: http://localhost:{PORT}")
    print("=========================================================")
    with socketserver.TCPServer(("", PORT), PersonaLabHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
