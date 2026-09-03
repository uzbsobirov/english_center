import re

def parse_test_questions(text: str):
    # Normalize characters
    text = text.replace('\xa0', ' ').replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('“', '"').replace('”', '"').replace('’', "'")
    
    # 1. Clean headers and footers
    text = re.sub(r'(?i)page\s+\d+\s*(?:of\s*\d+)?', '', text)
    text = re.sub(r'(?i)cambridge\s+(?:english|university\s+press)[\w\s\d]*', '', text)
    
    # 2. Extract and Strip Answer Keys section
    answer_keys = {}
    key_pattern = r'(?i)(?:\n|^)(?:answers?|answer\s*key|keys?|correct\s*answers?|javoblar)[\s\:\-]+(.*?)(?:\Z)'
    key_match = re.search(key_pattern, text, re.DOTALL)
    if key_match:
        key_text = key_match.group(1)
        # Match '1. A' or '1-A' or '1 A' or '1: True' or '1. London'
        pairs = re.findall(r'(\d+)[\.\s\:\-\)]+([A-Za-z0-9_\-\s\']+?)(?=(?:,\s*\d+[\.\-\s\:\)]|\s+\d+[\.\-\s\:\)]|\n|$))', key_text)
        for q_num, ans in pairs:
            clean_ans = ans.strip()
            if clean_ans and len(clean_ans) < 50:
                answer_keys[int(q_num)] = clean_ans
        # Cut off the answer key section from body text
        text = text[:key_match.start()]
                
    # 3. Split questions by number (e.g. "1.", "1)", "Q1.", "Question 1:", "1  ")
    q_blocks = re.split(r'(?:\n|^)(?:Question\s*|Q\s*)?(\d+)[\.\)\:\-\s]\s+', text)
    
    questions = []
    if len(q_blocks) > 1:
        # q_blocks has [preamble, num1, content1, num2, content2, ...]
        for i in range(1, len(q_blocks), 2):
            q_num = int(q_blocks[i])
            content = q_blocks[i+1].strip()
            if not content:
                continue
                
            # Check for options A, B, C, D
            opt_matches = list(re.finditer(r'(?:^|\s{2,}|\n)(?:\(([A-Ea-e])\)|\[([A-Ea-e])\]|([A-Ea-e])[\.\)\:\-\s])\s*([^\n\r]+?)(?=(?:\s{2,}(?:\([A-Ea-e]\)|\[[A-Ea-e]\]|[A-Ea-e][\.\)\:\-\s])|\n(?:\([A-Ea-e]\)|\[[A-Ea-e]\]|[A-Ea-e][\.\)\:\-\s])|\Z))', content))
            
            if opt_matches and len(opt_matches) >= 2:
                first_opt_start = opt_matches[0].start()
                q_text = content[:first_opt_start].strip() if first_opt_start > 0 else content.split('\n')[0].strip()
                options = []
                for m in opt_matches:
                    letter = (m.group(1) or m.group(2) or m.group(3)).upper()
                    opt_val = m.group(4).strip()
                    options.append(f"{letter}) {opt_val}")
                    
                correct = answer_keys.get(q_num)
                correct_ans = None
                if correct:
                    for opt in options:
                        if opt.upper().startswith(f"{correct.upper()})") or correct.upper() == opt.upper():
                            correct_ans = opt
                            break
                if not correct_ans:
                    correct_ans = options[0]
                    
                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "mcq",
                    "text": q_text or f"Question {q_num}",
                    "options": options,
                    "correct_answer": correct_ans,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": len(options) < 3,
                })
            elif re.search(r'(?i)\b(true\s*/\s*false|true\s+or\s+false|t\s*/\s*f|not\s+given)\b', content):
                q_text = re.sub(r'(?i)[\(\[]?(?:true\s*/\s*false|true\s+or\s+false|t/f|not\s+given)[\)\]]?', '', content).strip()
                correct_val = answer_keys.get(q_num, "True")
                if correct_val.lower() in ("true", "t", "1"):
                    correct_val = "True"
                elif correct_val.lower() in ("false", "f", "0"):
                    correct_val = "False"
                else:
                    correct_val = "True"
                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "true_false",
                    "text": q_text or f"Question {q_num}",
                    "options": ["True", "False"],
                    "correct_answer": correct_val,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(answer_keys.get(q_num)),
                })
            elif "___" in content or "...." in content or "fill in" in content.lower():
                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "fill_blank",
                    "text": content,
                    "options": [],
                    "correct_answer": answer_keys.get(q_num, ""),
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(answer_keys.get(q_num)),
                })
            else:
                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "short_answer",
                    "text": content,
                    "options": [],
                    "correct_answer": answer_keys.get(q_num, ""),
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(answer_keys.get(q_num)),
                })
                
    return questions

sample = """
1. What is the main cause of global warming?
A) Carbon emissions   B) Solar flares   C) Ocean currents   D) Tree planting

2. The Great Wall of China is visible from the Moon. (True/False)

3. Water freezes at _____ degrees Celsius.

4. What is the synonym of the word 'rapid'?

Answers:
1. A, 2. False, 3. 0, 4. fast / quick
"""

res = parse_test_questions(sample)
print(f"Extracted {len(res)} questions:")
for q in res:
    print(q)
