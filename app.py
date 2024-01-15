import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from PIL import Image
import numpy as np
import smart_search as ai
import template as t
import sqlalchemy
import os

from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

bot = Image.open('Images/muslim.png') 
user = Image.open('Images/man.png')

bot_avatar = np.array(bot)
human_avatar = np.array(user)

template = t.getTemplate()
prompt_template = PromptTemplate(
    input_variables=["question", "answer"],
    template=template
)

st.set_page_config(page_title="Islamic chatbot", page_icon=":bird:")
st.header("Haji Chatbot :bird:")

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613",openai_api_key=openai_api_key)

chain = LLMChain(llm=llm, prompt=prompt_template)

def generate_response(question):
	hostname = st.secrets["database"]["database_hostname"]
	username = st.secrets["database"]["database_username"]
	password = st.secrets["database"]["database_password"]
	database_name = st.secrets["database"]["database_name"]
	engine = sqlalchemy.create_engine(f"mysql+pymysql://{username}:{password}@{hostname}/{database_name}")

	with engine.connect() as conn:
		answer = ai.getExampleAnswer(conn,question)

	response = chain.run(question=question, answer=answer)
	return response

def main():
	if "messages" not in st.session_state:
		st.session_state.messages = []

	for message in st.session_state.messages:
		with st.chat_message(message["role"],avatar=message["avatar"]):
			st.markdown(message["content"]) 

	if prompt := st.chat_input("Silakan bertanya"):
		st.chat_message("user",avatar=human_avatar).markdown(prompt)
		st.session_state.messages.append({"role": "user", "content": prompt, "avatar": human_avatar})

		response = generate_response(prompt)
		#response = ai.getAnswer(prompt)
		
		with st.chat_message("assistant",avatar=bot_avatar):
			st.markdown(response)

		st.session_state.messages.append({"role": "assistant", "content": response, "avatar": bot_avatar})
		


if __name__ == "__main__":
	main()
