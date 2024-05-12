import pyaudio
import queue
from threading import Thread

import sys
import html.parser as htmlparser

from google.cloud import speech
from google.cloud import translate_v2 as translate
import time

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 100)  # 100ms
# other parameters
PERIODIC_THRESHOLD =50

class MicrophoneStream(Thread):
    def __init__(self, event, input_language:str, text_original, text_1, text_2, chunk=CHUNK, format=pyaudio.paInt16, channels=1, rate=RATE):
        super().__init__()
        self.event = event
        self._chunk = chunk
        self.format = format
        self._channels = channels
        self._rate = rate
        self.text_original = text_original
        self.text_1 = text_1
        self.text_2 = text_2

    
        self.translate_client = translate.Client()
        # See http://g.co/cloud/speech/docs/languages
        # for a list of supported languages.
        if input_language == "fr-fr":
            self.language_text_1 = "it"
            self.language_text_2 = "es"
        elif input_language == "es-es":
            self.language_text_1 = "fr"
            self.language_text_2 = "it"
        elif input_language == "it-it":
            self.language_text_1 = "fr"
            self.language_text_2 = "es"

        self.client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=input_language,
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )
        
        # previously in self.__enter__
        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
        self._audio_interface = pyaudio.PyAudio()
        input_device_index=0
        info = self._audio_interface.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (self._audio_interface.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                if self._audio_interface.get_device_info_by_host_api_device_index(0, i).get('name').startswith("Yeti"):
                   input_device_index = i
                   break
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=self._channels,
            rate=self._rate,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False


    def run(self):
        print("Microphone stream started.")
        while True:
            if self.event.is_set():
                print(f'entering the listening loop for {self.language_text_1} and {self.language_text_2}')
                self._buff.queue.clear()
                audio_generator = (s for s in self.generator() if self.event.is_set())
                # data = self.stream.read(self.chunk)
                # self.frames.append(data)
                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator if self.event.is_set()
                )
                responses = self.client.streaming_recognize(self.streaming_config, requests)
                num_chars_printed = 0
                for response in responses:
                    if not self.event.is_set():
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
                        self.text_original.set(transcript + overwrite_chars)
                        num_chars_printed = len(transcript)

                    else:
                        # print(transcript + overwrite_chars)
                        response_1 = translate_text_with_model(self.translate_client, self.language_text_1, transcript + overwrite_chars)
                        #print(es_str)
                        
                        response_2 = translate_text_with_model(self.translate_client, self.language_text_2, transcript + overwrite_chars)
                        #print(it_str)

                        self.text_original.set(limit_text_length(response_1["input"]))
                        self.text_1.set(limit_text_length(response_1["translatedText"]))
                        self.text_2.set(limit_text_length(response_2["translatedText"]))

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
            else:
                self.event.wait()
                self._buff.empty()
                time.sleep(0.5)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        frame_count: int,
        time_info: object,
        status_flags: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
            in_data: The audio data as a bytes object
            frame_count: The number of frames captured
            time_info: The time information
            status_flags: The status flags

        Returns:
            The audio data as a bytes object
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Generates audio chunks from the stream of audio data in chunks.

        Args:
            self: The MicrophoneStream object

        Returns:
            A generator that outputs audio chunks.
        """
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def limit_text_length(text: str):
    text = htmlparser.unescape(text)
    if len(text) > 150:
        words = text.split(' ')
        text = ''
        words.reverse()
        for word in words:
            text = word + ' ' + text
            if len(text)>140:
                break
    return text  
        
            

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

    # print("Text: {}".format(result["input"]))
    # print("Translation: {}".format(result["translatedText"]))
    # print("Detected source language: {}".format(result["detectedSourceLanguage"]))

    return result
