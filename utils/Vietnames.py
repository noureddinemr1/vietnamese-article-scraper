import re
def is_vietnamese_text(text,vietnames_patterns):
        if not text or len(text) < 50:
            return False, 0.0
        
        # Count Vietnamese characters
        vietnamese_chars = len(re.findall(vietnames_patterns[0], text))
        total_alpha_chars = len(re.findall(r'[a-zA-ZàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ]', text))
        
        if total_alpha_chars == 0:
            return False, 0.0
        
        vietnamese_char_ratio = vietnamese_chars / total_alpha_chars
        
        # Count Vietnamese words
        vietnamese_words = len(re.findall(vietnames_patterns[1], text, re.IGNORECASE))
        total_words = len(text.split())
        
        vietnamese_word_ratio = vietnamese_words / max(total_words, 1)
        
        # Check for common Vietnamese phrases
        vietnamese_phrases = [
            r'\bviệt nam\b', r'\btheo báo\b', r'\btrong khi\b', r'\bngười dân\b',
            r'\bchính phủ\b', r'\bthành phố\b', r'\bhà nội\b', r'\btphcm\b',
            r'\bngười\b', r'\bviệc\b', r'\bthời gian\b', r'\bkhu vực\b'
        ]
        
        phrase_count = 0
        for phrase in vietnamese_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                phrase_count += 1
        
        phrase_score = min(phrase_count / 4, 1.0)
        
        # Combined score - more lenient
        confidence = (vietnamese_char_ratio * 0.4 + vietnamese_word_ratio * 0.4 + phrase_score * 0.2)
        
        # Lower threshold for acceptance
        return confidence > 0.15, confidence


vietnames_patterns = [
            r'[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ]',
            r'\b(và|hoặc|với|của|trong|ngoài|trên|dưới|sau|trước|bằng|theo|về|để|cho|từ|tại|này|đó|những|các|một|hai|ba|tôi|bạn|anh|chị|em)\b'
]