import json
import os
import random
import re
import string

import fitz
import pickle

import PySimpleGUI as sg


# TODO: Manual editing of questions
# TODO: Image processing or manual adding

def extract_chapter_map(doc):
    toc = doc.get_toc()
    chapter_map = []
    answer_match = 0
    for i, chapter in enumerate(toc):
        if chapter[0] == 1 and chapter[1].startswith("Chapter "):
            regex_question_and_choices = r"^\d[\d\s]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
            regex_choice_spillover = r"^[A-Z]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
            start_page_check = chapter[2] - 1
            end_page_check = toc[i + 1][2] - 2
            total_questions = 0
            spillover_case = False
            while True:
                # Goes through pages to see if they have questions to find real start and end page
                if re.findall(regex_question_and_choices, doc[start_page_check].get_text(), re.MULTILINE):
                    # Once start page is found checks for end page
                    last_page_text = re.findall(regex_question_and_choices, doc[end_page_check].get_text(),
                                                re.MULTILINE)
                    last_page_spillover_case = re.findall(regex_choice_spillover, doc[end_page_check].get_text(),
                                                re.MULTILINE)
                    if last_page_text:
                        regex_question_num = r"^\d[\d\s]*(?=\.\s)"
                        total_questions = int(re.findall(regex_question_num, last_page_text[-1], re.MULTILINE)[0])
                        if spillover_case:
                            end_page_check += 1
                        break
                    elif last_page_spillover_case and not last_page_text:
                        # Check if there is a page at the end that is just choices
                        spillover_case = True
                        end_page_check -= 1
                    else:
                        end_page_check -= 1
                        if end_page_check <= start_page_check:  # incase it checks all chapter pages and nothing found
                            break
                else:
                    start_page_check += 1
                    if start_page_check >= end_page_check:  # incase it checks all chapter pages and nothing found
                        break

            chapter_map.append({
                "number": int(chapter[1][8]),
                "title": chapter[1],
                "question_start_page": start_page_check,
                "question_end_page": end_page_check,
                "total_questions": total_questions

            })
        elif chapter[1].startswith("Answers to Chapter ") or (chapter[0] == 2 and chapter[1].startswith("Chapter ")):
            regex_answers = r"^(\d[\d' ']*)\.\s*((?:[A-Z],\s*)*[A-Z])\.\s*((?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*))"
            chapter_map[answer_match]["answer_start_page"] = chapter[2] - 1

            # Check for blank pages
            blank_check = 2
            while True:
                doc_text = doc[toc[i + 1][2] - blank_check].get_text()
                if not doc_text:
                    blank_check += 1
                else:
                    break

            last_answer_page_data = re.findall(regex_answers, doc_text, re.MULTILINE)
            if not last_answer_page_data:
                last_answer_page_data = [[0]]

            # check if last full page of answers has the final answer
            if last_answer_page_data[-1][0] == chapter_map[answer_match]["total_questions"]:
                # if it doesn't, last page should be the same as next chapter starting page
                chapter_map[answer_match]["answer_end_page"] = toc[i + 1][2] - 2
            else:
                # if it does, it should be a page before
                chapter_map[answer_match]["answer_end_page"] = toc[i + 1][2] - 1
            answer_match += 1

    return chapter_map


def extract_questions(doc, chapter, chapter_num, page_text_rect):
    def choice_cleanup(unclean_choices):
        choice_text = re.split('(^[a-zA-Z]\. +)', unclean_choices, flags=re.MULTILINE)
        choice_text = [choice.strip() for choice in choice_text if choice.strip()]
        clean_choices = [[choice_text[i][0], choice_text[i + 1]] for i in range(0, len(choice_text), 2)]
        return clean_choices

    # -------------------------------------------------
    regex_question_and_choices = r"^(\d[\d' ']*)\.\s(.*(?:\r?\n(?![a-zA-Z]\.)[^\n]*|)*)(.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    regex_question_num = r"^(\d[\d' ']*)"
    regex_choice_spillover = r"^[A-Z]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    question_bank = {}
    page_number = chapter["question_start_page"]

    cnt = 0
    i = 0
    multi_page = ""
    # for x in range(chapter["question_start_page"], chapter["question_end_page"] + 1):
    while page_number <= chapter["question_end_page"]:
        # print(doc[page_number].get_text())

        doc_text = doc[page_number].get_textbox(page_text_rect)

        if (re.match(regex_question_num, doc_text) and page_number != chapter["question_start_page"]) or page_number == chapter["question_end_page"]:
            if page_number == chapter["question_end_page"]:
                multi_page += f"\n{doc_text}"

            # print(f"\nMATCH!!\n")
            # print("*********************************")
            # print(multi_page)
            # print("*********************************")
            # cnt += 1

            # Finds all questions and splits into 3 groups: [0] is question number, [1] is question text and [2] is choices
            page_questions = re.findall(regex_question_and_choices, multi_page, re.MULTILINE)

            # spillover_check = re.findall(regex_choice_spillover, multi_page, re.MULTILINE)

            # Checks if there's more sets of choices than questions. If so it adds to last question
            # if len(spillover_check) > len(page_questions):
            #     clean_spilled_choices = choice_cleanup(spillover_check[0])
            #     # print(json.dumps(question_bank, indent=2))
            #     last_question = len(question_bank)
            #     question_bank[last_question]["choices"] += clean_spilled_choices
            for question in page_questions:
                # Choices come out with lots of new lines, this cleans them up and matches them together

                question_num = int(question[0])
                choices = choice_cleanup(question[2].strip())
                question_bank[question_num] = {
                    "question_num": question_num,
                    "question": question[1].strip(),
                    "choices": choices,
                    "chapter_number": chapter_num
                }

            multi_page = ""

        multi_page += f"\n{doc_text}"
        page_number += 1
    print(json.dumps(question_bank, indent=2))
    quit()
    return question_bank


def extract_answers(doc, chapter):
    regex_answers = r"^(\d[\d' ']*)\.\s*((?:[A-Z],\s*)*[A-Z])\.\s*((?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*))"
    regex_explanation_spillover = r"^(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    previous_result = 0

    for page in range(chapter["answer_start_page"], chapter["answer_end_page"] + 1):
        doc_text = doc[page].get_text()

        answer_data = re.findall(regex_answers, doc_text, re.MULTILINE)
        # -----------------------------------------------------------------------------------------
        # adds explanation spillover to previous question
        if previous_result:
            spillover_text = doc_text.split('\n')
            # checks if the page starts with a page number or chapter header to ignore
            if spillover_text[0].strip().isdigit():
                if "Chapter" in spillover_text[1] or "Answer" in spillover_text[1]:
                    spillover_text = spillover_text[2:]
            elif spillover_text[1].strip().isdigit():
                spillover_text = spillover_text[2:]
            elif "Chapter" in spillover_text[0] or "Answer" in spillover_text[0]:
                spillover_text = spillover_text[1:]

            spillover_text = '\n'.join(spillover_text)
            spillover_text = re.search(regex_explanation_spillover, spillover_text, re.MULTILINE)
            chapter["question_bank"][previous_result]["explanation"] += spillover_text.group()
        # -----------------------------------------------------------------------------------------
        for answer in answer_data:

            question_num = int(answer[0].replace(' ', ''))

            # check if the current question is not 1 and this chapters question 1 doesn't exist then skip
            print(json.dumps(chapter, indent=2))
            if question_num != 1 and "answer" not in chapter["question_bank"][1]:
                continue
            # check if there is already an answer built for the current question then break
            elif "answer" in chapter["question_bank"][question_num]:
                # print(json.dumps(chapter, indent=2))
                break
            # otherwise build the answer
            else:
                answers_list = answer[1].split(', ')
                chapter["question_bank"][question_num]["answer"] = answers_list
                chapter["question_bank"][question_num]["explanation"] = answer[2]
                if not answer[2].strip().endswith('.'):
                    previous_result = question_num
                else:
                    previous_result = 0


# Function to open and process the selected PDF file
def pdf_processing(file_path):
    doc = fitz.open(file_path)
    title = sanitize_file_name(doc.metadata["title"])

    # Check if the file already exists before overwriting
    if os.path.exists(f'./bins/{title}'):
        # file_exist_ans = 'OK' or 'Cancel'
        file_exists_ans = sg.popup_ok_cancel(f"'{title}' already exists. Do you want to overwrite it?")
        if file_exists_ans == 'Cancel':
            return

    # processes the mapping of chapters
    chapter_map = extract_chapter_map(doc)

    # create rect to remove header
    page_text_rect = (0, 60, doc[0].rect.width, doc[0].rect.height)

    # extract all questions and answers for each chapter
    for chapter_num, chapter in enumerate(chapter_map):
        chapter["question_bank"] = extract_questions(doc, chapter, chapter_num + 1, page_text_rect)
        extract_answers(doc, chapter, page_text_rect)

    # save the data to a binary file for later use
    with open(f'./bins/{title}', 'wb') as file:
        pickle.dump(chapter_map, file)


def sanitize_file_name(file_name):
    # Define a translation table to remove characters that are not allowed in file names
    # We'll keep all letters, digits, and some common file name-safe characters like '-', '_', and '.'
    allowed_characters = string.ascii_letters + string.digits + "-_."

    # Create a translation table that maps all characters not in the allowed set to None (removes them)
    translation_table = str.maketrans('', '', ''.join(c for c in string.printable if c not in allowed_characters))

    # Use translate() to remove disallowed characters from the file name
    sanitized_name = file_name.translate(translation_table)

    # Remove leading and trailing dots and spaces (common file name issues)
    sanitized_name = sanitized_name.strip('. ')

    return sanitized_name


def question_randomizer(pdf_questions, total_questions=100):
    # Choose which questions will be on the test and radomize their order
    total_chapters = len(pdf_questions)
    questions_per_chapter = [0 for _ in range(total_chapters)]
    chosen_questions = [[] for _ in range(total_chapters)]

    for _ in range(total_questions):
        while True:
            random_chapter = random.randint(0, total_chapters - 1)
            # add 1 if chosen random chapters value is less than the total number of questions for that chapter
            if questions_per_chapter[random_chapter] < pdf_questions[random_chapter]["total_questions"]:
                questions_per_chapter[random_chapter] += 1
                break

    for i in range(total_chapters):
        chosen_questions[i].extend(
            random.sample(list(pdf_questions[i]["question_bank"].values()), questions_per_chapter[i]))

    chosen_questions = [question for chapter in chosen_questions for question in chapter]
    for _ in range(5):
        random.shuffle(chosen_questions)

    return chosen_questions


def load_previous_pdfs():
    filelist = []
    for file in os.listdir('./bins'):
        filelist.append(file)
    return filelist


def nav_window(filelist):
    # starting window to add, remove, or select quiz
    layout = [
        [sg.Text("PDF Titles:")],
        [sg.Listbox(filelist, size=(60, 8), expand_y=True, enable_events=True, key="-LIST-")],
        [sg.pin(
            sg.Column([
                [sg.InputText(key="input_path"), sg.FileBrowse("Browse", key="browse_button", file_types=(("PDF files", "*.pdf"),)), sg.OK(key="add-OK")]
            ], key="add-browser", pad=(0, 0), visible=False)
        )],
        # [sg.Text("Select a PDF:")],

        [sg.Button(key="-ADD-", button_text="Add"), sg.Button('Remove')],
        [sg.pin(
            sg.Column([
                [sg.Text("Quiz Type:"), sg.Radio("Test", "quiz_type", key="test", enable_events=True),
                 sg.Radio("Practice", "quiz_type", key="practice", enable_events=True)],
                [sg.Text(f"Total questions? (max"), sg.Text(key="max-questions"),
                 sg.InputText(key="quiz-len", size=5, enable_events=True)],
                [sg.Button("Start")]
            ], key="settings-col", pad=(0, 0), visible=False)
        )],
    ]
    # Define the layout of the GUI
    # Create the window
    return sg.Window("PDF Reader", layout)


def quiz_window(question_number, current_question, quiz_type, score):
    # generates quiz window and dynamically adds choices
    layout = [
        [sg.Text(f'Question {question_number}: ')],
        [sg.Text(f"{current_question['question']}")],
    ]
    if len(current_question['answer']) == 1:
        choice_buttons = [[sg.Radio(choice[1], question_number, key=choice[0])] for choice in
                          current_question['choices']]
    else:
        choice_buttons = [[sg.Checkbox(choice[1], key=choice[0])] for choice in current_question['choices']]
    layout.append(choice_buttons)
    layout.append([sg.Button("Submit"), sg.Text(size=(10, 1)), sg.Button("Show Data")])
    if quiz_type == 'practice' and question_number - 1 > 0:
        layout.append(
            [sg.Text(f"Score: {score} / {question_number - 1}  -  {score / (question_number - 1) * 100:.2f}")])

    return sg.Window("Quiz", layout)


def main():
    # Main function to create and run the GUI
    test1 = "./CompTIA CySA_ Practice Tests_ Exam CS0-002 - Mike Chapple & David Seidl.pdf"
    test2 = "../../Network plus/Practice Test Generator/CompTIA Network+ Practice Tests.pdf"
    pdf_processing(test1)
    sg.set_options(font=('Arial Bold', 16))
    filelist = load_previous_pdfs()
    nav = nav_window(filelist)
    quiz = None
    settings = None
    quiz_questions = None
    toggle = True

    # Nav screen loop
    while True:
        event, values = nav.read()
        print(event)
        # Window closed
        if event == sg.WINDOW_CLOSED:
            break

        # Add new pdf
        if event == "-ADD-":

            # TODO change file browser to only show pdfs
            nav['add-browser'].update(visible=True)
        if event == 'add-OK':
            file_path = values["input_path"]
            if file_path:
                # Extract the pdf data and create a file for use
                pdf_processing(file_path)
                # Reload the list elements
                nav['-LIST-'].update(load_previous_pdfs())
                nav['add-browser'].update(visible=False)

            else:
                sg.popup_error("Please enter or select a PDF file path.")
        # Select valid PDF
        if event == '-LIST-' and nav["-LIST-"].get():
            try:
                # Get data from binary file
                with open(f'./bins/{nav["-LIST-"].get()[0]}', 'rb') as file:
                    pdf_questions = pickle.load(file)
                # Calculate total questions in pdf
                total_questions = 0
                for chapter in pdf_questions:
                    total_questions += len(chapter["question_bank"])
                nav["max-questions"].update(f"{total_questions} )")
                nav["settings-col"].update(visible=True)
            # Error if the file doesn't exist
            except FileNotFoundError:
                sg.popup_error("File Not Found! Try adding it again if this error persists.")

        # Typing quiz length validation
        if event == 'quiz-len' and values['quiz-len'] and values['quiz-len'][-1] not in '0123456789':
            nav['quiz-len'].update(values['quiz-len'][:-1])
        elif event == 'quiz-len' and values['quiz-len'] and int(values['quiz-len']) > total_questions:
            nav['quiz-len'].update(values['quiz-len'][:-1])

        if event == "Remove":
            pass

        # Start Quiz

        if event == "Start":
            print(values)
            if values['quiz-len'] and values['test'] or values['practice']:
                if not quiz and pdf_questions:
                    if values['test']:
                        quiz_type = 'test'
                    elif values['practice']:
                        quiz_type = 'practice'

                    total_questions = int(values['quiz-len'])
                    quiz_questions = question_randomizer(pdf_questions, total_questions)
                    current_question = 0
                    score = 0
                    closed = False

                    if quiz_questions:
                        while current_question + 1 < total_questions:
                            if closed:
                                quiz = None
                                break
                            while True:
                                quiz = quiz_window(current_question + 1, quiz_questions[current_question], quiz_type,
                                                   score)
                                quiz_event, quiz_values = quiz.read()

                                if quiz_event == sg.WINDOW_CLOSED:
                                    closed = True
                                    break
                                if quiz_event == "Show Data":
                                    print(json.dumps(quiz_questions[current_question], indent=2))
                                if quiz_event == "Submit":
                                    selected_answer = [choice for choice, value in quiz_values.items() if value]

                                    if quiz_questions[current_question]["answer"] == selected_answer:
                                        score += 1
                                        explain = quiz_questions[current_question]['explanation'].replace(f'\n', ' ')
                                        if values['practice']:
                                            sg.popup_ok(f"Good Job!\n\n{explain}")

                                    elif values['practice']:
                                        sg.popup_ok(f"OOP!\n\n{quiz_questions[current_question]['explanation']}")
                                    current_question += 1
                                    quiz.close()
                                    break

            else:
                sg.popup_ok("Select quiz type and length before beginning")

    # Close the window
    nav.close()
    if quiz:
        quiz.close()


if __name__ == "__main__":
    main()
