import os
import sqlite3
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

# ==========================================
# 1. DEFINE THE LLM TOOL (DATABASE CONNECTOR)
# ==========================================


@tool
def query_garmin_database(sql_query: str) -> str:
    """
    Executes a read-only SQL query against the Garmin daily health metrics database.
    The database contains a single table named 'daily_metrics'.
    Columns:
      - date (TEXT, format YYYY-MM-DD)
      - sleep_score (INTEGER, scale 0-100)
      - hrv_status (INTEGER, milliseconds)
      - resting_heart_rate (INTEGER, bpm)
      - body_battery_max (INTEGER, scale 0-100)
      - training_load (INTEGER, arbitrary metrics value)
    Returns the raw database output rows as a string list of tuples.
    """
    try:
        conn = sqlite3.connect("garmin_health.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return str(results)
    except Exception as e:
        return f"Database Error: {str(e)}"


# ==========================================
# 2. INITIALIZE THE CORE AGENT LOGIC
# ==========================================


def run_coaching_agent(user_prompt: str):
    # Verify OpenAI Key is present before attempting to run
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your terminal using: export OPENAI_API_KEY='your_key'")
        return

    print(f"\n🏃 User Question: {user_prompt}")

    # Initialize LLM with low temperature for high precision/no code hallucinations
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    # Bind the tool schema directly to the model configuration
    tools = [query_garmin_database]
    llm_with_tools = llm.bind_tools(tools)

    # Append the system context rules directly into the chat array
    messages = [
        HumanMessage(
            content=(
                f"You are a strict, elite athletic performance coach. Use the query_garmin_database "
                f"tool to pull physical historical context whenever a user asks about their performance trend. "
                f"If metrics show high training loads combined with poor sleep scores under 60, aggressively advise "
                f"them to take a recovery/rest day to prevent overtraining injuries.\n\nUser Question: {user_prompt}"
            )
        )
    ]

    # Step A: Let LLM analyze prompt and decide if it needs to call a tool
    response = llm_with_tools.invoke(messages)
    messages.append(response)

    # Step B: Check if the model requested tool execution
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(
                f"🛠️ [Agent Think]: I need to fetch data. Calling tool: {tool_call['name']}"
            )
            print(f"📊 [Generated SQL Query]: {tool_call['args']['sql_query']}")

            # Programmatically call the tool function locally using the LLM's arguments
            tool_output = query_garmin_database.invoke(tool_call["args"])

            # Pass the raw database output string back to the conversation chain
            messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )

        # Step C: Send full context (User Question + SQL Results) back for final synthesis
        final_response = llm_with_tools.invoke(messages)
        print(f"\n🤖 AI Coach Response:\n{final_response.content}")
    else:
        print(f"\n🤖 AI Coach Response:\n{response.content}")


if __name__ == "__main__":
    # Test execution prompt
    sample_question = "How has my sleep been trending over the last 3 days, and should I push hard on my run today?"
    run_coaching_agent(sample_question)
