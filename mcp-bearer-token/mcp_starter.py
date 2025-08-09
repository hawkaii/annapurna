import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Ensure project root is in sys.path for sibling imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# --- Standard Library Imports ---
import asyncio
from typing import Annotated
from datetime import date

# --- Third-Party Imports ---
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field

# --- Local Imports ---
from nutrition_tracker.tracker import get_nutrition_from_gemini
from datetime import datetime

# --- Load Environment Variables ---
load_dotenv()
TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# --- Tool Description Model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- MCP Server Setup ---
mcp = FastMCP(
    "Nutrition Tracker MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Validation Tool (required by Puch) ---
@mcp.tool
def validate() -> str:
    return MY_NUMBER

# --- Nutrition Logging Tool (commented out for now) ---
# LOG_FOOD_DESCRIPTION = RichToolDescription(
#     description="Log a food and amount for nutrition tracking (uses Gemini for nutrition info).",
#     use_when="User provides a food and amount to log for nutrition tracking.",
#     side_effects="Updates the user's nutrition log and returns a nutrition summary for the logged food.",
# )
#
# @mcp.tool(description=LOG_FOOD_DESCRIPTION.model_dump_json())
# async def log_food(
#     user_id: Annotated[str, Field(description="Unique user identifier")],
#     food: Annotated[str, Field(description="Food name, e.g. 'apple'")],
#     amount: Annotated[float, Field(description="Amount (e.g. 2 for 2 apples or 100 for 100g rice)")]
# ) -> str:
#     """
#     Log a food and amount for nutrition tracking (uses Gemini for nutrition info).
#     """
#     # if not user_id:
#     #     raise McpError(ErrorData(code=INVALID_PARAMS, message="User ID is required."))
#     # if not food or not isinstance(food, str):
#     #     raise McpError(ErrorData(code=INVALID_PARAMS, message="Food name is required."))
#     # if amount is None or not isinstance(amount, (int, float)):
#     #     raise McpError(ErrorData(code=INVALID_PARAMS, message="Amount must be a number."))
#
#     try:
#         nutrition = get_nutrition_from_gemini(food, amount)
#         if not nutrition:
#             return f"Sorry, I couldn't get nutrition info for {amount} {food}."
#         # db_log_food(user_id, food, amount, nutrition)  # Database logging disabled for testing
#         return (
#             f"✅ (Test) Logged {amount} {food}.\n"
#             f"Calories: {nutrition['calories']}, Protein: {nutrition['protein']}g, "
#             f"Carbs: {nutrition['carbs']}g, Fat: {nutrition['fat']}g"
#         )
#     except Exception as e:
#         raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error logging food: {e}"))

# --- Nutrition Details Tool (no DB, just Gemini) ---
GET_NUTRITION_DESCRIPTION = RichToolDescription(
    description="""
    Use this tool to get detailed nutrition information for any food or meal, and log it to a text file for tracking.\n
    Provide the user ID, food name, and the amount (with units, e.g., '2 eggs', '100g chicken breast').\n    The tool will return calories, macronutrients, and other nutrition facts as estimated by Gemini AI, and will log the entry in a plain text file (nutrition_log.txt) for future reference.
    """,
    use_when="User provides a food and amount to log for nutrition tracking (with text file logging).",
    side_effects="Logs the food, amount, and nutrition info to a text file (nutrition_log.txt) in the project directory.",
)

@mcp.tool(description=GET_NUTRITION_DESCRIPTION.model_dump_json())
async def get_nutrition(
    user_id: Annotated[str, Field(description="Unique user identifier")],
    food: Annotated[str, Field(description="Food name, e.g. 'apple'")],
    amount: Annotated[float, Field(description="Amount (e.g. 2 for 2 apples or 100 for 100g rice)")]
) -> dict:
    """
    Returns the nutrition details for the given food and amount using Gemini, and logs the entry in a text file.
    """
    if not user_id:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="User ID is required."))
    nutrition = get_nutrition_from_gemini(food, amount)
    if not nutrition:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Could not get nutrition info for {amount} {food}."))
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'food': food,
            'amount': amount,
            'nutrition': nutrition
        }
        with open('nutrition_log.txt', 'a') as f:
            f.write(str(log_entry) + '\n')
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error logging food to text file: {e}"))
    return nutrition

# --- Nutrition Summary Tool ---
@mcp.tool(description="Get today's nutrition summary for the user")
async def nutrition_summary(
    user_id: Annotated[str, Field(description="Unique user identifier")],
) -> str:
    if not user_id:
        return "Sorry, we couldn't identify you. Please try again."
    today = date.today()
    try:
        summary = get_daily_summary(user_id, today)
        return (
            f"Today's totals:\n"
            f"Calories: {summary['calories']}\n"
            f"Protein: {summary['protein']}g\n"
            f"Carbs: {summary['carbs']}g\n"
            f"Fat: {summary['fat']}g"
        )
    except Exception as e:
        return f"Sorry, there was an error getting your nutrition summary: {e}"

# --- Am I a Hero Tool ---
AM_I_A_HERO_DESCRIPTION = RichToolDescription(
    description="Responds 'you are hero' if the user asks 'am I a hero'.",
    use_when="User asks if they are a hero.",
    side_effects="Returns a positive affirmation if the user asks 'am I a hero'.",
)

@mcp.tool(description=AM_I_A_HERO_DESCRIPTION.model_dump_json())
async def am_i_a_hero(
    question: Annotated[str, Field(description="The user's question")]
) -> str:
    if question.strip().lower() == "am i a hero":
        return "you are hero"
    return "Ask me if you are a hero!"

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
