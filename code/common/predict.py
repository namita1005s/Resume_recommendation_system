import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from string import punctuation
# nltk.download("stopwords")
# nltk.download("punkt")

def preprocess_text(text):
    # remove punctations
    for char in punctuation:
        text = text.replace(char,'')
    
    # Lowercase the text
    text = text.lower()

    # Tokenize the text into words
    words = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word not in stop_words]

    # Stemming using Porter Stemmer
    stemmer = SnowballStemmer(language='english')
    words = [stemmer.stem(word) for word in words]

    # Join the words back into a single string
    processed_text = " ".join(words)

    return processed_text

def recommend(text1, text2):
    processed_text1 = preprocess_text(text1)
    processed_text2 = preprocess_text(text2)

    # print("Processed Text 1:", processed_text1)
    # print("Processed Text 2:", processed_text2)

    # Example Usage for Cosine Similarity
    vectorizer = TfidfVectorizer(stop_words="english")  # Automatically remove English stopwords
    vectors = vectorizer.fit_transform([processed_text1, processed_text2])

    similarity_score = cosine_similarity(vectors[0], vectors[1])[0][0]
    # print(f"Cosine Similarity: {similarity_score}")
    return {
        'recommend':similarity_score > .5,
        'similarity': similarity_score
    }




# Example Usage for Preprocessing
text1 = "This is a sample sentence for preprocessing."
text2 = "This is a sample sentence for"
recommend(text1, text2)