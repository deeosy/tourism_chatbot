import asyncio
import gradio as gr
from chatbot.responder import generate_response
from chatbot.config import get_config


async def chat_fn(message: str, history: list) -> str:
    return await generate_response(message)


def run_ui():
    cfg = get_config()
    mode = "AI-powered" if cfg["is_configured"] else "Guide mode (offline)"
    model_info = f" (model: {cfg['model']})" if cfg["is_configured"] else ""

    with gr.Blocks(
        title="Ghana Tourism Guide",
        # theme=gr.themes.Soft(primary_hue="orange", secondary_hue="green"),
    ) as demo:
        gr.Markdown(
            "# Akwaaba! - Your Ghana Travel Guide\n"
            f"_{mode}{model_info}_\n\n"
            "Ask me anything about travelling to Ghana - destinations, "
            "culture, food, itineraries, and practical tips."
        )

        chatbot = gr.ChatInterface(
            fn=chat_fn,
            # type="messages",
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

    demo.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft(primary_hue="orange", secondary_hue="green",),)


def main():
    run_ui()


if __name__ == "__main__":
    main()
