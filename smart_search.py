import streamlit as st
import pickle
import sqlalchemy
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fuzzywuzzy import fuzz
import os

from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def getTotalRows(conn):
    query = "SELECT * FROM questionsList"
    result = conn.execute(query)
    rows = result.fetchall()
    nums_rows = len(rows)
    return nums_rows


def findKeyword(sentence, keywords, threshold=80):
    sentence_lower = sentence.lower()
    matching_keywords = [keyword for keyword in keywords if fuzz.ratio(keyword.lower(), sentence_lower) >= threshold or keyword.lower() in sentence_lower]
    return matching_keywords

def getQuestion(conn,id):
    if not isinstance(id, int):
        id = int(id)
        
    select_query = f"SELECT Question FROM questionsList WHERE id = {id}" 
    result = conn.execute(select_query)
    question = result.fetchall()
    return question[0]

def getAnswer(conn,id):
    if not isinstance(id, int):
        id = int(id)
        
    select_query = f"SELECT Answer FROM questionsList WHERE id = {id}" 
    result = conn.execute(select_query)
    answer = result.fetchall()
    return answer[0]

def getVector(conn,id):
    if not isinstance(id, int):
        id = int(id)
        
    select_query = f"SELECT VectorizedQ FROM questionsList WHERE id = {id}" 
    result = conn.execute(select_query)
    vector_row = result.fetchone()
    if vector_row:
        vector_blob = vector_row[0]
        vector = pickle.loads(vector_blob)
        return vector
    else:
        return None
    
def vectorize(question):
    client = OpenAI()
    vector=client.embeddings.create(input = [question], model='text-embedding-ada-002')
    return vector.data[0].embedding

def _getVectorizedData(conn):
    vectorizedData = []
    rows = getTotalRows(conn)
    for i in range(1,rows+1):
        vector = getVector(conn,i)
        if vector is not None:
            vectorizedData.append(vector) 

    return vectorizedData


def getExampleAnswer(conn,question):

    #Get question vector
    question_vector = np.array(vectorize(question))
    question_vector = question_vector.reshape(1, -1)

    # Find keywords
    file_path = 'Data/keywords.txt'  

    with open(file_path, 'r') as file:
        keywords = file.readlines()

    keywords = [keyword.strip() for keyword in keywords]
    matching_keywords = findKeyword(question, keywords)
    if matching_keywords.__contains__(""):
        matching_keywords.remove("")

    print(matching_keywords)

    database_questions = getTotalRows(conn)
    relevant_questions = []
    similarities =[]

    #Find matching question with same keyword in database
    for i in range(1,database_questions+1):
        database_question = getQuestion(conn,i)
        question_keyword = all(keyword in database_question for keyword in matching_keywords)

        if question_keyword:
            database_vector = np.array(getVector(conn,i))
            database_vector = database_vector.reshape(1, -1)

            similarity_score = cosine_similarity(database_vector,question_vector)[0]
            similarities.append([similarity_score,i])
            relevant_questions.append(database_question)

    #If there is matching question
    if relevant_questions:
        similarities = sorted(similarities, key=lambda x: x[0], reverse=True)
        answer = getAnswer(conn,similarities[0][1])
        print("relevant question",similarities[0][1])

    #Else find similarity for all question
    else:
        vectorizedDataset = _getVectorizedData(conn)
        similarities = cosine_similarity(question_vector,vectorizedDataset)
        highest_score_index = np.argmax(similarities)
        highest_score = similarities[0, highest_score_index]
        answer = getAnswer(conn,highest_score_index)
        print(highest_score_index)

    return answer[0]




