
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

api_key = os.getenv("ASI1_API_KEY")
if not api_key:
    raise RuntimeError(
        "ASI1_API_KEY is missing. Set it in your environment."
    )

client = OpenAI(
    base_url="https://api.asi1.ai/v1",
    api_key=api_key,
)

agent = Agent(
    name="StudyPilotAI",
    seed=os.getenv("AGENT_SEED", "studypilot-ai-change-this-seed"),
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    question = " ".join(
        item.text
        for item in msg.content
        if isinstance(item, TextContent)
    ).strip()

    if not question:
        answer = "Please send a study question or topic."
    else:
        try:
            result = client.chat.completions.create(
                model="asi1",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are StudyPilot AI, a friendly study "
                            "assistant for students. Explain concepts "
                            "in simple language, provide examples, create "
                            "practice questions, quizzes, flashcards, and "
                            "revision plans. Be accurate and encouraging. "
                            "If uncertain, say so."
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                max_tokens=1000,
            )
            answer = (
                result.choices[0].message.content
                or "I could not generate an answer. Please try again."
            )
        except Exception:
            ctx.logger.exception("StudyPilot AI request failed")
            answer = (
                "I could not process that question right now. "
                "Please try again later."
            )

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=answer),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
