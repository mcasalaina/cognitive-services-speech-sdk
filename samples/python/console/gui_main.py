#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import platform
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from collections import OrderedDict

import intent_sample
import speech_language_detection_sample
import speech_sample
import speech_synthesis_sample
import transcription_sample
import meeting_transcription_sample
import translation_sample

class SpeechSDKDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech SDK Demo")
        self.root.geometry("800x600")
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a notebook with tabs for different categories
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Define the sample modules and their functions
        self.samples = OrderedDict([
            ("Speech Recognition", (speech_sample, [
                speech_sample.speech_recognize_once_from_mic,
                speech_sample.speech_recognize_once_from_file,
                speech_sample.speech_recognize_once_from_file_with_detailed_recognition_results,
                speech_sample.speech_recognize_once_compressed_input,
                speech_sample.speech_recognize_once_from_file_with_customized_model,
                speech_sample.speech_recognize_once_from_file_with_custom_endpoint_parameters,
                speech_sample.speech_recognize_async_from_file,
                speech_sample.speech_recognize_continuous_from_file,
                speech_sample.speech_recognize_continuous_async_from_microphone,
                speech_sample.speech_recognition_with_pull_stream,
                speech_sample.speech_recognition_with_push_stream,
                speech_sample.speech_recognition_with_push_stream_mulaw,
                speech_sample.speech_recognize_keyword_from_microphone,
                speech_sample.speech_recognize_keyword_locally_from_microphone,
                speech_sample.pronunciation_assessment_from_microphone,
                speech_sample.pronunciation_assessment_continuous_from_file,
                speech_sample.pronunciation_assessment_from_stream,
                speech_sample.pronunciation_assessment_configured_with_json,
                speech_sample.pronunciation_assessment_with_content_assessment,
            ])), 
            ("Intent Recognition", (intent_sample, [
                intent_sample.recognize_intent_once_from_mic,
                intent_sample.recognize_intent_once_async_from_mic,
                intent_sample.recognize_intent_once_from_file,
                intent_sample.recognize_intent_continuous,
            ])), 
            ("Translation", (translation_sample, [
                translation_sample.translation_once_from_mic,
                translation_sample.translation_once_from_file,
                translation_sample.translation_continuous,
                translation_sample.translation_once_with_lid_from_file,
                translation_sample.translation_continuous_with_lid_from_multilingual_file,
            ])), 
            ("Transcription", (transcription_sample, [
                transcription_sample.conversation_transcription,
                transcription_sample.conversation_transcription_from_microphone,
            ])), 
            ("Meeting Transcription", (meeting_transcription_sample, [
                meeting_transcription_sample.meeting_transcription_differentiate_speakers,
            ])), 
            ("Speech Synthesis", (speech_synthesis_sample, [
                speech_synthesis_sample.speech_synthesis_to_speaker,
                speech_synthesis_sample.speech_synthesis_with_language,
                speech_synthesis_sample.speech_synthesis_with_voice,
                speech_synthesis_sample.speech_synthesis_to_wave_file,
                speech_synthesis_sample.speech_synthesis_to_mp3_file,
                speech_synthesis_sample.speech_synthesis_to_pull_audio_output_stream,
                speech_synthesis_sample.speech_synthesis_to_push_audio_output_stream,
                speech_synthesis_sample.speech_synthesis_to_result,
                speech_synthesis_sample.speech_synthesis_to_audio_data_stream,
                speech_synthesis_sample.speech_synthesis_events,
                speech_synthesis_sample.speech_synthesis_word_boundary_event,
                speech_synthesis_sample.speech_synthesis_viseme_event,
                speech_synthesis_sample.speech_synthesis_bookmark_event,
                speech_synthesis_sample.speech_synthesis_with_auto_language_detection_to_speaker,
                speech_synthesis_sample.speech_synthesis_using_custom_voice,
                speech_synthesis_sample.speech_synthesis_get_available_voices,
            ])), 
            ("Language Detection", (speech_language_detection_sample, [
                speech_language_detection_sample.speech_language_detection_once_from_mic,
                speech_language_detection_sample.speech_language_detection_once_from_file,
                speech_language_detection_sample.speech_language_detection_once_from_continuous,
            ]))
        ])
        
        # Create tabs and populate them
        self.create_tabs()
        
        # API key and region configuration frame
        self.create_config_frame()
        
        # Output console
        self.create_output_console()
        
        # Check for API key and region
        self.check_api_credentials()
    
    def create_tabs(self):
        """Create tabs for each category of samples"""
        for category, (module, functions) in self.samples.items():
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=category)
            
            # Create a listbox with all functions in this category
            listbox_frame = ttk.LabelFrame(tab, text="Select a sample to run")
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create scrollbar for the listbox
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=15, font=("Courier", 10))
            listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.config(command=listbox.yview)
            
            # Populate the listbox
            for func in functions:
                function_name = func.__name__
                doc_string = func.__doc__.strip() if func.__doc__ else "No description available"
                listbox.insert(tk.END, f"{function_name}")
                # Add tooltip or description on hover (optional enhancement)
            
            # Add a button to run the selected function
            run_button = ttk.Button(
                tab, 
                text="Run Selected Sample", 
                command=lambda m=module, lb=listbox, funcs=functions: self.run_sample(m, lb, funcs)
            )
            run_button.pack(pady=10)
    
    def create_config_frame(self):
        """Create a frame for API key and region configuration"""
        config_frame = ttk.LabelFrame(self.main_frame, text="API Configuration")
        config_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Key entry (as password field)
        key_label = ttk.Label(config_frame, text="Speech Key:")
        key_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.key_var = tk.StringVar(value=os.environ.get('SPEECH_KEY', ''))
        key_entry = ttk.Entry(config_frame, width=40, textvariable=self.key_var, show="*")  # Using show="*" to hide the key
        key_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Region entry
        region_label = ttk.Label(config_frame, text="Service Region:")
        region_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.region_var = tk.StringVar(value=os.environ.get('SPEECH_REGION', ''))
        region_entry = ttk.Entry(config_frame, width=40, textvariable=self.region_var)
        region_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Show/Hide key button
        self.show_key = tk.BooleanVar(value=False)
        show_key_button = ttk.Checkbutton(
            config_frame, 
            text="Show Key", 
            variable=self.show_key,
            command=lambda: key_entry.configure(show="" if self.show_key.get() else "*")
        )
        show_key_button.grid(row=0, column=2, padx=(0, 10), pady=5, sticky=tk.W)
        
        # Save button
        save_button = ttk.Button(config_frame, text="Save Configuration", command=self.save_config)
        save_button.grid(row=1, column=2, padx=10, pady=5, sticky=tk.E)
    
    def create_output_console(self):
        """Create an output console that mimics print statements"""
        console_frame = ttk.LabelFrame(self.main_frame, text="Output Console")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create a scrolled text widget for output
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Courier", 10))
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)
        
        # Create a clear button
        clear_button = ttk.Button(console_frame, text="Clear Console", command=self.clear_console)
        clear_button.pack(pady=(0, 5))
        
        # Redirect stdout to the console
        import sys
        self.original_stdout = sys.stdout
        sys.stdout = self
    
    def write(self, text):
        """Redirects print statements to the console widget"""
        # Ensure speech key is not displayed in the console
        if "SPEECH_KEY" in text and self.key_var.get() in text:
            text = text.replace(self.key_var.get(), "********")
        
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        self.root.update_idletasks()  # Update the GUI while long processes run
    
    def flush(self):
        """Required for stdout redirection"""
        pass
    
    def clear_console(self):
        """Clear the output console"""
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
    
    def save_config(self):
        """Save the API key and region to environment variables"""
        os.environ['SPEECH_KEY'] = self.key_var.get()
        os.environ['SPEECH_REGION'] = self.region_var.get()
        messagebox.showinfo("Configuration Saved", "API Key and Region have been saved for this session.")
    
    def check_api_credentials(self):
        """Check if API credentials are set and warn if not"""
        if not self.key_var.get() or not self.region_var.get():
            messagebox.showwarning(
                "API Credentials Missing",
                "Please set your Speech API key and region in the configuration section."
            )
    
    def run_sample(self, module, listbox, functions):
        """Run the selected sample function in a separate thread"""
        selected_indices = listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Selection Required", "Please select a sample to run.")
            return
        
        selected_index = selected_indices[0]
        selected_function = functions[selected_index]
        
        # Check if credentials are set
        if not os.environ.get('SPEECH_KEY') or not os.environ.get('SPEECH_REGION'):
            messagebox.showwarning(
                "API Credentials Required",
                "Please set your Speech API key and region before running samples."
            )
            return
        
        # Display info about the sample being run
        self.write(f"\n{'-'*80}\n")
        self.write(f"Running: {selected_function.__name__}\n")
        if selected_function.__doc__:
            self.write(f"Description: {selected_function.__doc__.strip()}\n")
        self.write(f"{'-'*80}\n\n")
        
        # Run the function in a separate thread to keep the GUI responsive
        threading.Thread(target=self._run_function, args=(selected_function,), daemon=True).start()
    
    def _run_function(self, function):
        """Execute the function and handle exceptions"""
        try:
            function()
        except Exception as e:
            self.write(f"\nError running sample: {e}\n")

def main():
    root = tk.Tk()
    app = SpeechSDKDemoApp(root)
    root.mainloop()
    
    # Restore stdout when application closes
    import sys
    sys.stdout = app.original_stdout

if __name__ == "__main__":
    main()