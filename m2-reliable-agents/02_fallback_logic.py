"""
Module 2, Demo 2: Implementing Fallback and Recovery Logic
===========================================================
This demo shows how to add error handling, retry logic, and
graceful degradation to make agents more reliable.
"""

import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_order_status(order_id: str, simulate_error: str = None) -> dict:
    """Get order status - can simulate various errors for testing"""

    # Simulate different error types
    if simulate_error == "timeout":
        return {"error": "timeout", "message": "Request timed out", "retryable": True}
    if simulate_error == "service_unavailable":
        return {"error": "service_unavailable", "message": "Service temporarily unavailable", "retryable": True}
    
    # Real logic
    orders = {
        "ORD-12345": {"order_id": "ORD-12345", "status": "delivered", "items": ["Blue Widget"]},
        "ORD-67890": {"order_id": "ORD-67890", "status": "in_transit", "items": ["Green Tool"]}
    }
    return orders.get(order_id, {"error": "not_found", "message": f"Order {order_id} not found", "retryable": False})


def check_inventory(product_id: str, simulate_error: str = None) -> dict:
    """Check product inventory"""
    if simulate_error == "rate_limit":
        return {"error": "rate_limit", "message": "Too many requests", "retryable": True}
    
    inventory = {
        "blue-widget": {"product_id": "blue-widget", "name": "Blue Widget", "in_stock": True, "quantity": 45},
        "green-tool": {"product_id": "green-tool", "name": "Green Tool", "in_stock": False, "quantity": 0}
    }
    return inventory.get(product_id, {"error": "not_found", "message": f"Product {product_id} not found", "retryable": False})


# Tool schemas
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
            "description": "Check if a product is in stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product identifier"}
                },
                "required": ["product_id"]
            }
        }
    }
]

available_functions = {
    "get_order_status": get_order_status,
    "check_inventory": check_inventory
}


def execute_with_retry(func, args: dict, max_retries: int = 3) -> dict:
    """Execute function with exponential backoff retry for transient errors"""

    for attempt in range(max_retries):
        result = func(**args)
        
        # Success or non-retryable error - return immediately
        if "error" not in result or not result.get("retryable"):
            return result
        
        # Retryable error - wait and retry
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            print(f"  Retryable error: {result['error']}")
            print(f"  Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait_time)
    
    return {"error": "max_retries", "message": f"Failed after {max_retries} attempts", "retryable": False}


def get_fallback_response(error: str) -> str:
    """Generate user-friendly fallback response based on error type"""
    fallbacks = {
        "not_found": "I couldn't find that. Please double-check the ID and try again.",
        "timeout": "Our system is running slow. Would you like me to try again?",
        "rate_limit": "We're experiencing high traffic. Please wait a moment.",
        "service_unavailable": "Our system is temporarily unavailable. Try again in a few minutes.",
        "max_retries": "I'm having trouble accessing our systems. Let me connect you with support@globomantics.com"
    }
    return fallbacks.get(error, "I encountered an issue. Please contact support@globomantics.com")


def run_agent_with_fallback(user_message: str, simulate_error: str = None):
    """Run agent with error handling and fallback logic"""
    
    print(f"USER: {user_message}")
    if simulate_error:
        print(f"[Simulating: {simulate_error}]")
    
    system_prompt = """You are a customer support agent for Globomantics.
Use get_order_status for order questions and check_inventory for stock questions.
Be helpful and concise."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Get agent decision
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        tools=tools
    )
    
    response_message = response.choices[0].message
    
    # No tool call - just respond
    if not response_message.tool_calls:
        print(f"\nAgent: {response_message.content}")
        return
    
    # Process tool call
    tool_call = response_message.tool_calls[0]
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    # Inject error simulation
    if simulate_error:
        function_args["simulate_error"] = simulate_error
    
    arg_id = function_args.get('order_id') or function_args.get('product_id')
    print(f"\nCalling: {function_name}({arg_id})")
    
    # Execute with retry logic
    func = available_functions[function_name]
    result = execute_with_retry(func, function_args)
    
    # Handle error with fallback
    if "error" in result:
        print(f"\nError: {result['error']} - {result['message']}")
        print(f"\nAgent: {get_fallback_response(result['error'])}")
        return
    
    # Success - get final response
    print(f"\nSuccess: {json.dumps(result, indent=2)}")
    
    messages.append(response_message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    })
    
    final = client.chat.completions.create(model="gpt-5-mini", messages=messages)
    print(f"\nAgent: {final.choices[0].message.content}")


def main():
    print("\n" + "="*60)
    print("DEMO: Fallback and Recovery Logic")
    print("="*60)
    
    scenarios = [
        ("Success", "Where is order ORD-12345?", None),
        ("Retryable - timeout", "Check order ORD-67890", "timeout"),
        ("Retryable - rate limit", "Is blue-widget in stock?", "rate_limit"),
        ("Non-retryable - not found", "Where is order ORD-99999?", None),
    ]
    
    for title, query, error in scenarios:
        print(f"\n{'-'*60}")
        print(f"SCENARIO: {title}")
        print(f"{'-'*60}\n")
        run_agent_with_fallback(query, error)
        input("\n[Press Enter to continue...]")
    

if __name__ == "__main__":
    main()


# =============================================================================
# Example output:
# =============================================================================

# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
# DEMO: Fallback and Recovery Logic
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# ------------------------------------------------------------
# SCENARIO: Success
# ------------------------------------------------------------

# USER: Where is order ORD-12345?

# Calling: get_order_status(ORD-12345)

# Success: {
#   "order_id": "ORD-12345",
#   "status": "delivered",
#   "items": [
#     "Blue Widget"
#   ]
# }

# Agent: Your order ORD-12345 has been delivered. It included a Blue Widget. If you have any further questions, feel free to ask!

# [Press Enter to continue ...]

# ------------------------------------------------------------
# SCENARIO: Retryable - timeout
# ------------------------------------------------------------

# USER: Check order ORD-67890
# [Simulating: timeout]

# Calling: get_order_status(ORD-67890)
#   Retryable error: timeout
#   Waiting 1s before retry(attempt 1/3)...
#   Retryable error: timeout
#   Waiting 2s before retry(attempt 2/3)...

# Error: max_retries - Failed after 3 attempts

# Agent: I'm having trouble accessing our systems. Let me connect you with support@globomantics.com

# [Press Enter to continue...]

# ------------------------------------------------------------
# SCENARIO: Retryable - rate limit
# ------------------------------------------------------------

# USER: Is blue-widget in stock?
# [Simulating: rate_limit]

# Calling: check_inventory(blue-widget)
#   Retryable error: rate_limit
#   Waiting 1s before retry (attempt 1/3)...
#   Retryable error: rate_limit
#   Waiting 2s before retry (attempt 2/3)...

# Error: max_retries - Failed after 3 attempts

# Agent: I'm having trouble accessing our systems. Let me connect you with support@globomantics.com

# [Press Enter to continue...]

# ------------------------------------------------------------
# SCENARIO: Non-retryable - not found
# ------------------------------------------------------------

# USER: Where is order ORD-99999?

# Calling: get_order_status(ORD-99999)

# Error: not_found - Order ORD-99999 not found

# Agent: I couldn't find that. Please double-check the ID and try again.

# [Press Enter to continue...]