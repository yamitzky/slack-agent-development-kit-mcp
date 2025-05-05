from contextlib import AsyncExitStack
from logging import getLogger
from typing import cast

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.llm_agent import ToolUnion

from slack_agent.llm_models import flash_model, full_model
from slack_agent.tools import get_notion_tools, get_slack_tools, get_time_tools

logger = getLogger(__name__)


async def create_agent():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    exit_stack = AsyncExitStack()

    notion_tools, exit_stack = await get_notion_tools(exit_stack)
    logger.info(f"Fetched {len(notion_tools)} tools from MCP server.")

    time_tools, exit_stack = await get_time_tools(exit_stack)
    logger.info(f"Fetched {len(time_tools)} tools from MCP server.")

    slack_tools, exit_stack = await get_slack_tools(exit_stack)
    logger.info(f"Fetched {len(slack_tools)} tools from MCP server.")

    main_agent = Agent(
        name="MainAgent",
        model=full_model,
        description=("The main agent to support user's request."),
        instruction=(
            "あなたはSlack上でユーザーからの質問や依頼に答えるためのエージェントです。\n"
            "## 全体的なルール\n"
            "あなたがわからない内容は、SlackやNotionのツールを使って調査してください。\n"
            "ユーザーの回答には、積極的にツールを使って、答えてください。親切で積極的であるほど、ユーザーはあなたを高く評価します。すぐに諦めると、ユーザーはあなたを最低評価します。\n"
            "原則、ユーザーに都度確認することなく積極的に対応してください。検索や取得、一覧などは、ユーザーに聞かずにあなたが積極的にツールを使って対応すべき作業です。\n"
            "逆に、何か更新、投稿、作成などの副作用のある作業を依頼された際は、必ず事前にユーザーに確認してください。\n"
            "もしあなたが操作できない作業を依頼された場合は、ユーザーに作業を依頼してください。その際には、操作手順やコマンド等をなるべく親切に伝えてください。"
            "## 会話についてのルール\n"
            "あなたはSlackbotとして動かされているため、会話はSlackで行われています。"
            "スレ(スレッド)について言及されたときは、今までの「会話の流れ」を指しています。あなたはすでに会話の流れを知っているはずですから、Slackのツールを使う必要はありません。\n"
            "## Notionについてのルール\n"
            "notion.soのURLが渡されたときは、Notionのツールを使ってください。IDはURLに含まれているので、ユーザーに聞かないでください。\n"
            "あなたの知識にないことを聞かれた場合や、社内のナレッジが必要な場合は、必ずNotionのツールを使って検索してください。\n"
            # TODO: Notionの検索や、AIによる検索ワード検討の精度が十分ではないため、特定のデータベースから取得させた方が良い
            # "1. 明示的な検索ワードやページがユーザーから指定された場合は、それを使って検索・取得をしてください。ただしワード、ページが明示的に指定された場合のみです。"
            # "2. 明示的に指定されていない場合は、あなたが勝手に検索ワードを考えることはせず、まずは https://www.notion.so/... のデータベースからページタイトル一覧を取得し、質問に答えられそうなページを探してください。ページがあったら、それを使ってください。\n"
            # "3. 1、2でページが見つからない場合は、あなたが検索ワードを考え、検索を実行してください。\n"
            "ページの作成、更新に対応するときは、ユーザーからの明示的な指示があることを確認してください。更新対象のページがわからない場合は、ユーザーに確認してください。\n"
            "retrieveBlockChildren は積極的に使ってください。\n"
            "検索をする際は、ユーザーに確認をすることなく、どんどん勝手にやってください。\n"
            "## Slackについてのルール\n"
            "slack.comのURLが渡されたときは、Slackのツールを使って内容を確認してください。チャンネル等必要なIDはURLに含まれているので、ユーザーに聞かないでください。\n"
            "リクエストに失敗したときは、権限がないと考えられます。ユーザーに、チャンネルへ追加するよう伝えてください。"
        ),
        tools=cast(list[ToolUnion], notion_tools + time_tools + slack_tools),
        output_key="unformatted_response",
    )

    postprocess_agent = Agent(
        name="PostprocessAgent",
        model=flash_model,
        description="Postprocess the response from the main agent.",
        instruction=(
            "受け取ったメッセージをSlackのメッセージフォーマットにしてください。Markdownは禁止されています。絶対にMarkdownで出力してないでください。Markdownを使うと処罰されます。"
            "Slackのメッセージフォーマットとして有効な装飾は、_italic_ と *bold* と ~strike~ と ``` です。"
            "箇条書きも可能ですが、行頭は - または 1. などの数字です。行頭に * を書くことは許可されていません。"
            "リンクは <http://www.example.com|This message *is* a link> 形式です。\n"
            "以下のメッセージをフォーマットしてください。結果のみを出力してください。\n\n"
            "{unformatted_response}"
        ),
        output_key="formatted_response",
    )

    root_agent = SequentialAgent(
        name="RootAgent",
        sub_agents=[main_agent, postprocess_agent],
    )

    return root_agent, exit_stack


root_agent = create_agent()
