import json
import os
import random
import re

import PyPDF2
import pickle

import PySimpleGUI as sg


# Function to open and process the selected PDF file
def start_process_pdf(file_path):
    try:
        pdf_reader = PyPDF2.PdfReader(file_path)

        for item in pdf_reader.outline:
            print("*************************")
            if isinstance(item, list):
                for subitem in item:
                    print(subitem.title)
                    print(pdf_reader.get_destination_page_number(subitem))

            else:
                print(item.title)
                print(pdf_reader.get_destination_page_number(item))
        print(pdf_reader.pages[24].images)
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
                start_process_pdf(file_path)
            else:
                sg.popup_error("Please enter or select a PDF file path.")

    # Close the window
    nav.close()


if __name__ == "__main__":
    main()
