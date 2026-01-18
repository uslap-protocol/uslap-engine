"""
app.py - Simple USLaP File Viewer
Shows correct surgical robot files
"""

import gradio as gr
import json

def show_correct_files():
    """Show the actual files with correct names"""
    
    try:
        with open("Surgery robot specs.txt", "r", encoding="utf-8") as f:
            specs = f.read()
    except:
        specs = "File 'Surgery robot specs.txt' not found"
    
    try:
        with open("Surgery robot.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
            json_pretty = json.dumps(json_data, indent=2)
    except:
        json_pretty = "File 'Surgery robot.json' not found"
    
    explanation = """
    # ✅ CORRECT FILE NAMES CONFIRMED
    
    ## Available in this repository:
    
    **1. Surgery robot specs.txt**
    - Executive summary
    - USLaP Q=1, U=1, F=1 compliance
    - 0.1mm precision from Qur'anic measurement
    
    **2. Surgery robot.json**
    - JSON specifications
    - System modules
    - Performance metrics
    
    ## Direct Access URLs:
    ```
    https://huggingface.co/uslap/uslap-multilingual/raw/main/Surgery%20robot%20specs.txt
    https://huggingface.co/uslap/uslap-multilingual/raw/main/Surgery%20robot.json
    ```
    
    ## Builder Tool:
    Run `python3 uslap.py` for interactive builder
    """
    
    return explanation, specs, json_pretty

# Simple interface
with gr.Blocks() as demo:
    gr.Markdown("# ⚕️ USLaP Surgical Robot Files")
    btn = gr.Button("Show Files", variant="primary")
    
    with gr.Row():
        explanation = gr.Markdown()
    
    with gr.Row():
        specs_display = gr.Textbox(label="Surgery robot specs.txt", lines=20)
        json_display = gr.Textbox(label="Surgery robot.json", lines=20)
    
    btn.click(show_correct_files, outputs=[explanation, specs_display, json_display])

demo.launch()