import re
import random
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# myproject/myApp/utils.py

import re
import random
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from myApp.models import GeneratedQuestion

def generate_questions_from_text(text, uploaded_material):
    words = text.split()
    questions = []
    unique_questions = set()
    
    # Process the text to identify meaningful content
    sentences = re.split(r'\.|\n', text)
    meaningful_sentences = [sentence.strip() for sentence in sentences if len(sentence.split()) > 5]

    # Fill in the blanks
    for sentence in meaningful_sentences:
        if len(sentence.split()) > 6:
            question = re.sub(r'\b(\w+)\b', '_____', sentence)
            if question not in unique_questions:
                if not GeneratedQuestion.objects.filter(question_text=question).exists():
                    generated_question = GeneratedQuestion(
                        material=uploaded_material,
                        question_type='fill_in_the_blank',
                        question_text=question,
                        marks=1
                    )
                    generated_question.save()
                    questions.append(generated_question)
                    unique_questions.add(question)

    # Short questions based on key concepts
    for word in words:
        if len(word) > 6 and word[0].isupper():
            question = f"What is the definition or explanation of '{word}'?"
            if question not in unique_questions:
                if not GeneratedQuestion.objects.filter(question_text=question).exists():
                    generated_question = GeneratedQuestion(
                        material=uploaded_material,
                        question_type='two_mark',
                        question_text=question,
                        marks=2
                    )
                    generated_question.save()
                    questions.append(generated_question)
                    unique_questions.add(question)

    # Concept-based questions
    for sentence in meaningful_sentences:
        if len(sentence.split()) > 10:
            question = f"Explain the concept or significance of: {sentence}"
            if question not in unique_questions:
                if not GeneratedQuestion.objects.filter(question_text=question).exists():
                    generated_question = GeneratedQuestion(
                        material=uploaded_material,
                        question_type='six_mark',
                        question_text=question,
                        marks=6
                    )
                    generated_question.save()
                    questions.append(generated_question)
                    unique_questions.add(question)

    # Descriptive questions
    for sentence in meaningful_sentences:
        if len(sentence.split()) > 15:
            question = f"Discuss in detail: {sentence}"
            if question not in unique_questions:
                if not GeneratedQuestion.objects.filter(question_text=question).exists():
                    generated_question = GeneratedQuestion(
                        material=uploaded_material,
                        question_type='ten_mark',
                        question_text=question,
                        marks=10
                    )
                    generated_question.save()
                    questions.append(generated_question)
                    unique_questions.add(question)

    return questions

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()
        return text
    except Exception as e:
        return f"Error: {str(e)}"  

def generate_pdf(questions, answer_key=False):
    pdf_filename = "question_paper_with_answer_key.pdf" if answer_key else "question_paper.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 50, "Question Paper")
    
    # Generate questions
    y_position = height - 80
    for idx, question in enumerate(questions):
        c.setFont("Helvetica", 12)
        question_text = f"{idx + 1}. {question['text']} ({question['marks']} marks)"
        c.drawString(100, y_position, question_text)
        y_position -= 20
        
        # Ensure the text does not overflow the page
        if y_position < 100:
            c.showPage()
            y_position = height - 50

    if answer_key:
        # Include answer key at the end
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 50, "Answer Key")
        y_position = height - 80
        for idx, question in enumerate(questions):
            answer_text = f"Answer to Question {idx + 1}: (Your answer here)"
            c.setFont("Helvetica", 12)
            c.drawString(100, y_position, answer_text)
            y_position -= 20
            
            if y_position < 100:
                c.showPage()
                y_position = height - 50

    c.save()
    return pdf_filename
