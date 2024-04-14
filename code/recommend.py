from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from entity_recognizer import extract_names


def match_resume_to_job(resume_text, job_text):
    # Create a tf-idf matrix of the resume and job  (text to matrix)
    tfidf = TfidfVectorizer(stop_words='english')
    # create a list of the resume and job    
    data = [resume_text, job_text]
    # create a combined matrix of the resume and job 
    mat = tfidf.fit_transform(data)
    # calculate the cosine similarity between the resume and job 
    cosine_sim = cosine_similarity(mat, mat)
    # get the match percentage
    match_percentage = cosine_sim[0][1] * 100
    # return the match percentage
    return match_percentage

def get_resume_keywords(resume_text):
    result = extract_names(resume_text)
    # remove all duplicates
    result = list(set(result))
    return result