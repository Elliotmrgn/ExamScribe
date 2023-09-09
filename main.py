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
    # Contains title and page number for chapters with questions
    chapter_outline = []
    # Contains title and page number for chapters with answers
    answer_outline = []
    for item in pdf_reader.outline:
        if isinstance(item, list):
            for subitem in item:
                table_of_contents.append([subitem.title, pdf_reader.get_destination_page_number(subitem)])
                if subitem.title.startswith('Chapter '):
                    chapter_outline.append([subitem.title, pdf_reader.get_destination_page_number(subitem)])
                elif subitem.title.startswith('Answers to Chapter '):
                    answer_outline.append([subitem.title, pdf_reader.get_destination_page_number(subitem)])

        else:
            table_of_contents.append([item.title, pdf_reader.get_destination_page_number(item)])
            if item.title.startswith('Chapter '):
                chapter_outline.append([item.title, pdf_reader.get_destination_page_number(item)])
            elif item.title.startswith('Answers to Chapter '):
                answer_outline.append([item.title, pdf_reader.get_destination_page_number(item)])
    return table_of_contents, chapter_outline, answer_outline

def extract_questions(pdf_reader):
    pass
# Function to open and process the selected PDF file
def pdf_processing(file_path):
    try:
        pdf_reader = pypdf.PdfReader(file_path)
        table_of_contents, chapter_outline, answer_outline = extract_chapter_outline(pdf_reader)
        starting_page_num = chapter_outline[0][1]

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
