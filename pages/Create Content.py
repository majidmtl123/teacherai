import streamlit as st
import streamlit as st
import time
import json
import openai
import requests
from openai import OpenAI
import os
import re
from markupsafe import Markup

import ast
import shutil
from PIL import Image
from reportlab.lib.pagesizes import letter
import json
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import SimpleDocTemplate,PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer,Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageTemplate, Image, Frame
from reportlab.lib.styles import getSampleStyleSheet


st.set_page_config(
    page_title="Book Writer App",
    page_icon="📚",
)

# CSS for styling
css = """
<style>
    .stApp {
        background-color: Black:
        font-family: 'Helvetica Neue', sans-serif;
    }
    .header {
        color: White;  /* Black text for header */
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .sub-header, .content {
        color: black;  /* Black text for sub-header and content */
        text-align: center;
        font-size: 1.2em;
    }
    .content {
        padding: 20px;
        font-size: 1.1em;
    }
</style>
"""

if 'content_topic' not in st.session_state:
    st.session_state['content_topic'] = '' 

if 'age' not in st.session_state:
    st.session_state['age'] = None 

if 'theme' not in st.session_state:
    st.session_state['theme'] = '' 


if 'instructions' not in st.session_state:
    st.session_state['instructions'] = '' 

if 'num_chapters' not in st.session_state:
    st.session_state['num_chapters'] = '' 



prompt_les_structure_1="""

Generate description of lessons for a children focusing on the topic given below. The content should be straightforward, engaging, and centered around the main topic, taking into account any provided instructions. Create lesson descriptions for the specified number of chapters mentioned below. The content should captivate the young audience and follow the structure outlined in the provided format. Please present the contents in the specified JSON format, ensuring there is no additional text before or after the content.
The content should be detailed and lengthy, both description and story should be abale to understand the concept well. 
Topic:{}
Age  : {}
Theme: {}
Instructions:{}
Number of Chapters :{}
"""


prompt_les_structure_2="""

Output Json Format:
{
    "lesson_title": "",
    "lesson_introduction": "",
    "chapters": [
        {
            "title": "",
            "description": ""
            
        },
        {
            "title": "",
            "description": ""

        },
        /next chapter 
    ],
    "lesson_conclusion": ""
}

Output:
"""

prompt_les_1="""

Generate a Chapter for a children lesson focusing on the below given Chapter Title and Chapter Description given below. The content should be straightforward, engaging, and centered around the main topic, taking into account any provided instructions. The content should captivate the young audience and follow the structure outlined in the provided format. Please present the contents in the specified JSON format, ensuring there is no additional text before or after the content.
The Chapter should be structured with a title , followed by a description of the topic. Use a story-driven approach from real life considering the given theme to explain the concept to kids, making it engaging and relatable. Conclude with an assessment that includes a story-based test based on the theme, comprising 3 multiple-choice questions and 2 open-ended questions for the students to answer which help them to learn the perticular lesson.
The description and story should be detailed and lengthy for abale to understand the concept well. 

Chapter Details:

Chapter Title:{}
Chapter Description:{}

Lesson Details:

Main Topic:{}
Kid Age  : {}
Main Theme: {}
Instructions:{}

"""


prompt_les_2="""

Output Json Format:

{
    "title": "",
    "description": "",
    "example_story": "",
    "assessment_story": "",
    "multiselect_questions": [
        {
            "question": "",
            "choices": ["","",""],
            "answer": ""
        },
        {
            "question": "",
            "choices": ["","",""],
            "answer": ""
        },
        {
            "question": "",
            "choices": ["","",""],
            "answer": ""
        }
    ],
    "open_questions": [
        "",
        ""
    ]
}


Output:
"""

prompt_pic_topic="""
Below given is a lesson created for kids, I need to create an image for the perticular lesson. Based on the given lesson idea, please generating a quality image, it should be attractive for kids and minimal and most importnatly allign with the lesson theme:
There should be no text in the image and also it should be cartoon type and make it suitable for kids.
Lesson Name:{}
Lesson Introduction:{}

"""
prompt_pic_story="""
Below given a Chapter content from a lesson of a kid, I need to create an image for the perticular Story of the lesson. Based on the given lesson description and Story, understand the concept and create an image, please generate a quality image, it should be attractive for kids and minimal and  most importnatly allign with the lesson content:
There should be no text in the image and also it should be cartoon type and make it suitable for kids.

Lesson Topic:{}
Chapter Name:{}
Chapter Description:{}
Story:{}

"""
prompt_pic_descriptiom="""
Below is a Chapter content from a lesson of a kid, I need to create an image for the perticular chapter Description of the lesson. Based on the given Chapter description, please generating a quality image, it should be attractive for kids and minimal and most importnatly allign with the Chapter  Description:
There should be no text in the image and also it should be cartoon type and make it suitable for kids.

Lesson Topic:{}
Chapter Name:{}
Chapter Description:{}

"""
prompt_pic_chapter="""
Below is a Chapter Name and Description from a lesson of a kid, I need to create an image for the perticular chapter Name. Based on the given Chapter Name and description, please generating a quality image, it should be attractive for kids and minimal and attractive and most importnatly allign with the lesson content:
There should be no text in the image and also it should be cartoon type and make it suitable for kids.

Chapter Name:{}
Chapter Description:{}

"""

directories=['output']
def createFolders():
    try:
        for dir in directories:
            if not os.path.exists(dir):
                os.makedirs(dir, exist_ok=True)
                print("DIRECTORIES CREATED")
            # else:
                # print("DIRECTORY ALREADY EXIST")
    except Exception as e:
        ('Failed to create folders  Reason: %s' % ( e))

createFolders()

def deleteOutput(folder):
    file_path='downloads.zip'
    if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
    elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


# deleteOutput('output')


def convert_str_to_list(my_string):
   start_index = my_string.find('[')
   end_index = my_string.find(']')
   if not ((start_index == -1) or (end_index == -1)):
      extracted_substring = my_string[start_index : end_index+1]
      res = ast.literal_eval(extracted_substring)
      return res
   else:
      return "error"

def deleteOutput(folder):
    file_path='downloads.zip'
    if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
    elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


def createFolders(dir):
    try:
            if not os.path.exists(dir):
                os.makedirs(dir, exist_ok=True)
                print("DIRECTORIES CREATED")
    except Exception as e:
        ('Failed to create folders  Reason: %s' % ( e))


def get_openai_Response(prompt_in):
  try:
    # print(prompt_in)

    client = OpenAI()

    response = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[
        {
          "role": "user",
          "content":prompt_in
        }
      ],
      temperature=1,
      max_tokens=3000,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response.choices[0].message.content
  except Exception as e:
    print(e)

def generate_iamge_e_2(prompt_in,image_name):
    response = client.images.generate(
    model="dall-e-2",
    prompt=prompt_in,
    size='1024x1024',
    n=1,
    )
    
    image_url = response.data[0].url
    time.sleep(2)
    img_data = requests.get(image_url).content
    completeName = os.path.join('output', image_name+'.jpg')  
    with open(completeName, 'wb') as handler:
        handler.write(img_data)

def generate_iamge_e_3(prompt_in,file_name):
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt_in,
    size='1024x1024',
    quality='standard',
    style='vivid',
    n=1,
    )

    image_url = response.data[0].url
    time.sleep(2)
    img_data = requests.get(image_url).content
    with open('output/'+file_name+'.jpg', 'wb') as handler:
        handler.write(img_data)


def draw_page_border(canvas, doc):
    canvas.saveState()
    page_width, page_height = letter
    border_margin = 20  # You can adjust this value to change the border size
    canvas.setFillColorRGB(0.898, 0.867, 0.784)  # RGB values for #e5ddc8
        # Set the border color and width
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)

    # Draw the border lines
    canvas.rect(border_margin, border_margin, page_width - 2 * border_margin, page_height - 2 * border_margin, stroke=1,fill=True)

    canvas.restoreState()
# Create a PDF document
def pdf_lesson(lesson_data):  
    pdf_file = "lesson.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    border_template = PageTemplate(id='border_template', onPage=draw_page_border)
    border_margin =20
    page_width, page_height = letter
    content_frame = Frame(border_margin, border_margin, page_width - 2 * border_margin, page_height - 2 * border_margin)

    border_template.frames.append(content_frame)
    story = []

    styles = getSampleStyleSheet()
    style = ParagraphStyle(
        name='Normal',
        fontSize=13,
        leading=17,  # Line spacing, adjust as needed
        textColor='black',  # Text color
        fontName='Helvetica'
    )

    title_style = ParagraphStyle(
        name='Title',
        fontSize=26,
        leading=24,  # Line spacing, adjust as needed
        spaceAfter=60,  # Space after each paragraph, adjust as needed
        spaceBefore=40,  # Space before each paragraph, adjust as needed
        textColor='#D10000',  # Text color
        alignment=1,  # Centered text
        fontName='Helvetica-Bold'
    )
    chapter_style = ParagraphStyle(
        name='Chapter',
        fontSize=20,
        leading=20,  # Line spacing, adjust as needed
        spaceAfter=60,  # Space after each paragraph, adjust as needed
        spaceBefore=40,  # Space before each paragraph, adjust as needed
        textColor='#01949A',  # Text color
        alignment=1,  # Centered text
        fontName='Helvetica-Bold'
    )
    small_heading = ParagraphStyle(
        name='Title',
        fontSize=15,
        spaceAfter=10,  # Space after each paragraph, adjust as needed
        spaceBefore=20,  # Space before each paragraph, adjust as needed
        textColor='green',  # Text color
        fontName='Helvetica-Bold'
    )
    gray_style = ParagraphStyle(
        name="Gray",
        textColor="gray",
        fontSize=13,
    )
    centered = ParagraphStyle(
        name="Centered",
        alignment=1,
        fontSize=15,
        fontName="Helvetica-Bold",

    )
    bold = ParagraphStyle(
        name="Bold",
        fontName="Helvetica-Bold",
        fontSize=13,
    )

    #Heading
    text = lesson_data["main_title"]
    story.append(Spacer(1, 1*inch))
    paragraph = Paragraph(text, title_style)
    story.append(paragraph)
    image_path = f"./output/lesson_image.jpg"  # Replace with the actual image file path
    image = Image(image_path, width=350, height=350)  # Adjust the width and height as needed
    story.append(image)
    story.append(PageBreak())
    #Introduction
    story.append(Spacer(1, 1.5*inch))
    paragraph = Paragraph("INTRODUCTION", centered)
    story.append(paragraph)
    story.append(Spacer(1, 0.5*inch))
    text = lesson_data["main_introduction"]
    paragraph = Paragraph(text, style)
    story.append(paragraph)
    story.append(PageBreak())
    def convertNumbersToAlphabets(num):
        return chr(num+65)

    #Chapters
    for chapterIdx,chapter in enumerate(lesson_data["chapters"]):
        text = chapter["title"]
        paragraph = Paragraph(text, chapter_style)
        story.append(paragraph)
        image_path = f"./output/Chapter_main{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path
        image = Image(image_path, width=200, height=200)  # Adjust the width and height as needed
        story.append(image)
        story.append(Spacer(1, 0.5*inch))
        description = chapter["description"]
        example_story = chapter["example_story"]
        assessment_story = chapter["assessment_story"]
        story.append(Paragraph("DESCRIPTION", small_heading))
        #image 
        story.append(Spacer(1, 0.5*inch))

        image_path = f"./output/Chapter_description{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path
        image = Image(image_path, width=200, height=200)  # Adjust the width and height as needed
        story.append(image)
        story.append(Spacer(1, 0.5*inch))    
        story.append(Paragraph(description, style))
        story.append(Paragraph("EXAMPLE STORY", small_heading))
        image_path = f"./output/Chapter_story{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path
        image = Image(image_path, width=200, height=200)  # Adjust the width and height as needed
        story.append(Spacer(1, 0.5*inch))
        story.append(image)
        story.append(Spacer(1, 0.5*inch)) 
        story.append(Paragraph(example_story, style))
        story.append(Paragraph("ASSESSMENT STORY", small_heading))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(assessment_story, style))
        multiselect_questions = chapter["multiselect_questions"]
        open_questions = chapter["open_questions"]
        story.append(Spacer(1, 0.5*inch))
        for id1,question in enumerate(multiselect_questions):
            story.append(Paragraph(f'{id1+1}. {question["question"]}', bold))
            # story.append(Paragraph("Choices:", style))
            story.append(Spacer(1, 0.1*inch))
            for id2,choice in enumerate(question["choices"]):
                story.append(Paragraph(f'{convertNumbersToAlphabets(id2)}. {choice}', style, bulletText=' '))
            # story.append(Paragraph("Answer: "+question["answer"], gray_style,bulletText=' '))
            story.append(Spacer(0, 0.1*inch))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("OPEN QUESTIONS", small_heading))
        story.append(Spacer(1, 0.5*inch))

        for ind2,question in enumerate(open_questions):
            story.append(Paragraph(f'{ind2+1}. {question}', style))
        story.append(PageBreak())

    #Answers
    story.append(Spacer(1, 1.5*inch))
    paragraph = Paragraph("ANSWERS", centered)
    story.append(paragraph)
    story.append(Spacer(1, 0.5*inch))
    for ind,i in enumerate(lesson_data["chapters"]):
        story.append(Paragraph(f"Chapter {ind+1}", bold))
        story.append(Spacer(1, 0.1*inch))
        for index,x in enumerate(i["multiselect_questions"]):
            story.append(Paragraph(f"{index+1}. "+x["answer"],style))
        story.append(Spacer(0, 0.1*inch))

    #Conclusion
    story.append(PageBreak())
    story.append(Spacer(1, 1.5*inch))
    paragraph = Paragraph("CONCLUSION", centered)
    story.append(paragraph)
    story.append(Spacer(1, 0.5*inch))
    text = lesson_data["main_conclusion"]
    paragraph = Paragraph(text, style)
    story.append(paragraph)
    story.append(Spacer(1, 0.5*inch))
    # Save the PDF
    doc.addPageTemplates([border_template])
    doc.build(story, onFirstPage=draw_page_border, onLaterPages=draw_page_border)

    return ("PDF created successfully")

def create_html_from_data(data):
    html_content = f"<h1>{data['main_title']}</h1>"
    st.markdown(Markup(html_content), unsafe_allow_html=True)
    html_content=""
    chapter_image_path = f"./output/lesson_image.jpg"  # Replace with the actual image file path

    st.image(chapter_image_path, use_column_width=True)
    html_content += f"<p style='font-size:20px;'>{data['main_introduction']}</p>"

    for chapterIdx,chapter in enumerate(data["chapters"]):

        html_content += f"<h2>{chapter['title']}</h2>"
        st.markdown(Markup(html_content), unsafe_allow_html=True)
        html_content=""

        chapter_image_path = f"./output/Chapter_main{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path

        st.image(chapter_image_path, use_column_width=True)

        html_content += f"<p style='font-size:20px;'>{chapter['description']}</p>"
        st.markdown(Markup(html_content), unsafe_allow_html=True)
        html_content=""

        chapter_image_path = f"./output/Chapter_description{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path

        st.image(chapter_image_path, use_column_width=True)

        html_content += f"<h3><strong>Example Story:</strong></h3>"
        st.markdown(Markup(html_content), unsafe_allow_html=True)
        html_content=""

        chapter_image_path = f"./output/Chapter_story{str(chapterIdx+1)}.jpg"  # Replace with the actual image file path

        st.image(chapter_image_path, use_column_width=True)

        html_content += f"<p style='font-size:20px;'>{chapter['example_story']}</p>"
        html_content += f"<h3><strong>Assessment Story:</strong> </h3>"
        html_content += f"<p style='font-size:20px;'> {chapter['assessment_story']}</p>"

        html_content += "<ul>"

        for question in chapter['multiselect_questions']:
            html_content += f"<li><strong>{question['question']}</strong>"
            html_content += "<ul>"
            for choice in question['choices']:
                html_content += f"<li>{choice}</li>"
            html_content += "</ul></li>"

        html_content += "</ul>"
        html_content += "<p style='font-size:20px;'>Open Questions:</p><ul>"

        for open_question in chapter['open_questions']:
            html_content += f"<li>{open_question}</li>"

        html_content += "</ul>"

    html_content += f"<p style='font-size:20px;'>{data['main_conclusion']}</p>"
    st.markdown(Markup(html_content), unsafe_allow_html=True)

    return html_content

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''

if 'setup_complete' not in st.session_state:
    st.session_state['setup_complete'] = False

if 'all_data_lesson' not in st.session_state:
    st.session_state['all_data_lesson'] = None

# Input for OpenAI API key and Project Name
with st.form("api_key_form"):
    st.session_state['api_key'] = st.text_input("Enter OpenAI API Key", value="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",type="password")
    openai.api_key = st.session_state['api_key']
    os.environ['OPENAI_API_KEY'] = st.session_state['api_key']
    client = OpenAI()
    # When the 'Start' button is clicked, it will set the setup_complete to True
    submitted = st.form_submit_button("Start")
    if submitted and st.session_state['api_key']:
        st.session_state['setup_complete'] = True

# If setup is complete, show the rest of the fields
if st.session_state['setup_complete']:
    st.subheader("Create Educational Material for Kids")

    content_topic= st.text_input("Enter the subject or topic you want to teach:")

    age= st.number_input("Select the age range of the kids:", min_value=3, max_value=20, value=3)

    themes = ['Adventure', 'Science', 'Fantasy', 'History', 'Nature', 'Space', 'Other']
    theme = st.selectbox("Choose a theme for the stories/concepts:",themes,index=None)
    if theme == 'Other':
        
        theme = st.text_input("type a custom theme for the stories/concepts")


    instructions = st.text_area("Additional Instructions or Notes:")

    num_chapters = st.number_input("Number of Chapters (3-10):", min_value=3, max_value=10, value=3, step=1)
    
    if content_topic and age and theme and instructions and instructions and num_chapters:

       submitted_form = st.form("Generate")
       if submitted_form:
            if  st.button('Generate Content'):
                    with st.spinner('Generating...'):
                        prg = st.progress(0) 
                        prompt_final=prompt_les_structure_1.format(content_topic,age,theme,instructions,num_chapters)+prompt_les_structure_2
                        resp=get_openai_Response(prompt_final)
                        prg.progress(25) 
                        res = json.loads(resp)
                        # clean_res=convert_str_to_list(resp)
                        main_title=res["lesson_title"]
                        main_introduction=res["lesson_introduction"]
                        main_conclusion=res["lesson_conclusion"]

                        st.session_state['all_data_lesson']={"main_title":main_title,"main_introduction":main_introduction,"main_conclusion": main_conclusion,"chapters":[]}
                        for i in res["chapters"]:
                            chapter_title=i["title"]
                            chapter_description=i["description"]
                            prompt_final=prompt_les_1.format(chapter_title,chapter_description,content_topic,age,theme,instructions)+prompt_les_2
                            resp=get_openai_Response(prompt_final)
                            res = json.loads(resp)
                            st.session_state['all_data_lesson']['chapters'].append(res)

                        prg.progress(50) 

                        main_title_fianl=main_title
                        main_introduction_final=main_introduction
                        main_conclusion_final=main_conclusion
                        chapters_final=st.session_state['all_data_lesson']["chapters"]
                                                                   
                                                
                        prompt_img=prompt_pic_topic.format(main_title_fianl,main_introduction_final)
                        generate_iamge_e_3(prompt_img,"lesson_image")   

                        for index,k in enumerate(chapters_final):
                            chapter_name=k["title"]
                            chapter_description=["description"]
                            chapter_example_story=["example_story"]

                            prompt_img=prompt_pic_chapter.format(chapter_name,chapter_description)
                            generate_iamge_e_3(prompt_img,"Chapter_main"+str(index+1)) 

                            prompt_img=prompt_pic_story.format(main_title_fianl,chapter_name,chapter_description,chapter_example_story)
                            generate_iamge_e_3(prompt_img,"Chapter_story"+str(index+1))

                            prompt_img=prompt_pic_descriptiom.format(main_title_fianl,chapter_name,chapter_description)
                            generate_iamge_e_3(prompt_img,"Chapter_description"+str(index+1))
                            prg.progress(75) 
                   
                    pdf_lesson(st.session_state['all_data_lesson'])             
                    prg.progress(100) 
                    st.download_button(label=f"Download", data=open('lesson.pdf', "rb"), file_name='lesson.pdf', mime="application/pdf")
                    create_html_from_data(st.session_state['all_data_lesson'])

                     

else:
 st.write("Note: Input your Open Ai API key To start!")


