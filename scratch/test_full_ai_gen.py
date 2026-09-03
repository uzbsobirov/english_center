import asyncio
from dotenv import load_dotenv
load_dotenv()

from backend.services.ai_test_generator import generate_test_from_pdf_text

async def run_test():
    sample_text = """
    CAMBRIDGE IELTS ACADEMIC READING TEST 1
    
    Reading Passage 1: The History of Tea
    
    Questions 1-4:
    Choose the correct letter, A, B, C or D.
    
    1. Tea was first discovered in ancient China by
    A) A farmer searching for herbs
    B) Emperor Shennong while boiling water
    C) Buddhist monks during meditation
    D) Merchants trading along the Silk Road
    
    2. True or False: In the 17th century, tea became the national beverage of England.
    
    3. Complete the sentence: Green tea differs from black tea because it does not undergo the process of _____.
    
    4. What mineral found in tea helps protect teeth from decay?
    
    Answers:
    1. B
    2. True
    3. fermentation / oxidation
    4. fluoride
    """
    
    print("Testing generate_test_from_pdf_text with Gemini API...")
    questions = await generate_test_from_pdf_text(sample_text, cert_type="IELTS", level="B2")
    print(f"Total questions extracted: {len(questions)}")
    for q in questions:
        print("\n---")
        print(f"#{q.get('order_num')} [{q.get('type')}] {q.get('text')}")
        print(f"Options: {q.get('options')}")
        print(f"Correct: {q.get('correct_answer')}")

if __name__ == "__main__":
    asyncio.run(run_test())
