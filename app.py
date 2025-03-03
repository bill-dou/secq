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
            border: 0;
            background-color: transparent;
            justify-content: flex-start;
            transition: background-color 0.3s, color 0.3s;
        }
        .stButton > button:hover,
        .stButton > button:active {
            color: inherit;
            background-color: rgba(0, 0, 0, 0.1); /* 轻微灰色悬停效果 */
        }
        .st-key-btn_selected_A,
        .st-key-btn_selected_B,
        .st-key-btn_selected_C,
        .st-key-btn_selected_D,
        .st-key-btn_selected_E {
            background-color: green;
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

    # 存储用户答案和按钮状态
    if f"user_answer_{question_id}" not in st.session_state:
        st.session_state[f"user_answer_{question_id}"] = []
    if f"button_states_{question_id}" not in st.session_state:
        st.session_state[f"button_states_{question_id}"] = {}  # 跟踪每个按钮的选中状态

    def handle_option_click(option: str):
        selected_answers = st.session_state[f"user_answer_{question_id}"]
        button_states = st.session_state[f"button_states_{question_id}"]
        option_letter = option[0]  # 提取选项字母（如 "A"）

        if is_multichoice:
            # 多选：切换选择状态
            if option_letter in selected_answers:
                selected_answers.remove(option_letter)
                button_states[option] = False
            else:
                selected_answers.append(option_letter)
                button_states[option] = True
        else:
            # 单选：只能选择一个选项，清除之前的选择
            selected_answers = [option_letter] if option_letter not in selected_answers else []
            button_states = {opt: opt[0] == option_letter for opt in data["options"]}

        st.session_state[f"user_answer_{question_id}"] = selected_answers
        st.session_state[f"button_states_{question_id}"] = button_states
        # 移除 st.rerun()，依赖状态更新和 CSS 样式

    # 使用按钮显示选项，并动态应用样式
    selected_answers: List[str] = st.session_state[f"user_answer_{question_id}"]

    for option in data["options"]:
        option_letter = option[0]  # 提取选项字母（如 "A"）
        is_selected = option_letter in selected_answers

        # 动态生成按钮的类名，添加 selected 类如果选中
        button_class = ""
        if is_selected:
            button_class += f"btn_selected_{option_letter}"

        st.button(
            option,
            use_container_width=True,
            key=button_class,
            on_click=handle_option_click,
            args=[option]
        )

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