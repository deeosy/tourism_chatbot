import asyncio
import gradio as gr
from chatbot.responder import generate_response
from chatbot.config import get_config


# This function is registered with Gradio's ChatInterface.
# Gradio calls it when the user sends a message.
#   message - the user's latest text input
#   history - list of past [user_message, bot_reply] pairs (used for context)
async def chat_fn(message: str, history: list) -> str:
    return await generate_response(message)


def run_ui():
    cfg = get_config()
    # Show the user what mode we're in based on whether an API key is set
    mode = "AI-powered" if cfg["is_configured"] else "Guide mode (offline)"
    model_info = f" (model: {cfg['model']})" if cfg["is_configured"] else ""

    # Build the Gradio web interface using Blocks layout
    with gr.Blocks(title="Ghana Tourism Guide") as demo:
        # Header text displayed above the chat
        gr.Markdown(
            "# Akwaaba! - Your Ghana Travel Guide\n"
            f"_{mode}{model_info}_\n\n"
            "Ask me anything about travelling to Ghana - destinations, "
            "culture, food, itineraries, and practical tips."
        )

        # ChatInterface wraps a text input, chatbot display, and example prompts
        chatbot = gr.ChatInterface(
            fn=chat_fn,
            title=None,
            description=None,
            examples=[
                "What's there to do in Accra?",
                "Tell me about Cape Coast Castle",
                "Plan a 5-day Ghana itinerary",
                "What food should I try in Ghana?",
                "How do I get around Ghana?",
            ],
        )

    # Launch on localhost:7860 (the port the frontend connects to)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=gr.themes.Soft(primary_hue="orange", secondary_hue="green"),
    )


def main():
    run_ui()


if __name__ == "__main__":
    main()
