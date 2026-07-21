from sentence_transformers import SentenceTransformer, util
import spacy
import re
import random
import spacy
import ast
import operator
from datetime import datetime, timedelta, date, time
from dateutil import parser as dateutil_parser
from dateutil import parser


model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_sm")


model = SentenceTransformer("all-MiniLM-L6-v2")  # small & fast


# 2. Define intents and example phrases
from intent import intents



intent_embeddings = {}
for intent, examples in intents.items():
    intent_embeddings[intent] = model.encode(examples, convert_to_tensor=True)

# 4. Function: classify intent
def classify_intent(user_input):
    user_embedding = model.encode(user_input, convert_to_tensor=True)
    best_intent = None
    best_score = -1

    for intent, examples_emb in intent_embeddings.items():
        # cosine similarity between input and each intent's examples
        similarity = util.cos_sim(user_embedding, examples_emb).max().item()
        if similarity > best_score:
            best_score = similarity
            best_intent = intent

    return best_intent,best_score


GENERIC_SONG_WORDS = {"a song", "song", "some music", "music", "a track", "track", "songs"}

_UNITS = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,
          "ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,
          "seventeen":17,"eighteen":18,"nineteen":19}
_TENS = {"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90}
_SCALES = {"hundred":100,"thousand":1000,"million":10**6}
_NUMBER_WORDS = set(list(_UNITS)+list(_TENS)+list(_SCALES)+["and"])

def text_to_int(text):
    text = text.lower().replace('-', ' ')
    parts = text.split()
    if not parts:
        return None
    total = 0
    current = 0
    seen = False
    for w in parts:
        if w == 'and':
            continue
        if w in _UNITS:
            current += _UNITS[w]; seen = True
        elif w in _TENS:
            current += _TENS[w]; seen = True
        elif w in _SCALES:
            scale = _SCALES[w]
            if current == 0:
                current = 1
            current *= scale
            total += current
            current = 0
            seen = True
        else:
            return None
    total += current
    return total if seen else None

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow
}

class SafeEval(ast.NodeVisitor):
    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        return super().visit(node)
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = type(node.op)
        if op not in _OPS:
            raise ValueError("Operator not allowed")
        return _OPS[op](left, right)
    def visit_UnaryOp(self, node):
        val = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd): return +val
        if isinstance(node.op, ast.USub): return -val
        raise ValueError("Unary operator not allowed")
    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed")
    def visit_Num(self, node):
        return node.n
    def generic_visit(self, node):
        raise ValueError(f"Disallowed node: {type(node).__name__}")

def safe_eval(expr):
    tree = ast.parse(expr, mode='eval')
    return SafeEval().visit(tree)

_OPERATOR_REPL = [
    (r'\bdivided by\b', '/'), (r'\bdivide\b','/'),
    (r'\bmultiplied by\b','*'), (r'\bmultiply\b','*'), (r'\btimes\b','*'),
    (r'\bplus\b','+'), (r'\badd\b','+'),
    (r'\bminus\b','-'), (r'\bsubtract\b','-'),
]

_TOKEN_PATTERN = re.compile(r'\d+\.\d+|\d+|[A-Za-z]+(?:-[A-Za-z]+)*|[+\-*/()^]')

def replace_number_words_with_digits(text):
    tokens = _TOKEN_PATTERN.findall(text)
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r'\d+\.\d+|\d+', t) or re.fullmatch(r'[+\-*/()^]', t):
            out.append(t); i += 1; continue
        j = i
        run = []
        while j < len(tokens):
            part = tokens[j].lower()
            pieces = part.split('-')
            if all(p in _NUMBER_WORDS for p in pieces):
                run.append(part); j += 1
            else:
                break
        if run:
            num = text_to_int(" ".join(run))
            if num is None:
                i = j; continue
            out.append(str(num))
            i = j
        else:
            i += 1
    return " ".join(out)

def normalize_input_to_expr(text):
    s = text.lower()
    for pat, repl in _OPERATOR_REPL:
        s = re.sub(pat, repl, s)
    s = s.replace(',', ' ').replace('^','**').replace('÷','/')
    s = replace_number_words_with_digits(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def calculate_expression(user_input):
    expr = normalize_input_to_expr(user_input)
    if not expr:
        raise ValueError("Could not parse expression")
    result = safe_eval(expr)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return expr, result
    return eval(compile(node, "<string>", "eval"))


def extract_parameters(user_input, intent):
    doc = nlp(user_input)
    params = {}

    if intent == "play_song":
        text = user_input.lower().strip()

        # Case 1: Song + Artist ("<song> by <artist>")
        match = re.search(r"(?:play|put on|spin|start playing|listen to)\s+(.+?)\s+by\s+(.+)",
                          text, re.IGNORECASE)
        if match:
            song = match.group(1).strip()
            artist = match.group(2).strip()

            # Normalize generic song words
            if song in GENERIC_SONG_WORDS:
                song = "any"

            params["song"] = song
            params["artist"] = artist
            return params

        # Case 2: Only Artist ("play a song by BTS")
        match = re.search(r"(?:play|put on|spin|start playing|listen to)\s+(?:.+?)\s+by\s+(.+)",
                          text, re.IGNORECASE)
        if match:
            artist = match.group(1).strip()
            params["song"] = "any"
            params["artist"] = artist
            return params

        # Case 3: Only Song ("play despacito")
        match = re.search(r"(?:play|put on|spin|start playing|listen to)\s+(.+)",
                          text, re.IGNORECASE)
        if match:
            song = match.group(1).strip()
            if song in GENERIC_SONG_WORDS:
                params["song"] = "any"
                params["artist"] = "unknown"
            else:
                params["song"] = song
                params["artist"] = "unknown"
            return params

        # Default fallback
        params["song"] = "any"
        params["artist"] = "unknown"

    elif intent == "get_weather":
    # self-contained get_weather parameter extraction (paste-replace your old block



        # try to use dateutil.parser if available (best for "5th May", "next Friday", etc.)
        try:

            HAVE_DATEUTIL = True
        except Exception:
            dateutil_parser = None
            HAVE_DATEUTIL = False

        now = datetime.now()
        location = None
        raw_date = None     # extracted date text (like "5th May", "tomorrow", etc.)
        raw_time = None     # extracted time text (like "5pm", "17:30", "evening")
        date_obj = None
        time_obj = None

        # 1) get spaCy entities if present
        for ent in doc.ents:
            if ent.label_ == "GPE" and not location:
                location = ent.text
            elif ent.label_ == "DATE" and not raw_date:
                raw_date = ent.text.strip()
            elif ent.label_ == "TIME" and not raw_time:
                raw_time = ent.text.strip()

        # 2) fallback regex for location ("in Paris", "at London")
        if not location:
            m_loc = re.search(r"(?:in|at)\s+([A-Za-z][A-Za-z\s\.\-]+)", user_input, re.IGNORECASE)
            if m_loc:
                location = m_loc.group(1).strip()
        if not location:
            location = "Eluru"

        # 3) fallback regex for explicit date: "on 5th May", "for tomorrow" (stop before "at")
        if not raw_date:
            m_date = re.search(r"\b(?:on|for)\s+(.+?)(?:\s+at\s+|$)", user_input, re.IGNORECASE)
            if m_date:
                raw_date = m_date.group(1).strip()

        # 4) fallback regex for time: "at 5pm", "at 17:30", and some keywords
        if not raw_time:
            m_time = re.search(
                r"\bat\s+((?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?)|noon|midnight|morning|afternoon|evening|night|tonight)",
                user_input, re.IGNORECASE
            )
            if m_time:
                raw_time = m_time.group(1).strip()

        # helper: parse weekday/relative words (today/tomorrow/day after tomorrow)
        def parse_relative_date(text):
            t = text.strip().lower()
            if t in ("today",):
                return now.date()
            if t in ("tomorrow",):
                return (now + timedelta(days=1)).date()
            if "day after tomorrow" in t or "day-after-tomorrow" in t:
                return (now + timedelta(days=2)).date()
            # weekday names (next monday, monday, next friday, this tuesday)
            weekdays = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
            for name, idx in weekdays.items():
                if name in t:
                    # find next occurrence of that weekday
                    days_ahead = (idx - now.weekday() + 7) % 7
                    # if user says "next", prefer next week even if same day
                    if "next" in t:
                        days_ahead = days_ahead or 7
                        if days_ahead == 0:
                            days_ahead = 7
                    # if user just says "monday" and it's today, assume next occurrence (common in scheduling)
                    if days_ahead == 0:
                        days_ahead = 7
                    return (now + timedelta(days=days_ahead)).date()
            return None

        # helper: manual parse for numeric day+month patterns (e.g. "5th May", "May 5")
        def parse_day_month(text):
            t = text.strip()
            m1 = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)", t, re.IGNORECASE)  # "5th May"
            m2 = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?", t, re.IGNORECASE)  # "May 5"
            month_map = {
                "jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,
                "may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"september":9,
                "oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12
            }
            try:
                if m1:
                    day = int(m1.group(1))
                    mo = m1.group(2).lower()
                    month = month_map.get(mo[:3], None) or month_map.get(mo, None)
                    if month:
                        # choose year: if date passed, and no year in text, choose next year
                        year = now.year
                        cand = datetime(year, month, day).date()
                        if cand < now.date():
                            year += 1
                        return datetime(year, month, day).date()
                if m2:
                    mo = m2.group(1).lower()
                    day = int(m2.group(2))
                    month = month_map.get(mo[:3], None) or month_map.get(mo, None)
                    if month:
                        year = now.year
                        cand = datetime(year, month, day).date()
                        if cand < now.date():
                            year += 1
                        return datetime(year, month, day).date()
            except Exception:
                return None
            return None

        # parse date text into a date object
        def parse_date_text(text):
            if not text:
                return None
            text_str = text.strip()
            # relative/weekday shortcuts
            rel = parse_relative_date(text_str)
            if rel:
                return rel
            # try dateutil if available
            if HAVE_DATEUTIL:
                try:
                    # default to now so parser can fill missing parts
                    dt = dateutil_parser.parse(text_str, fuzzy=True, default=now)
                    res_date = dt.date()
                    # if parsed date already passed and no explicit year in text -> assume next year
                    if res_date < now.date() and not re.search(r"\d{4}", text_str):
                        res_date = res_date.replace(year=now.year + 1)
                    return res_date
                except Exception:
                    pass
            # fallback manual day+month parser
            dm = parse_day_month(text_str)
            if dm:
                return dm
            # as last fallback, check for explicit words
            if re.search(r"\btoday\b", text_str, re.IGNORECASE):
                return now.date()
            if re.search(r"\btomorrow\b", text_str, re.IGNORECASE):
                return (now + timedelta(days=1)).date()
            return None

        # helper: parse time text into a time object
        def parse_time_text(text):
            if not text:
                return None
            t = text.strip().lower()
            if t in ("noon",):
                return datetime(now.year, now.month, now.day, 12, 0, 0).time()
            if t in ("midnight",):
                return datetime(now.year, now.month, now.day, 0, 0, 0).time()
            if "morning" in t:
                return datetime(now.year, now.month, now.day, 9, 0, 0).time()
            if "afternoon" in t:
                return datetime(now.year, now.month, now.day, 15, 0, 0).time()
            if "evening" in t:
                return datetime(now.year, now.month, now.day, 19, 0, 0).time()
            if "night" in t or "tonight" in t:
                return datetime(now.year, now.month, now.day, 21, 0, 0).time()
            # try dateutil if available
            if HAVE_DATEUTIL:
                try:
                    dt = dateutil_parser.parse(t, fuzzy=True, default=now)
                    return dt.time()
                except Exception:
                    pass
            # regex: "5pm", "5 pm", "17:30", "5:30am"
            m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
            if m:
                hh = int(m.group(1))
                mm = int(m.group(2)) if m.group(2) else 0
                ampm = m.group(3)
                if ampm:
                    ampm = ampm.lower()
                    if ampm == "pm" and hh != 12:
                        hh += 12
                    if ampm == "am" and hh == 12:
                        hh = 0
                # guard for 24-hour numbers >23
                hh = hh % 24
                return datetime(now.year, now.month, now.day, hh, mm, 0).time()
            return None

        # actually parse raw_date/raw_time
        if raw_date:
            date_obj = parse_date_text(raw_date)
        if raw_time:
            time_obj = parse_time_text(raw_time)

        # Defaults as you requested:
        # - if date provided, use it; else use current date
        # - if time provided, use it; else use current time
        if not date_obj:
            date_obj = now.date()
        if not time_obj:
            time_obj = now.time().replace(microsecond=0)

        # Save results into params (safe formatting)
        params["location"] = location
        try:
            params["date"] = date_obj.strftime("%Y-%m-%d")
        except Exception:
            params["date"] = str(date_obj)
        try:
            params["time"] = time_obj.strftime("%H:%M:%S")
        except Exception:
            params["time"] = str(time_obj)


    elif intent == "tell_joke":

        jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the math book look sad? Because it had too many problems.",
    "Why was the computer cold? It left its Windows open!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't programmers like nature? It has too many bugs.",
    "Why did the coffee file a police report? It got mugged.",
    "Why did the bicycle fall over? Because it was two-tired!",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
    "Why do cows wear bells? Because their horns don't work.",
    "Why was the math lecture so long? The professor kept going off on tangents.",
    "Why did the cookie go to the doctor? Because it felt crummy.",
    "Why did the computer go to therapy? It had too many bytes of emotional baggage.",
    "Why did the music teacher go to jail? Because she got caught with too many sharp objects.",
    "Why don't skeletons fight each other? They don't have the guts."
]

        params["joke"] = random.choice(jokes)

    elif intent == "club_info":
        #   clubs = {
        #       "robotics": "The Robotics Club meets every Wednesday at 5 PM in Lab 3.",
        #       "coding": "The Coding Club focuses on Python and AI. Meetings are on Fridays at 4 PM.",
        #       "drama": "The Drama Club prepares stage performances and meets on Tuesdays at 6 PM."
        #   }

        #   # Try to extract club name
        #   found_club = None
        #   for club in clubs:
        #       if club in user_input.lower():
        #           found_club = club
        #           break

        #   if found_club:
        #       params["club_name"] = found_club
        #       params["info"] = clubs[found_club]
        #   else:
        #       params["error"] = "Could not find club information."
        pass
    elif intent == "add_event":
        now = datetime.now()
        date_val, time_val, event_name = None, None, None

        # 1. Regex for explicit date (on/for <date>)
        m_date = re.search(r"\b(?:on|for)\s+([A-Za-z0-9\s\-]+)", user_input, re.IGNORECASE)
        if m_date:
            raw_date = m_date.group(1).strip().lower()

        # Handle natural language dates
            if raw_date in ["today"]:
                date_val = now.date()
            elif raw_date in ["tomorrow"]:
                date_val = (now + timedelta(days=1)).date()
            elif raw_date in ["day after tomorrow"]:
                date_val = (now + timedelta(days=2)).date()
            else:
                try:
                    parsed_date = parser.parse(raw_date, fuzzy=True, dayfirst=True)
                    if parsed_date.date() < now.date() and not re.search(r"\d{4}", raw_date):
                        parsed_date = parsed_date.replace(year=now.year + 1)
                    date_val = parsed_date.date()
                except:
                    date_val = now.date()

        # 2. Regex for explicit time (at <time>)
        m_time = re.search(r"\bat\s+([0-9]{1,2}(?::[0-9]{2})?\s*(am|pm)?)", user_input, re.IGNORECASE)
        if m_time:
            raw_time = m_time.group(1).strip()
            try:
                time_val = parser.parse(raw_time, fuzzy=True).time()
            except:
                time_val = None

        # 3. Apply defaults
        if date_val and not time_val:
            # If only date is given → default morning 08:00
            time_val = datetime(now.year, now.month, now.day, 8, 0, 0).time()
        elif not date_val and not time_val:
            # If nothing given → default today 20:00
            date_val = now.date()
            time_val = datetime(now.year, now.month, now.day, 20, 0, 0).time()
        elif not date_val and time_val:
            # If only time is given → default today
            date_val = now.date()

        # 4. Event name = input minus detected parts
        event_name = user_input
        if m_date:
            event_name = event_name.replace(m_date.group(0), "")
        if m_time:
            event_name = event_name.replace(m_time.group(0), "")
        event_name = event_name.strip()

        # 5. Save results
        params["event"] = event_name if event_name else "Unnamed Event"
        params["date"] = date_val.strftime("%Y-%m-%d")
        params["time"] = time_val.strftime("%H:%M:%S")

    elif intent == "general_question":
        params["answer"] = "I'm not sure about that. I can help with weather, math, jokes, or club information. Could you rephrase?"

    elif intent == "calculate":
        try:
            expr, result = calculate_expression(user_input)
            print(f"Expression: {expr}, Result: {result}")
            params["expression"] = expr
            params["result"] = result
            params["response"] = f"The answer is {result}."
        except Exception as e:
            print("Error:", e)
            params["error"] = "Sorry, I couldn't understand the calculation."

    return params