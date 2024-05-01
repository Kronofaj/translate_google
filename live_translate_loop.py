# import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\Nans\\Documents\\Code\\boda\\keys\\boda-418508-1ef85dcfc34e.json"
import re
import sys
import html.parser as htmlparser

from google.cloud import speech
from google.cloud import translate_v2 as translate

from microphone import MicrophoneStream, RATE, CHUNK

PERIODIC_THRESHOLD =50

def translate_text_with_model(translate_client, target: str, text: str, model: str = "nmt") -> dict:
    """Translates text into the target language.

    Make sure your project is allowlisted.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, target_language=target, model=model)

    print("Text: {}".format(result["input"]))
    print("Translation: {}".format(result["translatedText"]))
    print("Detected source language: {}".format(result["detectedSourceLanguage"]))

    return result

def listen_translate_loop(responses: object, 
                          language_text_1:str, 
                          language_text_2:str, 
                          text_original,
                          text_1,
                          text_2,
                          client) -> str:
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.

    Args:
        responses: List of server responses

    Returns:
        The transcribed text.
    """
    print("enter the translate loop")
    num_chars_printed = 0
    for response in responses:
        if stop_event.is_set():
            break
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        
        # set a logic to translate every 50 characters
        threshold = PERIODIC_THRESHOLD

        if not result.is_final and num_chars_printed < threshold:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            text_original.set(transcript + overwrite_chars)
            num_chars_printed = len(transcript)

        else:
            # print(transcript + overwrite_chars)
            response_1 = translate_text_with_model(client, language_text_1, transcript + overwrite_chars)
            #print(es_str)
            
            response_2 = translate_text_with_model(client, language_text_2, transcript + overwrite_chars)
            #print(it_str)

            text_original.set(htmlparser.unescape(response_1["input"]))
            text_1.set(htmlparser.unescape(response_1["translatedText"]))
            text_2.set(htmlparser.unescape(response_2["translatedText"]))

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            # if re.search(r"\b(stop)\b", transcript, re.I):
            #     print("Exiting..")
            #     break
            if result.is_final:
                num_chars_printed = 0
                threshold = PERIODIC_THRESHOLD
            else:
                threshold += PERIODIC_THRESHOLD

    return text_original, text_1, text_2

def translate_loop(input_language:str, text_original, text_1, text_2) -> None:
    
    translate_client = translate.Client()
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    if input_language == "fr-fr":
        language_text_1 = "it"
        language_text_2 = "es"
    elif input_language == "es-es":
        language_text_1 = "fr"
        language_text_2 = "it"
    elif input_language == "it-it":
        language_text_1 = "fr"
        language_text_2 = "es"

    """Transcribe speech from audio file."""


    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=input_language,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        print("micro stream launched")
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_translate_loop(responses, 
                              language_text_1, 
                              language_text_2, 
                              text_original,
                              text_1, 
                              text_2,
                              translate_client)

