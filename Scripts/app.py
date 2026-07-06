import sys
import io
# Force UTF-8 output on Windows to avoid encoding errors
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from flask import Flask, request, jsonify, render_template
import os
import json
import threading
import re
import random

try:
    import requests
except ImportError:
    requests = None

import urllib.request
import urllib.error

# ─── Load .env file automatically ─────────────────────────────────────────────
def _load_dotenv():
    """Load .env file from script directory or parent directory."""
    search_dirs = [
        Path(__file__).parent,
        Path(__file__).parent.parent,
    ]
    for d in search_dirs:
        env_file = d / '.env'
        if env_file.exists():
            print(f'[ENV] Loading .env from: {env_file}')
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, val = line.partition('=')
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key and not os.getenv(key):  # Don't override existing env vars
                            os.environ[key] = val
            return True
    return False

_load_dotenv()

# Import ML libraries lazily
faiss = None
SentenceTransformer = None
np = None

app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variables
notices = []
model = None
index = None
loading_complete = False

# ─── Small Talk ────────────────────────────────────────────────────────────────

SMALL_TALK_PATTERNS = {
    'greetings': ['hello', 'hi', 'hey', 'hiya', 'hii', 'good morning', 'good afternoon', 'good evening', 'sup'],
    'status':    ['how are you', 'how are u', "what's up", 'whats up', 'how are things', 'how is it going'],
    'thanks':    ['thank you', 'thanks', 'thx', 'thankyou', 'thank u', 'ty'],
    'farewell':  ['bye', 'goodbye', 'see you', 'see ya', 'talk later', 'later'],
    'identity':  ['who are you', 'what are you', 'what can you do', 'are you a bot', 'are you human', 'your name'],
}

SMALL_TALK_RESPONSES = {
    'greeting': [
        "👋 Hi there! I'm your DBGI College Assistant. Ask me anything about placements, exams, notices, admissions, or campus events!",
        "Hello! Great to see you here. I can help you with college notices, exam schedules, placement drives, and more. What would you like to know?",
        "Hey! I'm your AI-powered college assistant. Feel free to ask me about AKTU, BTEUP, MSU exams, placements, or any college notice! 🎓",
    ],
    'status': [
        "I'm doing great, thanks for asking! 😊 Ready to help you with any college-related questions. What do you need?",
        "All systems go! 🚀 I'm here and ready to assist. Ask me about exams, placements, admissions, or college notices.",
    ],
    'thanks': [
        "You're welcome! 😊 Feel free to ask anything else about college notices, exams, or placements.",
        "Happy to help! 🎉 Let me know if you have more questions about DBGI or any college-related topics.",
    ],
    'farewell': [
        "Goodbye! 👋 Come back anytime you need help with college information.",
        "See you soon! Take care. I'll be here whenever you need college assistance. 🎓",
    ],
    'identity': [
        "I'm the DBGI College Assistant — an AI chatbot built to help students with college notices, placement drives, exam schedules (AKTU/BTEUP/MSU), admissions, and campus events. Just ask me anything! 🤖",
        "I'm your AI-powered assistant for DBGI Saharanpur. I know about placements, exams, notices, admissions, and campus life. What can I help you with today?",
    ],
}

WEBSITE_QUERY_KEYWORDS = [
    'official website',
    'official site',
    'website link',
    'website of',
    'site of',
    'website for',
    'link for',
    'url for',
]

WEBSITE_LINKS = [
    {
        'name': 'DBGI official website',
        'url': 'https://dbgisre.edu.in',
        'aliases': ['dbgi', 'dev bhoomi', 'dbgi site', 'dbgi website', 'dbgi homepage'],
    },
    {
        'name': 'DBGI notice board',
        'url': 'https://dbgisre.edu.in/category/notice-board/',
        'aliases': ['notice board', 'notice-board', 'noticeboard', 'dbgi notice board', 'dbgi notices', 'notices'],
    },
    {
        'name': 'DBGI placements page',
        'url': 'https://dbgisre.edu.in/category/placements/',
        'aliases': ['placement', 'placements', 'placement drive', 'campus drive', 'job fair', 'job drive', 'placement page'],
    },
    {
        'name': 'DBGI AKTU page',
        'url': 'https://dbgisre.edu.in/category/aktu/',
        'aliases': ['aktu', 'aktu site', 'aktu website', 'aktu page', 'aktu section'],
    },
    {
        'name': 'DBGI BTEUP page',
        'url': 'https://dbgisre.edu.in/category/bteup/',
        'aliases': ['bteup', 'bteup site', 'bteup website', 'bteup page', 'bteup section'],
    },
    {
        'name': 'DBGI MSU page',
        'url': 'https://dbgisre.edu.in/category/msu/',
        'aliases': ['msu', 'msu site', 'msu website', 'msu page', 'msu section'],
    },
    {
        'name': 'DBGI news page',
        'url': 'https://dbgisre.edu.in/category/news/',
        'aliases': ['news', 'dbgi news', 'news page'],
    },
]


def find_official_websites(message: str) -> list:
    """Return official website links for known DBGI pages mentioned in the message."""
    text = message.strip().lower()
    
    # Only trigger if the user explicitly asks for a link, URL, site, or website
    has_website_intent = any(keyword in text for keyword in WEBSITE_QUERY_KEYWORDS) or any(kw in text for kw in ['website', 'link', 'url', 'site', 'page', 'portal'])
    
    if not has_website_intent:
        return []

    matches = []
    seen_urls = set()

    for site in WEBSITE_LINKS:
        for alias in site['aliases']:
            if alias in text:
                if site['url'] not in seen_urls:
                    matches.append(site)
                    seen_urls.add(site['url'])
                break

    if matches:
        return matches

    return [
        WEBSITE_LINKS[0],  # DBGI official website
        WEBSITE_LINKS[3],  # DBGI AKTU page
        WEBSITE_LINKS[4],  # DBGI BTEUP page
        WEBSITE_LINKS[5],  # DBGI MSU page
        WEBSITE_LINKS[1],  # DBGI notice board
    ]


def website_link_response(sites: list) -> str:
    lines = ['Here are the official links you asked for:']
    for site in sites:
        lines.append(f"- [{site['name']}]({site['url']})")
    lines.append('Click any link above to visit the site directly.')
    return '\n'.join(lines)


def is_small_talk(message: str) -> bool:
    text = message.strip().lower()
    if not text or len(text) > 100:
        return False
    for phrases in SMALL_TALK_PATTERNS.values():
        for phrase in phrases:
            if phrase in text:
                return True
    return False

def generate_small_talk_response(message: str) -> str:
    text = message.strip().lower()
    for phrase in SMALL_TALK_PATTERNS['greetings']:
        if phrase in text:
            return random.choice(SMALL_TALK_RESPONSES['greeting'])
    for phrase in SMALL_TALK_PATTERNS['status']:
        if phrase in text:
            return random.choice(SMALL_TALK_RESPONSES['status'])
    for phrase in SMALL_TALK_PATTERNS['thanks']:
        if phrase in text:
            return random.choice(SMALL_TALK_RESPONSES['thanks'])
    for phrase in SMALL_TALK_PATTERNS['farewell']:
        if phrase in text:
            return random.choice(SMALL_TALK_RESPONSES['farewell'])
    for phrase in SMALL_TALK_PATTERNS['identity']:
        if phrase in text:
            return random.choice(SMALL_TALK_RESPONSES['identity'])
    return "I'm here to help with your college-related questions! Ask me about placements, exams, notices, or admissions. 🎓"


# ─── Gemini API ────────────────────────────────────────────────────────────────

def get_gemini_api_key() -> str:
    """Try multiple env var names for the Gemini API key."""
    for key_name in ['GEMINI_API_KEY', 'GOOGLE_AI_STUDIO_API_KEY', 'AI_STUDIO_API_KEY', 'GOOGLE_API_KEY']:
        val = os.getenv(key_name, '')
        if val and len(val) > 10:
            return val
    return ''


def call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini 1.5 Flash via REST API."""
    # Try gemini-1.5-flash first, fallback to gemini-pro
    # Use v1 API with the correct available models
    models_to_try = [
        'gemini-3.5-flash',
        'gemini-3.1-flash-lite',
        'gemini-2.5-flash-lite',
        'gemini-2.0-flash-lite'
    ]
    
    for model_name in models_to_try:
        try:
            url = f'https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}'
            payload = {
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'temperature': 0.7,
                    'maxOutputTokens': 600,
                    'topK': 40,
                    'topP': 0.95,
                }
            }
            if requests is not None:
                resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=25)
                resp.raise_for_status()
                result = resp.json()
            else:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    body = resp.read().decode('utf-8')
                    result = json.loads(body)
            
            candidates = result.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', '').strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
            print(f"Gemini HTTP error ({model_name}): {e.code} - {err_body[:200]}")
            if e.code == 404:
                continue  # Try next model
            raise
        except Exception as e:
            print(f"Gemini error ({model_name}): {e}")
            if model_name == models_to_try[-1]:
                raise
            continue
    
    return ''



def generate_gemini_response(message: str, context: str) -> str:
    """Generate a response using Gemini with college context."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError('No Gemini API key configured')

    system_instructions = (
        "You are a friendly, professional, and helpful AI college assistant for DBGI (Dev Bhoomi Group of Institutions) Saharanpur. "
        "Your goal is to help students by providing clear, detailed, conversational, and elaborative answers so that they fully understand "
        "the information they need. Use all relevant details from the provided context (dates, links, instructions, contact details, branch/course eligibility).\n\n"
        "YOUR PERSONALITY:\n"
        "- Friendly, helpful, conversational, supportive, and highly informative.\n"
        "- Thorough, structured, and easy to talk to, making sure answers are engaging and clear.\n\n"
        "HOW TO ANSWER EVERY TYPE OF QUESTION:\n"
        "1. COLLEGE questions (exams, syllabus, placements, notices, admissions, AKTU/BTEUP/MSU): Use the college data context if available. "
        "Provide comprehensive, detailed, and structured explanations. Include key dates, eligibility, registration/official links, and any step-by-step instructions from the notice. "
        "Use bullet points and bold headers for clarity so it is easy for students to read. Keep the output detailed, not truncated.\n"
        "   - CRITICAL RULE FOR LINKS & OVERVIEW: You must ALWAYS include the official markdown link (e.g. `[View Official Notice Here](URL)`) when referencing any notice or event. "
        "If the notice details/content in the context is very brief, empty, or simply repeats the title, DO NOT just output the title. Instead, write a helpful description/overview explaining what the notice is about (e.g. an exam schedule update, sessional date sheet, or job placement drive) and provide the markdown link so they can click and read it.\n"
        "   - EXPERT FALLBACK RULE: If the college context is empty, unrelated, or does not contain the answer to the student's question (for example, asking for a syllabus, study topics, exam patterns, or admission criteria that aren't in the notices), DO NOT say 'I do not have that detail' or give a short/empty reply. Instead, answer the question like an expert using your general knowledge. For example, explain the typical syllabus subjects, general exam rules, or standard academic requirements, and guide them on how to find the exact details on the university/college website.\n"
        "2. CASUAL / GENERAL QUESTIONS: Answer naturally, warmly, and politely (just like ChatGPT or Gemini would). Explain concepts thoroughly with structured points.\n"
        "3. CAREER / JOB HELP: Give actionable advice, insights, and practical next steps.\n"
        "4. GENERAL KNOWLEDGE questions: Answer confidently, thoroughly, and directly.\n"
        "5. MOTIVATIONAL / EMOTIONAL support: Be supportive, encouraging, and empathetic.\n\n"
        "STRICT RULES:\n"
        "- Be natural and conversational. Feel free to use polite opening/closing phrases if they make the interaction friendlier (e.g. 'I can help you with that!', 'Here is the detailed information:').\n"
        "- Use relevant emojis naturally to make the response visually friendly and engaging (e.g. 📅, 📝, 💼, 🎓, 📌, 🚀, 👍).\n"
        "- Do not truncate or leave out important information from the context. If a notice has links, eligibility criteria, or specific instructions, explain them fully.\n"
        "- If a highly specific local detail (like a personal student score or private event) is missing from the context, clearly explain what the general procedure is, and provide helpful advice along with a link to the official DBGI portal.\n\n"
        "RESPONSE FORMAT:\n"
        "- Use rich markdown formatting (bolding, lists, headers, bullet points) to make information highly readable and easy to scan.\n"
        "- Always output URLs using standard markdown link syntax like `[Link Text](URL)`. This is essential so the frontend can display clickable links.\n"
        "- Provide a complete, fully detailed, and elaborative answer. Do not limit the length of your response artificially.\n"
        "- Answer like a friendly, polished, and intelligent AI assistant in one clear, helpful response.\n\n"
    )

    if context:
        full_prompt = (
            system_instructions
            + "COLLEGE DATA CONTEXT (only use if relevant to the question below — ignore if unrelated):\n"
            + context
            + "\n\nStudent's message: "
            + message
            + "\n\nYour response (if the context above is unrelated to the question, just answer from your general knowledge — don't mention the context):"
        )
    else:
        full_prompt = (
            system_instructions
            + "Student's message: "
            + message
            + "\n\nYour response:"
        )

    return call_gemini(full_prompt, api_key)



# ─── Data Loading ──────────────────────────────────────────────────────────────

def load_data():
    global notices, model, index, loading_complete

    try:
        dataset_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'notice_dataset.json')
        print(f'[LOAD] Loading dataset from: {dataset_path}')

        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        notices = data
        print(f'[OK] Loaded {len(notices)} notices')

        if not notices:
            print('[WARN] Notice dataset is empty!')
            loading_complete = True
            return False

        # Try loading ML models
        if os.getenv('LOW_MEMORY', '').lower() == 'true':
            print('[INFO] LOW_MEMORY mode is active. Skipping ML model loading.')
            model = None
            index = None
        else:
            try:
                import faiss as faiss_module
                import numpy as np_module
                from sentence_transformers import SentenceTransformer as ST

                print('[LOAD] Loading sentence transformer model...')
                model = ST('all-MiniLM-L6-v2')
                print('[OK] Loaded sentence transformer model')

                vector_db_path = os.path.join(os.path.dirname(__file__), '..', 'vector_db')
                index_path = os.path.join(vector_db_path, 'notice_index.faiss')

                if os.path.exists(index_path):
                    index = faiss_module.read_index(index_path)
                    print('[OK] Loaded FAISS index successfully')
                else:
                    print('[LOAD] Creating FAISS index from scratch...')
                    texts = [f"{n.get('title','')} {n.get('category','')} {n.get('content','')}" for n in notices]
                    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
                    embeddings = np_module.array(embeddings).astype('float32')
                    dimension = embeddings.shape[1]
                    index = faiss_module.IndexFlatL2(dimension)
                    index.add(embeddings)
                    os.makedirs(vector_db_path, exist_ok=True)
                    faiss_module.write_index(index, index_path)
                    print(f'[OK] Created and saved FAISS index with {len(notices)} items')

            except Exception as e:
                print(f'[WARN] Could not load ML models: {e}')
                print('  App will use keyword search')
                model = None
                index = None

        loading_complete = True
        print('[OK] College assistant fully loaded and ready!')
        return True

    except Exception as e:
        print(f'[ERROR] Error in load_data: {e}')
        import traceback
        traceback.print_exc()
        loading_complete = True
        return False


print('Initializing college assistant...')
init_thread = threading.Thread(target=load_data, daemon=True)
init_thread.start()
print('College assistant initializing in background...')


# ─── Search ────────────────────────────────────────────────────────────────────

def search_relevant_notices(query: str, top_k: int = 6) -> list:
    global model, index, notices

    if model is not None and index is not None:
        try:
            query_vector = model.encode([query])
            D, I = index.search(query_vector, min(top_k, len(notices)))
            results = []
            for idx in I[0]:
                if 0 <= idx < len(notices):
                    n = notices[idx]
                    results.append({
                        'title':    n.get('title', ''),
                        'date':     n.get('date', ''),
                        'category': n.get('category', ''),
                        'content':  n.get('content', ''),
                        'source':   n.get('source_file', ''),
                    })
            return results
        except Exception as e:
            print(f'Vector search error: {e}, falling back to keyword search')

    return basic_search(query, top_k)


def basic_search(query: str, top_k: int = 6) -> list:
    if not notices:
        return []

    query_lower = query.lower()
    query_words = [w for w in re.split(r'\W+', query_lower) if len(w) > 1]

    if not query_words:
        return notices[:top_k]

    # Generate search terms including singular forms for plurals to prevent mismatch (e.g., 'fees' matching 'fee')
    search_words = set(query_words)
    for word in query_words:
        if word.endswith('s') and len(word) > 3:
            search_words.add(word[:-1])
        if word.endswith('es') and len(word) > 4:
            search_words.add(word[:-2])

    scored = []
    for notice in notices:
        title   = notice.get('title', '').lower()
        content = notice.get('content', '').lower()
        category = notice.get('category', '').lower()
        score = 0

        # Exact substring checks for full query
        if query_lower in title:
            score += 25
        if query_lower in content:
            score += 15

        # Individual word matches (using search_words with singular stem fallback)
        for word in search_words:
            if word in title:
                score += 5
            if word in content:
                score += 3
            if word in category:
                score += 2
            for tw in title.split():
                if len(word) > 2 and len(tw) > 3 and word in tw:
                    score += 1

        if score > 0:
            scored.append((score, notice))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            'title':    n.get('title', ''),
            'date':     n.get('date', ''),
            'category': n.get('category', ''),
            'content':  n.get('content', ''),
            'source':   n.get('source_file', ''),
        }
        for _, n in scored[:top_k]
    ]


def build_context(notices_data: list) -> str:
    if not notices_data:
        return ''
    ctx = 'Relevant college notices and information:\n\n'
    for i, n in enumerate(notices_data, 1):
        ctx += f'{i}. {n["title"]}\n'
        if n.get('date'):
            ctx += f'   Date: {n["date"]}\n'
        if n.get('category'):
            ctx += f'   Category: {n["category"]}\n'
        if n.get('content'):
            ctx += f'   Details: {n["content"]}\n'
        if n.get('url'):
            ctx += f'   Official URL/Link: {n["url"]}\n'
        ctx += '\n'
    return ctx


# ─── Main Chat Logic ───────────────────────────────────────────────────────────

def chat_response(message: str) -> str:
    global loading_complete, model, index, notices

    message = message.strip()
    if not message:
        return "Please type a question and I'll help you! 😊"

    # Handle basic small talk quickly (greetings, bye, etc.)
    if is_small_talk(message):
        return generate_small_talk_response(message)

    # Handle official website requests with clickable links
    websites = find_official_websites(message)
    if websites:
        return website_link_response(websites)

    print(f'[QUERY] {message}')

    # Try Gemini AI for EVERYTHING — casual, college, general, career, emotional
    api_key = get_gemini_api_key()
    if api_key:
        try:
            # Build college context only if data is loaded (don't block if still loading)
            context = ''
            if notices:
                relevant = search_relevant_notices(message, top_k=6)
                context = build_context(relevant)

            response = generate_gemini_response(message, context)
            if response:
                return response
        except Exception as e:
            print(f'Gemini API error: {e}')
            # Fall through to local response

    # Local fallback (when no API key)
    if not notices:
        return 'College database is still loading... Please wait a moment and try again.'

    relevant = search_relevant_notices(message, top_k=6)
    return generate_local_response(message, relevant)



def generate_local_response(message: str, relevant_notices: list) -> str:
    """Generate a structured local response when no API is available."""
    if not relevant_notices:
        return (
            "I couldn't find specific information about that in my database. "
            "Try asking about: **placements**, **AKTU exams**, **BTEUP notices**, "
            "**MSU results**, **admissions**, or **campus events**."
        )

    msg_lower = message.lower()

    def format_notices(notices_list, label):
        resp = f'Here are {label} I found:\n\n'
        for n in notices_list[:4]:
            resp += f'📌 **{n["title"]}**\n'
            if n.get('date'):
                resp += f'   📅 **Date**: {n["date"]}'
            if n.get('category'):
                resp += f' | 🏷️ **Category**: {n["category"]}'
            resp += '\n'
            if n.get('content'):
                resp += f'   📝 **Details**: {n["content"]}\n'
            if n.get('url'):
                resp += f'   🔗 **Link**: [{n["title"]}]({n["url"]})\n'
            resp += '\n'
        return resp.strip()

    # Placement queries
    if any(w in msg_lower for w in ['placement', 'job', 'hiring', 'recruit', 'company', 'interview', 'campus drive']):
        items = [n for n in relevant_notices if 'placement' in (n.get('category','') + n.get('title','')).lower() or 'job' in n.get('title','').lower()]
        if items:
            return format_notices(items, 'placement-related notices')

    # Exam/result queries
    if any(w in msg_lower for w in ['exam', 'schedule', 'result', 'admit card', 'test', 'date sheet', 'time table', 'aktu', 'bteup', 'msu']):
        items = [n for n in relevant_notices if any(w in (n.get('title','') + n.get('category','')).lower()
                 for w in ['exam', 'schedule', 'result', 'admit', 'aktu', 'bteup', 'msu'])]
        if items:
            return format_notices(items, 'exam-related notices')

    # Admission queries
    if any(w in msg_lower for w in ['admission', 'enroll', 'apply', 'form', 'registration']):
        items = [n for n in relevant_notices if 'admission' in (n.get('title','') + n.get('category','')).lower()]
        if items:
            return format_notices(items, 'admission-related notices')

    # Generic — show top results
    resp = 'Based on college records, here\'s what I found:\n\n'
    for n in relevant_notices[:4]:
        resp += f'📌 **{n["title"]}**\n'
        if n.get('date'):
            resp += f'   📅 **Date**: {n["date"]}'
        if n.get('category'):
            resp += f' | 🏷️ **Category**: {n["category"]}'
        resp += '\n'
        if n.get('content'):
            resp += f'   📝 **Details**: {n["content"]}\n'
        if n.get('url'):
            resp += f'   🔗 **Link**: [{n["title"]}]({n["url"]})\n'
        resp += '\n'
    resp += '\nNeed more details? Try rephrasing your question with specific keywords.'
    return resp.strip()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'reply': 'Please send a message.'})
    reply = chat_response(msg)
    return jsonify({'reply': reply})


@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'loading_complete': loading_complete,
        'notices_loaded': len(notices),
        'ml_model_loaded': model is not None,
        'faiss_index_loaded': index is not None,
        'gemini_configured': bool(get_gemini_api_key()),
    })


from datetime import datetime

def parse_notice_date(date_str):
    if not date_str:
        return datetime.min
    try:
        # e.g., "July 8, 2025" or "June 30, 2026"
        return datetime.strptime(date_str.strip(), "%B %d, %Y")
    except Exception:
        pass
    try:
        # e.g., "June 2026"
        return datetime.strptime(date_str.strip(), "%B %Y")
    except Exception:
        pass
    return datetime.min

@app.route('/api/notices/latest', methods=['GET'])
def get_latest_notices():
    # Sort notices in descending chronological order
    sorted_notices = sorted(
        notices,
        key=lambda x: parse_notice_date(x.get('date', '')),
        reverse=True
    )
    
    seen_titles = set()
    latest_four = []
    for item in sorted_notices:
        title = item.get('title', '').strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        latest_four.append({
            'title': title,
            'category': item.get('category', 'Notice Board'),
            'date': item.get('date', 'Recent'),
            'url': item.get('url', '')
        })
        if len(latest_four) >= 4:
            break
            
    return jsonify(latest_four)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
