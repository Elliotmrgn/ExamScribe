# ExamScribe - Practice Exam Generator and Quiz App

ExamScribe is a Python GUI application designed to simplify the process of creating and taking practice exams. With ExamScribe, you can upload a PDF containing practice exam questions, scrape and store those questions and answers, and then generate quizzes for self-assessment. The app offers two types of quizzes: "Test" for grading at the end and "Practice" with immediate feedback.

## Features

- **PDF Question Scraping:** ExamScribe allows you to upload a PDF file containing practice exam questions. The application will automatically extract the questions and match them with their corresponding answers.

- **Quiz Generation:** You can create practice quizzes of varying lengths and quiz types (Test or Practice). Simply select the PDF you've scraped, choose the quiz type, and specify the desired quiz length.

- **Test Mode:** In Test mode, users answer all the questions in the quiz, and after submitting the last answer, they receive a grade indicating how they performed.

- **Practice Mode:** Practice mode provides immediate feedback for each question. Users can submit answers and receive instant feedback, including explanations for incorrect answers.

- **Data Persistence:** ExamScribe saves the scraped questions and answers in a dictionary and stores it as a binary file. This ensures that you can access your quiz data without the need to re-scrape the PDF, saving you time.

## Getting Started

### Prerequisites

Before you can use ExamScribe, make sure you have the following prerequisites installed:

- Python 3.x
- PyMuPDF (fitz)
- PySimpleGUI

You can install these libraries using pip:
```
pip install PyMuPDF PySimpleGUI
```
## Installation

1. Clone or download the ExamScribe repository to your local machine.
```
git clone https://github.com/elliotmrgn/ExamScribe.git
```
2. Change to the ExamScribe directory.
```
cd ExamScribe
```
3. Run the exam_scribe.py script to launch the application.
```
python exam_scribe.py
```

## Usage

1. **Scrape Questions:** Start by uploading a PDF containing practice exam questions using the "Scrape PDF" button. ExamScribe will extract and match questions with answers, saving them to a dictionary.

2. **Generate a Quiz:** Select the scraped PDF, choose the quiz type (Test or Practice), and specify the quiz length.

3. **Take the Quiz:**
   - In **Test Mode**, answer all the questions, and after submitting the last answer, receive a grade.
   - In **Practice Mode**, submit answers one by one and receive immediate feedback with explanations for incorrect answers.

4. **Data Persistence:** ExamScribe saves your scraped data as a binary file, so you can load it later without re-scraping the PDF.

## Contributing

We welcome contributions to ExamScribe! Feel free to open issues, submit pull requests, or suggest new features and improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the developers of PyMuPDF and PySimpleGUI for their valuable contributions.

## Contact

If you have any questions or suggestions regarding ExamScribe, please contact me at elliotmrgn@gmail.com.

Happy studying and practicing with ExamScribe!
