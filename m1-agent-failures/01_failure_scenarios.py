"""
Module 1, Demo 1: Agent Failure Scenarios
==========================================
Demonstrates three common agent failure modes:
1. Planning failure - agent selects wrong tool
2. Grounding failure - agent hallucinates missing information  
3. Invocation failure - agent provides wrong parameters
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =============================================================================
# SCENARIO 1: Planning Failure (Wrong Tool Selection)
# =============================================================================

def planning_failure():
    """Agent picks wrong tool due to ambiguous descriptions"""
    print("\n" + "="*60)
    print("SCENARIO 1: Planning Failure")
    print("="*60)
    
    # BAD: Tool descriptions are too similar/vague
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_order_info",
                "description": "Get information about an item",  # Vague!
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_stock",
                "description": "Check information about an item",  # Almost identical!
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            }
        }
    ]
    
    user_query = "Is the blue widget available to purchase?"
    print(f"\nUser: \"{user_query}\"")
    print(f"Expected: check_stock (inventory query)")
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_query}
        ],
        tools=tools
    )
    
    if response.choices[0].message.tool_calls:
        tool = response.choices[0].message.tool_calls[0]
        print(f"Actual: {tool.function.name}")
        
        if tool.function.name != "check_stock":
            print("PLANNING FAILURE: Agent chose wrong tool!")
        else:
            print("Agent chose correctly (may vary between runs)")
    else:
        print("Agent didn't call any tool")


# =============================================================================
# SCENARIO 2: Grounding Failure (Hallucinated Information)
# =============================================================================

def grounding_failure():
    """Agent hallucinates order ID that wasn't provided"""
    print("\n" + "="*60)
    print("SCENARIO 2: Grounding Failure")
    print("="*60)
    
    tools = [{
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get the status of an order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            }
        }
    }]
    
    # User doesn't provide order ID!
    user_query = "Where is my order? It should have arrived by now."
    print(f"\nUser: \"{user_query}\"")
    print(f"Expected: Agent should ask for order_id (not provided)")
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You must use tools to help users. Do not ask questions."},
            {"role": "user", "content": user_query}
        ],
        tools=tools,
        tool_choice="required"  # Force tool usage
    )
    
    if response.choices[0].message.tool_calls:
        tool = response.choices[0].message.tool_calls[0]
        args = json.loads(tool.function.arguments)
        print(f"Actual: {tool.function.name}({args})")
        
        if args.get("order_id"):
            print(f"GROUNDING FAILURE: Agent hallucinated order_id = '{args['order_id']}'")
    else:
        print("Agent asked for clarification (good behavior)")


# =============================================================================
# SCENARIO 3: Invocation Failure (Wrong Parameters)
# =============================================================================

def invocation_failure():
    """Agent provides wrong parameter format"""
    print("\n" + "="*60)
    print("SCENARIO 3: Invocation Failure")
    print("="*60)
    
    tools = [{
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund for an order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},  # No format hint!
                    "reason": {"type": "string"}     # No description!
                },
                "required": ["order_id", "reason"]
            }
        }
    }]
    
    # User provides incomplete/ambiguous info
    user_query = "Refund order 12345, it was damaged"
    print(f"\nUser: \"{user_query}\"")
    print(f"Expected format: order_id='ORD-12345' (with prefix)")
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_query}
        ],
        tools=tools
    )
    
    if response.choices[0].message.tool_calls:
        tool = response.choices[0].message.tool_calls[0]
        args = json.loads(tool.function.arguments)
        print(f"Actual: {tool.function.name}({json.dumps(args)})")
        
        order_id = args.get("order_id", "")
        if not order_id.startswith("ORD-"):
            print(f"INVOCATION FAILURE: Wrong format '{order_id}' (missing ORD- prefix)")
        else:
            print("Agent used correct format")
    else:
        print("Agent didn't call tool")


def main():
    print("\n" + "="*60)
    print("DEMO: Common Agent Failure Modes")
    print("="*60)
    print("""
This demo shows three types of failures that occur in AI agents: planning failure, grounding failure, and invocation failure.
    """)
    
    input("[Press Enter to see Planning Failure...]")
    planning_failure()
    
    input("\n[Press Enter to see Grounding Failure...]")
    grounding_failure()
    
    input("\n[Press Enter to see Invocation Failure...]")
    invocation_failure()
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()


# =============================================================================
# Example output:
# =============================================================================

# DEMO: Common Agent Failure Modes
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# This demo shows three types of failures that occur in AI agents: planning failure, grounding failure, and invocation failure.

# [Press Enter to see Planning Failure...]

# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
# SCENARIO 1: Planning Failure
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# User: "Is the blue widget available to purchase?"
# Expected: check_stock(inventory query)
# Agent didn't call any tool

# [Press Enter to see Grounding Failure...]

# ============================================================
# SCENARIO 2: Grounding Failure
# ============================================================

# User: "Where is my order? It should have arrived by now."
# Expected: Agent should ask for order_id (not provided)
# Actual: get_order_status({'order_id': 'unknown'})
# GROUNDING FAILURE: Agent hallucinated order_id = 'unknown'
#    Root cause: No instruction to ask for missing info

# [Press Enter to see Invocation Failure...]

# ============================================================
# SCENARIO 3: Invocation Failure
# ============================================================

# User: "Refund order 12345, it was damaged"
# Expected format: order_id='ORD-12345' (with prefix)
# Actual: process_refund({"order_id": "12345", "reason": "Damaged item received"})
# INVOCATION FAILURE: Wrong format '12345' (missing ORD- prefix)
#    Root cause: No format example in parameter description

# ============================================================