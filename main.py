import json
import os
import random
import re

import pypdf
import fitz
import pickle

import PySimpleGUI as sg

# TODO: Image check (chapter 2, q 34)

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
        # TODO: create a check for actual answer start and end page
        elif chapter[0] == 2 and chapter[1].startswith("Chapter "):  # TOC format option
            chapter_map[answer_match]["answer_start_page"] = chapter[2] - 1
            chapter_map[answer_match]["answer_end_page"] = toc[i + 1][2] - 2
            answer_match += 1

        elif chapter[1].startswith("Answers to Chapter "):  # TOC format option
            chapter_map[answer_match]["answer_start_page"] = chapter[2] - 1
            chapter_map[answer_match]["answer_end_page"] = toc[i + 1][2] - 2
            answer_match += 1
    # for i in chapter_map:
        # print(i)

    return chapter_map


def extract_questions(doc, chapter):
    def choice_cleanup(unclean_choices):
        choice_text = re.split('(^[A-Z]\. +)', unclean_choices, flags=re.MULTILINE)
        choice_text = [choice.strip() for choice in choice_text if choice.strip()]
        clean_choices = [[choice_text[i][0], choice_text[i + 1]] for i in range(0, len(choice_text), 2)]
        return clean_choices
    # -------------------------------------------------
    regex_question_and_choices = r"^(\d[\d' ']*)\.\s(.*(?:\r?\n(?![A-Z]\.)[^\n]*|)*)(.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    regex_choice_spillover = r"^[A-Z]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    question_bank = []

    for x in range(chapter["question_start_page"], chapter["question_end_page"] + 1):
        doc_text = doc[x].get_text()
        page_questions = re.findall(regex_question_and_choices, doc_text, re.MULTILINE)
        spillover_check = re.findall(regex_choice_spillover, doc_text, re.MULTILINE)
        # Checks if theres more sets of choices than questions. If so it adds to last question
        if len(spillover_check) > len(page_questions):
            clean_spilled_choices = choice_cleanup(spillover_check[0])
            question_bank[len(question_bank)-1]["choices"] += clean_spilled_choices
        for question in page_questions:
            # Choices come out with lots of new lines, this cleans them up and matches them together

            choices = choice_cleanup(question[2].strip())
            question_bank.append({
                "number": int(question[0]),
                "text": question[1].strip(),
                "choices": choices
            })

    return question_bank



# Function to open and process the selected PDF file
def pdf_processing(file_path):
    # try:
    regex_question_and_choices = r"^\d[\d\s]*\.\s(?:.*(?:\r?\n(?!\d[\d\s]*\.\s)[^\n]*|)*)"
    doc = fitz.open(file_path)
    chapter_map = extract_chapter_map(doc)
    # extract_questions(doc, chapter_map[1])
    # quit()
    for chapter in chapter_map:
        chapter["question_bank"] = extract_questions(doc, chapter)

    print(json.dumps(chapter_map[1], indent=2))
    quit()
    # extract image and save -- change filename to question number
    # for image in pdf_reader.pages[24].images:
    #     with open(image.name, "wb") as fp:
    #         fp.write(image.data)

    # Add more processing code here as needed


# except Exception as e:
#     sg.popup_error(f"Error: {e}")


# Function to load PDF titles and file paths from a text file
def load_previous_pdfs():
    pass


def nav_window():
    # Define the layout of the GUI
    layout = [
        [sg.Text("PDF Titles:")],
        [sg.Listbox([], size=(60, 8), key="pdf_titles")],
        [sg.Text("Enter or select a PDF file path:")],
        [sg.InputText(key="input_path"), sg.FileBrowse("Browse", key="browse_button")],
        [sg.Button("Process PDF")],
    ]

    # Create the window
    return sg.Window("PDF Reader", layout)


def test_window():
    pass


# Main function to create and run the GUI
def main():
    test_path = "CompTIA CySA_ Practice Tests_ Exam CS0-002 - Mike Chapple & David Seidl.pdf"
    test_path2 = "../../Network plus/Practice Test Generator/CompTIA Network+ Practice Tests.pdf"
    pdf_processing(test_path2)

    nav = nav_window()
    while True:
        event, values = nav.read()

        if event == sg.WINDOW_CLOSED:
            break
        elif event == "Process PDF":
            file_path = values["input_path"]
            if file_path:
                pdf_processing(file_path)
            else:
                sg.popup_error("Please enter or select a PDF file path.")

    # Close the window
    nav.close()


if __name__ == "__main__":
    main()
