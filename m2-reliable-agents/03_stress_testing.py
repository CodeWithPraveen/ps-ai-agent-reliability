"""
Module 2, Demo 3: Stress Testing Agent Behavior
================================================
Shows how to run automated tests to verify agent reliability.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Retrieve order status. Use when customer asks about order delivery or tracking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order identifier (ORD-XXXXX)"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check if a product is in stock. Use for availability questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product ID (lowercase-hyphen format)"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund. Use when customer explicitly requests return or refund.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order identifier"},
                    "reason": {"type": "string", "description": "Reason for refund"}
                },
                "required": ["order_id", "reason"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a customer support agent for Globomantics.

Tools:
- get_order_status: Check order status (requires order_id)
- check_inventory: Check product availability (requires product_id)
- process_refund: Process refund (requires order_id and reason)

Rules:
1. If order_id is not provided, ASK for it - never guess
2. Convert product names to IDs: "Blue Widget" -> "blue-widget"
"""


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_test(query: str, expected_tool: str = None, expected_args: dict = None) -> dict:
    """Run a single test and return results"""
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        tools=tools
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        tool = msg.tool_calls[0]
        actual_tool = tool.function.name
        actual_args = json.loads(tool.function.arguments)
        
        # Check tool selection
        tool_match = (actual_tool == expected_tool) if expected_tool else True
        
        # Check arguments (if specified)
        args_match = True
        if expected_args:
            for key, value in expected_args.items():
                if actual_args.get(key) != value:
                    args_match = False
                    break
        
        return {
            "tool": actual_tool,
            "args": actual_args,
            "passed": tool_match and args_match
        }
    else:
        # No tool call - pass if we expected no tool
        return {
            "text": msg.content[:60] + "...",
            "passed": expected_tool is None
        }


def print_result(name: str, query: str, result: dict, expected: str):
    """Print formatted test result"""
    status = "PASS" if result["passed"] else "FAIL"
    print(f"\n  {name}: {status}")
    print(f"    Query: \"{query}\"")
    print(f"    Expected: {expected}")
    
    if "tool" in result:
        print(f"    Actual: {result['tool']}({result['args']})")
    else:
        print(f"    Actual: [No tool] {result['text']}")


def main():
    print("\n" + "="*60)
    print("DEMO: Stress Testing Agent Behavior")
    print("="*60)
    print("\nThis demo runs automated tests to verify agent reliability.")
    
    results = []
    
    # -------------------------------------------------------------------------
    # TEST CATEGORY 1: Tool Selection
    # -------------------------------------------------------------------------
    input("\n[Press Enter to run Tool Selection tests...]")
    print("\n" + "-"*60)
    print("CATEGORY 1: Tool Selection")
    print("-"*60)
    
    tests = [
        ("Inventory check", "Is the blue widget in stock?", 
         "check_inventory", {"product_id": "blue-widget"}),
        ("Order tracking", "Where is my order ORD-12345?", 
         "get_order_status", {"order_id": "ORD-12345"}),
        ("Refund request", "I want to refund ORD-67890, it was damaged", 
         "process_refund", {"order_id": "ORD-67890"}),
    ]
    
    for name, query, tool, args in tests:
        result = run_test(query, tool, args)
        results.append(result)
        print_result(name, query, result, f"{tool}({args})")
    
    # -------------------------------------------------------------------------
    # TEST CATEGORY 2: Missing Information Handling
    # -------------------------------------------------------------------------
    input("\n[Press Enter to run Missing Information tests...]")
    print("\n" + "-"*60)
    print("CATEGORY 2: Missing Information Handling")
    print("-"*60)
    
    tests = [
        ("No order ID", "I want to return my order", None, None),
        ("No product", "Check if it's in stock", None, None),
    ]
    
    for name, query, tool, args in tests:
        result = run_test(query, tool, args)
        results.append(result)
        print_result(name, query, result, "Should ask for clarification (no tool)")
    
    # -------------------------------------------------------------------------
    # TEST CATEGORY 3: Edge Cases
    # -------------------------------------------------------------------------
    input("\n[Press Enter to run Edge Case tests...]")
    print("\n" + "-"*60)
    print("CATEGORY 3: Edge Cases")
    print("-"*60)
    
    tests = [
        ("Terse query", "blue widget stock?", 
         "check_inventory", {"product_id": "blue-widget"}),
        ("Natural phrasing", "Do you have red gadgets available?", 
         "check_inventory", {"product_id": "red-gadget"}),
    ]
    
    for name, query, tool, args in tests:
        result = run_test(query, tool, args)
        results.append(result)
        print_result(name, query, result, f"{tool}({args})")
    
    # SUMMARY
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\n  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass Rate: {(passed/total)*100:.0f}%")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()


# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
# Example output:
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
# DEMO: Stress Testing Agent Behavior
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# This demo runs automated tests to verify agent reliability.

# [Press Enter to run Tool Selection tests...]

# ------------------------------------------------------------
# CATEGORY 1: Tool Selection
# ------------------------------------------------------------

#  Inventory check: PASS
#    Query: "Is the blue widget in stock?"
#     Expected: check_inventory({'product_id': 'blue-widget'})
#     Actual: check_inventory({'product_id': 'blue-widget'})

#   Order tracking: PASS
#    Query: "Where is my order ORD-12345?"
#     Expected: get_order_status({'order_id': 'ORD-12345'})
#     Actual: get_order_status({'order_id': 'ORD-12345'})

#   Refund request: PASS
#    Query: "I want to refund ORD-67890, it was damaged"
#     Expected: process_refund({'order_id': 'ORD-67890'})
#     Actual: process_refund({'order_id': 'ORD-67890', 'reason': 'Damaged item'})

# [Press Enter to run Missing Information tests...]

# ------------------------------------------------------------
# CATEGORY 2: Missing Information Handling
# ------------------------------------------------------------

#  No order ID: PASS
#    Query: "I want to return my order"
#     Expected: Should ask for clarification(no tool)
#     Actual: [No tool] I can help with that. Please provide your order ID(format l...

#                                                                          No product: PASS
#                                                                          Query: "Check if it's in stock"
#                                                                          Expected: Should ask for clarification(no tool)
#         Actual: [No tool] Which product would you like me to check? Please give either...

#         [Press Enter to run Edge Case tests...]

#         - -----------------------------------------------------------
#         CATEGORY 3: Edge Cases
#         - -----------------------------------------------------------

#         Terse query: PASS
#         Query: "blue widget stock?"
#         Expected: check_inventory({'product_id': 'blue-widget'})
#         Actual: check_inventory({'product_id': 'blue-widget'})

#         Natural phrasing: FAIL
#         Query: "Do you have red gadgets available?"
#         Expected: check_inventory({'product_id': 'red-gadget'})
#         Actual: [No tool] I can check that — could you tell me which product you mean?...

# == == ========================================================
#         TEST SUMMARY
# == == ========================================================

#         Total: 7
#         Passed: 6
#         Failed: 1
#         Pass Rate: 86 %

# == ==========================================================