from PIL import Image
#from pytesser.pytesser import *
import pytesseract
from pytesseract import Output
import cv2
import numpy as np
import sys

from tqdm import tqdm
import shutil
import re
import os
from dotenv import load_dotenv

from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)


############### FOR DEBUGGING PURPOSES ####################
def add_text(image, result, txt, img_num):
    """
    INPUT:
    image -- np.ndarray : image stored as ndarray
    result -- dictionary: output of pytesseract.image_to_data
    txt -- list of strings to put on image
    img_num -- int: for naming the output image
    """
    for i in range(len(result['text'])):
        x = result["left"][i]
        y = result["top"][i]
        w = result["width"][i]
        h = result["height"][i]

        text = result["text"][i]
        conf = int(result["conf"][i])
        
#         if text in txt:
#             print(text, txt)
#             cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                 0.5, (0, 0, 200), 2)
        if conf > 50:
            text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    im = Image.fromarray(image)
    im.save("all_boxes_with_text_{}.jpg".format(img_num))  
    return
  
  
def draw_squares(image, result):
    """
    INPUT:
    image -- np.ndarray : image stored as ndarray
    result -- dictionary: output of pytesseract.image_to_data
    """
    for i in range(len(result['text'])):
        x = result["left"][i]
        y = result["top"][i]
        w = result["width"][i]
        h = result["height"][i]

        text = result["text"][i]
        conf = int(result["conf"][i])
        if conf > 50:
            text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            #cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
             #   0.5, (0, 0, 200), 2)
    im = Image.fromarray(image)
    im.save("all_boxes.jpg")  
    return
  
############### END OF CODE FOR DEBUGGING PURPOSES ####################

# extract bounding box 
# ref: https://fahmisalman.medium.com/an-easy-way-of-creating-text-localization-and-detection-in-tesseract-ocr-24cc89ed6fbc
def get_possible_title(res, orig_filename, DEBUG=False):
    """
    
    INPUT
    res: dictionary, result of pytesseract.image_to_data; should contain left, top. width, height, text
    """
    max_h = 0
    former_max_h = 0
    h_diff_allowance = 7 # margin of error for max_h, since same sizes get recognised as different sometimes
    possible_title = []
    former_possible_title = []
    prev_is_possible_title = False # for the NEXT word to see whether prev is also a part of the possible title, 
    hw_ratio = 1/2
    cont_smaller = 2
    title_len_lower_lim = 3

    for i, text in enumerate(res["text"]):
        h = res["height"][i] # use this as font size
        w = res["width"][i]
        l = res["left"][i]
        t = res["top"][i]
        conf = res["conf"][i]
        if int(conf) < 50: 
            #print(text)
            continue
        if (text == " " or "") or len(text.split())==0:
            #print('-')
            continue
        elif text == "?":
            continue
        elif h/w >= hw_ratio:
            if DEBUG:
                print(text, "h/w > hw_ratio = 1/2")
            prev_is_possibel_title = False
            continue
            # if prev_is_possible_title: keep collecting words as title, this word might just be a tall rectangle
        else:
            if abs(h-max_h)<=h_diff_allowance: # h in allowable range, 
                if prev_is_possible_title==True:
                    possible_title.append({"text": text, "index": i, "height": h, "width": w, "left": l, "top": t})
                else:
                    if len(possible_title):
                        continue
                    else:
                        # initiate new title sequence
                        former_possible_title = possible_title.copy()
                        possible_title = [{"text": text, "index": i, "height": h, "width": w, "left": l, "top": t}]
                        prev_is_possible_title = True
            elif h > max_h+h_diff_allowance:
                if DEBUG:
                    print("new max found!")
                    print(text)
                # dump prev possible title, start new one
                former_max_h = max_h
                max_h = h
                former_possible_title = possible_title.copy()
                possible_title = [{"text": text, "index": i, "height": h, "width": w, "left": l, "top": t}] # store index and text
                prev_is_possible_title=True # for the next iteration to check
            else: # h < max_h-h_diff_allowance <- we're going from big text to small text
                # keep possible title, go on looking at next word
                # do nothing with max_h or possible_title
                #print("Next word is smaller in size! word: ", text)
                #print("Title so far:", join_ocr_title(possible_title))
                prev_is_possible_title=False
                # continue
                #check if prev title is a one-word title
                if len(possible_title) < title_len_lower_lim:
                    #print("Title not long enough! Reverting to prev title:", join_ocr_title(former_possible_title))
                    max_h = former_max_h
                    possible_title = former_possible_title.copy()
                    continue
        if len(possible_title) > 32:
            prev_is_possible_title=False
            possible_title = former_possible_title.copy()
        #print("possible title of this round:" , join_ocr_title(possible_title))
    if len(possible_title) == 0:
        return orig_filename
    else:
        return possible_title, former_possible_title
      
  # join ocr results as string
def join_ocr_title(poss_title):
    """
    INPUT:
    poss_title = a list of dictionaries: [{'text': , 'index': , 'height': , 'width': }, {...}, ... ] 
    
    OUTPUT:
    q_title: a string
    """
    query_title = []
    
    for t in poss_title:
        txt = t['text']
        if ':' in txt:
            txt = re.sub(':', ' - ', t['text']) #search for :, replace with - in t['text']
        if '?' in txt:
            txt = re.sub("\?", "", txt)
        if '"' in txt:
            txt = re.sub('"', "", txt)
        if "'" in txt:
            txt = re.sub("'", "", txt)
        if "’" in txt:
            txt = re.sub("’", "", txt)
        if "”" in txt:
            txt = re.sub("”", "", txt)
        query_title.append(txt)
    q_title = " ".join(query_title)
    return q_title
  
# source: https://stackoverflow.com/a/62037708
import pprint
from googleapiclient.discovery import build

# Build a service object for interacting with the API. Visit
# the Google APIs Console <http://code.google.com/apis/console>
# to get an API key for your own application.

def google_search(search_term, api_key, cse_id, **kwargs):
    term_lst = search_term.split()
    #print(term_lst)
    term_len = len(term_lst)
    if term_len > 32:
        search_term = " ".join(term_lst[term_len//2-16 : term_len//2+16])
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    try:
        return res['items']
    except KeyError:
        return res
      
  def get_n_paper_info(query_result, n):
    info_dict_lst = []
    for i in range(n):    
        info_dict = {}
        date = ""
        author = ""
        try:
            date = query_result[i]['pagemap']['metatags'][0]['citation_date']
        except KeyError:
            try:
                date = query_result[i]['pagemap']['metatags'][0]["citation_publication_date"]
            except KeyError:
                date = "Date not found"
                pass
        year = date.split('/')[0]

        try:
            author = query_result[i]['pagemap']['metatags'][0]['citation_author']
        except KeyError:
            author = "Author info not found"
            pass

        info_dict['year'] = year
        info_dict['author'] = author
        info_dict_lst.append(info_dict)
    return info_dict_lst
  
  
def get_best_paper_info(info_dict_lst):
    best_score = 0
    best_dict = info_dict_lst[0]
    for info_dict in info_dict_lst:
        score = 0
        if info_dict['year'].isdigit():
            score += 1
        if info_dict['author'] != "Author info not found":
            score += 1
        if score > best_score:
            best_dict = info_dict.copy()
            best_score = score
    return best_dict
  
  
################### END OF FUNCTIONS #####################
################### MAIN BEGINS BELOW #####################

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
search_eng_id = os.getenv("SEARCH_ENGINE_ID")

old_dir = "./papers"
new_dir = input("Enter new folder name:")
#new_dir = os.path.join('.', new_folder)
#new_dir = "./new_files_here"

to_rename = []
for file in os.listdir(old_dir):
    if file[-4:] == ".pdf":
        filepath = os.path.join(old_dir, file)
        to_rename.append(filepath)


while os.path.isdir(new_dir) and os.path.exists(new_dir):
    resp = input("This directory already exists. Overwrite? ['Y'/'N']")
    if resp == 'y' or resp == 'Y':
        shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        break
    else:
        new_folder = input("Enter another filename or abort by pressing Enter/Return:")
        if bool(new_folder) == False:
            print("Process aborted.")
            break
        else:
            new_dir = new_folder
            os.mkdir(new_dir)

if not os.path.exists(new_dir):
    os.mkdir(new_dir)
        
if bool(new_dir) == True:        
    print("A new folder is created here: ", new_dir)
    filenum = 1
    for filepath in tqdm(to_rename):
        orig_filename = filepath.split("/")[-1]
        print("File being converted:", orig_filename)
        tmp_filename = "tmp_img.jpg"
        image = convert_from_path(filepath, dpi=100, first_page=1, last_page=1)[0]
        image.save(tmp_filename, 'JPEG')

        img = Image.open(tmp_filename)
        width, height = img.size
        # crop image
        left = 0
        top = 0
        right = width
        bottom = height / 2
        img = np.array(img.crop((left, top, right, bottom)))

        result = pytesseract.image_to_data(image, output_type=Output.DICT)
        poss_titles = get_possible_title(result, orig_filename)
        identified_titles = []
        for title in poss_titles:
            if str(type(title)) == "<class 'str'>":
                q_title = title
                #draw_squares(img, result)
            else:
                q_title = join_ocr_title(title)
                #add_text(img, result, [q_title], filenum)
            identified_titles.append(q_title)
            
        print("Titles identified:")
        for i, title in enumerate(identified_titles):
            print("\nindex {}: {}".format(i, title))
        title_id = input("Enter index for title of your choice:")
        if len(identified_titles):
            while int(title_id) > len(identified_titles)-1 or int(title_id) < 0:
                title_id = input("Invalid index! Please input an index between (incl.) 0 and {}!".
                                 format(len(identified_titles)-1))
        else:
            continue
        q_title = identified_titles[int(title_id)]
            
        google_res = google_search(q_title, google_api_key, search_eng_id)
        paper_info = get_n_paper_info(google_res, 5)
        paper_info = get_best_paper_info(paper_info)
        
        author = "".join(paper_info['author'].split())
        title_as_lst = q_title.split()
        if len(title_as_lst) > 15:
            q_title = " ".join(title_as_lst[:15])
        if not paper_info['year'].isdigit() or author == "AuthorInfo_NOT_FOUND":
            new_filename = "{} {} {}.pdf".format(q_title, paper_info['year'], author)
        else:
            new_filename = "{} {} {}.pdf".format(paper_info['year'], author, q_title)

        new_filepath = os.path.join(new_dir, new_filename)

        shutil.copy(filepath, new_filepath)
        filenum+=1

# clean up
if os.path.exists("page_1.jpg"): 
    os.remove("page_1.jpg")
