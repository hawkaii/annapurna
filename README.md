# MCP Starter for Puch AI

This is a starter template for creating your own Model Context Protocol (MCP) server that works with Puch AI. It comes with ready-to-use tools for job searching and image processing.

## What is MCP?

MCP (Model Context Protocol) allows AI assistants like Puch to connect to external tools and data sources safely. Think of it like giving your AI extra superpowers without compromising security.

## What's Included in This Starter?

### 🎯 Job Finder Tool
- **Analyze job descriptions** - Paste any job description and get smart insights
- **Fetch job postings from URLs** - Give a job posting link and get the full details
- **Search for jobs** - Use natural language to find relevant job opportunities

### 🖼️ Image Processing Tool
- **Convert images to black & white** - Upload any image and get a monochrome version

### 🧾 Grocery Bill OCR Tool
- **Scan grocery bills for items** - Upload a photo of a grocery bill and extract a list of purchased items using Microsoft Azure AI Vision OCR

### 🔐 Built-in Authentication
- Bearer token authentication (required by Puch AI)
- Validation tool that returns your phone number

## Quick Setup Guide

### Step 1: Install Dependencies

First, make sure you have Python 3.11 or higher installed. Then:

```bash
# Create virtual environment
uv venv

# Install all required packages
uv sync

# Activate the environment
source .venv/bin/activate
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and add your details:

```env
AUTH_TOKEN=your_secret_token_here
MY_NUMBER=919876543210
VISION_KEY=your_azure_vision_key_here
VISION_ENDPOINT=your_azure_vision_endpoint_here
```

**Important Notes:**
- `AUTH_TOKEN`: This is your secret token for authentication. Keep it safe!
- `MY_NUMBER`: Your WhatsApp number in format `{country_code}{number}` (e.g., `919876543210` for +91-9876543210)
- `VISION_KEY` and `VISION_ENDPOINT`: Required for the grocery bill OCR tool. Get these from your Azure AI Vision resource in the Azure Portal.

### Step 3: Run the Server

```bash
cd mcp-bearer-token
python mcp_starter.py
```

You'll see: `🚀 Starting MCP server on http://0.0.0.0:8086`

### Step 4: Make It Public (Required by Puch)

Since Puch needs to access your server over HTTPS, you need to expose your local server:

#### Option A: Using ngrok (Recommended)

1. **Install ngrok:**
   Download from https://ngrok.com/download

2. **Get your authtoken:**
   - Go to https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your authtoken
   - Run: `ngrok config add-authtoken YOUR_AUTHTOKEN`

3. **Start the tunnel:**
   ```bash
   ngrok http 8086
   ```

#### Option B: Deploy to Cloud

You can also deploy this to services like:
- Railway
- Render
- Heroku
- DigitalOcean App Platform

## Usage Example: Scan Grocery Bill

You can call the `scan_grocery_bill` tool with a base64-encoded image of a grocery bill. The tool will return a list of detected items (excluding totals, prices, etc.) using Microsoft Azure AI Vision OCR.

**Example tool call:**
```json
{
  "tool": "scan_grocery_bill",
  "params": {
    "puch_image_data": "<base64-encoded-image>"
  }
}
```

---

## How to Connect with Puch AI

1. **[Open Puch AI](https://wa.me/+919998881729)** in your browser
2. **Start a new conversation**
3. **Use the connect command:**
   ```
   /mcp connect https://your-domain.ngrok.app/mcp your_secret_token_here
   ```

### Debug Mode

To get more detailed error messages:

```
/mcp diagnostics-level debug
```

## Customizing the Starter

### Adding New Tools

1. **Create a new tool function:**
   ```python
   @mcp.tool(description="Your tool description")
   async def your_tool_name(
       parameter: Annotated[str, Field(description="Parameter description")]
   ) -> str:
       # Your tool logic here
       return "Tool result"
   ```

2. **Add required imports** if needed


## 📚 **Additional Documentation Resources**

### **Official Puch AI MCP Documentation**
- **Main Documentation**: https://puch.ai/mcp
- **Protocol Compatibility**: Core MCP specification with Bearer & OAuth support
- **Command Reference**: Complete MCP command documentation
- **Server Requirements**: Tool registration, validation, HTTPS requirements

### **Technical Specifications**
- **JSON-RPC 2.0 Specification**: https://www.jsonrpc.org/specification (for error handling)
- **MCP Protocol**: Core protocol messages, tool definitions, authentication

### **Supported vs Unsupported Features**

**✓ Supported:**
- Core protocol messages
- Tool definitions and calls
- Authentication (Bearer & OAuth)
- Error handling

**✗ Not Supported:**
- Videos extension
- Resources extension
- Prompts extension

## Getting Help

- **Join Puch AI Discord:** https://discord.gg/VMCnMvYx
- **Check Puch AI MCP docs:** https://puch.ai/mcp
- **Puch WhatsApp Number:** +91 99988 81729

---

**Happy coding! 🚀**

Use the hashtag `#BuildWithPuch` in your posts about your MCP!

This starter makes it super easy to create your own MCP server for Puch AI. Just follow the setup steps and you'll be ready to extend Puch with your custom tools!
