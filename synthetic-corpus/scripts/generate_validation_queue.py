#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_validation_queue.py
Generates an interactive, premium HTML dashboard for pilot teachers to review, 
edit, and sign off candidate examples.
"""

import os
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(BASE_DIR, "prompts", "candidate-results.jsonl")
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(BASE_DIR), "teacher_validation_queue.html")

def escape_html(text):
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace('"', "&quot;").replace("'", "&#39;")
    return text

def main():
    if not os.path.exists(CANDIDATES_PATH):
        print(f"Error: Candidate file {CANDIDATES_PATH} not found. Run candidate generation first.")
        return

    records = []
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except Exception as e:
                    print(f"Skipping malformed line: {e}")

    # Start constructing HTML
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teacher Sign-off Queue & QA Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.6);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
            background-image: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 45%),
                              radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.1) 0%, transparent 40%);
            background-attachment: fixed;
        }

        header {
            max-width: 1200px;
            margin: 0 auto 3rem auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        p.subtitle {
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }

        .stats-bar {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            backdrop-filter: blur(12px);
            display: flex;
            gap: 1.5rem;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stat-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .stat-dot.total { background: var(--accent); }
        .stat-dot.approved { background: var(--success); }
        .stat-dot.revision { background: var(--danger); }
        .stat-dot.pending { background: var(--text-secondary); }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            gap: 2rem;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .card:hover {
            border-color: rgba(99, 102, 241, 0.3);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 1rem;
        }

        .meta-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge.id { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; }
        .badge.subject { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .badge.grade { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .badge.district { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .badge.setting { background: rgba(255, 255, 255, 0.1); color: var(--text-primary); }

        .review-status-label {
            font-weight: 700;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #a5b4fc;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) {
            .grid-layout {
                grid-template-columns: 1fr;
            }
        }

        .context-box {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 1rem;
            font-size: 0.85rem;
            line-height: 1.5;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        .context-item {
            margin-bottom: 0.5rem;
            display: flex;
            flex-wrap: wrap;
        }

        .context-key {
            font-weight: 600;
            color: var(--text-secondary);
            width: 120px;
        }

        .context-val {
            color: var(--text-primary);
            flex: 1;
        }

        .prompt-box {
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid rgba(99, 102, 241, 0.1);
            border-radius: 8px;
            padding: 1rem;
            font-size: 1rem;
            line-height: 1.5;
            font-weight: 500;
        }

        .editor-container {
            margin-bottom: 1.5rem;
        }

        textarea.response-editor {
            width: 100%;
            height: 180px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 1rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.95rem;
            line-height: 1.6;
            resize: vertical;
            transition: border-color 0.2s ease;
        }

        textarea.response-editor:focus {
            outline: none;
            border-color: var(--accent);
        }

        .actions-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            background: rgba(0, 0, 0, 0.15);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.02);
        }

        .decision-group {
            display: flex;
            gap: 1rem;
        }

        .decision-btn {
            background: transparent;
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 0.5rem 1.25rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .decision-btn.approve:hover, .decision-btn.approve.active {
            background: var(--success);
            border-color: var(--success);
            color: #ffffff;
        }

        .decision-btn.revision:hover, .decision-btn.revision.active {
            background: var(--danger);
            border-color: var(--danger);
            color: #ffffff;
        }

        .corrections-input {
            flex: 1;
            min-width: 250px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            color: var(--text-primary);
            font-size: 0.85rem;
            transition: border-color 0.2s;
        }

        .corrections-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        .export-footer {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 100;
        }

        .export-btn {
            background: var(--accent);
            color: #ffffff;
            border: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4);
            cursor: pointer;
            transition: transform 0.2s, background-color 0.2s;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .export-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
        }

        .export-btn:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>

    <header>
        <div>
            <h1>Teacher Sign-off & QA Portal</h1>
            <p class="subtitle">North Bengal (WBBSE Bengali Medium) Candidate Examples Queue</p>
        </div>
        <div class="stats-bar">
            <div class="stat-item">
                <span class="stat-dot total"></span>
                <span>Total: <span id="total-count">0</span></span>
            </div>
            <div class="stat-item">
                <span class="stat-dot approved"></span>
                <span>Approved: <span id="approved-count">0</span></span>
            </div>
            <div class="stat-item">
                <span class="stat-dot revision"></span>
                <span>Revision: <span id="revision-count">0</span></span>
            </div>
            <div class="stat-item">
                <span class="stat-dot pending"></span>
                <span>Pending: <span id="pending-count">0</span></span>
            </div>
        </div>
    </header>

    <div class="container" id="cards-container">
"""

    for record in records:
        ctx = record.get("context", {})
        rec_id = record.get("id", "")
        task_type = record.get("task_type", "")
        subject = ctx.get("subject", "")
        grade = ctx.get("grade", "")
        district = ctx.get("district", "")
        setting = ctx.get("setting", "")
        prompt = record.get("prompt", "")
        ideal_response = record.get("ideal_response", "")
        notes = record.get("notes", "")

        # Format context item list
        context_items_html = ""
        for key, val in ctx.items():
            if key in ["board", "medium", "region"]:
                continue
            context_items_html += f"""
            <div class="context-item">
                <span class="context-key">{key}:</span>
                <span class="context-val">{escape_html(str(val))}</span>
            </div>"""

        html_content += f"""
        <!-- CARD {rec_id} -->
        <div class="card" id="card-{rec_id}" data-id="{rec_id}" data-status="pending">
            <div class="card-header">
                <div class="meta-badges">
                    <span class="badge id">{escape_html(rec_id)}</span>
                    <span class="badge subject">{escape_html(subject)}</span>
                    <span class="badge grade">Grade {escape_html(str(grade))}</span>
                    <span class="badge district">{escape_html(district)}</span>
                    <span class="badge setting">{escape_html(setting)}</span>
                </div>
                <div class="review-status-label" id="status-label-{rec_id}">
                    <span class="stat-dot pending"></span> PENDING REVIEW
                </div>
            </div>

            <div class="grid-layout">
                <div>
                    <div class="section-title">Context Parameters</div>
                    <div class="context-box">
                        {context_items_html}
                    </div>
                </div>
                <div>
                    <div class="section-title">Teacher Prompt / Request</div>
                    <div class="prompt-box">
                        {escape_html(prompt)}
                    </div>
                </div>
            </div>

            <div class="editor-container">
                <div class="section-title">Draft Model Response (Edit directly to refine)</div>
                <textarea class="response-editor" id="editor-{rec_id}" placeholder="Final response goes here...">{escape_html(ideal_response)}</textarea>
            </div>

            <div class="actions-row">
                <div class="decision-group">
                    <button class="decision-btn approve" onclick="setDecision('{rec_id}', 'approved')">
                        Approve as Gold
                    </button>
                    <button class="decision-btn revision" onclick="setDecision('{rec_id}', 'revision')">
                        Request Changes
                    </button>
                </div>
                <input type="text" class="corrections-input" id="comments-{rec_id}" placeholder="Add private feedback / correction notes..." value="{escape_html(notes)}">
            </div>
        </div>
"""

    html_content += """
    </div>

    <div class="export-footer">
        <button class="export-btn" onclick="exportData()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            Export Signed-off Dataset
        </button>
    </div>

    <script>
        const recordsData = """ + json.dumps(records, ensure_ascii=False) + """;

        function updateStats() {
            let total = 0, approved = 0, revision = 0, pending = 0;
            document.querySelectorAll('.card').forEach(card => {
                total++;
                const status = card.getAttribute('data-status');
                if (status === 'approved') approved++;
                else if (status === 'revision') revision++;
                else pending++;
            });
            document.getElementById('total-count').innerText = total;
            document.getElementById('approved-count').innerText = approved;
            document.getElementById('revision-count').innerText = revision;
            document.getElementById('pending-count').innerText = pending;
        }

        function setDecision(recId, decision) {
            const card = document.getElementById('card-' + recId);
            const statusLabel = document.getElementById('status-label-' + recId);
            const approveBtn = card.querySelector('.decision-btn.approve');
            const revisionBtn = card.querySelector('.decision-btn.revision');

            approveBtn.classList.remove('active');
            revisionBtn.classList.remove('active');

            if (decision === 'approved') {
                card.setAttribute('data-status', 'approved');
                approveBtn.classList.add('active');
                statusLabel.innerHTML = '<span class="stat-dot approved"></span> APPROVED';
                statusLabel.style.color = 'var(--success)';
            } else {
                card.setAttribute('data-status', 'revision');
                revisionBtn.classList.add('active');
                statusLabel.innerHTML = '<span class="stat-dot revision"></span> REVISION NEEDED';
                statusLabel.style.color = 'var(--danger)';
            }
            updateStats();
        }

        function exportData() {
            const finalLines = [];
            recordsData.forEach(rec => {
                const card = document.getElementById('card-' + rec.id);
                const status = card.getAttribute('data-status');
                const editedResponse = document.getElementById('editor-' + rec.id).value;
                const comments = document.getElementById('comments-' + rec.id).value;

                // Build a copy of record
                const finalRec = {
                    id: rec.id,
                    task_type: rec.task_type,
                    context: rec.context,
                    prompt: rec.prompt,
                    ideal_response: editedResponse,
                    notes: comments,
                    status: status === 'approved' ? 'gold' : 'candidate'
                };
                finalLines.push(JSON.stringify(finalRec));
            });

            const blob = new Blob([finalLines.join('\\n')], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'northbengal_gold_dataset.jsonl';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            alert("Dataset successfully exported! Save the file to your output directory.");
        }

        // Initialize Stats
        window.onload = function() {
            updateStats();
        }
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Validation dashboard successfully generated at: {OUTPUT_HTML_PATH}")

if __name__ == "__main__":
    main()
