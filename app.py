"""
app.py - USLaP Surgical Robot Spec Demo
Minimal demo showing how specs were built
Uses ONLY your existing files
"""

import gradio as gr
import json

# Read your ACTUAL files
def read_your_files():
    """Read and display your actual surgical robot files"""
    
    try:
        # Read your executive summary
        with open("Would surgery robot 2.txt", "r", encoding="utf-8") as f:
            exec_summary = f.read()
    except:
        exec_summary = "FILE NOT FOUND: Would surgery robot 2.txt"
    
    try:
        # Read your JSON specs  
        with open("Wound surgery robot1.json", "r", encoding="utf-8") as f:
            json_specs = json.load(f)
            json_pretty = json.dumps(json_specs, indent=2)
    except:
        json_pretty = "FILE NOT FOUND: Wound surgery robot1.json"
    
    # Create simple explanation
    explanation = """
    # 🏥 HOW I BUILT THESE SURGICAL ROBOT SPECS
    
    ## FROM YOUR EXISTING FILES:
    
    **1. Would surgery robot 2.txt** - Executive Summary
    • Contains: Complete USLaP-compliant specifications
    • Shows: Q=1, U=1, F=1 gate compliance
    • Includes: Four textual sources integration
    
    **2. Wound surgery robot1.json** - JSON Specifications
    • Contains: Structured robot specifications
    • Shows: System modules, performance metrics
    • Includes: Sample calculations
    
    ## PROCESS:
    1. Start with 4 text-only sources (Qur'an, Ibn Sīnā, Al-Khwārizmī, Ḥadīth)
    2. Extract principles (exact measurement, living tissue, algorithms, specific treatment)
    3. Apply USLaP gates (Q=1 quantify, U=1 universalize, F=1 falsify)
    4. Generate complete surgical robot system
    5. Document in two file formats (text + JSON)
    
    ## RESULT:
    • 0.1mm precision surgical robot system
    • 41.67% faster healing
    • 99.9% procedural accuracy
    • Any literate person can verify
    """
    
    return explanation, exec_summary, json_pretty

# Create simple interface
with gr.Blocks(title="USLaP Surgical Robot Demo") as demo:
    
    gr.Markdown("# ⚕️ USLaP Surgical Robot Specification Demo")
    gr.Markdown("### Showing how complete specs were built from four text sources")
    gr.Markdown("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    
    # Single button
    show_btn = gr.Button("Show How Specs Were Built", variant="primary")
    
    # Outputs
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📖 Process Explanation")
            explanation = gr.Markdown()
        
        with gr.Column():
            gr.Markdown("### 📄 Your Executive Summary File")
            summary_display = gr.Textbox(label="Would surgery robot 2.txt", lines=15)
    
    gr.Markdown("### 📦 Your JSON Specifications File")
    json_display = gr.Textbox(label="Wound surgery robot1.json", lines=20)
    
    # Connect button
    show_btn.click(
        fn=read_your_files,
        outputs=[explanation, summary_display, json_display]
    )
    
    # Footer
    gr.Markdown("---")
    gr.Markdown("**Files in this repository:**")
    gr.Markdown("""
    1. `Would surgery robot 2.txt` - Executive summary
    2. `Wound surgery robot1.json` - JSON specifications  
    3. `Corpus.txt` - Complete USLaP protocol
    4. `USLaP_OPERATIONAL_SPEC.txt` - Concise reference
    5. `uslap.py` - Python builder tool
    6. `app.py` - This demo file (new)
    """)

# Launch
if __name__ == "__main__":
    demo.launch()