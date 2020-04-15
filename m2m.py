#----------------------------------------------------------------------------------------------
# Original repo at: https://github.com/goFrendiAsgard/markdown-to-moodle-xml.git
#
# The specification of Moodle XML format: https://docs.moodle.org/38/en/Moodle_XML_format
#
# -----
# 
# The original code uses regular expressions and a top-down parser to build a dictionary
# that is later converted in Moodle XML format. This behavior is maintained.
#
# This fork makes the following changes and/or improvements:
#
# - `[DONE]` Allow different answer numbering from allowed values: 'none', 'abc', 'ABCD' or '123'
# - `[DONE]` Usage of prefix '!' in answer to mark it as correct (instead of space at the end)
# - `[DONE]` Usage of section name for quiz category (adds a dummy question, as per Moodle spec.)
#   - This only works if you have "Get category from file" checked, when importing in Moodle
# - `[FIX]`  Output of inline code should be wrapped only inside <code> tag
# - `[DONE]` Allow code formatting in answers for single block code and single dollar math 
# - `[DONE]` Output file based on (input filename + section text), but further sanitized
# - `[DONE]` Use of MD5 hash for question names instead of SHA224 -- more compact in Moodle view
#   - Probability of collision should remain fairly low within the expected question bank size)
# - `[FIX]` Fix html escaping for <, > and & inside code blocks
# - `[DONE]` Automatic conversion of block code snippets to image format
#----------------------------------------------------------------------------------------------

import os
import sys
import re
import hashlib
import random
import json
import base64
from markdown import markdown

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import ImageFormatter
from pygments.lexers import ClassNotFound
import tempfile


if sys.version_info[0] == 3:
    from urllib.request import urlopen
else:
    from urllib import urlopen

NEW_LINE = '\n'
HEADER_PATTERN = re.compile(r'^\s*# (.*)$')
QUESTION_PATTERN = re.compile(r'^(\s*)\*(\s)(.*)$')
CORRECT_ANSWER_PATTERN = re.compile(r'^(\s*)-(\s)!(.*)$')
WRONG_ANSWER_PATTERN = re.compile(r'^(\s*)-(\s)(.*[^ ])$')
SWITCH_PRE_TAG_PATTERN = re.compile(r'^```.*$')
EMPTY_LINE_PATTERN = re.compile(r'^\s*$')
IMAGE_PATTERN = re.compile(r'!\[.*\]\((.+)\)')
MULTI_LINE_CODE_PATTERN = re.compile(r'```(.*)\n([\s\S]+)```', re.MULTILINE)
SINGLE_LINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
SINGLE_DOLLAR_LATEX_PATTERN = re.compile(r'\$(.+)\$')
DOUBLE_DOLLAR_LATEX_PATTERN = re.compile(r'\$\$(.+)\$\$')

# (allowed values: 'none', 'abc', 'ABCD' or '123')
ANSWER_NUMBERING = 'abc'

def get_header(string):
    match = re.match(HEADER_PATTERN, string)
    if match:
        return match.group(1)
    return None


def get_question(string):
    match = re.match(QUESTION_PATTERN, string)
    if match:
        return match.group(3)
    return None


def get_correct_answer(string):
    match = re.match(CORRECT_ANSWER_PATTERN, string)
    if match:
        return match.group(3)
    return None


def get_wrong_answer(string):
    match = re.match(WRONG_ANSWER_PATTERN, string)
    if match:
        return match.group(3)
    return None


def is_header(string):
    return False if get_header(string) is None else True


def is_question(string):
    return False if get_question(string) is None else True


def is_correct_answer(string):
    return False if get_correct_answer(string) is None else True


def is_wrong_answer(string):
    return False if get_wrong_answer(string) is None else True


def md_script_to_dictionary(md_script):
    """
    Implements a top-down parser for the script and extracts elements
    to a dictionary.
    """
    dictionary = {}
    section, current_question, current_answer = ([], {}, {})
    for md_row in md_script.split(NEW_LINE):
        md_row = md_row.rstrip('\r')
        md_row = md_row.rstrip('\n')
        
        if is_header(md_row):
            
            section = []
            dictionary[get_header(md_row)] = section
        
        elif is_question(md_row):
            
            current_question = {'text': get_question(md_row), 'answers': []}
            section.append(current_question)
        
        elif is_correct_answer(md_row):
            
            current_answer = {
                'text': get_correct_answer(md_row),
                'correct': True
                }
            
            current_question['answers'].append(current_answer)
        
        elif is_wrong_answer(md_row):
            
            current_answer = {
                'text': get_wrong_answer(md_row),
                'correct': False
                }
            
            current_question['answers'].append(current_answer)
        
        elif not re.match(EMPTY_LINE_PATTERN, md_row):
            
            if not('text' in current_question):
                current_question['text'] = ''
            
            current_question['text'] += md_row + '\n'

        else:
            # if we get an empy line pattern but are parsing inside
            # a code block, we need that line break to keep code 
            # structure
            if 'text' in current_question:
                if current_question['text'].find('```') > -1:
                    current_question['text'] += md_row + '\n'
    
    dictionary = completing_dictionary(dictionary)
    return dictionary


def completing_dictionary(dictionary):
    """Completes parsed information with 'fraction' values for answers."""

    for key in dictionary:
        section = dictionary[key]
        for question in section:
            correct_answers = [x for x in question['answers'] if x['correct']]
            correct_answer_count = len(correct_answers)
            if correct_answer_count < 1:
                correct_answer_count = 1
            question['single'] = correct_answer_count == 1
            weight = round(100.0 / correct_answer_count, 7)
            for answer in question['answers']:
                if answer['correct']:
                    answer['weight'] = weight
                else:
                    answer['weight'] = 0
    return dictionary


def section_to_xml(section_caption, section, md_dir_path):
    """Convert a parsed section to XML

    Keyword arguments:
    section_caption -- Title of section (used to assign category)
    section -- dictionary mapped content from 'md_script_to_dictionary'
    md_dir_path -- path of the markdown file
    """

    xml = '<?xml version="1.0" ?><quiz>'
    
    #create dummy question to specify category for questions
    xml += '<question type="category"><category><text>' + section_caption + '</text></category></question>'
    
    #add parsed questions
    for index, question in enumerate(section):
        xml += question_to_xml(question, index, md_dir_path)
    xml += '</quiz>'
    return xml


def question_to_xml(question, index, md_dir_path):
    """
    Converts a parsed question to XML.

    <name> is automatically generated from a hash (question text + rand)
    <single> is derived from correct answers (1/0)
    <questiontext> is encoded in CDATA and html format
    """

    #convert question text to CDATA html
    rendered_question_text = render_text(question['text'], md_dir_path)

    index_part = str(index + 1).rjust(4, '0')
    q_part = (question['text'] + str(random.random())).encode('utf-8')
    question_single_status = ('true' if question['single'] else 'false')
    
    xml = '<question type="multichoice">'
    # question name
    xml += '<name><text>'
    xml += index_part + hashlib.md5(q_part).hexdigest()
    xml += '</text></name>'
    # question text
    xml += '<questiontext format="html"><text><![CDATA['
    xml += rendered_question_text
    xml += ']]></text></questiontext>'
    # answer
    for answer in question['answers']:
        xml += answer_to_xml(answer)
    
    # other properties
    xml += '<shuffleanswers>1</shuffleanswers>'
    xml += '<single>' + question_single_status + '</single>'
    xml += '<answernumbering>' + ANSWER_NUMBERING +'</answernumbering>'
    xml += '</question>'
    return xml


def answer_to_xml(answer):
    """Produces the XML output for an answer."""

    text = answer['text']

    #make any necessary transformatins to answer
    text = render_answer(text)

    xml = '<answer fraction="'+str(answer['weight'])+'">'
    xml += '<text>'+text+'</text>'
    xml += '</answer>'
    return xml

def wrap_cdata(html):
    """Wraps content inside a CDATA xml block."""
    return '<![CDATA[' + html + ']]>'

def sanitize_entities(text):
    """Converts <, > and & to html entities."""

    #unfortunately, this order is important
    text = text.replace('&','&amp;')
    text = text.replace('>','&gt;')
    text = text.replace('<','&lt;')
        
    return text

def render_answer(text):
    """Produces the output for an answer's text.

    If any of the following transformations are made, then 
    a CDATA html block is returned, else plain text:

    - Includes single line code pattern
    - Includes single dollar latex pattern
    """

    convert_html = False
    if re.search(SINGLE_LINE_CODE_PATTERN, text):
        #replace entities before conversion to XML
        text = sanitize_entities(text)

        text = re.sub(SINGLE_LINE_CODE_PATTERN, replace_single_line_code, text)
        convert_html = True
    
    if re.search(SINGLE_DOLLAR_LATEX_PATTERN, text):
        text = re.sub(SINGLE_DOLLAR_LATEX_PATTERN, replace_latex, text)
        convert_html = True

    return wrap_cdata( markdown( text ) ) if convert_html is True else text

def render_text(text, md_dir_path):
    text = re.sub(MULTI_LINE_CODE_PATTERN, replace_multi_line_code, text)
    text = re.sub(SINGLE_LINE_CODE_PATTERN, replace_single_line_code, text)
    text = re.sub(IMAGE_PATTERN, replace_image_wrapper(md_dir_path), text)
    text = re.sub(DOUBLE_DOLLAR_LATEX_PATTERN, replace_latex, text)
    text = re.sub(SINGLE_DOLLAR_LATEX_PATTERN, replace_latex, text)
    text = markdown(text)
    return text


def replace_latex(match):
    code = match.group(1)
    code = code.replace('(', '\\left(')
    code = code.replace(')', '\\right)')
    return '\\\\\(' + code + '\\\\)'


def replace_single_line_code(match):
    """
    Produces the output for an inline markdown code bock.

    Output should only be wrapped inside a <code> tag.
    """
    code = match.group(1)
    code = sanitize_entities(code)
    #return '<pre style="display:inline-block;"><code>' + code + '</code></pre>'
    return '<code>' + code + '</code>'


def replace_multi_line_code(match):
    lexer = match.group(1)
    code = match.group(2)

    if not lexer:
        lexer = ''
    
    to_image = True if lexer.find('{img}') > 0 else False

    if to_image:
        lexer = lexer.replace('{img}', '')
        return convert_code_image_base64(lexer, code)
    else:
        #sanitize entities before any conversion to XML
        code = sanitize_entities(code)
        return '<pre><code>' + code + '</code></pre>'


def replace_image_wrapper(md_dir_path):
    def replace_image(match):
        file_name = match.group(1)
        if (not os.path.isabs(file_name)) and ('://' not in file_name):
            file_name = os.path.join(md_dir_path, file_name)
        return build_image_tag(file_name)
    return replace_image


def build_image_tag(file_name):
    extension = file_name.split('.')[-1]
    try:
        data = urlopen(file_name).read()
    except Exception:
        f = open(file_name, 'rb')
        data = f.read()
    base64_image = (base64.b64encode(data)).decode('utf-8')
    src_part = 'data:image/' + extension + ';base64,' + base64_image
    return '<img style="display:block;" src="' + src_part + '" />'

def convert_code_image_base64(lexer_name, code):
    """Converts a code snippet to an image in base64 format."""
    
    if not lexer_name:
        lexer_name = 'pascal'
    try:
        lexer = get_lexer_by_name(lexer_name)
    except ClassNotFound:
        lexer = get_lexer_by_name('pascal')

    imgBytes = highlight(code, lexer, ImageFormatter(font_size=18, line_numbers = False))

    temp = tempfile.NamedTemporaryFile()
    temp.write(imgBytes)
    temp.seek(0)

    extension = 'png'
    base64_image = (base64.b64encode(temp.read())).decode('utf-8')
    src_part = 'data:image/' + extension + ';base64,' + base64_image
    
    temp.close()
    return '<img style="display:block;" src="' + src_part + '" />'

def md_to_xml_file(md_file_name):
    md_dir_path = os.path.dirname(os.path.abspath(md_file_name))
    md_file = open(md_file_name, 'r')
    md_script = md_file.read()
    dictionary = md_script_to_dictionary(md_script)
    for section_caption in dictionary:
        section = dictionary[section_caption]
        xml_file = open(md_file_name.replace('.md','')+'-'+section_caption.replace(' ', '')+'.xml', 'w')
        xml_file.write(section_to_xml(section_caption, section, md_dir_path))
    return dictionary


def md_to_xml_string(md_script):
    md_dir_path = os.getcwd()
    result = {}
    dictionary = md_script_to_dictionary(md_script)
    for section_caption in dictionary:
        section = dictionary[section_caption]
        result[section_caption] = section_to_xml(section_caption, section, md_dir_path)
    return json.dumps(result, indent=2)


if __name__ == '__main__':
    try:
        md_file_name = sys.argv[1]
        md_file = open(md_file_name, 'r')
        md_to_xml_file(md_file_name)
    except Exception:
        md_script = sys.argv[1]
        print(md_to_xml_string(md_script))
