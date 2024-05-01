import tkinter as tk

from live_translate_loop import translate_loop
from thread_with_exception import ThreadWithException
from threading import Event


def button1_click():
    thread.raise_exception()
    thread.join()
    start_thread("fr-fr")

def button2_click():
    thread.raise_exception()
    thread.join()
    start_thread("es-es")

def button3_click():
    thread.raise_exception()
    thread.join()
    start_thread("it-it")

# Start a separate thread to update text asynchronously
def start_thread(input_language:str):
    if input_language == "fr-fr":
        text_original = label_fr_text
        text_1 = label_it_text
        text_2 = label_es_text
    elif input_language == "es-es":
        text_original = label_es_text
        text_1 = label_fr_text
        text_2 = label_it_text
    elif input_language == "it-it":
        text_original = label_it_text
        text_1 = label_fr_text
        text_2 = label_es_text
    thread = ThreadWithException(target=translate_loop, args =(input_language,
                                                            text_original,
                                                            text_1,
                                                            text_2))
    thread.daemon = True
    thread.start()
    globals()["thread"] = thread


fr_event = Event()
globals()["fr_event"] = fr_event
it_event = Event()
globals()["fr_event"] = it_event

# Create the main window
root = tk.Tk()
root.title("Live Translate")
root.configure(background="white")
root.geometry("1920x1080")
height=300

# Create labels
tk.Label(root, text="Texte en Français", font=('Arial', '40'), wraplength=1800, justify="center", fg='navy', background="white").pack()
label_fr_text = tk.StringVar()
label_fr_text.set("texte en Français")
label_fr = tk.Label(root, textvariable=label_fr_text, 
                    font=('Arial', '60'), 
                    wraplength=1800, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    #   height=height
                    )
label_fr.pack(anchor="nw")
tk.Label(root, text="Texto en Español", font=('Arial', '40'), wraplength=1800, justify="center", fg='red4', background="white").pack()
label_es_text = tk.StringVar()
label_es_text.set("texto en Español")
label_es = tk.Label(root, textvariable=label_es_text, 
                    font=('Arial', '60'), 
                    wraplength=1800, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    # height=height
                    )
label_es.pack(anchor="nw")
tk.Label(root, text="Testo in Italiano", font=('Arial', '40'), wraplength=1800, justify="center", fg='dark green', background="white").pack()
label_it_text = tk.StringVar()
label_it_text.set("testo in Italiano")
label_it = tk.Label(root, textvariable=label_it_text, 
                    font=('Arial', '60'), 
                    wraplength=1800, 
                    justify="left", 
                    background="white", 
                    anchor="w", 
                    # height=height
                    )
label_it.pack(anchor="nw")

# Create buttons
label_buttons = tk.Label(root, text="Langue parlée / Idioma hablado / Lingua parlata")
label_buttons.pack()
button1 = tk.Button(root, text="Français", command=button1_click)
button1.pack(side=tk.LEFT, padx=5, pady=5)
button2 = tk.Button(root, text="Español", command=button2_click)
button2.pack(side=tk.LEFT, padx=5, pady=5)
button3 = tk.Button(root, text="Italiano", command=button3_click)
button3.pack(side=tk.LEFT, padx=5, pady=5)

#label_frame.place(x=10, y=10)

thread = None
input_language = "fr-fr"
start_thread(input_language)

# Run the GUI
root.mainloop()
