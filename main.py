import json
import os
import random
import re

import pypdf
import pickle

import PySimpleGUI as sg


def extract_chapter_outline(pdf_reader):
    # Contains title and page number in table of contents (might not need)
    table_of_contents = []
    chapter_outline = []

    # Initialize variables to store the previous chapter's starting page number
    current_chapter = 0
    for item in pdf_reader.info:

        if isinstance(item, list):
            for subitem in item:
                title = subitem.title
                page_num = pdf_reader.get_destination_page_number(subitem)
                table_of_contents.append([title, page_num])
                if current_chapter:
                    if chapter_outline[current_chapter - 1]["end_page"] is None:
                        chapter_outline[current_chapter - 1]["end_page"] = page_num - 1

                    else:
                        chapter_outline[current_chapter - 1]["answer_end_page"] = page_num - 1
                if title.startswith('Chapter '):
                    chapter_outline.append({
                        "chapter_number": title[8],
                        "chapter_name": title,
                        "start_page": page_num,
                        "end_page": None,
                        "answer_start_page": None,
                        "answer_end_page": None
                    })
                    current_chapter += 1

                elif subitem.title.startswith('Answers to Chapter '):
                    chapter_outline[current_chapter]["answer_start_page"] = page_num
                    current_chapter += 1

                else:
                    current_chapter = 0

        else:
            title = item.title
            page_num = pdf_reader.get_destination_page_number(item)
            table_of_contents.append([title, page_num])

            if current_chapter:
                if chapter_outline[current_chapter - 1]["end_page"] is None:
                    chapter_outline[current_chapter - 1]["end_page"] = page_num - 1

                else:
                    chapter_outline[current_chapter - 1]["answer_end_page"] = page_num - 1
            if title.startswith('Chapter '):
                chapter_outline.append({
                    "chapter_number": title[8],
                    "chapter_name": title,
                    "start_page": page_num,
                    "end_page": None,
                    "answer_start_page": None,
                    "answer_end_page": None
                })
                current_chapter += 1

            elif item.title.startswith('Answers to Chapter '):
                chapter_outline[current_chapter]["answer_start_page"] = page_num
                current_chapter += 1

            else:
                current_chapter = 0

    return table_of_contents, chapter_outline


# def extract_chapter_outline(pdf_reader):
#   GPT VERSION TEST LATER
#     def process_item(item):
#         title = item.title
#         page_num = pdf_reader.get_destination_page_number(item)
#         table_of_contents.append([title, page_num])
#
#         if current_chapter:
#             key = "end_page" if chapter_outline[current_chapter - 1]["end_page"] is None else "answer_end_page"
#             chapter_outline[current_chapter - 1][key] = page_num - 1
#
#         if title.startswith('Chapter '):
#             chapter_outline.append({
#                 "chapter_number": title[8],
#                 "chapter_name": title,
#                 "start_page": page_num,
#                 "end_page": None,
#                 "answer_start_page": None,
#                 "answer_end_page": None
#             })
#             return current_chapter + 1
#
#         elif title.startswith('Answers to Chapter '):
#             chapter_outline[current_chapter]["answer_start_page"] = page_num
#             return current_chapter + 1
#
#         return 0
#
#     table_of_contents = []
#     chapter_outline = []
#     current_chapter = 0
#
#     items_to_process = (subitem for item in pdf_reader.info if isinstance(item, list) for subitem in item)  # Generator
#
#     for item in items_to_process:
#         current_chapter = process_item(item)
#
#     return table_of_contents, chapter_outline


def extract_questions(pdf_reader):
    pass


# Function to open and process the selected PDF file
def pdf_processing(file_path):
    try:
        pdf_reader = pypdf.PdfReader(file_path)
        table_of_contents, chapter_outline, answer_outline = extract_chapter_outline(pdf_reader)
        current_chapter = 0
        for chapter in chapter_outline:
            current_chapter += 1
            starting_page_num = chapter[1]
            ending_page_num = chapter_outline[current_chapter]

        # extract image and save -- change filename to question number
        # for image in pdf_reader.pages[24].images:
        #     with open(image.name, "wb") as fp:
        #         fp.write(image.data)

        # Add more processing code here as needed
    except Exception as e:
        sg.popup_error(f"Error: {e}")


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
        [sg.Button("Process PDF")]
    ]

    # Create the window
    return sg.Window("PDF Reader", layout)


def test_window():
    pass


# Main function to create and run the GUI
def main():
    # List to store PDF titles
    previous_pdfs = []
    previous_pdfs = load_previous_pdfs()
    print(os.getcwd())

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
