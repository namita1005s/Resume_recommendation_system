from pdf2text import extract_text_from_pdf
from doctotext import extract_text_from_docx
import os
import nltk
import re

# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')
# nltk.download('stopwords')


PHONE_REG = re.compile(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]')
EMAIL_REG = re.compile(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+')


SKILLS_DB = [
        'machine learning',
        'data science',
        'python',
        'Java',
        'php',
        'web development',
    ]

def get_skills(skilllist):
    return [skill.lower() for skill in skilllist]

def extract_names(txt):
    person_names = []

    for sent in nltk.sent_tokenize(txt):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
            if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                person_names.append(
                    ' '.join(chunk_leave[0] for chunk_leave in chunk.leaves())
                )

    return person_names

def extract_phone_number(resume_text):
    phone = re.findall(PHONE_REG, resume_text)

    if phone:
        number = ''.join(phone[0])

        if resume_text.find(number) >= 0 and len(number) < 16:
            return number
    return None

def extract_emails(resume_text):
    return re.findall(EMAIL_REG, resume_text)

def extract_skills(input_text,skills):

    stop_words = set(nltk.corpus.stopwords.words('english'))
    word_tokens = nltk.tokenize.word_tokenize(input_text)

    # remove the stop words
    filtered_tokens = [w for w in word_tokens if w not in stop_words]

    # remove the punctuation
    filtered_tokens = [w for w in word_tokens if w.isalpha()]

    # generate bigrams and trigrams (such as artificial intelligence)
    bigrams_trigrams = list(map(' '.join, nltk.everygrams(filtered_tokens, 2, 3)))

    # we create a set to keep the results in.
    found_skills = set()

    # we search for each token in our skills database
    for token in filtered_tokens:
        if token.lower() in get_skills(skills):
            found_skills.add(token.lower())

    # we search for each bigram and trigram in our skills database
    for ngram in bigrams_trigrams:
        if ngram.lower() in SKILLS_DB:
            found_skills.add(ngram.lower())

    return list(set(found_skills))


def extract_text_from_file(file_path):
    if not os.path.exists(file_path):
        return None
    text = extract_text_from_pdf(file_path)
    print(text)
    names = extract_names(text)
    phone_number = extract_phone_number(text)
    emails = extract_emails(text)
    skills = extract_skills(text,SKILLS_DB)
    if names and phone_number and emails and skills:
        print(names[0])
        print(phone_number)
        print(emails[0])
        print(skills)
    return text
        
if __name__ == '__main__':
    o=extract_text_from_file(r'code\data\Resume_SoftwareEng-Intern.pdf')
    print(o)