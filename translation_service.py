"""
Professional Multilingual Chatbot Translation Service
Supports English, French, Kiswahili, and Kinyarwanda

Features:
- Automatic language detection from user input
- Exclusively responds in the detected language
- Uses GoogleTranslator from deep_translator for accurate translation
- Maintains natural tone, accuracy, and clarity in all supported languages
"""
from typing import Dict, List, Optional, Tuple, Any
from langdetect import detect, detect_langs, DetectorFactory
from deep_translator import GoogleTranslator
import re

# Optional, higher-quality detectors/translators
try:
    import langid
    # Lightweight, fast language id
except Exception:  # pragma: no cover
    langid = None

try:
    import pycld3
    # Google Compact Language Detector v3
except Exception:  # pragma: no cover
    pycld3 = None

# Set seed for consistent language detection
DetectorFactory.seed = 0

class TranslationService:
    def __init__(self):
        # Initialize GoogleTranslator for all translations
        try:
            self.translator = GoogleTranslator()
        except Exception as e:
            print(f"Warning: Failed to initialize GoogleTranslator: {e}")
            self.translator = None
        
        # Language mappings for supported languages
        self.language_codes = {
            'kinyarwanda': 'rw',
            'french': 'fr', 
            'kiswahili': 'sw',
            'english': 'en'
        }
        
        # Supported language codes for detection
        self.supported_languages = ['en', 'fr', 'sw', 'rw']

        # Domain glossary for consistent Kinyarwanda phrasing
        # Maps common English/French mental health phrases to preferred Kinyarwanda
        self.rw_glossary = [
            # Emergency contacts and hotlines
            (r"(?i)mental health hotline\s*:?\s*105", "umurongo wa telefone w'ubufasha mu by'ubuzima bwo mu mutwe: 105"),
            (r"(?i)ligne d'assistance en santé mentale\s*:?\s*105", "umurongo wa telefone w'ubufasha mu by'ubuzima bwo mu mutwe: 105"),
            (r"(?i)call\s*112", "hamagara 112 mu gihe cy'ibyago byihutirwa"),
            (r"(?i)emergency", "ibyago byihutirwa"),
            (r"(?i)hotline", "umurongo wa telefone"),
            (r"(?i)helpline", "umurongo wa telefone w'ubufasha"),
            
            # Hospitals and facilities
            (r"(?i)caraes\s*ndera\s*hospital", "CARAES Ndera"),
            (r"(?i)hdi\s*rwanda\s*counseling", "HDI Rwanda (Inama n'Ubujyanama)"),
            (r"(?i)arct\s*ruhuka", "ARCT Ruhuka"),
            
            # Mental health terms - comprehensive
            (r"(?i)mental health", "ubuzima bw'ubwoba"),
            (r"(?i)anxiety", "impungenge"),
            (r"(?i)depression", "agahinda kenshi"),
            (r"(?i)stress", "umunaniro w'ubwonko"),
            (r"(?i)coping strategies", "uburyo bwo kwifasha"),
            (r"(?i)suicide", "kwiyica"),
            (r"(?i)self-harm", "kwibangamira"),
            (r"(?i)trauma", "akababaro"),
            (r"(?i)ptsd", "indwara y'akababaro"),
            (r"(?i)panic", "guhangayika"),
            (r"(?i)worry", "kwitwara"),
            (r"(?i)sad", "guhangayika"),
            (r"(?i)sadness", "agahinda"),
            (r"(?i)lonely", "kubera wenyine"),
            (r"(?i)loneliness", "kwiyumva wenyine"),
            (r"(?i)hopeless", "kwiyumva nta hope"),
            (r"(?i)hopelessness", "kwiyumva nta hope"),
            (r"(?i)help", "ubufasha"),
            (r"(?i)support", "ubufasha"),
            (r"(?i)feeling", "kwiyumva"),
            (r"(?i)feelings", "imyumvire"),
            (r"(?i)emotion", "imyumvire"),
            (r"(?i)emotions", "imyumvire"),
            (r"(?i)counseling", "ubujyanama"),
            (r"(?i)therapy", "ubuvuzi"),
            (r"(?i)psychologist", "muganga w'ubuzima bw'ubwoba"),
            (r"(?i)psychiatrist", "muganga w'ubuzima bw'ubwoba"),
            (r"(?i)counselor", "umujyanama"),
            (r"(?i)professional", "umuhanga"),
            (r"(?i)session", "isaha"),
            (r"(?i)appointment", "gahunda"),
            (r"(?i)emergency", "ibyago byihutirwa"),
            (r"(?i)urgent", "byihutirwa"),
            (r"(?i)crisis", "ibyago"),
            (r"(?i)hospital", "ivuriro"),
            (r"(?i)doctor", "muganga"),
            (r"(?i)patient", "umuvurwa"),
            (r"(?i)treatment", "ubuvuzi"),
            (r"(?i)medication", "imiti"),
            (r"(?i)medicine", "imiti"),
            (r"(?i)sleep", "guhaguruka"),
            (r"(?i)insomnia", "kutagira amahoro mu cyaro"),
            (r"(?i)nightmare", "inzara"),
            (r"(?i)pain", "ububabare"),
            (r"(?i)hurt", "guhumeka"),
            (r"(?i)worry", "kwitwara"),
            (r"(?i)concern", "kwitwara"),
            (r"(?i)problem", "ikibazo"),
            (r"(?i)issue", "ikibazo"),
            (r"(?i)difficulty", "ingorane"),
            (r"(?i)challenge", "ingorane"),
            (r"(?i)better", "byiza"),
            (r"(?i)worse", "bibi"),
            (r"(?i)improve", "gukemura"),
            (r"(?i)recovery", "gukira"),
            (r"(?i)healing", "gukira"),
            (r"(?i)well-being", "ubuzima bwiza"),
            (r"(?i)wellbeing", "ubuzima bwiza"),
            (r"(?i)health", "ubuzima"),
            (r"(?i)mind", "ubwonko"),
            (r"(?i)brain", "ubwonko"),
            (r"(?i)thought", "igitekerezo"),
            (r"(?i)thoughts", "imitekerezo"),
            (r"(?i)thinking", "gukeka"),
            (r"(?i)memory", "kwibuka"),
            (r"(?i)remember", "kwibuka"),
            (r"(?i)forget", "kwibagirwa"),
            (r"(?i)family", "umuryango"),
            (r"(?i)friend", "inshuti"),
            (r"(?i)friends", "inshuti"),
            (r"(?i)relationship", "ukwiyunga"),
            (r"(?i)work", "akazi"),
            (r"(?i)job", "akazi"),
            (r"(?i)school", "ishuri"),
            (r"(?i)study", "kwiga"),
            (r"(?i)learn", "kwiga"),
            (r"(?i)today", "uyu munsi"),
            (r"(?i)tomorrow", "ejo hazaza"),
            (r"(?i)yesterday", "ejo hashize"),
            (r"(?i)now", "ubu"),
            (r"(?i)here", "hano"),
            (r"(?i)there", "aho"),
            (r"(?i)where", "he"),
            (r"(?i)when", "ryari"),
            (r"(?i)how", "ni gute"),
            (r"(?i)what", "iki"),
            (r"(?i)why", "kubera iki"),
            (r"(?i)who", "nde"),
            (r"(?i)yes", "yego"),
            (r"(?i)no", "oya"),
            (r"(?i)thank you", "murakoze"),
            (r"(?i)thanks", "murakoze"),
            (r"(?i)please", "murakoze"),
            (r"(?i)sorry", "ndamukanya"),
            (r"(?i)hello", "muraho"),
            (r"(?i)hi", "muraho"),
            (r"(?i)goodbye", "murabeho"),
            (r"(?i)good morning", "mwaramutse"),
            (r"(?i)good afternoon", "mwiriwe"),
            (r"(?i)good evening", "mwiriwe"),
            (r"(?i)good night", "murabeho"),
            (r"(?i)i am", "ndi"),
            (r"(?i)i'm", "ndi"),
            (r"(?i)i have", "mfite"),
            (r"(?i)i can", "ndashobora"),
            (r"(?i)i will", "nzajya"),
            (r"(?i)i would", "nzajya"),
            (r"(?i)i need", "nkeneye"),
            (r"(?i)i want", "nshaka"),
            (r"(?i)i feel", "nkwiyumva"),
            (r"(?i)how are you", "muraho"),
            (r"(?i)how do you", "ni gute"),
            (r"(?i)can you", "murashobora"),
            (r"(?i)could you", "murashobora"),
            (r"(?i)would you", "murashobora"),
            (r"(?i)should i", "ni ngomba"),
            (r"(?i)must i", "ni ngomba"),
            (r"(?i)contact", "guhamagara"),
            (r"(?i)call", "guhamagara"),
            (r"(?i)phone", "telefone"),
            (r"(?i)number", "nimero"),
            (r"(?i)address", "aho uri"),
            (r"(?i)location", "aho uri"),
            (r"(?i)district", "akarere"),
            (r"(?i)province", "intara"),
            (r"(?i)city", "umujyi"),
            (r"(?i)town", "umujyi"),
            (r"(?i)village", "umudugudu"),
            (r"(?i)rwandan", "w'u Rwanda"),
            (r"(?i)rwanda", "Rwanda"),
            (r"(?i)kigali", "Kigali"),
            (r"(?i)available", "birashoboka"),
            (r"(?i)available now", "birashoboka ubu"),
            (r"(?i)immediate", "bwihuse"),
            (r"(?i)immediately", "bwihuse"),
            (r"(?i)soon", "vuba"),
            (r"(?i)later", "nyuma"),
            (r"(?i)later today", "nyuma uyu munsi"),
            (r"(?i)tomorrow", "ejo hazaza"),
            (r"(?i)next week", "icyumweru gikurikira"),
            (r"(?i)next month", "ukwezi gukurikira"),
            (r"(?i)schedule", "gahunda"),
            (r"(?i)book", "kwiyandikisha"),
            (r"(?i)booking", "kwiyandikisha"),
            (r"(?i)appointment", "gahunda"),
            (r"(?i)meeting", "inama"),
            (r"(?i)consultation", "ubujyanama"),
            (r"(?i)free", "gratis"),
            (r"(?i)cost", "igiciro"),
            (r"(?i)price", "igiciro"),
            (r"(?i)fee", "igiciro"),
            (r"(?i)payment", "kwishyura"),
            (r"(?i)pay", "kwishyura"),
            (r"(?i)money", "amafaranga"),
            (r"(?i)currency", "amafaranga"),
            (r"(?i)rwf", "amafaranga y'u Rwanda"),
            (r"(?i)rwandan franc", "amafaranga y'u Rwanda"),
            (r"(?i)hour", "isaha"),
            (r"(?i)hours", "amasaha"),
            (r"(?i)minute", "umunota"),
            (r"(?i)minutes", "iminota"),
            (r"(?i)day", "umunsi"),
            (r"(?i)days", "iminsi"),
            (r"(?i)week", "icyumweru"),
            (r"(?i)weeks", "iminsi"),
            (r"(?i)month", "ukwezi"),
            (r"(?i)months", "amezi"),
            (r"(?i)year", "umwaka"),
            (r"(?i)years", "imyaka"),
            (r"(?i)age", "imyaka"),
            (r"(?i)old", "mukuru"),
            (r"(?i)young", "muto"),
            (r"(?i)child", "umwana"),
            (r"(?i)children", "abana"),
            (r"(?i)teenager", "umukobwa cyangwa umuhungu"),
            (r"(?i)teen", "umukobwa cyangwa umuhungu"),
            (r"(?i)adult", "umukuru"),
            (r"(?i)adults", "abakuru"),
            (r"(?i)elderly", "abakuru"),
            (r"(?i)senior", "umukuru"),
            (r"(?i)man", "umugabo"),
            (r"(?i)men", "abagabo"),
            (r"(?i)woman", "umugore"),
            (r"(?i)women", "abagore"),
            (r"(?i)boy", "umuhungu"),
            (r"(?i)boys", "abahungu"),
            (r"(?i)girl", "umukobwa"),
            (r"(?i)girls", "abakobwa"),
            (r"(?i)person", "umuntu"),
            (r"(?i)people", "abantu"),
            (r"(?i)someone", "umuntu"),
            (r"(?i)anyone", "umuntu"),
            (r"(?i)everyone", "abantu bose"),
            (r"(?i)everybody", "abantu bose"),
            (r"(?i)nobody", "nta muntu"),
            (r"(?i)no one", "nta muntu"),
            (r"(?i)someone else", "undi muntu"),
            (r"(?i)other", "undi"),
            (r"(?i)others", "abandi"),
            (r"(?i)another", "undi"),
            (r"(?i)different", "bidatanye"),
            (r"(?i)same", "kimwe"),
            (r"(?i)similar", "bifitanye"),
            (r"(?i)like", "nk'"),
            (r"(?i)unlike", "nta kintu"),
            (r"(?i)different from", "bidatanye na"),
            (r"(?i)same as", "kimwe na"),
            (r"(?i)similar to", "bifitanye na"),
            (r"(?i)like this", "nk'ibi"),
            (r"(?i)like that", "nk'aho"),
            (r"(?i)this way", "nk'ubu"),
            (r"(?i)that way", "nk'aho"),
            (r"(?i)here", "hano"),
            (r"(?i)there", "aho"),
            (r"(?i)where", "he"),
            (r"(?i)when", "ryari"),
            (r"(?i)how", "ni gute"),
            (r"(?i)what", "iki"),
            (r"(?i)why", "kubera iki"),
            (r"(?i)who", "nde"),
            (r"(?i)which", "iki"),
            (r"(?i)whose", "wa nde"),
            (r"(?i)whom", "nde"),
            
            # Common phrases that get mistranslated
            (r"(?i)pour\s+", ""),  # Remove French "pour"
            (r"(?i)avec\s+", ""),  # Remove French "avec"
            (r"(?i)sans\s+", ""),  # Remove French "sans"
            (r"(?i)dans\s+", ""),  # Remove French "dans"
            (r"(?i)sur\s+", ""),  # Remove French "sur"
            (r"(?i)car\s+", ""),  # Remove French "car"
            (r"(?i)donc\s+", ""),  # Remove French "donc"
            (r"(?i)mais\s+", ""),  # Remove French "mais"
            (r"(?i)ku bihano[,\s]*", ""),
            (r"(?i)komeza amajwi make ariko akunze", ""),
            
            # Fix common translation artifacts
            (r"\bje\s+suis\b", ""),  # Remove French "je suis"
            (r"\bje\s+vais\b", ""),  # Remove French "je vais"
            (r"\btrès\s+bien\b", ""),  # Remove French "très bien"
            (r"\bcomment\s+allez-vous\b", ""),  # Remove French "comment allez-vous"
            (r"\bça\s+va\b", ""),  # Remove French "ça va"
        ]

    def detect_language(self, text: str) -> str:
        """
        Backwards-compatible language detection helper.
        """
        result = self.detect_language_confidence(text)
        return result["language"]

    def detect_language_confidence(self, text: str) -> Dict[str, Any]:
        """
        Advanced language detection returning both language and confidence score.
        Combines pattern heuristics, multiple detectors, and contextual signals.
        """
        scores = {lang: 0.0 for lang in self.supported_languages}
        reasons: Dict[str, List[str]] = {lang: [] for lang in self.supported_languages}
        baseline_language = 'en'
        baseline_confidence = 0.25
        
        if not text or not text.strip():
            return {
                "language": baseline_language,
                "confidence": 0.0,
                "source": "empty",
                "scores": scores,
                "reasons": reasons
            }
        
        cleaned_text = re.sub(r'[^\w\s]', '', text.strip().lower())
        if len(cleaned_text) < 2:
            return {
                "language": baseline_language,
                "confidence": baseline_confidence,
                "source": "short_text",
                "scores": scores,
                "reasons": reasons
            }
        
        def _add_score(lang: str, value: float, reason: str):
            if lang not in scores:
                return
            scores[lang] += value
            reasons[lang].append(reason)
        
        # Pattern heuristics
        try:
            pattern_lang = self._detect_by_patterns(text)
            if pattern_lang:
                _add_score(pattern_lang, 0.55, "pattern_match")
        except Exception as e:
            print(f"Pattern detection error: {e}")
        
        # Strong token heuristics per language
        text_lower = text.lower()
        if self._has_strong_kinyarwanda_tokens(text_lower):
            _add_score('rw', 0.25, "strong_kinyarwanda_tokens")
        if self._has_strong_french_tokens(text_lower):
            _add_score('fr', 0.2, "strong_french_tokens")
        if self._has_strong_kiswahili_tokens(text_lower):
            _add_score('sw', 0.2, "strong_kiswahili_tokens")
        if self._is_common_greeting(text):
            _add_score('en', 0.1, "common_greeting")
        
        # langdetect probabilities
        try:
            lang_probs = detect_langs(text)
            for idx, langprob in enumerate(lang_probs[:3]):
                mapped = self._map_code(langprob.lang)
                if mapped in scores:
                    weight = max(0.05, langprob.prob * 0.35)
                    _add_score(mapped, weight, f"langdetect:{langprob.prob:.2f}")
                    if idx == 0 and langprob.prob > 0.95:
                        break
        except Exception as e:
            print(f"langdetect error: {e}")
        
        # langid fallback
        if langid:
            try:
                lid_lang, lid_prob = langid.classify(text)
                mapped = self._map_code(lid_lang)
                if mapped in scores:
                    weight = lid_prob * 0.25
                    _add_score(mapped, weight, f"langid:{lid_prob:.2f}")
            except Exception as e:
                print(f"langid error: {e}")
        
        # pycld3 detector
        if pycld3:
            try:
                prediction = pycld3.get_language(text)
                if prediction and prediction.is_reliable:
                    mapped = self._map_code(prediction.language)
                    if mapped in scores:
                        weight = min(0.25, prediction.probability * 0.25)
                        _add_score(mapped, weight, f"pycld3:{prediction.probability:.2f}")
            except Exception as e:
                print(f"pycld3 error: {e}")
        
        # Ensure baseline score
        scores[baseline_language] = max(scores[baseline_language], baseline_confidence)
        
        best_language = max(scores, key=scores.get)
        best_score = min(1.0, round(scores[best_language], 3))
        
        return {
            "language": best_language,
            "confidence": best_score,
            "source": "ensemble",
            "scores": scores,
            "reasons": reasons
        }
    
    def _detect_by_patterns(self, text: str) -> str:
        """
        Detect language using comprehensive pattern matching for better accuracy
        """
        text_lower = text.lower().strip()
        
        # Count matches for each language to determine the strongest signal
        language_scores = {'rw': 0, 'fr': 0, 'sw': 0, 'en': 0}
        
        # Kinyarwanda patterns - more comprehensive
        kinyarwanda_patterns = [
            r'\b(muraho|murakaza|murabe|murakoze|mwiriwe|mwaramutse|murakaza neza|muraho rwose|muraho neza)\b',
            r'\b(ndabizi|ntabwo|ndabishaka|ndabishimira|ndabishimye|ndabishimye cyane|ndumva)\b',
            r'\b(umunsi|umunsi mwiza|umunsi mubi|ejo|ejo hazaza|ejo hashize|uyu munsi)\b',
            r'\b(amahoro|amahoro yose|amahoro yanyu|amahoro yanjye)\b',
            r'\b(ubwoba|ubwoba bubabaje|ubwoba bunyuma|ubwoba bwinshi|umutwe|umereye|nabi)\b',
            r'\b(umutima|umutima wanjye|umutima wanyu|umutima wanjye)\b',
            r'\b(ubuzima|ubuzima bwiza|ubuzima bubi|ubuzima bwinshi)\b',
            r'\b(nshaka|ntabwo|ndabizi|ndabishimira|ndabishimye|ndumva|ndabishimye)\b',
            r'\b(jewe|wewe|we|jewe|twebwe|mwebwe|bo)\b',
            r'\b(murakoze|murakoze cyane|murakoze cane|murakoze rwose)\b',
            r"\b(ntabwo|ntabwo bimeze|ntabwo bimeze nk'uko)\b",
            r'\b(umutwe|umereye|nabi|ndumva|cyane|rwose|neza)\b'
        ]
        
        # French patterns - more comprehensive
        french_patterns = [
            r'\b(bonjour|bonsoir|salut|bonne journée|bonne soirée)\b',
            r'\b(merci|merci beaucoup|merci bien|de rien)\b',
            r'\b(comment allez-vous|comment ça va|ça va bien|ça va mal)\b',
            r'\b(je suis|je vais|je peux|je veux|je dois|je fais)\b',
            r'\b(très bien|très mal|pas mal|comme ci comme ça|ça va)\b',
            r'\b(anxieux|anxieuse|déprimé|déprimée|stressé|stressée)\b',
            r"\b(depuis|pendant|maintenant|hier|demain|aujourd'hui)\b",
            r'\b(problème|difficulté|souci|inquiétude|santé mentale)\b',
            r'\b(santé|mental|psychologique|émotionnel|psychologue)\b',
            r'\b(avec|sans|pour|dans|sur|sous|entre|parmi)\b',
            r'\b(et|ou|mais|donc|car|ni|puis)\b'
        ]
        
        # Kiswahili patterns - more comprehensive
        kiswahili_patterns = [
            r'\b(hujambo|hamjambo|habari|habari yako|habari za asubuhi|habari za mchana)\b',
            r'\b(asante|asante sana|karibu|pole|pole sana|pole kwa ajili)\b',
            r'\b(sijambo|hajambo|hatujambo|hamjambo|hawajambo)\b',
            r'\b(mimi|wewe|yeye|sisi|nyinyi|wao)\b',
            r'\b(nina|una|ana|tuna|mna|wana|niko|uko|ako|tuko|mko|wako)\b',
            r'\b(shida|matatizo|huzuni|furaha|wasiwasi|msongo wa mawazo)\b',
            r'\b(afya ya akili|moyo|roho|hisia|mawazo)\b',
            r'\b(rafiki|mpenzi|mama|baba|mtoto|mzee|mke|mume)\b',
            r'\b(leo|jana|kesho|sasa|zamani|baadaye)\b',
            r'\b(naomba|tafadhali|samahani|pole|pole sana)\b'
        ]
        
        # English patterns - to distinguish from other languages
        english_patterns = [
            r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
            r'\b(thank you|thanks|please|sorry|excuse me)\b',
            r"\b(i am|i'm|i have|i can|i will|i would)\b",
            r'\b(help|support|assistance|mental health|anxiety|depression)\b',
            r'\b(how are you|how do you|what is|where is|when is)\b'
        ]
        
        # Count pattern matches
        for pattern in kinyarwanda_patterns:
            if re.search(pattern, text_lower):
                language_scores['rw'] += 1
        
        for pattern in french_patterns:
            if re.search(pattern, text_lower):
                language_scores['fr'] += 1
        
        for pattern in kiswahili_patterns:
            if re.search(pattern, text_lower):
                language_scores['sw'] += 1
                
        for pattern in english_patterns:
            if re.search(pattern, text_lower):
                language_scores['en'] += 1
        
        # Return the language with the highest score
        if max(language_scores.values()) > 0:
            return max(language_scores, key=language_scores.get)
        
        return None

    def _map_code(self, code: str) -> str:
        """Map various detector codes into our set {en, fr, sw, rw}."""
        mapping = {
            'en': 'en', 'eng': 'en',
            'fr': 'fr', 'fra': 'fr', 'fre': 'fr',
            'sw': 'sw', 'swa': 'sw', 'swc': 'sw',
            'rw': 'rw', 'kin': 'rw',
        }
        return mapping.get(code, 'en')

    def _has_strong_kinyarwanda_tokens(self, text_lower: str) -> bool:
        """Check for strong Kinyarwanda indicators"""
        tokens = [
            'muraho', 'mwiriwe', 'mwaramutse', 'murakoze', 'ndumva',
            'ubwoba', 'umutwe', 'umereye', 'nabi', 'amahoro', 'ubuzima',
            'ndabizi', 'ntabwo', 'ndabishaka', 'ndabishimira', 'cyane', 'rwose'
        ]
        return any(t in text_lower for t in tokens)
    
    def _has_strong_french_tokens(self, text_lower: str) -> bool:
        """Check for strong French indicators"""
        tokens = [
            'bonjour', 'bonsoir', 'merci', 'comment', 'allez-vous', 'ça va',
            'je suis', 'je vais', 'je peux', 'très bien', 'très mal',
            'anxieux', 'déprimé', 'stressé', 'santé mentale', 'problème'
        ]
        return any(t in text_lower for t in tokens)
    
    def _has_strong_kiswahili_tokens(self, text_lower: str) -> bool:
        """Check for strong Kiswahili indicators"""
        tokens = [
            'hujambo', 'hamjambo', 'habari', 'asante', 'karibu', 'pole',
            'sijambo', 'hajambo', 'mimi', 'wewe', 'yeye', 'sisi', 'nyinyi',
            'nina', 'una', 'ana', 'tuna', 'mna', 'wana', 'shida', 'matatizo'
        ]
        return any(t in text_lower for t in tokens)
    
    def _is_common_greeting(self, text: str) -> bool:
        """Check if text is a common greeting that should default to English"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        return text.lower().strip() in greetings

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Professional translation using GoogleTranslator exclusively.
        Translates text to target language with high accuracy and natural tone.
        
        Args:
            text: Text to translate
            target_language: Target language code ('en', 'fr', 'sw', 'rw')
            
        Returns:
            Translated text in target language
        """
        if not text or not text.strip():
            return text
            
        if target_language == 'en':
            return text
            
        try:
            # Normalize language code for GoogleTranslator
            target_code = self._normalize_language_code(target_language)
            
            # Translate using GoogleTranslator
            if self.translator:
                translated = GoogleTranslator(source='auto', target=target_code).translate(text)
                
                # Post-process based on target language
                if target_language == 'rw':
                    translated = self.normalize_kinyarwanda(translated)
                elif target_language == 'fr':
                    translated = self.normalize_french(translated)
                elif target_language == 'sw':
                    translated = self.normalize_kiswahili(translated)
                
                return translated
            else:
                return text
                
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def _normalize_language_code(self, lang: str) -> str:
        """Normalize language code to GoogleTranslator format"""
        mapping = {
            'en': 'en', 'english': 'en',
            'fr': 'fr', 'french': 'fr', 'français': 'fr',
            'sw': 'sw', 'kiswahili': 'sw', 'swahili': 'sw',
            'rw': 'rw', 'kinyarwanda': 'rw', 'kin': 'rw', 'ikinyarwanda': 'rw'
        }
        return mapping.get(lang.lower(), 'en')

    def normalize_kinyarwanda(self, text: str) -> str:
        """
        Post-process Kinyarwanda to remove mixed-language fragments and enforce
        consistent, professional terminology using a comprehensive domain glossary.
        """
        if not text:
            return text
        
        normalized = text
        
        # First, apply glossary replacements (more specific patterns first)
        # Sort by pattern length (longer first) to avoid partial replacements
        sorted_glossary = sorted(self.rw_glossary, key=lambda x: len(x[0]), reverse=True)
        for pat, repl in sorted_glossary:
            normalized = re.sub(pat, repl, normalized, flags=re.IGNORECASE)

        # Remove common French connective phrases that sometimes leak in
        french_leak_patterns = [
            r"\b(pour|avec|sans|dans|sur|entre|car|donc|mais|ou)\s+",
            r"\b(je|tu|il|elle|nous|vous|ils|elles)\s+(suis|es|est|sommes|êtes|sont)\s+",
            r"\b(très|trop|beaucoup|peu|plus|moins)\s+",
            r"\b(comment|pourquoi|quand|où|qui|quoi)\s+",
            r"\b(ça|ce|ces|ceux|cette|cet)\s+",
            r"\b(bien|mal|bon|mauvais|meilleur|pire)\s+",
        ]
        for pat in french_leak_patterns:
            normalized = re.sub(pat, "", normalized, flags=re.IGNORECASE)

        # Remove English phrases that leak in
        english_leak_patterns = [
            r"\b(hello|hi|hey|thank you|thanks|please|sorry)\b",
            r"\b(i am|i'm|i have|i can|i will|i would)\b",
            r"\b(how are you|what is|where is|when is)\b",
        ]
        for pat in english_leak_patterns:
            normalized = re.sub(pat, "", normalized, flags=re.IGNORECASE)

        # Remove Kiswahili phrases that leak in
        kiswahili_leak_patterns = [
            r"\b(hujambo|asante|karibu|pole|sijambo)\b",
            r"\b(mimi|wewe|yeye|sisi|nyinyi|wao)\b",
        ]
        for pat in kiswahili_leak_patterns:
            normalized = re.sub(pat, "", normalized, flags=re.IGNORECASE)

        # Fix common Kinyarwanda grammar issues
        kinyarwanda_fixes = [
            (r'\b(umutima|umutima)\s+(umutima|umutima)\b', 'umutima'),  # Remove duplicate "umutima"
            (r'\b(ubuzima|ubuzima)\s+(ubuzima|ubuzima)\b', 'ubuzima'),  # Remove duplicate "ubuzima"
            (r'\b(murakoze|murakoze)\s+(murakoze|murakoze)\b', 'murakoze'),  # Remove duplicate "murakoze"
            (r'\b(ndumva|ndumva)\s+(ndumva|ndumva)\b', 'ndumva'),  # Remove duplicate "ndumva"
        ]
        for pattern, replacement in kinyarwanda_fixes:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # Trim repetitive spaces and stray punctuation
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = re.sub(r"\s+,", ",", normalized)
        normalized = re.sub(r"\s+\.", ".", normalized)
        normalized = re.sub(r"\s+\?", "?", normalized)
        normalized = re.sub(r"\s+!", "!", normalized)
        
        # Remove leading/trailing punctuation artifacts
        normalized = re.sub(r"^[,\s\.!?]+", "", normalized)
        normalized = re.sub(r"[,\s\.!?]+$", "", normalized)
        
        return normalized
    
    def normalize_french(self, text: str) -> str:
        """
        Post-process French text to ensure natural, professional tone
        """
        if not text:
            return text
            
        normalized = text
        
        # Fix common translation artifacts
        french_fixes = [
            (r'\bje suis\s+je suis\b', 'je suis'),
            (r'\btrès\s+très\b', 'très'),
            (r'\bde\s+de\b', 'de'),
            (r'\bdu\s+du\b', 'du'),
            (r'\bdes\s+des\b', 'des'),
        ]
        
        for pattern, replacement in french_fixes:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Clean up spacing and punctuation
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = re.sub(r"\s+,", ",", normalized)
        normalized = re.sub(r"\s+\.", ".", normalized)
        
        return normalized
    
    def normalize_kiswahili(self, text: str) -> str:
        """
        Post-process Kiswahili text to ensure natural, professional tone
        """
        if not text:
            return text
            
        normalized = text
        
        # Fix common translation artifacts
        kiswahili_fixes = [
            (r'\bmimi\s+mimi\b', 'mimi'),
            (r'\bwewe\s+wewe\b', 'wewe'),
            (r'\byeye\s+yeye\b', 'yeye'),
            (r'\bsisi\s+sisi\b', 'sisi'),
            (r'\bnyinyi\s+nyinyi\b', 'nyinyi'),
            (r'\bwao\s+wao\b', 'wao'),
        ]
        
        for pattern, replacement in kiswahili_fixes:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Clean up spacing and punctuation
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = re.sub(r"\s+,", ",", normalized)
        normalized = re.sub(r"\s+\.", ".", normalized)
        
        return normalized

    def get_appropriate_response(self, english_response: str, user_language: str) -> str:
        """
        Get response in the user's detected language with improved reliability.
        This is the main method for ensuring single-language responses.
        """
        if user_language == 'en' or not user_language:
            return english_response
        
        try:
            return self.translate_text(english_response, user_language)
        except Exception as e:
            print(f"Translation failed: {e}")
            return english_response
    
    def process_user_message(self, user_message: str, english_response: str) -> str:
        """
        Main method for professional multilingual chatbot.
        
        Automatically detects the user's language from their message and responds
        exclusively in that same language. This is the primary interface method.
        
        Args:
            user_message: The user's input message
            english_response: The AI-generated response in English
            
        Returns:
            Response translated to the user's detected language
        """
        if not user_message or not english_response:
            return english_response
        
        # Detect language from user's message
        detected_language = self.detect_language(user_message)
        
        print(f"User message language detected: {detected_language}")
        print(f"User message: {user_message[:100]}...")

        return self.get_appropriate_response(english_response, detected_language)

    def get_multilingual_response(self, english_response: str, user_language: str) -> Dict[str, str]:
        responses = {'en': english_response}
        for lang in ['fr', 'sw', 'rw']:
            if lang != user_language:
                responses[lang] = self.translate_text(english_response, lang)
        return responses

    def get_language_name(self, lang_code: str) -> str:
        names = {'en': 'English', 'fr': 'French', 'sw': 'Kiswahili', 'rw': 'Kinyarwanda'}
        return names.get(lang_code, 'English')
    
    def is_supported_language(self, lang_code: str) -> bool:
        return lang_code in self.supported_languages
    
    def get_supported_languages(self) -> List[str]:
        return self.supported_languages

# Global translation service instance
translation_service = TranslationService()

# Convenience function for easy integration
def translate_chatbot_response(user_message: str, english_response: str) -> str:
    """
    Convenience function for translating chatbot responses.
    
    This is the main function to use for integrating the multilingual
    chatbot functionality into your application.
    
    Args:
        user_message: The user's input message
        english_response: The AI-generated response in English
        
    Returns:
        Response translated to the user's detected language
    """
    return translation_service.process_user_message(user_message, english_response)
