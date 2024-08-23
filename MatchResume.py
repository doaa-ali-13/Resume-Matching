from sentence_transformers import SentenceTransformer
import spacy
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import ExtractResumeInfo
from skillsextraction import get_skills, getSkills, unique_skills, getTitles
import fitz,sys
from deep_translator import GoogleTranslator

nlp = spacy.load('en_core_web_sm')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def preprocess_text(text):
    doc = nlp(text)
    preprocessed_text = " ".join([token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha])
    return preprocessed_text

def match_resume_job(resume_text, job_description_text):
#     nlp = spacy.load('en_core_web_sm')

    # Preprocess texts
    preprocessed_resume = preprocess_text(resume_text)
    preprocessed_job_description = preprocess_text(job_description_text)
    # Keyword matching
    resume_keywords = set([token.lemma_.lower() for token in nlp(preprocessed_resume) if token.pos_ != 'VERB'])
    job_description_keywords = set([token.lemma_.lower() for token in nlp(preprocessed_job_description) if token.pos_ != 'VERB'])
    if len(job_description_keywords):
        keyword_match_score = len(resume_keywords.intersection(job_description_keywords)) / (len(job_description_keywords)+0.001)
    else:
        keyword_match_score = 0

    sentences = [preprocessed_job_description,preprocessed_resume]
    embeddings = model.encode(sentences)
    similarity_score = cosine_similarity(embeddings)[0][1]
    # Combine the scores and return as a dictionary
    scores = {
        'keyword_match_score': keyword_match_score,
        'similarity_score': similarity_score
    }

    return scores


def evaluate_resume(matching_scores,keyword_match_threshold = 0.5, similarity_threshold = 0.6):

    

    return  keyword_match_threshold * matching_scores['keyword_match_score'] + (1-keyword_match_threshold) * matching_scores['similarity_score']


def matchSkills(jS,rS):
    score = 0
    mS = []
    for x in jS:
        if x in rS:
            mS.append(x)
            score += 1
    req_skills_len = len(jS)
    match = len(jS.intersection(rS)) / (len(jS)+0.001)


    similarity_score = 0
    embeddings = model.encode([' '.join(jS),' '.join(rS)])
    similarity_score += cosine_similarity(embeddings)[0][1]

    scores = {
        'keyword_match_score': match,
        'similarity_score': similarity_score
    }
    return scores,mS


def matchResumes(filesPath,jobDSC,jobtitle):
#     translator = google_translator()
#     detected_language = translator.detect(jobDSC)
#     translated = translator.translate(jobDSC, lang_tgt='en')
#     if detected_language[0] == 'ar':
#     jobDSC = GoogleTranslator(source='auto', target='en').translate(jobDSC)

    candidates= {'name':[],'email':[],'degree':[],'matched_skills': [],'skill_score':[],'overAll_score':[]}
    for i in filesPath:
        path = i.candidate_resume_path
        name = i.candidate_name
        email = i.candidate_email
        extractor = ExtractResumeInfo.ExtractResumeInfo(path)
        txt = extractor.extract_text_from_pdf()
#         translated = translator.translate(txt, dest='en')
#         detected_language = translator.detect(txt)
#         if etected_language[0] == 'ar':
#         txt = GoogleTranslator(source='auto', target='en').translate(txt)
        tt, ss = getTitles(txt,jobtitle)
        if ss>0.6:
                degree = extractor.extract_education_from_resume(txt)
                sections = extractor.extract_resume_sections(txt)

                jobSkills = getSkills(jobDSC)
                resumeSkills = getSkills(txt)

                skillScore,mS = matchSkills(jobSkills,resumeSkills)
                skillFinalScore = evaluate_resume(skillScore)

                scores = match_resume_job(txt,jobDSC)
                finalScore = evaluate_resume(scores)

                if degree:
                    candidates['degree'].append(degree[0])
                else:
                    candidates['degree'].append('Not Found')
                candidates['email'].append(email)
                candidates['name'].append(name)
                if mS :
                    candidates['matched_skills'].append(mS)
                else:
                    candidates['matched_skills'].append('Not FOUND')
                candidates['skill_score'].append(skillFinalScore)
                candidates['overAll_score'].append((0.3 * finalScore)+(0.7 * skillFinalScore))
        else:
                candidates['email'].append(email)
                candidates['name'].append(name)
                candidates['matched_skills'].append('Not FOUND')
                candidates['degree'].append('Not FOUND')
                candidates['skill_score'].append(0)
                candidates['overAll_score'].append(0)
    df = pd.DataFrame(candidates)
    
    
        
        
        

    return df.sort_values(by=['overAll_score'], ascending=False)
        