import re
from datetime import date
import datefinder
import fitz
import pdfx
import os

import spacy
from spacy.matcher import Matcher

import geotext
from phonenumbers import PhoneNumberMatcher
import pdfminer
from pdfminer.high_level import extract_text

class ExtractResumeInfo:
    
    RESUME_SECTIONS = ['skills',"education","work","experience",'work experience','study']

    def __init__(self,pdf_path):
        self.pdf_path = pdf_path


    def extract_text_from_pdf(self):
        text = extract_text(self.pdf_path)
        return text



    
    def get_date(self,txt):
        '''Get date from text'''
        matches = list(datefinder.find_dates(txt))
        res = []
        for i in matches:
            date_str = str(i).split(' ')
            extracted_date = date_str[0]
            res.append(extracted_date)
        return res


    def get_years(self,txt):
        '''Get years from text'''
        pattern = r'19[0-9]{2}|20[0-9]{2}'
        lst = re.findall(pattern, txt)
    
        current_date = date.today()
        current_year = current_date.year
        res = []
        for i in lst:
            year = int(i)
            if 1900 <= year <= (current_year + 10):
                res.append(i + "-01-01")
        return res
    
    
    def get_duration(self,txt):
        '''Get duration from text'''
    
        # dates = get_date(input_text)
        years = get_years(txt)
    
        # for i in years:
        #     years.append(i)
        years.sort()
    
        duration = {
            "start_date": "",
            "end_date": ""
        }
        if len(dates) > 1:
            duration["start_date"] = years[0]
            duration["end_date"] = years[len(years) - 1]
        return duration


    def get_urls_from_pdf(self):
        '''extract urls from pdf file'''
        url_list = []
    
        # for invalid file path
        if os.path.exists(self.pdf_path) is False:
            return url_list
    
        pdf = pdfx.PDFx(self.pdf_path)
    
        # get urls
        pdf_url_dict = pdf.get_references_as_dict()
    
        if "url" not in pdf_url_dict.keys():
            return url_list
    
        url_list = pdf_url_dict["url"]
    
        return url_list

    def extract_name(self,txt):
        nlp = spacy.load('en_core_web_sm')
        matcher = Matcher(nlp.vocab)
    
        # Define name patterns
        patterns = [
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name and Last name
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name, Middle name, and Last name
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # First name, Middle name, Middle name, and Last name
            # Add more patterns as needed
        ]
    
        for pattern in patterns:
            matcher.add('NAME', patterns=[pattern])
    
        doc = nlp(txt)
        matches = matcher(doc)
    
        for match_id, start, end in matches:
            span = doc[start:end]
            return span.text
    
        return None

    def get_address(self,input_text):
        '''get address information from input array'''
    
        # input_text = " \n ".join(input_arr)
    
        res = {}
        # getting all countries
        countries_dict = geotext.GeoText(input_text).country_mentions
        res["country"] = []
        for i in countries_dict:
            res["country"].append(i)
    
        # getting all cities
        res["city"] = geotext.GeoText(input_text).cities
    
        # zip code
        pattern = "\b([1-9]{1}[0-9]{5}|[1-9]{1}[0-9]{2}\\s[0-9]{3})\b"
        res["zipcode"] = re.findall(pattern, input_text)
        if res['country']:
            self.country_code = res['country'][0]
            return res['country'][0]
        else:
            self.country_code = ''
            if res['city']:
                return res['city'][0]
            else:
                return "No country found"
        self.country_code = ''
        return None

    def get_phone(self,input_text):
        '''extract phone number from text'''
    
        phone_numbers = []
    
        countries_dict = geotext.GeoText(input_text).country_mentions
        
        # country_code = "SG"
        for i in countries_dict.items():
            country_code = i[0]
            break
    
        search_result = PhoneNumberMatcher(input_text,'' )
    
        phone_number_list = []
        for i in search_result:
            i = str(i).split(' ')
            match = i[2:]
    
            phone_number = ''.join(match)
            phone_number_list.append(phone_number)
    
        for i in phone_number_list:
            if i not in phone_numbers:
                phone_numbers.append(i)
    
        return phone_numbers


    def get_email(self,input_text):
        '''extract email from text'''
        email_pattern = '[^\s]+@[^\s]+[.][com]+'
    
        emails = []
        emails = re.findall(email_pattern, input_text)
    
        # pick only unique emails
        emails = set(emails)
        emails = list(emails)
    
        return emails


    
    def extract_resume_sections(self,text):
        '''Extract section based on resume heading keywords'''
        text_split = [i.strip() for i in text.split('\n')]
    
        entities = {}
        entities["extra"] = []
        key = 'extra'
        for sent in text_split:
            if len(sent.split(" "))<=3:
                for word in sent.lower().split(" "):
                    if word in  ExtractResumeInfo.RESUME_SECTIONS:
                        key = word
                        entities[key]=[]
                        break
                continue
            if sent:
                entities[key].append(sent)
        return entities
        
    def extract_education_from_resume(self,text):
        education = []
    
        # Use regex pattern to find education information Institute 
        pattern = r"(?i)(?:Bsc|\bB\.\w+|\bM\.\w+|\bPh\.D\.\w+|\bBachelor(?:'s)?|\bMaster(?:'s)?|\bcollege(?:'s)?|\binstitute(?:'s)?|\bUniversity(?:'s)?|\bPh\.D)\s(?:\w+\s)*\w+"
        matches = re.findall(pattern, text)
        for match in matches:
            education.append(match.strip())
    
        return education


    def get_percentage(self,txt):
        '''Extract percentage from text'''
        pattern = r'((\d+\.)?\d+%)'
        lst = re.findall(pattern, txt)
        lst = [i[0] for i in lst]
        return lst
    
    
    def get_gpa(self,txt):
        '''Extract cgpa or gpa from text in format x.x/x'''
        pattern = r'((\d+\.)?\d+\/\d+)'
        lst = re.findall(pattern, txt)
        lst = [i[0] for i in lst]
        return lst
    
    
    def get_grades(self,input_text):
        '''Extract grades from text'''
        input_text = input_text.lower()
        # gpa
        gpa = get_gpa(input_text)
    
        if (len(gpa) != 0):
            return gpa

        # percentage
        percentage = get_percentage(input_text)
    
        if (len(percentage) != 0):
            return percentage
    
        return []