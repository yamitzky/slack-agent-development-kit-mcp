# slack-agent

[Agent Development Kit (ADK)](https://google.github.io/adk-docs/) を使用して構築された Slack エージェントのサンプルです。
MCP (Model Context Protocol) も使用しています。

## 主な機能

* Slack のメッセージやスレッドでのメンションに応答
* 会話履歴に基づいたコンテキスト維持 (スレッド単位)
* LiteLLM を使用した LLM の切り替え、フォールバック
* MCP 経由での外部ツール連携:
    * [Time MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/time)
    * [Notion MCP](https://github.com/suekou/mcp-notion-server)
    * [Slack MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/slack)

## 技術スタック

*   Python 3.12+
*   [Agent Development Kit (ADK) by Google](https://google.github.io/adk-docs/)
*   [Slack Bolt for Python](https://tools.slack.dev/bolt-python/)
*   [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol/modelcontextprotocol)
*   [LiteLLM](https://github.com/BerriAI/litellm)
*   [uv](https://github.com/astral-sh/uv) (Python パッケージ管理)

## セットアップ

1.  **リポジトリのクローン:**
    ```bash
    git clone <repository_url>
    cd slack-agent-development-kit-mcp
    ```

2.  **環境変数の設定:**

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定します。`.env.example` を参考にしてください。

```dotenv
# Slack
SLACK_BOT_TOKEN="xoxb-..." # Bot User OAuth Token
SLACK_APP_TOKEN="xapp-..." # App-Level Token (Socket Mode を使用する場合)
SLACK_TEAM_ID="T..."      # Slack Team ID (Slack MCP Server 用)

# Notion
NOTION_API_TOKEN="secret_..." # Notion Integration Token

# Google AI (Gemini) - 使用するモデルに応じて設定
# GOOGLE_API_KEY="AI..."

# その他 (必要に応じて)
# PORT=3000 # HTTP モードで使用するポート (デフォルト: 3000)
```

*   **Slack トークン**: Slack アプリの設定ページから取得します。Socket Mode を有効にする場合は `SLACK_APP_TOKEN` が必要です。
*   **Notion トークン**: Notion のインテグレーション設定ページから取得します。

3.  **依存関係のインストール:**

[uv](https://github.com/astral-sh/uv) を使用して依存関係をインストールします。

```bash
uv sync
```

## 実行

以下のコマンドでアプリケーションを実行します。

```bash
uv run python slack_agent/app.py
```

*   `.env` ファイルに `SLACK_APP_TOKEN` が設定されている場合、**Socket Mode** で起動します。
*   `SLACK_APP_TOKEN` が設定されていない場合、**HTTP Mode** で起動します (デフォルトポート: 3000)。HTTP Mode を使用するには、Slack アプリ設定で Request URL の設定が必要です。


または、 `adk web` でエージェントの動作確認をすることもできます。

```bash
uv run adk web
```
