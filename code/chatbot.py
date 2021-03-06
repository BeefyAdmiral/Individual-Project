from stanfordcorenlp import StanfordCoreNLP
import nltk
nltk.download("wordnet")
nltk.download("punkt")
from nltk.tag import pos_tag
import re, string
from nltk.stem import WordNetLemmatizer
l = WordNetLemmatizer()
import pickle
import numpy as np
from nltk.tokenize import word_tokenize
from keras.models import load_model
model = load_model('model.h5')
import json
import random
import time
import wikipedia
import requests
from flickrapi import FlickrAPI
from io import BytesIO
import urllib
from googletrans import Translator
translator = Translator()

#Load the intents
nlp = StanfordCoreNLP(r'D:\COSC 310\Assignments\A2\Test\Clone\Chat-bot-team-20\code\stanford-corenlp-4.2.0')
intents = json.loads(open('intents.json').read())
sentiment = pickle.load(open("SentimentalAnalysis.pkl", "rb"))

#Load the words and classes files using pickle
words = pickle.load(open('words.pkl','rb'))
classes = pickle.load(open('classes.pkl','rb'))

saveData = ""
try:
    saveData = pickle.load(open("saveData.pkl", "rb"))
except IOError:
    saveData = [['',{}]]




def lemma(s):
    # Make an array by tokenizing the sentence
    array = nltk.word_tokenize(s)
    newArray = []
    # Lemmatize the words in the array
    for word in array:
        newArray.append(l.lemmatize(word.lower()))
    return newArray

# Return array of 0 or 1 which represents if a word exists or not

def word_bag(s, words):
    # Lemmatize the input sentence
    array = lemma(s)
    # empty array of 0
    bag = [0]*len(words)  
    for s in array:
        for i,w in enumerate(words):
            if w == s: 
                # assign 1 if current word exists
                bag[i] = 1
                break
                
    return(np.array(bag))

def predict(s, model):
    # filter out predictions below a threshold
    test = nlp.pos_tag(s)
    testsen = ''
    for t in test:
        if t[1] == 'NN' or t[1] == 'NNP' or t[1] == 'JJ' and t[0].lower() not in words:
            testsen = testsen + t[0] + " "
    
    if (testsen != ''):
        testnp = word_bag(testsen, words)
        testRes = model.predict(np.array([testnp]))[0]
        thresh = 0.25
        testresults = []
        for i,r in enumerate(testRes):
            if r>thresh:
                testresults.append([i,r])
                # sort in descending order of probabilities
        testresults.sort(key=lambda x: x[1], reverse=True)
        
        for r in testresults:
            if classes[r[0]] == "noanswer":
                return [{"intent": "noanswer", "probability": str(r[1])},word_tokenize(testsen)]
            else:
                break
        
    p = word_bag(s, words)
    res = model.predict(np.array([p]))[0]
    thresh = 0.25
    results = []
    #generate an array of probabilities
    for i,r in enumerate(res):
        if r>thresh:
           results.append([i,r])
    # sort in descending order of probabilities
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    return_list.append({"intent": classes[results[0][0]], "probability": str(results[0][1])})
    return_list.append('')
    return return_list


def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_intents = intents_json['intents']
    result = ['','','']
    for i in list_intents:
        if(i['tag']== tag):
            result[0] = random.choice(i['responses'])
            if tag == 'goodbye':
                result[1] = 'save'
            elif tag == 'noanswer':
                result[1] = 'noanswer'
                if ints[1] != '':
                    result[2] = (ints[1])
            break
    return result

def gen_output(msg):
    ints = predict(msg, model)
    response = getResponse(ints, intents)
    return response


#Creating UI with tkinter
import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image

def recent():
    textbox.delete("0.0",END)
    for i in range(len(saveData)-1):
        output = str(i + 1) + ")\n"
        output = output + "Number turns: " + str(saveData[i][0]) + "\n\n"
        for key in saveData[i][1]:
            output = output + "User: " + "'" + key + "'" + "\n" + "Bot: " + saveData[i][1][key] + "\n\n"
        output = output + "-----------------------------------------------" + "\n"
        textbox.insert(END,output)

def remove_noise(tweet_tokens, stop_words = ()):

    cleaned_tokens = []

    for token, tag in pos_tag(tweet_tokens):
        token = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|'\
                       '(?:%[0-9a-fA-F][0-9a-fA-F]))+','', token)
        token = re.sub("(@[A-Za-z0-9_]+)","", token)

        if tag.startswith("NN"):
            pos = 'n'
        elif tag.startswith('VB'):
            pos = 'v'
        else:
            pos = 'a'

        lemmatizer = WordNetLemmatizer()
        token = lemmatizer.lemmatize(token, pos)

        if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token.lower())
    return cleaned_tokens

KEY = '1fbfb9fa2ae54df2f118cb5b95f72acd'
SECRET = 'f7fb901795d0cadb'
SIZES = ["url_q"]

def url(photo):
    for p in photo:
        url=p.get('url_q')
        return url


def search_image(image_name):
    extras = ','.join(SIZES)
    flickr = FlickrAPI(KEY, SECRET)
    photo = flickr.walk(text = image_name, privacy_filter = 1, extras = extras, sort ='relevance', per_page = 5)
    
    img_url = url(photo)
    t = check_url(img_url)
    if t == False:
        return False
    return img_url

def check_url(url):
    try:
        headers = {
            "Range": "bytes=0-10",
            "User-Agent": "MyTestAgent",
            "Accept": "*/*"
        }

        request = urllib.request.Request(url, headers = headers)
        response = urllib.request.urlopen(request)
        
        return response.code in range(200, 209)
    except Exception:
        return False

def send():
    	    #Read the message from user and clear the message window
            msg = EntryBox.get("1.0",'end-1c').strip()
            #msg = "Lieblingsanime"
            chat_msg = msg
            EntryBox.delete("0.0",END)
            
            if translator.detect(msg).lang != 'en':
                if isinstance(translator.detect(msg).lang, str) == True:
                    msg_lang = [translator.detect(msg).lang]
                    msg = translator.translate(msg, dest = 'en').text
                elif isinstance(translator.detect(msg).lang, str) == False:
                    msg_lang = [translator.detect(msg).lang[0]]
                    msg = translator.translate(msg, dest = 'en').text                    
                else:
                    msg_lang = ['en']
            else:
                    msg_lang = ['en']
                    
            
            
            custom_token = remove_noise(word_tokenize(msg))
            for t in custom_token:
                    t = word_tokenize(t)
                    emotion = sentiment.classify(dict([token, True] for token in t))
                    if emotion == "Negative":
                        if nlp.pos_tag(t[0])[0][1] == "NN" or nlp.pos_tag(t[0])[0][1] == "VB":
                            if t[0].lower() in words:
                                emotion = "Positive"
                            else:
                                break
                        else:
                            emotion = "Positive"
                            break
            
            if msg != '':
                ChatLog.config(state=NORMAL)
        
                ChatLog.image_create(END, image = userimg)
                ChatLog.insert(END, " : " + chat_msg + '\n\n')
                ChatLog.config(foreground="#442265", font=("Verdana", 12 ))
                ChatLog.tag_configure("center", justify='center')
        
                res = gen_output(msg)
                result = ' '
                search = ""
                ChatLog.image_create(END, image = botimg)
                ChatLog.insert(END, " : ")
                if emotion == "Negative" and res[1] == "noanswer" and res[2] == '':
                    result = result + "I am sorry to hear that \n\n"
                    ChatLog.image_create(END, image = sad)
                elif emotion == "Positive" and res[1] == "noanswer":
                    ChatLog.image_create(END, image = confused)
                    if res[2] != "":
                        
                        for r in res[2]:
                            search = search + r + " "
                        result = result + res[0].replace("%",search)
                        result = " " + result + " This is what I found on Wikipedia about " + search + ":\n"
                        try:
                            r = wikipedia.summary(search.replace(" ", ""), sentences =3, auto_suggest=False)
                            result = result + r + "\n\n"
                        except wikipedia.exceptions.DisambiguationError as e:
                            r = wikipedia.summary(e.options[0], sentences =3)
                            result = result + r + "\n\n"
                    else:
                        result = res[0].replace("%",msg) + "\n\n"
                elif emotion == "Positive":
                    ChatLog.image_create(END, image = happy)
                    result = result + res[0] + "\n\n"
                elif emotion == "Negative" and res[1] != "noanswer":
                    result = result + "I am sorry to hear that \n\n"
                    ChatLog.image_create(END, image = sad)
                elif emotion == "Negative" and res[1] == "noanswer" and res[2] != '':
                    ChatLog.image_create(END, image = confused)
                    for r in res[2]:
                        search = search + r + " "
                    result = result + res[0].replace("%",search) + "\n"
                    result = result + "This is what I found on Wikipedia about " + search + ":\n"
                    try:
                        r = wikipedia.summary(search.replace(" ", ""), sentences =3, auto_suggest=False)
                        result = result + r + "\n\n"
                    except wikipedia.exceptions.DisambiguationError as e:
                        r = wikipedia.summary(e.options[0], sentences =3)
                        result = result + r + "\n\n"
                
                if search != '':
                    try:
                        u = search_image(search)
                        img_url = u
                        response = requests.get(img_url)
                        if msg_lang[0] != 'en':
                            result = translator.translate(result, dest = msg_lang[0]).text
                        ChatLog.insert(END, result )
                        ChatLog.insert(END, "\n\n")
                        img_data = response.content
                        global test
                        test = ImageTk.PhotoImage(Image.open(BytesIO(img_data)).resize((100, 100), Image. ANTIALIAS))
                        ChatLog.image_create(END, image = test)
                        ChatLog.insert(END, "\n\n")
                    except:
                        result = result + "Sorry no image found\n"
                        if msg_lang[0] != 'en':
                            result = translator.translate(result, dest = msg_lang[0]).text
                        ChatLog.insert(END, result )
                        ChatLog.insert(END, "\n\n")
                else:
                    if msg_lang[0] != 'en':
                        result = translator.translate(result, dest = msg_lang[0]).text
                    ChatLog.insert(END, result )
                    ChatLog.insert(END, "\n\n")

                ChatLog.config(state=DISABLED)
                ChatLog.yview(END)
                if saveData[-1][0] == "":
                    saveData[-1][0] = 0
                    saveData[-1][1][msg] = result
                else:
                    saveData[-1][0] = saveData[-1][0] + 1
                    saveData[-1][1][msg] = result
                if res[1] == 'save':
                    saveData[-1][0] = saveData[-1][0] + 1
                    saveData.append(['',{}])
                    pickle.dump(saveData,open('saveData.pkl','wb'))
                    print("SAVED")




LARGE_FONT= ("Verdana", 12)


class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        image1 = Image. open("botpic.jpg")
        image1 = image1.resize((25, 25), Image. ANTIALIAS)
        image2 = Image. open("user-24.gif")
        image2 = image2.resize((25, 25), Image. ANTIALIAS)
        image3 = Image.open("sinchronize-32.gif")
        image3 = image3.resize((20, 20), Image. ANTIALIAS)
        image4 = Image.open("sad.png")
        image4 = image4.resize((20, 20), Image. ANTIALIAS)
        image5 = Image.open("confused.png")
        image5 = image5.resize((20, 20), Image. ANTIALIAS)
        image6 = Image.open("happy.png")
        image6 = image6.resize((40, 40), Image. ANTIALIAS)
        global happy
        happy = ImageTk.PhotoImage(image6)
        global confused
        confused = ImageTk.PhotoImage(image5)
        global sad
        sad = ImageTk.PhotoImage(image4)
        global refresh
        refresh = ImageTk.PhotoImage(image3)
        global botimg
        botimg = ImageTk.PhotoImage(image1)
        global userimg
        userimg = ImageTk.PhotoImage(image2)

        #Changing window image
        self.tk.call('wm', 'iconphoto', self._w,botimg )
        self.title("Anime Bot")
        self.geometry("400x500")
        
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (Home, Recent):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Home)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()
        
    
   
class Home(tk.Frame):
        

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        global ChatLog
        ChatLog = Text(self, bd=2,relief = "ridge", bg="beige", height="100", width="50", font="Arial", wrap = WORD)
        ChatLog.config(state=NORMAL)
        
        SendButton = Button(self, font=("Verdana",12,'bold','italic'), text="Send", width="12", height=5,
                    bd=0, bg="#030bfc", activebackground="#7373ff",fg='#ffffff',
                    command= send )
        RecentButton = Button(self, font=("Verdana",12,'bold','italic'), text="Recent", width="12", height=5,
                    bd=0, bg="#030bfc", activebackground="#7373ff",fg='#ffffff',
                    command= lambda: controller.show_frame(Recent))
        global EntryBox
        EntryBox = Text(self, bd=2,relief = "ridge", bg="#e6e6e6",width="29", height="5", font="Arial",wrap = WORD)

        #Aranging the objects
        ChatLog.place(x=6,y=6, height=386, width=388)
        EntryBox.place(x=6, y=401, height=90, width=265)
        SendButton.place(x=290, y=401, height=45, width = 104)
        RecentButton.place(x=290, y=450, height=45, width = 104)
       


class Recent(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Recent Conversation", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text = "Back", command=lambda: controller.show_frame(Home),bg="#030bfc", activebackground="#7373ff", fg='#ffffff')
        re = tk.Button(self, image = refresh, command = recent)
        sb = Scrollbar(self)  
        global textbox
        textbox = Text(self, bd =2, relief = "ridge", bg="beige", height="100", width="40",yscrollcommand = sb.set, wrap = WORD)
        for i in range(len(saveData)-1):
            output = str(i + 1) + ")\n"
            output = output + "Number turns: " + str(saveData[i][0]) + "\n\n"
            for key in saveData[i][1]:
                output = output + "User: " + "'" + key + "'" + "\n" + "Bot: " + saveData[i][1][key] + "\n\n"
            output = output + "---------------------------------------------" + "\n"
            textbox.insert(END,output)
        
        sb.pack(side = RIGHT, fill = Y)
        sb.config(command = textbox.yview)
        re.place(x=360,y=9)
        textbox.place(x=6,y=40, height=450, width=370)
        button1.place(x=6,y=9)


app = GUI()
send()
app.mainloop()



if saveData[-1][0] != '':
    saveData[-1][0] = saveData[-1][0] + 1
    saveData.append(['',{}])
    pickle.dump(saveData,open('saveData.pkl','wb'))
    print("SAVED")
