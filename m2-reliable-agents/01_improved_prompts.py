"""
Module 2, Demo 1: Improving Agent Prompts
=========================================
Shows how better system prompts and tool descriptions improve agent reliability.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =============================================================================
# BAD CONFIG: Vague prompts + confusing tool descriptions
# =============================================================================

BAD_SYSTEM_PROMPT = "You are an assistant. Always use a tool to help. Never ask clarifying questions."

BAD_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get info",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check info",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "string"}},
                "required": ["product_id"]
            }
        }
    }
]


# =============================================================================
# GOOD CONFIG: Clear prompts + distinct tool descriptions
# =============================================================================

GOOD_SYSTEM_PROMPT = """You are a customer support agent for Globomantics.

AVAILABLE TOOLS:
- get_order: Get order status. Use ONLY for order tracking questions.
- check_stock: Check product availability. Use ONLY for stock questions.

RULES:
1. If order_id is not provided, ASK for it - never guess.
2. Convert product names to IDs: "Laptop Stand" -> "laptop-stand"
"""

GOOD_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get order status. USE WHEN: 'where is my order', 'order status'. DO NOT USE for product questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID (format: ORD-XXX). Ask if not provided."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check product availability. USE WHEN: 'is X in stock', 'do you have X', 'check X'. DO NOT USE for orders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID in lowercase-hyphen format. Example: 'Blue Widget' -> 'blue-widget'"
                    }
                },
                "required": ["product_id"]
            }
        }
    }
]


def run_agent(system_prompt: str, tools: list, query: str) -> dict:
    """Run agent and return tool call or text response"""
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        tools=tools
    )
    
    msg = response.choices[0].message
    if msg.tool_calls:
        tool = msg.tool_calls[0]
        return {"tool": tool.function.name, "args": json.loads(tool.function.arguments)}
    return {"text": msg.content}


def compare(query: str, expected: str):
    """Compare bad vs good config responses"""
    print(f"\nQuery: \"{query}\"")
    print(f"Expected: {expected}")
    
    bad = run_agent(BAD_SYSTEM_PROMPT, BAD_TOOLS, query)
    good = run_agent(GOOD_SYSTEM_PROMPT, GOOD_TOOLS, query)
    
    print(f"\n  [BAD]  ", end="")
    if "tool" in bad:
        print(f"{bad['tool']}({bad['args']})")
    else:
        print(f"Text: {bad['text'][:60]}...")
    
    print(f"  [GOOD] ", end="")
    if "tool" in good:
        print(f"{good['tool']}({good['args']})")
    else:
        print(f"Text: {good['text'][:60]}...")


def main():
    print("="*60)
    print("DEMO: Improving Agent Prompts")
    print("="*60)
    
    print("\nBAD CONFIG: Vague descriptions like 'Get information'")
    print("GOOD CONFIG: Clear guidance with 'USE WHEN' / 'DO NOT USE'\n")
    
    input("[Press Enter to continue...]")
    
    # Test 1: Parameter formatting - BAD passes raw name, GOOD converts
    print("-"*60)
    print("TEST 1: Parameter Format (product name -> ID)")
    print("-"*60)
    compare(
        query="Do you have the Laptop Stand in stock?",
        expected="GOOD: 'laptop-stand', BAD: 'Laptop Stand' or similar"
    )
    
    input("\n[Press Enter to continue...]")
    
    # Test 2: Missing info - BAD guesses, GOOD asks
    print("\n" + "-"*60)
    print("TEST 2: Missing Information Handling")
    print("-"*60)
    compare(
        query="Where is my order?",
        expected="GOOD asks for order_id, BAD hallucinates one"
    )
    
    print("\n" + "="*60)
    print("KEY TAKEAWAYS")
    print("="*60)
    print("""
Good prompts include:
  - Parameter format examples (name -> ID conversion)
  - Rules for missing info (ask, don't guess)
""")


if __name__ == "__main__":
    main()


# =============================================================================
# Example output:
# =============================================================================

# == == == == == == == == == == == == == == == == == == == == == == == == ==
# DEMO: Improving Agent Prompts
# == == == == == == == == == == == == == == == == == == == == == == == == ==

# BAD CONFIG: Vague descriptions like 'Get information'
# GOOD CONFIG: Clear guidance with 'USE WHEN' / 'DO NOT USE'

# --------------------------------------------------
# TEST 1: Parameter Format(product name -> ID)
# --------------------------------------------------

# Query: "Do you have the Laptop Stand in stock?"
# Expected: GOOD: 'laptop-stand', BAD: 'Laptop Stand' or similar

#   [BAD]  check_stock({'product_id': 'Laptop Stand'})
#   [GOOD] check_stock({'product_id': 'laptop-stand'})

# --------------------------------------------------
# TEST 2: Missing Information Handling
# --------------------------------------------------

# Query: "Where is my order?"
# Expected: GOOD asks for order_id, BAD hallucinates one

#   [BAD]  get_order({'order_id': '12345'})
#   [GOOD] Text: Could you please provide your order ID so I can check the st...

# == == == == == == == == == == == == == == == == == == == == == == == == ==
# KEY TAKEAWAYS
# == == == == == == == == == == == == == == == == == == == == == == == == ==

# Good prompts include:
#   - Parameter format examples(name -> ID conversion)
#   - Rules for missing info(ask, don't guess)
