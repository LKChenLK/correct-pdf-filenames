# correct pdf filenames

This is a tool that helps rename the papers downlowded from the internet with correct filenames and relevant information (year published, authors). Currently the accuracy is still not high (3/5 are correct for the testing papers), but the whole pipeline is complete and can be easily modified or optimized.

Currently the code only works when you place all the papers you want to rename in a folder named "papers" (case sensitive!) under the same directory as the code. There are a couple of sample papers in the folder, which you can replace with your own papers to rename. 

The program will generate a new folder under the same directory as ```main.py```. You will be asked to name the subfolder during runtime. The directory tree is as shown:

```
This project
│   README.md
│   main.py   
│   .env
│   requirements.txt
│
└───papers
│   │   paper_to_rename_1.pdf
│   │   paper_to_rename_2.pdf
│   │   ...
│   │   
│───[where the renamed pdfs will be]
│   │   renamed_pdf_1.pdf
│   │   renamed_pdf_2.pdf
│   │   ...
│   └───  
```

### Dependencies
Download and install before running the code
- [Tesseract](https://github.com/tesseract-ocr/tesseract/releases)
    - Mac: ```brew install tesseract```
- Poppler
    - Windows: download [here](), install, add to PATH
    - Mac: ```brew install poppler```

### Python dependencies 
Please refer to ```requirements.txt```, and run ```pip3 install -r requirements.txt``` in your terminal to install all packages at once. You may want to create a virtual environment first.

#### Troubleshooting for installing python packages
<details>
  <summary>Click to expand</summary>

Here are some possible problems you may encounter if you're running the code with a Jupyter notebook:  
Problem with importing cv2
- check if juyter is installed in virtual env
- check if 
```
import sys
sys.path
```
in both Jupyter and in the terminal report the same path

- if error message is ```ImportError: libGL.so.1: cannot open shared object file: No such file or directory```:  
do in terminal:
```
sudo apt update
sudo apt install libgl1-mesa-glx
```
source: https://github.com/conda-forge/pygridgen-feedstock/issues/10

</details>

  
### Google API key
If you want to run this code on your own computer, you will need to sign up for a google api key for yourself! For the code to read your API key, please save it as a ```.env``` file under the same directory as the ```main.py``` file (refer to directory tree above) like so:
```
GOOGLE_API_KEY="your api key here"
SEARCH_ENGINE_ID="your search engine id here"
```

For more information on getting a Google API key: 
- https://stackoverflow.com/a/62037708
- http://code.google.com/apis/console



Othe references:  
https://fosshelp.blogspot.com/2013/04/how-to-convert-jpg-to-tiff-for-ocr-with.html  
https://www.manejandodatos.es/2014/11/ocr-python-easy/  
https://www.pyimagesearch.com/2020/09/14/getting-started-with-easyocr-for-optical-character-recognition/  
https://nanonets.com/blog/ocr-with-tesseract/#introduction  
https://towardsdatascience.com/create-simple-optical-character-recognition-ocr-with-python-6d90adb82bb8  
https://fahmisalman.medium.com/an-easy-way-of-creating-text-localization-and-detection-in-tesseract-ocr-24cc89ed6fbc  
https://towardsdatascience.com/optical-character-recognition-ocr-with-less-than-12-lines-of-code-using-python-48404218cccb  


