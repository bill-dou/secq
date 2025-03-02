import streamlit as st
import csv
from typing import Dict, List

# 登录函数
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.title("Login to Access Salesforce App Builder Quiz")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username == "admin" and password == "secret123":
                st.session_state.logged_in = True
                st.success("Login successful! Redirecting to quiz...")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
        
        st.stop()

def read_qa_from_csv(csv_path: str) -> Dict:
    qa_pairs = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                question_id = row["number"]
                options = [row[f"option{chr(65+i)}"] for i in range(6) if row[f"option{chr(65+i)}"]]
                answers = row["answer"].split(",") if row["answer"] else []
                qa_pairs[question_id] = {
                    "question": row["question"],
                    "options": options,
                    "answer": answers,
                    "explanation": row["explanation"]  # 添加解释内容
                }
    except FileNotFoundError:
        return {}
    return qa_pairs

def main():
    check_login()

    st.title("Salesforce App Builder Quiz")

    csv_path = "app_builder.csv"

    # 初始化session_state
    if "qa_pairs" not in st.session_state:
        qa_pairs = read_qa_from_csv(csv_path)
        st.session_state.qa_pairs = qa_pairs
        st.session_state.current_index = 0  # 当前问题索引

    qa_pairs = st.session_state.qa_pairs
    if not qa_pairs:
        st.error("No questions found in the CSV file.")
        return
    
    

    # 获取问题列表（按编号排序）
    questions = list(qa_pairs.items())
    questions.sort(key=lambda x: int(x[0].replace("QUESTION NO:", "").strip()))  # 按数字排序
    total_questions = len(questions)

    # 当前问题索引
    current_index = st.session_state.current_index

    st.markdown("""
        <style>
        .stButton > button {
            text-align: left;
        }
        .st-key-next_button > .stButton {
            text-align: right;
        }
        </style>
    """, unsafe_allow_html=True)

    # 导航按钮
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("Previous", disabled=current_index == 0):
            st.session_state.current_index -= 1
            st.rerun()
    with col4:
        if st.button("Next", key="next_button", disabled=current_index == total_questions - 1):
            st.session_state.current_index += 1
            st.rerun()

    # 显示当前问题
    question_id, data = questions[current_index]
    st.markdown(f"### Question {int(question_id.replace('QUESTION NO:', '').strip())} of {total_questions}")

    st.write(data["question"])

    # 判断是否为多选题（根据正确答案数量）
    is_multichoice = len(data["answer"]) > 1

    # 存储用户答案
    if f"user_answer_{question_id}" not in st.session_state:
        st.session_state[f"user_answer_{question_id}"] = []

    # 使用按钮显示选项
    selected_answers: List[str] = st.session_state[f"user_answer_{question_id}"]
    for option in data["options"]:
        if st.button(option, key=f"btn_{question_id}_{option}"):
            if is_multichoice:
                # 多选：切换选择状态（添加或移除）
                if option in selected_answers:
                    selected_answers.remove(option)
                else:
                    selected_answers.append(option)
            else:
                # 单选：只能选择一个选项，清除之前的选择
                selected_answers = [option] if option not in selected_answers else []
            st.session_state[f"user_answer_{question_id}"] = selected_answers
            st.rerun()  # 刷新页面以更新按钮状态

    # 显示当前选择（可选，用于用户确认）
    # if selected_answers:
    #     st.write(f"Selected: {', '.join(selected_answers)}")

   # Submit 按钮占一行，全宽
    if st.button("Submit", type="primary", use_container_width=True, key="submit_button", help="Submit your answer"):
        # 检查答案
        user_answer_letters = sorted([opt[0] for opt in selected_answers])
        correct_answer_letters = sorted(data["answer"])
        
        if user_answer_letters == correct_answer_letters:
            st.session_state[f"feedback_{question_id}"] = "Correct! 🎉"
        else:
            correct_display = ", ".join(data["answer"])
            st.session_state[f"feedback_{question_id}"] = f"Wrong. The correct answer(s): {correct_display}"

    # 正确性反馈占一行，全宽
    if f"feedback_{question_id}" in st.session_state:
        if "Correct!" in st.session_state[f"feedback_{question_id}"]:
            st.success(st.session_state[f"feedback_{question_id}"])
        else:
            st.error(st.session_state[f"feedback_{question_id}"])
        # 在下一行显示解释内容，全宽
        st.write(data["explanation"])

if __name__ == "__main__":
    main()