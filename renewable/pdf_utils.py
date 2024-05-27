# generic libraries
import uuid
import os
import platform
import glob

# PDF processing libraries
import fitz # extract text from true PDF
import pytesseract # extract text from scanned PDF
import spacy # parsing text into sentences

# function to extract text from a 'true' PDF
def true_pdf2text(path):
    # doc = fitz.open(path) # uncomment to test on local file
    doc = fitz.open(stream=path, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        
    return text

# get tesseract installation path based on operating system
def get_tesseract_path():
    current_os = platform.system() # detect OS on which python is running
    
    if current_os == 'Windows':
        res = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    elif current_os == 'Darwin':  # macOS
        res = '/usr/local/bin/tesseract'
    elif current_os == 'Linux':
        res = '/usr/bin/tesseract' # default path on most Linux distributions
    else:
        raise Exception(f'Unsupported operating system: {current_os}')
        
    return res

# function to extract text from a 'scanned' PDF using OCR
def scan_pdf2text(path, output_dir):
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
    
    # doc = fitz.open(path) # uncomment to test on local file
    doc = fitz.open(stream=path, filetype="pdf")
    
    # create a unique temp dir to store .png files
    unique_id = str(uuid.uuid4())[:8]
    newdir = os.path.join(output_dir, unique_id)
    os.mkdir(newdir)
    
    # convert pages to images > run OCR on image files
    text = ""
    for page in doc:
        img = page.get_pixmap(dpi=300)  # 300 dpi is high resolution
        img_file = os.path.join(newdir, f"page-{page.number}.png")
        img.save(img_file)
        text += pytesseract.image_to_string(img_file)
        
    # delete image files and temp dir
    files = glob.glob(os.path.join(newdir, "*.png"))
    for f in files:
        os.remove(f)
    os.rmdir(newdir)
    
    return text

# function to extract sentences from text using spacy
def text2sents(text, min_words):
    # returns no. of words in a sentence
    def no_words(txt):
        return len(txt.strip().split())
    
    # parse text into sentences using spacy
    nlp = spacy.load('en_core_web_sm')
    text = nlp(text)
    sentences = list(map(str, text.sents))
    
    # clean up sentences
    sentences = [x.replace("\n", "") for x in sentences] # remove newline chars
    sentences = [x for x in sentences if x != ""] # remove blanks
    sentences = [x for x in sentences if x[0].isupper()] # sentence should start with uppercase
    sentences = [x for x in sentences if not "....." in x] # remove table of contents
    sentences = [x for x in sentences if no_words(x) >= min_words] # remove sentences shorter than 'min_words'
    
    return sentences

# function to annotate PDF for all target text found
def annotate_target_text(path, target_text):    
    res = []
    with fitz.open(stream=path, filetype="pdf") as doc:
        for page in doc:
            found = False
            for text in target_text:
                areas = page.search_for(text)
                if len(areas) > 0:
                    found = True
                    for area in areas:
                        page.add_rect_annot(area) # mark red box around target text(s)
            if found:
                # include page only if it contains a target
                p = page.get_pixmap(dpi=300).tobytes()
                res.append(p)
    
    return res
