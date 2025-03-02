import pdfplumber
import csv
from typing import Dict
import re

def clean_text(text: str) -> str:
    """清理文本，移除页码和常见页眉/页脚"""
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'IT Certification Guaranteed, The Easy Way!', '', text)
    text = '\n'.join(line for line in text.splitlines() if line.strip())
    return text.strip()

def split_into_questions(text: str) -> list:
    """将文本按 'QUESTION NO:' 分成问题块"""
    blocks = []
    start_pos = 0
    
    while True:
        next_question = text.find("QUESTION NO:", start_pos + 1)
        if next_question == -1:
            blocks.append(text[start_pos:].strip())
            break
        blocks.append(text[start_pos:next_question].strip())
        start_pos = next_question
    
    return blocks

def process_question_block(block: str) -> tuple:
    """处理单个问题块，返回 (question_id, data)"""
    try:
        # 提取问题编号（包括完整的“QUESTION NO: 4”）
        no_end = block.find("\n")
        if no_end == -1:
            no_end = len(block)
        question_id = block[:no_end].strip()  # 直接提取完整的“QUESTION NO: 4”
        
        # 提取问题内容（介于“QUESTION NO: 4”与“A.”之间的所有内容）
        question_start = no_end  # 从问题编号末尾开始
        a_start = block.find("A.", question_start)
        if a_start == -1:
            return question_id, None
        
        question_text = block[question_start:a_start].strip()
        # question_text = " ".join(question_text.split())  # 清理多余空格
        
        # 提取选项（从第一个“A.”开始）
        options = []
        current_pos = a_start  # 直接从“A.”开始，无需冗余变量
        
        option_letters = ["A.", "B.", "C.", "D.", "E.", "F."]
        for letter in option_letters:
            option_start = block.find(letter, current_pos)
            if option_start == -1:
                break
            
            next_letter = option_letters[option_letters.index(letter) + 1] if option_letters.index(letter) + 1 < len(option_letters) else "Answer:"
            option_end = block.find(next_letter, option_start)
            if option_end == -1:
                if next_letter == "Answer:":
                    option_end = block.find("Answer:", option_start)
                    if option_end == -1:
                        option_end = block.find("Explanation:", option_start)
                        if option_end == -1:
                            option_end = len(block)
                else:
                    break
            
            option_text = block[option_start:option_end].strip()
            option_text = " ".join(option_text.split())
            if len(option_text) > 3:
                options.append(option_text)
            current_pos = option_end
        
        # 提取答案
        answer_start = block.find("Answer:")
        if answer_start != -1:
            explanation_start = block.find("Explanation:", answer_start)
            if explanation_start == -1:
                explanation_start = len(block)
            answer_content = block[answer_start + len("Answer:"):explanation_start].strip()
            answers = [ans.strip() for ans in answer_content.split(",")] if "," in answer_content else [answer_content] if answer_content else []

            # 提取解释内容（从“Explanation:”开始到块末尾）
            if explanation_start != -1:
                explanation_text = block[explanation_start + len("Explanation:"):].strip()
            else:
                explanation_text = ""
        else:
            answers = []
            explanation_text = ""
        
        return question_id, {
            "question": question_text,
            "options": options,
            "answer": answers,
            "explanation": explanation_text  # 添加解释内容
        }
    except Exception as e:
        print(f"Error processing question block: {e}")
        return question_id, None

def extract_qa_from_pdf(pdf_path: str) -> Dict:
    qa_pairs = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += clean_text(text) + "\n"
            
            question_blocks = split_into_questions(full_text)
            for block in question_blocks:
                if block.startswith("QUESTION NO:"):
                    qid, data = process_question_block(block)
                    if data:
                        qa_pairs[qid] = data
                        print(f"Question {qid} processed: {data['question'][:50]}...")
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return qa_pairs

def save_qa_to_csv(qa_pairs: Dict, csv_path: str):
    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["number", "question", "optionA", "optionB", "optionC", "optionD", "optionE", "optionF", "answer", "explanation"])
        for qid, data in qa_pairs.items():
            options = data["options"] + [""] * (6 - len(data["options"]))
            answer_str = ",".join(data["answer"]) if data["answer"] else ""
            writer.writerow([
                qid,
                data["question"],
                options[0], options[1], options[2], options[3], options[4], options[5],
                answer_str,
                data["explanation"]
            ])

if __name__ == "__main__":
    qa_pairs = extract_qa_from_pdf('app_builder.pdf')
    if qa_pairs:
        save_qa_to_csv(qa_pairs, 'app_builder.csv')
        print("CSV file 'app_builder.csv' has been generated successfully.")