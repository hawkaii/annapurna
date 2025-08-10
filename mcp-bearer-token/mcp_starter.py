import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Ensure project root is in sys.path for sibling imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# --- Standard Library Imports ---
import asyncio
from typing import Annotated
from datetime import date
import ast
import base64
import io
import time

# --- Third-Party Imports ---
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

# --- Local Imports ---
from nutrition_tracker.tracker import get_nutrition_from_gemini, suggest_dishes_from_gemini
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
    # Database logging removed as requested
    return nutrition

# --- Nutrition Board Tool ---
NUTRITION_BOARD_DESCRIPTION = RichToolDescription(
    description="""
    Returns the user's current nutrition scoreboard (totals) from nutrition_totals.txt.\n
    Use this to see the running total of calories, protein, carbs, and fat consumed by the user so far.
    """,
    use_when="User wants to see their nutrition totals/scoreboard.",
    side_effects="None. Only reads from nutrition_totals.txt.",
)

@mcp.tool(description=NUTRITION_BOARD_DESCRIPTION.model_dump_json())
async def nutrition_board(
    user_id: Annotated[str, Field(description="Unique user identifier")],
) -> dict:
    """
    Returns the user's current nutrition scoreboard (totals) from nutrition_totals.txt.
    """
    import ast
    if not user_id:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="User ID is required."))
    from nutrition_tracker.db import AsyncSessionLocal
    from nutrition_tracker.models import User, NutritionTotals
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.user_id == user_id))).scalar_one_or_none()
        if not user:
            return {"user_id": user_id, "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        totals = (await session.execute(select(NutritionTotals).where(NutritionTotals.user_id == user.id))).scalar_one_or_none()
        if not totals:
            return {"user_id": user_id, "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        return {
            "user_id": user_id,
            "calories": totals.calories,
            "protein": totals.protein,
            "carbs": totals.carbs,
            "fat": totals.fat,
        }

# --- Dish Suggestion Tool ---
SUGGEST_DISHES_DESCRIPTION = RichToolDescription(
    description="""
    Suggests 3 creative, healthy dish names using ONLY the provided ingredients.\n
    Provide a list of ingredients (e.g., ['egg', 'spinach', 'cheese']).\n    The tool will return a JSON array of 3 possible dish names.\n    Powered by Gemini.
    """,
    use_when="User wants to know what dishes they can make with available ingredients.",
    side_effects="None. Only returns dish name suggestions, does not log or store anything.",
)

@mcp.tool(description=SUGGEST_DISHES_DESCRIPTION.model_dump_json())
async def suggest_dishes(
    ingredients: Annotated[list[str], Field(description="List of available ingredients (e.g. ['egg', 'spinach', 'cheese'])")],
) -> list[str]:
    """
    Suggests 3 and dish names using ONLY the provided ingredients, write the quantiy of ingredients used and returned them in a numbered list, via Gemini.
    """
    if not ingredients or not isinstance(ingredients, list):
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Ingredients must be a non-empty list of strings."))
    dishes = suggest_dishes_from_gemini(ingredients)
    if not dishes:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Could not get dish suggestions from Gemini."))
    return dishes

# --- Lock Dish Tool ---
LOCK_DISH_DESCRIPTION = RichToolDescription(
    description="""
    Log a custom dish and its nutrition facts to the nutrition tracker (text file database).\n
    Provide the user ID, dish name, and a nutrition dictionary (calories, protein, carbs, fat).\n    The tool will append this entry to nutrition_log.txt for the user, with amount=1.\n    This allows custom or suggested dishes to be included in the user's daily nutrition summary.
    """,
    use_when="User wants to add a custom or suggested dish to their daily nutrition log.",
    side_effects="Appends the dish and its nutrition to nutrition_log.txt for the user.",
)

@mcp.tool(description=LOCK_DISH_DESCRIPTION.model_dump_json())
async def lock_dish(
    user_id: Annotated[str, Field(description="Unique user identifier")],
    dish: Annotated[str, Field(description="Name of the dish to log")],
    nutrition: Annotated[dict, Field(description="Nutrition facts for the dish (must include: calories, protein, carbs, fat)")],
) -> dict:
    """
    Log a custom dish and its nutrition facts to the nutrition tracker (text file database), and increment the user's nutrition totals in nutrition_totals.txt.
    """
    from datetime import datetime
    import ast
    required_keys = {"calories", "protein", "carbs", "fat"}
    if not user_id:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="User ID is required."))
    if not dish:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Dish name is required."))
    if not nutrition or not required_keys.issubset(nutrition):
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Nutrition must include calories, protein, carbs, and fat."))
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'food': dish,
        'amount': 1,
        'nutrition': {k: float(nutrition[k]) for k in required_keys}
    }
    from nutrition_tracker.db import AsyncSessionLocal
    from nutrition_tracker.models import User, NutritionLog, NutritionTotals
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        # Get or create user
        user = (await session.execute(select(User).where(User.user_id == user_id))).scalar_one_or_none()
        if not user:
            user = User(user_id=user_id)
            session.add(user)
            await session.flush()
        # Add nutrition log for dish
        log = NutritionLog(user_id=user.id, food=dish, amount=1, calories=nutrition['calories'], protein=nutrition['protein'], carbs=nutrition['carbs'], fat=nutrition['fat'])
        session.add(log)
        # Update totals
        totals = (await session.execute(select(NutritionTotals).where(NutritionTotals.user_id == user.id))).scalar_one_or_none()
        if not totals:
            totals = NutritionTotals(
                user_id=user.id,
                calories=0.0,
                protein=0.0,
                carbs=0.0,
                fat=0.0,
            )
            session.add(totals)
        totals.calories = (totals.calories or 0.0) + nutrition['calories']
        totals.protein = (totals.protein or 0.0) + nutrition['protein']
        totals.carbs = (totals.carbs or 0.0) + nutrition['carbs']
        totals.fat = (totals.fat or 0.0) + nutrition['fat']
        await session.commit()
    return log_entry

# --- Am I a Hero Tool ---

AM_I_A_HERO_DESCRIPTION = RichToolDescription(
    description="Responds 'you are hero' if the user asks 'am I a hero'. Optionally, echoes the user's mobile number if provided.",
    use_when="User asks if they are a hero. Use the mobile parameter to personalize the response.",
    side_effects="Returns a positive affirmation if the user asks 'am I a hero', and echoes the mobile number if provided.",
)

@mcp.tool(description=AM_I_A_HERO_DESCRIPTION.model_dump_json())
async def am_i_a_hero(
    question: Annotated[str, Field(description="The user's question")],
    mobile: Annotated[str, Field(description="The user's mobile number")]
) -> str:
    if question.strip().lower() == "am i a hero":
        return f"you are hero (mobile: {mobile})"
    return "Ask me if you are a hero!"

# --- Grocery Bill OCR Tool ---
SCAN_GROCERY_BILL_DESCRIPTION = RichToolDescription(
    description="Scan a grocery bill image and extract a list of purchased items using Azure AI Vision OCR.",
    use_when="Use this tool when the user sends a photo of a grocery bill to extract item names.",
    side_effects="Returns a list of detected grocery items as text.",
)

@mcp.tool(description=SCAN_GROCERY_BILL_DESCRIPTION.model_dump_json())
async def scan_grocery_bill(
    user_id: Annotated[str, Field(description="Unique user identifier")],
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data of the grocery bill")],
) -> list:
    import base64
    import io
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    import time

    VISION_KEY = os.environ.get("VISION_KEY")
    VISION_ENDPOINT = os.environ.get("VISION_ENDPOINT")
    if not VISION_KEY or not VISION_ENDPOINT:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Azure Vision credentials not set in environment."))
    try:
        image_bytes = base64.b64decode(puch_image_data)
        computervision_client = ComputerVisionClient(
            VISION_ENDPOINT, CognitiveServicesCredentials(VISION_KEY)
        )
        image_stream = io.BytesIO(image_bytes)
        read_response = computervision_client.read_in_stream(image_stream, raw=True)
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        while True:
            result = computervision_client.get_read_result(operation_id)
            if result.status not in ["notStarted", "running"]:
                break
            time.sleep(1)
        if result.status == OperationStatusCodes.succeeded:
            lines = []
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    lines.append(line.text)
            # Simple heuristic: filter out lines that look like totals, prices, etc.
            items = [l for l in lines if l and not any(x in l.lower() for x in ["total", "amount", "price", "rs", "$", "qty", "tax"])]
            # Return detected items (no inventory update)
            return items
        else:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="OCR failed to extract text from image."))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
