import asyncio
from typing import Annotated
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import TextContent, ImageContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field, AnyUrl

import markdownify
import httpx
import readabilipy

# --- Load environment variables ---
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

# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- Fetch Utility Class ---
class Fetch:
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(
        cls,
        url: str,
        user_agent: str,
        force_raw: bool = False,
    ) -> tuple[str, str]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": user_agent},
                    timeout=30,
                )
            except httpx.HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))

            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))

            page_raw = response.text

        content_type = response.headers.get("content-type", "")
        is_page_html = "text/html" in content_type

        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""

        return (
            page_raw,
            f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
        )

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        """Extract and convert HTML content to Markdown format."""
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret or not ret.get("content"):
            return "<error>Page failed to be simplified from HTML</error>"
        content = markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)
        return content

    @staticmethod
    async def google_search_links(query: str, num_results: int = 5) -> list[str]:
        """
        Perform a scoped DuckDuckGo search and return a list of job posting URLs.
        (Using DuckDuckGo because Google blocks most programmatic scraping.)
        """
        ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        links = []

        async with httpx.AsyncClient() as client:
            resp = await client.get(ddg_url, headers={"User-Agent": Fetch.USER_AGENT})
            if resp.status_code != 200:
                return ["<error>Failed to perform search.</error>"]

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", class_="result__a", href=True):
            href = a["href"]
            if "http" in href:
                links.append(href)
            if len(links) >= num_results:
                break

        return links or ["<error>No results found.</error>"]

# --- MCP Server Setup ---
mcp = FastMCP(
    "Job Finder MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Tool: job_finder (now smart!) ---
JobFinderDescription = RichToolDescription(
    description="Smart job tool: analyze descriptions, fetch URLs, or search jobs based on free text.",
    use_when="Use this to evaluate job descriptions or search for jobs using freeform goals.",
    side_effects="Returns insights, fetched job descriptions, or relevant job links.",
)

# --- job_finder tool commented out ---
# @mcp.tool(description=JobFinderDescription.model_dump_json())
# async def job_finder(
#     user_goal: Annotated[str, Field(description="The user's goal (can be a description, intent, or freeform query)")],
#     job_description: Annotated[str | None, Field(description="Full job description text, if available.")] = None,
#     job_url: Annotated[AnyUrl | None, Field(description="A URL to fetch a job description from.")] = None,
#     raw: Annotated[bool, Field(description="Return raw HTML content if True")] = False,
# ) -> str:
#     """
#     Handles multiple job discovery methods: direct description, URL fetch, or freeform search query.
#     """
#     if job_description:
#         return (
#             f"📝 **Job Description Analysis**\n\n"
#             f"---\n{job_description.strip()}\n---\n\n"
#             f"User Goal: **{user_goal}**\n\n"
#             f"💡 Suggestions:\n- Tailor your resume.\n- Evaluate skill match.\n- Consider applying if relevant."
#         )
#
#     if job_url:
#         content, _ = await Fetch.fetch_url(str(job_url), Fetch.USER_AGENT, force_raw=raw)
#         return (
#             f"🔗 **Fetched Job Posting from URL**: {job_url}\n\n"
#             f"---\n{content.strip()}\n---\n\n"
#             f"User Goal: **{user_goal}**"
#         )
#
#     if "look for" in user_goal.lower() or "find" in user_goal.lower():
#         links = await Fetch.google_search_links(user_goal)
#         return (
#             f"🔍 **Search Results for**: _{user_goal}_\n\n" +
#             "\n".join(f"- {link}" for link in links)
#         )
#
#     raise McpError(ErrorData(code=INVALID_PARAMS, message="Please provide either a job description, a job URL, or a search query in user_goal."))

#    user_goal: Annotated[str, Field(description="The user's goal (can be a description, intent, or freeform query)")],
#    job_description: Annotated[str | None, Field(description="Full job description text, if available.")] = None,
#    job_url: Annotated[AnyUrl | None, Field(description="A URL to fetch a job description from.")] = None,
#    raw: Annotated[bool, Field(description="Return raw HTML content if True")] = False,
#) -> str:
#    """
#    Handles multiple job discovery methods: direct description, URL fetch, or freeform search query.
#    """
#    if job_description:
#        return (
#            f"📝 **Job Description Analysis**\n\n"
#            f"---\n{job_description.strip()}\n---\n\n"
#            f"User Goal: **{user_goal}**\n\n"
#            f"💡 Suggestions:\n- Tailor your resume.\n- Evaluate skill match.\n- Consider applying if relevant."
#        )
#
#    if job_url:
#        content, _ = await Fetch.fetch_url(str(job_url), Fetch.USER_AGENT, force_raw=raw)
#        return (
#            f"🔗 **Fetched Job Posting from URL**: {job_url}\n\n"
#            f"---\n{content.strip()}\n---\n\n"
#            f"User Goal: **{user_goal}**"
#        )
#
#    if "look for" in user_goal.lower() or "find" in user_goal.lower():
#        links = await Fetch.google_search_links(user_goal)
#        return (
#            f"🔍 **Search Results for**: _{user_goal}_\n\n" +
#            "\n".join(f"- {link}" for link in links)
#        )
#
#    raise McpError(ErrorData(code=INVALID_PARAMS, message="Please provide either a job description, a job URL, or a search query in user_goal."))


# --- In-memory inventory store ---
# For demo: user_id -> list of ingredients
user_inventories = {}

# For demo: add a test user with some ingredients
user_inventories["demo_user"] = ["Paneer", "Tomatoes", "Onions", "Capsicum", "Milk"]

# # --- Placeholder: Fridge & Pantry Scan Tool ---
# SCAN_FRIDGE_PANTRY_DESCRIPTION = RichToolDescription(
#     description="Scan a fridge or pantry image and extract a list of visible ingredients using Gemini Vision (placeholder).",
#     use_when="User sends a photo of their fridge or pantry to get a list of ingredients.",
#     side_effects="Returns a list of detected ingredients as text.",
# )
#
# @mcp.tool(description=SCAN_FRIDGE_PANTRY_DESCRIPTION.model_dump_json())
# async def scan_fridge_pantry(
#     user_id: Annotated[str, Field(description="Unique user identifier")],
#     puch_image_data: Annotated[str, Field(description="Base64-encoded image data of the fridge or pantry")],
# ) -> list[TextContent]:
#     # Placeholder: return a static list for demo
#     example_ingredients = ["Paneer", "Tomatoes", "Onions", "Capsicum", "Milk"]
#     user_inventories[user_id] = example_ingredients
#     return [TextContent(type="text", text=", ".join(example_ingredients))]
#
# --- Suggest Recipe Tool ---
from typing import Dict

SUGGEST_RECIPE_DESCRIPTION = RichToolDescription(
    description="Suggest a recipe based on a provided list of ingredients using Gemini LLM.",
    use_when="User provides a list of ingredients and asks for a recipe suggestion.",
    side_effects="Returns a recipe suggestion and a static image URL.",
)

@mcp.tool(description=SUGGEST_RECIPE_DESCRIPTION.model_dump_json())
@mcp.tool(description=SUGGEST_RECIPE_DESCRIPTION.model_dump_json())
async def suggest_recipe(
    ingredients_text: Annotated[str, Field(description="Comma- or newline-separated list of ingredients")],
) -> Dict[str, str]:
    """
    Suggest a recipe based on the user's inventory using Gemini LLM.
    Returns: {recipe: str, image_url: str}
    """
    # 1. Parse ingredients from provided text
    inventory = [item.strip() for item in ingredients_text.replace('\n', ',').split(',') if item.strip()]
    if not inventory:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="No valid ingredients found in provided text."))

    # 2. Use Gemini LLM to suggest a recipe
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="google-genai is not installed. Please install it with 'pip install google-genai'."))

    # API key from env
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="GEMINI_API_KEY or GOOGLE_API_KEY not set in environment."))

    client = genai.Client(api_key=api_key)
    prompt = f"Given these ingredients: {', '.join(inventory)}, suggest a simple Indian vegetarian recipe that uses mostly these items. Reply with the recipe name and a short description."  # You can tune this prompt
    response = await asyncio.to_thread(
        client.models.generate_content,
        model='gemini-2.0-flash-001',
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=256, temperature=0.4),
    )
    recipe_text = response.text.strip()

    # 3. Map recipe name to image URL (hardcoded for demo)
    # Extract recipe name (first line or up to first period)
    recipe_name = recipe_text.split('\n')[0].split('.')[0].strip()
    recipe_image_map = {
        "Paneer Bhurji": "https://static.toiimg.com/thumb/53099611.cms?imgsize=275494&width=800&height=800",
        "Aloo Gobi": "https://www.indianhealthyrecipes.com/wp-content/uploads/2021/12/aloo-gobi-recipe.jpg",
        "Tomato Soup": "https://www.vegrecipesofindia.com/wp-content/uploads/2021/01/tomato-soup-recipe-1.jpg",
        # Add more mappings as needed
    }
    # Default image if not found
    image_url = recipe_image_map.get(recipe_name, "https://www.themealdb.com/images/media/meals/ustsqw1468250014.jpg")

    return {"recipe": recipe_text, "image_url": image_url}

# Image inputs and sending images

SCAN_GROCERY_BILL_DESCRIPTION = RichToolDescription(
    description="Scan a grocery bill image and extract a list of purchased items using Azure AI Vision OCR.",
    use_when="Use this tool when the user sends a photo of a grocery bill to extract item names.",
    side_effects="Returns a list of detected grocery items as text.",
)

@mcp.tool(description=SCAN_GROCERY_BILL_DESCRIPTION.model_dump_json())
async def scan_grocery_bill(
    user_id: Annotated[str, Field(description="Unique user identifier")],
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data of the grocery bill")],
) -> list[TextContent]:
    import base64
    import io
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    
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
        import time
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
            # Update inventory for user
            if user_id in user_inventories:
                user_inventories[user_id].extend([item for item in items if item not in user_inventories[user_id]])
            else:
                user_inventories[user_id] = items
            return [TextContent(type="text", text="\n".join(items))]
        else:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="OCR failed to extract text from image."))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION = RichToolDescription(
#     description="Convert an image to black and white and save it.",
#     use_when="Use this tool when the user provides an image URL and requests it to be converted to black and white.",
#     side_effects="The image will be processed and saved in a black and white format.",
# )

# @mcp.tool(description=MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION.model_dump_json())
# async def make_img_black_and_white(
#    puch_image_data: Annotated[str, Field(description="Base64-encoded image data to convert to black and white")] = None,
#) -> list[TextContent | ImageContent]:
#    import base64
#    import io
#
#    from PIL import Image
#
#    try:
#        image_bytes = base64.b64decode(puch_image_data)
#        image = Image.open(io.BytesIO(image_bytes))
#
#        bw_image = image.convert("L")
#
#        buf = io.BytesIO()
#        bw_image.save(buf, format="PNG")
#        bw_bytes = buf.getvalue()
#        bw_base64 = base64.b64encode(bw_bytes).decode("utf-8")
#
#        return [ImageContent(type="image", mimeType="image/png", data=bw_base64)]
#    except Exception as e:
#        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
