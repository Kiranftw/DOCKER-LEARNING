import google.generativeai as genai
import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from flask import render_template
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Any
import pytesseract
from typing import List, Dict
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
from dotenv import load_dotenv, find_dotenv
from json import JSONDecodeError
from functools import wraps
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from PIL import Image
from pymongo import MongoClient

@staticmethod
def ExceptionHandeler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as E:
            print(f"An error occurred: {E}")
    return wrapper

class ResumeAnalytics(object):
    def __init__(self, modelname: str = 'gemini-2.0-flash', chatmodel = "gemma-1.1-7b-it") ->None:
        load_dotenv(find_dotenv())          
        self.__API = os.getenv("GOOGLE_API_KEY")
        if not self.__API:
            raise ValueError("API key not found. Please set the GEMINIAPI environment variable.")
        genai.configure(api_key = self.__API)
        self.outputsFOLDER = "outputs"
        for model in genai.list_models():
            pass
        self.model: genai.GenerativeModel = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash",
            generation_config={
                "response_mime_type":"application/json"
            }
        )
    
    @ExceptionHandeler
    def datacleaning(self, textfile: str) -> str:
        if not textfile or textfile.strip() == "":
            return ""
        
        text = textfile
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\x00-\x7F]', ' ', text)
        text = re.sub(r'[-–]', ' ', text) 
        text = re.sub(r'(\w)[|](\w)', r'\1, \2', text)

        text = text.replace(" - ", "\n- ").replace(":", ":\n")
        return text.strip
    
    @ExceptionHandeler
    def documentParser(self, resume: str) -> str:
        if not os.path.exists(resume):
            raise FileNotFoundError(f"The file {resume} does not exist.")
        data: str = ""
        if resume.endswith(".pdf"):
            loader = PyMuPDFLoader(resume)
            data = loader.load()
            return data
        else:
            raise ValueError("Invalid file typ!")
        
    @ExceptionHandeler
    def resumeanalytics(self, resumepath: str) -> Optional[Dict[str, Any]]:
        resume = self.documentParser(resumepath)
        self.outputsFOLDER = "outputs"
     
        if not os.path.exists(self.outputsFOLDER):
            os.makedirs(self.outputsFOLDER, exist_ok=True)
        filename = os.path.basename(resumepath).split(".")[0]
        savePath = f"{os.path.join(self.outputsFOLDER,filename)}.json"
        prompt = f"""analyze the following{resume} and parse it in JSON"""
        try:
            response = self.model.generate_content(prompt)
            response.resolve()
            responseJSON = json.loads(response.text)
            print(responseJSON)
            with open(savePath, "w", encoding="utf-8") as file:
                json.dump(responseJSON, file, indent=4, ensure_ascii=False)
            print(f"JSON file saved: {savePath}")
            return responseJSON
        except Exception as e:
            print(f"Error in resumeanalytics: {e}")
            return None

if __name__ == "__main__":
    object = ResumeAnalytics()
    resume = input("[FILE:]")
    data = object.resumeanalytics(resume)
