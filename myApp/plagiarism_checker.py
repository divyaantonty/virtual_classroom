from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import difflib  # This is a built-in module, no need to install

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

class PlagiarismAIChecker:
    def __init__(self):
        # Initialize BERT model for semantic similarity
        self.bert_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        
        # Initialize spaCy for text processing
        self.nlp = spacy.load('en_core_web_sm')
        
        # Initialize RoBERTa model for AI content detection
        self.tokenizer = AutoTokenizer.from_pretrained("roberta-base")
        self.ai_detector = AutoModelForSequenceClassification.from_pretrained("roberta-base")

    def preprocess_text(self, text):
        """Clean and preprocess text"""
        doc = self.nlp(text)
        # Remove stopwords and punctuation, convert to lowercase
        cleaned_text = ' '.join([token.text.lower() for token in doc 
                               if not token.is_stop and not token.is_punct])
        return cleaned_text

    def get_text_chunks(self, text, chunk_size=300):
        """Split text into chunks for processing"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def check_plagiarism(self, text1, text2):
        """Check plagiarism between two texts using BERT embeddings"""
        # Preprocess texts
        text1_clean = self.preprocess_text(text1)
        text2_clean = self.preprocess_text(text2)
        
        # Split into chunks
        chunks1 = self.get_text_chunks(text1_clean)
        chunks2 = self.get_text_chunks(text2_clean)
        
        # Get embeddings
        embeddings1 = self.bert_model.encode(chunks1)
        embeddings2 = self.bert_model.encode(chunks2)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings1, embeddings2)
        
        # Find maximum similarity for each chunk
        max_similarities = np.max(similarity_matrix, axis=1)
        
        # Calculate overall similarity score
        plagiarism_score = np.mean(max_similarities)
        
        # Find matching passages
        matching_passages = []
        for i, chunk1 in enumerate(chunks1):
            for j, chunk2 in enumerate(chunks2):
                if similarity_matrix[i][j] > 0.8:  # Threshold for similarity
                    matching_passages.append({
                        'text1': chunk1,
                        'text2': chunk2,
                        'similarity': similarity_matrix[i][j]
                    })
        
        return {
            'plagiarism_score': float(plagiarism_score),
            'matching_passages': matching_passages
        }

    def detect_ai_content(self, text):
        """Detect if content is AI-generated using RoBERTa"""
        chunks = self.get_text_chunks(text)
        ai_scores = []
        
        for chunk in chunks:
            # Prepare input
            inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.ai_detector(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1)
                ai_score = probabilities[:, 1].item()  # Probability of AI-generated content
                ai_scores.append(ai_score)
        
        # Calculate overall AI probability
        overall_ai_score = np.mean(ai_scores)
        
        # Analyze writing patterns
        doc = self.nlp(text)
        
        # Calculate additional metrics
        sentence_lengths = [len(sent) for sent in doc.sents]
        vocab_diversity = len(set([token.text.lower() for token in doc])) / len(doc)
        
        return {
            'ai_probability': float(overall_ai_score),
            'metrics': {
                'vocabulary_diversity': float(vocab_diversity),
                'avg_sentence_length': float(np.mean(sentence_lengths)),
                'sentence_length_variance': float(np.var(sentence_lengths))
            },
            'interpretation': self._interpret_ai_scores(overall_ai_score, vocab_diversity)
        }

    def _interpret_ai_scores(self, ai_score, vocab_diversity):
        """Interpret the AI detection scores"""
        interpretation = []
        
        if ai_score > 0.8:
            interpretation.append("High probability of AI-generated content")
        elif ai_score > 0.5:
            interpretation.append("Moderate indicators of AI-generated content")
        else:
            interpretation.append("Likely human-written content")
            
        if vocab_diversity < 0.4:
            interpretation.append("Limited vocabulary diversity (possible AI indicator)")
        elif vocab_diversity > 0.7:
            interpretation.append("High vocabulary diversity (typical of human writing)")
            
        return interpretation 