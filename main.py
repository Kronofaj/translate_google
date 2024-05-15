import tkinter as tk

from microphone import MicrophoneStream
from threading import Event


def button1_click():
    fr_event.set()
    es_event.clear()
    it_event.clear()

def button2_click():
    fr_event.clear()
    es_event.set()
    it_event.clear()

def button3_click():
    fr_event.clear()
    es_event.clear()
    it_event.set()

# Start a separate thread to update text asynchronously
def start_thread(input_language:str):
    if input_language == "fr-fr":
        text_original = label_fr_text
        text_1 = label_it_text
        text_2 = label_es_text
        event = fr_event
    elif input_language == "es-es":
        text_original = label_es_text
        text_1 = label_fr_text
        text_2 = label_it_text
        event = es_event
    elif input_language == "it-it":
        text_original = label_it_text
        text_1 = label_fr_text
        text_2 = label_es_text
        event = it_event
    thread = MicrophoneStream(event=event, input_language=input_language, text_original=text_original, text_1=text_1, text_2=text_2)
    thread.daemon = True
    thread.start()

fr_event = Event()
globals()["fr_event"] = fr_event
es_event = Event()
globals()["es_event"] = es_event
it_event = Event()
globals()["it_event"] = it_event

# Create the main window
root = tk.Tk()
root.title("Live Translate")
root.configure(background="white")
root.geometry("1920x1080")
height=300

# Create labels
button1 = tk.Button(root, text="Français", command=button1_click, font=('Arial', '30'), wraplength=1250, justify="center", fg='navy', background="white")
button1.pack()
# tk.Label(root, text="Texte en Français", font=('Arial', '30'), wraplength=1250, justify="center", fg='navy', background="white").pack()
label_fr_text = tk.StringVar()
label_fr_text.set("texte en Français")
label_fr = tk.Label(root, textvariable=label_fr_text, 
                    font=('Arial', '50'), 
                    wraplength=1250, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    #   height=height
                    )
label_fr.pack(anchor="nw")
button2 = tk.Button(root, text="Español", command=button2_click, font=('Arial', '30'), wraplength=1250, justify="center", fg='red4', background="white")
button2.pack()
label_es_text = tk.StringVar()
label_es_text.set("texto en Español")
label_es = tk.Label(root, textvariable=label_es_text, 
                    font=('Arial', '50'), 
                    wraplength=1250, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    # height=height
                    )
label_es.pack(anchor="nw")
button3 = tk.Button(root, text="Italiano", command=button3_click, font=('Arial', '30'), wraplength=1250, justify="center", fg='dark green', background="white")
button3.pack()
label_it_text = tk.StringVar()
label_it_text.set("testo in Italiano")
label_it = tk.Label(root, textvariable=label_it_text, 
                    font=('Arial', '50'), 
                    wraplength=1250, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    # height=height
                    )
label_it.pack(anchor="nw")


start_thread("fr-fr")   
start_thread("es-es")
start_thread("it-it")

# Run the GUI
root.mainloop()
