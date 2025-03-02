import streamlit as st
import pdfplumber
import csv
from typing import Dict

# 登录函数
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.title("Login to Access Salesforce AI Specialist Quiz")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # 硬编码的用户名和密码（仅为示例）
            if username == "admin" and password == "secret123":
                st.session_state.logged_in = True
                st.success("Login successful! Redirecting to quiz...")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
        
        st.stop()  # 停止应用执行，防止未登录用户看到内容

def extract_qa_from_pdf(pdf_path: str) -> Dict:
    qa_pairs = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # 查找所有NO.xx和A.的位置
                    start_marker = "NO."
                    end_marker = "A."
                    start_pos = 0
                    
                    while True:
                        # 查找下一个NO.xx
                        no_start = text.find(start_marker, start_pos)
                        if no_start == -1:
                            break
                        
                        # 提取NO.xx的完整部分（包括编号）
                        no_end = text.find(" ", no_start)
                        if no_end == -1:
                            no_end = len(text)
                        question_id = text[no_start:no_end].strip()
                        
                        # 查找对应的A.（问题结束标记）
                        a_start = text.find(end_marker, no_end)
                        if a_start == -1:
                            break
                        
                        # 提取问题：从NO.xx后的第一个字符到A.前的最后一个字符，合并为段落
                        question_start = no_end + 1
                        question = text[question_start:a_start].strip()
                        # 清理多余空格，确保连贯段落
                        question = " ".join(question.split())
                        
                        # 提取选项（A、B、C分别合并为段落）
                        options = []
                        current_pos = a_start
                        
                        # 提取A选项（从A.到B.之间的内容）
                        a_start_pos = text.find("A.", current_pos)
                        if a_start_pos != -1:
                            b_start_pos = text.find("B.", a_start_pos)
                            if b_start_pos != -1:
                                option_a = text[a_start_pos:b_start_pos].strip()
                                # 清理多余空格，确保连贯段落
                                option_a = " ".join(option_a.split())
                                options.append(option_a)
                                current_pos = b_start_pos
                            else:
                                # 如果没有B选项，A选项到文本末尾
                                option_a = text[a_start_pos:].strip()
                                option_a = " ".join(option_a.split())
                                options.append(option_a)
                                break
                        
                        # 提取B选项（从B.到C.之间的内容）
                        b_start_pos = text.find("B.", current_pos)
                        if b_start_pos != -1:
                            c_start_pos = text.find("C.", b_start_pos)
                            if c_start_pos != -1:
                                option_b = text[b_start_pos:c_start_pos].strip()
                                option_b = " ".join(option_b.split())
                                options.append(option_b)
                                current_pos = c_start_pos
                            else:
                                # 如果没有C选项，B选项到文本末尾
                                option_b = text[b_start_pos:].strip()
                                option_b = " ".join(option_b.split())
                                options.append(option_b)
                                break
                        
                        # 提取C选项（从C.到Answer之间的内容）
                        c_start_pos = text.find("C.", current_pos)
                        if c_start_pos != -1:
                            # 查找Answer:（假设答案以"Answer:"开头）
                            answer_start = text.find("Answer:", c_start_pos)
                            if answer_start != -1:
                                option_c = text[c_start_pos:answer_start].strip()
                                option_c = " ".join(option_c.split())
                                options.append(option_c)
                            else:
                                # 如果没有Answer:，C选项到文本末尾
                                option_c = text[c_start_pos:].strip()
                                option_c = " ".join(option_c.split())
                                options.append(option_c)
                        else:
                            break
                        
                        # 提取答案（假设答案在选项C后一行，最后一个字符是A/B/C）
                        if answer_start != -1:
                            answer_content = text[answer_start + len("Answer:"):].strip()
                            if answer_content and len(answer_content) > 0:
                                answer = answer_content[0]  # 提取Answer:后的第一个字符（如A、B、C）
                            else:
                                answer = ""
                        else:
                            answer = ""
                        
                        qa_pairs[question_id] = {
                            "question": question,
                            "options": options,
                            "answer": answer
                        }
                        
                        start_pos = current_pos
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return qa_pairs

def read_qa_from_csv(csv_path: str) -> Dict:
    qa_pairs = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                question_id = row["number"]
                qa_pairs[question_id] = {
                    "question": row["question"],
                    "options": [row["optionA"], row["optionB"], row["optionC"]],
                    "answer": row["answer"]
                }
    except FileNotFoundError:
        return {}  # 如果CSV文件不存在，返回空字典
    return qa_pairs

def save_qa_to_csv(qa_pairs: Dict, csv_path: str = "ai_specialist.csv"):
    # 保存为CSV文件，结构为：number, question, optionA, optionB, optionC, answer
    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["number", "question", "optionA", "optionB", "optionC", "answer"])
        for qid, data in qa_pairs.items():
            # 确保有3个选项，如果少于3个，用空字符串填充
            options = data["options"] + [""] * (3 - len(data["options"]))
            writer.writerow([qid, data["question"], options[0], options[1], options[2], data["answer"]])

def main():

    check_login()

    st.title("Salesforce AI Specialist Quiz")

    pdf_path = "ai_specialist.pdf"
    csv_path = "ai_specialist.csv"

    # 初始化session_state
    if "qa_pairs" not in st.session_state:
        qa_pairs = read_qa_from_csv(csv_path)
        if not qa_pairs:
            st.info("CSV is empty or not found. Extracting data from ai_specialist.pdf and filling CSV...")
            qa_pairs = extract_qa_from_pdf(pdf_path)
            if qa_pairs:
                save_qa_to_csv(qa_pairs, csv_path)
                st.success("Data extracted from ai_specialist.pdf and saved to ai_specialist.csv.")
            else:
                st.error("No questions found in ai_specialist.pdf. Please check the PDF format.")
        else:
            st.success("Data loaded successfully!")
        st.session_state.qa_pairs = qa_pairs

    # 显示题目和选项
    for question_id, data in st.session_state.qa_pairs.items():
        st.markdown(f"### {question_id}")
        st.write(data["question"])

        # 显示选项
        options_list = [opt for opt in data["options"] if opt]
        selected_answer = st.radio("Select one option:", options_list, index=None, key=f"radio_{question_id}")

        # 检查答案并显示结果
        if selected_answer:
            user_answer = selected_answer[0]  # 提取用户选择的答案（A、B或C）
            correct_answer = data["answer"]
            
            # 将正确答案存储在session_state中（可选，实际上直接用data["answer"]即可）
            if f"correct_{question_id}" not in st.session_state:
                st.session_state[f"correct_{question_id}"] = correct_answer

            # 本地对比答案
            if user_answer == correct_answer:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong. The correct answer is {correct_answer}.")
        
        st.write("---")

if __name__ == "__main__":
    main()