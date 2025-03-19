import PyPDF2
import re
import spacy
import random
from typing import List, Dict

class PDFProcessor:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_sm")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract clean text from PDF
        """
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    # Split the page into lines
                    lines = page_text.splitlines()
                    
                    # Remove header and footer based on patterns or positions
                    filtered_lines = lines[1:-1]
                    
                    # Further refine by removing lines with patterns
                    filtered_lines = [
                        line for line in filtered_lines
                        if not re.match(r'^\s*Page\s*\d+|^\d+$|^\s*$', line)
                    ]
                    
                    # Join the filtered lines back into the page content
                    text.append(" ".join(filtered_lines))
            
            return " ".join(text)

    def generate_questions(self, text: str, total_marks: int = 80) -> List[Dict]:
        """
        Generate questions from extracted text
        """
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract meaningful sentences
        sentences = [
            sent.text.strip() 
            for sent in doc.sents 
            if len(sent.text.strip()) > 20
        ]
        
        questions = []
        marks_distributed = 0
        
        # Shuffle sentences for randomness
        random.shuffle(sentences)
        
        # Generate different types of questions
        for sentence in sentences:
            # Short answer questions (2-3 marks)
            if marks_distributed + 2 <= total_marks:
                short_q = self._generate_short_answer_question(sentence)
                if short_q:
                    questions.append({
                        'text': short_q,
                        'marks': 2,
                        'type': 'short'
                    })
                    marks_distributed += 2
            
            # Long answer questions (5-6 marks)
            if marks_distributed + 5 <= total_marks:
                long_q = self._generate_long_answer_question(sentence)
                if long_q:
                    questions.append({
                        'text': long_q,
                        'marks': 5,
                        'type': 'long'
                    })
                    marks_distributed += 5
            
            # Conceptual questions (10 marks)
            if marks_distributed + 10 <= total_marks:
                conceptual_q = self._generate_conceptual_question(sentence)
                if conceptual_q:
                    questions.append({
                        'text': conceptual_q,
                        'marks': 10,
                        'type': 'conceptual'
                    })
                    marks_distributed += 10
            
            # Stop if we've reached total marks
            if marks_distributed >= total_marks:
                break
        
        return questions

    def _generate_short_answer_question(self, sentence: str) -> str:
        """Generate a short answer question"""
        # Extract key entities or concepts
        doc = self.nlp(sentence)
        entities = [ent.text for ent in doc.ents if ent.label_ in ['ORG', 'PERSON', 'GPE', 'PRODUCT']]
        
        if entities:
            return f"Briefly explain the role of {random.choice(entities)} in the given context."
        
        # Fallback to a generic short question
        return f"Provide a concise explanation of: {sentence}"

    def _generate_long_answer_question(self, sentence: str) -> str:
        """Generate a long answer question"""
        doc = self.nlp(sentence)
        
        # Look for complex sentences with multiple clauses
        if len(doc.sents) > 1 or len(sentence.split()) > 20:
            return f"Discuss in detail: {sentence}"
        
        return None

    def _generate_conceptual_question(self, sentence: str) -> str:
        """Generate a conceptual question"""
        doc = self.nlp(sentence)
        
        # Look for sentences with abstract concepts
        abstract_keywords = [
            'impact', 'significance', 'role', 'importance', 
            'relationship', 'influence', 'connection'
        ]
        
        for keyword in abstract_keywords:
            if keyword in sentence.lower():
                return f"Critically analyze the {keyword} of the following concept: {sentence}"
        
        return f"Provide a comprehensive analysis of: {sentence}"