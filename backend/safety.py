MIN_CARD_DIGITS = 13  
MAX_CARD_DIGITS = 19
PUNCTUATION = [":", "=", ".", ",", "?", "!", "-", "_", "/", "\\"] #replace with spaces to detect

from language_support import expand_bangla_banglish_text, normalize_bangla_digits

SAFETY_RESPONSE = ( #warning text
    "For your security, please do not share OTP, PIN, password, CVV, "
    "full card number or other sensitive banking details. "
    "For account-specific help, please contact official Eastern Bank PLC support "
    "or visit your nearest branch."
)


def contains_sensitive_data(message: str) -> bool: #if a text is unsafe
    """Return True if the user's message contains sensitive banking data."""

    if not message:
        return False #empty text is not sensitive

    text = clean_text(message) #normalize the text before checking

    if has_number_after(text, "otp", 4, 8): 
        return True
    if has_number_after(text, "pin", 4, 8):
        return True
    if has_number_after(text, "cvv", 3, 4):
        return True
    if has_text_after(text, "password"):
        return True
    if has_text_after(text, "passcode"):
        return True

    if has_card_number(text):
        return True 

    return False #no sensitive pattern


def has_number_after(text: str, word: str, min_digits: int, max_digits: int) -> bool: #if a specifc word followed by a number with a valid length.
    digits = only_digits(text_after(text, word))  #gets only digits after the target word

    return min_digits <= len(digits) <= max_digits #true if digit count is suspicious or matches


def has_text_after(text: str, word: str) -> bool: #comes after a word like password or passcode
    return text_after(text, word).strip() != ""


def has_card_number(text: str) -> bool:
    digits = only_digits(text) #remove everything expect digits

    return MIN_CARD_DIGITS <= len(digits) <= MAX_CARD_DIGITS 


def text_after(text: str, word: str) -> str:
    search_word = f" {word} " #add spaces around the word 

    if search_word not in text:
        return "" #return empty string

    return text.split(search_word, 1)[1] #if founf return eveything after that word


def clean_text(text: str) -> str: #prepares the text to make checking easier 
    text = normalize_bangla_digits(expand_bangla_banglish_text(text)).lower() #all letters to lowercase

    for symbol in PUNCTUATION: #replace pun with spaces
        text = text.replace(symbol, " ")

    return f" {text} "


def only_digits(text: str) -> str:
    return "".join(character for character in text if character.isdigit()) #Builds and returns a new string with digits only.


def get_safety_response() -> str:
    return SAFETY_RESPONSE
