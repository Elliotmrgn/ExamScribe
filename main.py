import json
import os
import random
import re
import string

import pypdf
import fitz
import pickle

import PySimpleGUI as sg



# TODO: Study mode & Test Mode
# TODO: Manual changing of questions
# TODO: Answer and explanation popup
# TODO: Image processing

def extract_chapter_map(doc):
    toc = doc.get_toc()
    chapter_map = []
    answer_match = 0
    for i, chapter in enumerate(toc):
        if chapter[0] == 1 and chapter[1].startswith("Chapter "):
            regex_question_and_choices = r"^\d[\d\s]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
            start_page_check = chapter[2] - 1
            end_page_check = toc[i + 1][2] - 2
            total_questions = 0
            while True:
                # Goes through pages to see if they have questions to find real start and end page
                if re.findall(regex_question_and_choices, doc[start_page_check].get_text(), re.MULTILINE):
                    # Once start page is found checks for end page
                    last_page_text = re.findall(regex_question_and_choices, doc[end_page_check].get_text(),
                                                re.MULTILINE)
                    if last_page_text:
                        regex_question_num = r"^\d[\d\s]*(?=\.\s)"
                        total_questions = int(re.findall(regex_question_num, last_page_text[-1], re.MULTILINE)[0])
                        break
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


def extract_questions(doc, chapter, chapter_num):
    def choice_cleanup(unclean_choices):
        choice_text = re.split('(^[a-zA-Z]\. +)', unclean_choices, flags=re.MULTILINE)
        choice_text = [choice.strip() for choice in choice_text if choice.strip()]
        clean_choices = [[choice_text[i][0], choice_text[i + 1]] for i in range(0, len(choice_text), 2)]
        return clean_choices

    # -------------------------------------------------
    regex_question_and_choices = r"^(\d[\d' ']*)\.\s(.*(?:\r?\n(?![a-zA-Z]\.)[^\n]*|)*)(.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    regex_choice_spillover = r"^[A-Z]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    question_bank = {}

    for x in range(chapter["question_start_page"], chapter["question_end_page"] + 1):
        doc_text = doc[x].get_text()
        page_questions = re.findall(regex_question_and_choices, doc_text, re.MULTILINE)
        spillover_check = re.findall(regex_choice_spillover, doc_text, re.MULTILINE)

        # Checks if there's more sets of choices than questions. If so it adds to last question
        if len(spillover_check) > len(page_questions):
            clean_spilled_choices = choice_cleanup(spillover_check[0])
            # print(json.dumps(question_bank, indent=2))
            last_question = len(question_bank)
            question_bank[last_question]["choices"] += clean_spilled_choices
        for question in page_questions:
            # Choices come out with lots of new lines, this cleans them up and matches them together

            choices = choice_cleanup(question[2].strip())
            question_num = int(question[0])
            question_bank[question_num] = {
                "question_num": question_num,
                "question": question[1].strip(),
                "choices": choices,
                "chapter_number": chapter_num
            }

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

    chapter_map = extract_chapter_map(doc)

    for chapter_num, chapter in enumerate(chapter_map):
        chapter["question_bank"] = extract_questions(doc, chapter, chapter_num+1)
        extract_answers(doc, chapter)
        # print(json.dumps(chapter, indent=2))
    print("TITLE: ", title)


    with open(f'./bins/{title}', 'wb') as file:
        pickle.dump(chapter_map, file)

    # return chapter_map
    # extract image and save -- change filename to question number
    # for image in pdf_reader.pages[24].images:
    #     with open(image.name, "wb") as fp:
    #         fp.write(image.data)

    # Add more processing code here as needed


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
        chosen_questions[i].extend(random.sample(list(pdf_questions[i]["question_bank"].values()), questions_per_chapter[i]))

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
    layout = [
        [sg.Text("PDF Titles:")],
        [sg.Listbox(filelist, size=(60, 8), expand_y=True, enable_events=True, key="-LIST-")],
        [sg.Text("Select a PDF:")],
        [sg.InputText(key="input_path"), sg.FileBrowse("Browse", key="browse_button")],
        [sg.Button(key="-ADD-", button_text="Add"), sg.Button('Remove'), sg.Button("Start"), sg.Button("Test")],
    ]
    # Define the layout of the GUI
    # Create the window
    return sg.Window("PDF Reader", layout)


def quiz_window(question_number, current_question, quiz_type, score):
    layout = [
        [sg.Text(f'Question {question_number}: ')],
        [sg.Text(f"{current_question['question']}")],
    ]
    if len(current_question['answer']) == 1:
        choice_buttons = [[sg.Radio(choice[1], question_number, key=choice[0])] for choice in current_question['choices']]
    else:
        choice_buttons = [[sg.Checkbox(choice[1], key=choice[0])] for choice in current_question['choices']]
    layout.append(choice_buttons)
    layout.append([sg.Button("Submit"), sg.Text(size=(10,1)), sg.Button("Show Data")])
    if quiz_type == 'practice' and question_number-1 > 0:
        layout.append([sg.Text(f"Score: { score } / { question_number - 1 }  -  {score/(question_number-1)*100:.2f}")])

    return sg.Window("Quiz", layout)


def settings_window(total_questions):
    layout = [
        [sg.Text("Quiz Type:"), sg.Radio("Test", "quiz_type", key="test", enable_events=True),
         sg.Radio("Practice", "quiz_type", key="practice", enable_events=True)],
        [sg.pin(
            sg.Column([
                [sg.Text(f"Total questions? (max {total_questions})"), sg.InputText(key="test-len", size=4, enable_events=True)]
            ], key="test-col", pad=(0, 0), visible=False)
        )],
        [sg.OK()]
    ]

    return sg.Window("Settings", layout)


# Main function to create and run the GUI
def main():
    test_path = "CompTIA CySA_ Practice Tests_ Exam CS0-002 - Mike Chapple & David Seidl.pdf"
    test_path2 = "../../Network plus/Practice Test Generator/CompTIA Network+ Practice Tests.pdf"
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
        # Window closed
        if event == sg.WINDOW_CLOSED:
            break

        # Add new pdf
        if event == "-ADD-":
            # TODO change the file browse to appear when add is pressed
            # TODO change file browser to only show pdfs
            file_path = values["input_path"]
            if file_path:
                # Extract the pdf data and create a file for use
                pdf_processing(file_path)
                # Reload the list elements
                nav['-LIST-'].update(load_previous_pdfs())

                # if pdf_questions:
                #     quiz_questions = question_randomizer(pdf_questions, 100)
                # quiz_questions = list(pdf_questions[0]["question_bank"].items())[:100]
                # quiz_questions = dict(quiz_questions)
                # print(json.dumps(quiz_questions, indent=1))

            else:
                sg.popup_error("Please enter or select a PDF file path.")

        if event == "Remove":
            pass

        if event == "Start":
            # Check if there is not a generated quiz yet and
            if not quiz and nav["-LIST-"].get():
                try:
                    # Get data from binary file
                    with open(f'./bins/{nav["-LIST-"].get()[0]}', 'rb') as file:
                        pdf_questions = pickle.load(file)
                    # Calculate total questions in pdf
                    total_questions = 0
                    for chapter in pdf_questions:
                        total_questions += len(chapter["question_bank"])
                    quiz_type = ""
                    # SETTINGS WINDOW LOOP ---------------------------------------------------------------------
                    settings = settings_window(total_questions)
                    while True:
                        settings_event, settings_values = settings.read()
                        if settings_event == sg.WINDOW_CLOSED:
                            break
                        if settings_event == 'test':
                            settings["test-col"].update(visible=True)

                        if settings_event == 'test-len' and settings_values['test-len'] and settings_values['test-len'][-1] not in '0123456789':
                            settings['test-len'].update(settings_values['test-len'][:-1])
                        elif settings_event == 'test-len' and settings_values['test-len'] and int(settings_values['test-len']) > total_questions:
                            settings['test-len'].update(settings_values['test-len'][:-1])

                        if settings_event == 'practice':
                            settings["test-len"].update("")
                            settings["test-col"].update(visible=False)
                        if settings_event == "OK" and (settings_values['test'] or settings_values['practice']):
                            if settings_values['test']:
                                quiz_type = 'test'
                                total_questions = int(settings_values['test-len'])
                            else:
                                quiz_type = 'practice'
                            break
                    settings.close()
                    # --------------------------------------------------------------------------------------------

                    # Randomize questions to be answered
                    quiz_questions = question_randomizer(pdf_questions, total_questions)

                    current_question = 0
                    score = 0
                    closed = False
                    if quiz_questions:
                        while current_question+1 < total_questions:
                            if closed:
                                quiz = None
                                break
                            while True:
                                quiz = quiz_window(current_question+1, quiz_questions[current_question], quiz_type, score)
                                quiz_event, quiz_values = quiz.read()

                                if quiz_event == sg.WINDOW_CLOSED:
                                    closed = True
                                    break
                                if quiz_event == "Show Data":
                                    print(json.dumps(quiz_questions[current_question], indent=2))
                                if quiz_event == "Submit":
                                    selected_answer = [choice for choice, value in quiz_values.items() if value]
                                    # print(json.dumps(quiz_questions[current_question], indent=1))
                                    # print(selected_answer)
                                    # print(quiz_questions[current_question]["answer"])
                                    if quiz_questions[current_question]["answer"] == selected_answer:
                                        score += 1
                                        if quiz_type == 'practice':
                                            sg.popup_ok(f"Good Job!\n\n{quiz_questions[current_question]['explanation']}")

                                    elif quiz_type == 'practice':
                                        sg.popup_ok(f"OOP!\n\n{quiz_questions[current_question]['explanation']}")
                                    current_question += 1
                                    quiz.close()
                                    break



                # Error if the file gets removed before starting
                except FileNotFoundError:
                    sg.popup_error("File Not Found! Try adding it again if this error persists.")
            elif quiz:
                sg.popup_error("You already have a quiz generated.")
            else:
                sg.popup_error("You must select a PDF before starting a quiz.")

    # Close the window
    nav.close()
    if quiz:
        quiz.close()
    if settings:
        settings.close()


if __name__ == "__main__":
    main()
