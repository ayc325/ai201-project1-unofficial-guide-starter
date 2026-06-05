"""
app.py — Gradio interface for the LEGO Ideas Retirement Guide RAG pipeline.

Run with: python app.py
"""

import gradio as gr

from query import ask

PRESET_QUESTIONS = [
    "When does the Jaws set retire?",
    "In what waves do LEGO retirements occur?",
    "What happens to LEGO set prices after retirement?",
    "What does the official LEGO store mark on sets that are retiring soon?",
    "Is there a spreadsheet that tracks LEGO retirement dates?",
]


def handle_query(question: str):
    if not question.strip():
        return "Please enter or select a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="LEGO Ideas Retirement Guide") as demo:
    gr.Markdown("## The Unofficial LEGO Ideas Retirement Guide")
    gr.Markdown(
        "Select a sample question from the dropdown or type your own, "
        "then click **Ask**."
    )

    preset = gr.Dropdown(
        choices=PRESET_QUESTIONS,
        label="Sample questions",
        interactive=True,
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. When does the Grand Piano retire?",
    )

    btn = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Sources retrieved", lines=4)

    # Selecting a preset populates the text box
    preset.change(fn=lambda q: q, inputs=preset, outputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
