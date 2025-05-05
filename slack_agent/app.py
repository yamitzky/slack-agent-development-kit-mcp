import asyncio
import os
import re
from logging import Logger, getLogger

from dotenv import load_dotenv
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part
from slack_bolt import BoltContext, BoltResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.agent import root_agent

logger = getLogger(__name__)

load_dotenv()

# 実際に渡されるプロンプトを確認するのに便利
# import litellm
# litellm._turn_on_debug()

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

APP_NAME = "slack_agent"

session_service = InMemorySessionService()


async def reaction_middleware(
    client: AsyncWebClient,
    channel_id: str,
    event: dict,
    context: BoltContext,
    logger: Logger,
    next,
):
    try:
        logger.info("Adding reaction")
        await client.reactions_add(
            channel=channel_id, name="loading", timestamp=event["ts"]
        )
    except Exception as e:
        logger.error(e)

    async def remove_reaction():
        try:
            logger.info("Removing reaction")
            await client.reactions_remove(
                channel=channel_id, name="loading", timestamp=event["ts"]
            )
        except Exception as e:
            logger.error(e)

    context["done"] = remove_reaction

    await next()


async def agent_middleware(
    client: AsyncWebClient,
    context: BoltContext,
    message: dict,
    bot_user_id: str,
    channel_id: str,
    logger: Logger,
    next,
):
    message_ts: str = message["ts"]
    thread_ts: str = message.get("thread_ts", message_ts)
    context["thread_ts"] = thread_ts

    if not message.get("user"):
        logger.info("Ignoring because bot")
        return BoltResponse(status=200)

    text: str = message.get("text", "")
    is_app_mention = f"<@{bot_user_id}>" in text

    # 本文がない場合はスルー
    text = text.replace(f"<@{bot_user_id}>", "").strip()
    if not text:
        logger.info("Ignoring because no text")
        return BoltResponse(status=200)
    context["text"] = text

    session = session_service.get_session(
        app_name=APP_NAME, user_id=channel_id, session_id=thread_ts
    )

    # メンションもされていないし作成もされていない場合は、スルー
    if not is_app_mention and not session:
        logger.info("Ignoring because not app mention and not session")
        return BoltResponse(status=200)

    # メンションされているがセッションがない場合は、作成、補完する
    if is_app_mention and not session:
        logger.info("Creating session")
        session = session_service.create_session(
            app_name=APP_NAME, user_id=channel_id, session_id=thread_ts
        )
        # スレッドがある場合は、スレッドを元に過去の会話を補完する
        if message.get("thread_ts"):
            try:
                logger.info(f"Getting thread history for {thread_ts}")
                response = await client.conversations_replies(
                    channel=message["channel"], ts=thread_ts, inclusive=True
                )

                if response["ok"] and response["messages"]:
                    # 古い順にメッセージを処理（最初のメッセージから順に。最終メッセージはここでは扱わない）
                    for message in response["messages"][:-1]:
                        text: str = message.get("text", "")
                        text = re.sub("<@[^>]+>", "", text).strip()
                        if not text:
                            continue
                        content = Content(
                            role="user"
                            if message.get("user") != bot_user_id
                            else "model",
                            parts=[Part(text=text)],
                        )
                        session_service.append_event(
                            session=session,
                            event=Event(
                                content=content,
                                author="user"
                                if message.get("user") != bot_user_id
                                else APP_NAME,
                                timestamp=message["ts"],
                            ),
                        )
            except Exception as e:
                logger.error(f"Error retrieving thread history: {e}")

    context["session"] = session

    await next()


@app.message(middleware=[agent_middleware, reaction_middleware])
async def message_handler(
    say: AsyncSay,
    thread_ts: str,
    session: Session,
    text: str,
    logger: Logger,
    done,
):
    content = Content(role="user", parts=[Part(text=text)])
    final_response_text = "Error"
    async for resp in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=content
    ):
        if resp.is_final_response():
            if resp.content and resp.content.parts:
                final_response_text = resp.content.parts[0].text
            elif resp.actions and resp.actions.escalate:
                final_response_text = (
                    f"Agent escalated: {resp.error_message or 'No specific message'}"
                )

    logger.info(f"🤖 Agent response: {final_response_text}")

    response_message = f"{final_response_text}"
    await say(
        text=response_message,
        thread_ts=thread_ts,
    )

    await done()


async def main():
    global runner

    agent, exit_stack = await root_agent
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    if SLACK_APP_TOKEN := os.environ.get("SLACK_APP_TOKEN"):
        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

        logger.info("connecting with socket mode")
        handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
        await handler.start_async()
    else:
        app.start(port=int(os.environ.get("PORT", 3000)))
    await exit_stack.aclose()


# アプリを起動します
if __name__ == "__main__":
    asyncio.run(main())
