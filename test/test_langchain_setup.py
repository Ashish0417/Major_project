"""
Test script to verify LangChain integration
Run this after installation to ensure everything works
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test that all required packages are installed"""
    print("\n" + "="*70)
    print("TESTING IMPORTS")
    print("="*70)
    
    tests = []
    
    # Test LangChain imports
    try:
        import langchain
        print(f"✅ langchain: {langchain.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ langchain: {e}")
        tests.append(False)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ langchain-google-genai: imported")
        tests.append(True)
    except ImportError as e:
        print(f"❌ langchain-google-genai: {e}")
        tests.append(False)
    
    try:
        from langchain.agents import create_react_agent, AgentExecutor
        print("✅ langchain.agents: imported")
        tests.append(True)
    except ImportError as e:
        print(f"❌ langchain.agents: {e}")
        tests.append(False)
    
    try:
        from langchain.tools import StructuredTool
        print("✅ langchain.tools: imported")
        tests.append(True)
    except ImportError as e:
        print(f"❌ langchain.tools: {e}")
        tests.append(False)
    
    try:
        from pydantic import BaseModel, Field
        import pydantic
        print(f"✅ pydantic: {pydantic.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ pydantic: {e}")
        tests.append(False)
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai: imported")
        tests.append(True)
    except ImportError as e:
        print(f"❌ google-generativeai: {e}")
        tests.append(False)
    
    try:
        from ortools.sat.python import cp_model
        print("✅ ortools: imported")
        tests.append(True)
    except ImportError as e:
        print(f"❌ ortools: {e}")
        tests.append(False)
    
    return all(tests)


def test_environment():
    """Test environment variables"""
    print("\n" + "="*70)
    print("TESTING ENVIRONMENT VARIABLES")
    print("="*70)
    
    tests = []
    
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        print(f"✅ GOOGLE_API_KEY: {google_key[:20]}...")
        tests.append(True)
    else:
        print("❌ GOOGLE_API_KEY: Not found")
        print("   Get your free key from: https://makersuite.google.com/app/apikey")
        tests.append(False)
    
    amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
    if amadeus_id:
        print(f"✅ AMADEUS_CLIENT_ID: {amadeus_id[:20]}...")
        tests.append(True)
    else:
        print("⚠️  AMADEUS_CLIENT_ID: Not found (using defaults)")
        tests.append(True)  # Not critical
    
    amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if amadeus_secret:
        print(f"✅ AMADEUS_CLIENT_SECRET: {amadeus_secret[:20]}...")
        tests.append(True)
    else:
        print("⚠️  AMADEUS_CLIENT_SECRET: Not found (using defaults)")
        tests.append(True)  # Not critical
    
    return all(tests)


def test_langchain_llm():
    """Test LangChain LLM initialization"""
    print("\n" + "="*70)
    print("TESTING LANGCHAIN LLM")
    print("="*70)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Cannot test LLM without GOOGLE_API_KEY")
            return False
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        print("✅ LLM initialized successfully")
        
        # Test a simple invocation
        response = llm.invoke("Say 'Hello from LangChain!'")
        print(f"✅ LLM response: {response.content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM test failed: {str(e)[:100]}")
        return False


def test_structured_tools():
    """Test structured tool creation"""
    print("\n" + "="*70)
    print("TESTING STRUCTURED TOOLS")
    print("="*70)
    
    try:
        from langchain.tools import StructuredTool
        from pydantic import BaseModel, Field
        
        class TestInput(BaseModel):
            text: str = Field(description="Input text")
        
        def test_function(text: str) -> str:
            return f"Processed: {text}"
        
        tool = StructuredTool.from_function(
            func=test_function,
            name="test_tool",
            description="A test tool",
            args_schema=TestInput
        )
        
        result = tool.invoke({"text": "hello"})
        
        if result == "Processed: hello":
            print("✅ Structured tool created and invoked successfully")
            return True
        else:
            print(f"❌ Tool returned unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Structured tool test failed: {str(e)[:100]}")
        return False


def test_agents():
    """Test project-specific agents"""
    print("\n" + "="*70)
    print("TESTING PROJECT AGENTS")
    print("="*70)
    
    tests = []
    
    try:
        from flight_agent import FlightAgent
        agent = FlightAgent(use_real_api=False)
        print("✅ FlightAgent: imported and initialized")
        tests.append(True)
    except Exception as e:
        print(f"❌ FlightAgent: {str(e)[:100]}")
        tests.append(False)
    
    try:
        from accommodation_agent import AccommodationAgent
        agent = AccommodationAgent()
        print("✅ AccommodationAgent: imported and initialized")
        tests.append(True)
    except Exception as e:
        print(f"❌ AccommodationAgent: {str(e)[:100]}")
        tests.append(False)
    
    try:
        from restaurant_agent import RestaurantAgent
        agent = RestaurantAgent()
        print("✅ RestaurantAgent: imported and initialized")
        tests.append(True)
    except Exception as e:
        print(f"❌ RestaurantAgent: {str(e)[:100]}")
        tests.append(False)
    
    try:
        from activity_agent import ActivityAgent
        agent = ActivityAgent()
        print("✅ ActivityAgent: imported and initialized")
        tests.append(True)
    except Exception as e:
        print(f"❌ ActivityAgent: {str(e)[:100]}")
        tests.append(False)
    
    return all(tests)


def test_main_orchestrator():
    """Test the main LangChain orchestrator"""
    print("\n" + "="*70)
    print("TESTING MAIN ORCHESTRATOR")
    print("="*70)
    
    try:
        from llm_orchestrator import LangChainTravelAgent
        
        agent = LangChainTravelAgent()
        
        if agent.llm is None:
            print("⚠️  Orchestrator initialized but LLM not available (check API key)")
            return False
        
        if agent.agent_executor is None:
            print("⚠️  Orchestrator initialized but agent executor not available")
            return False
        
        print("✅ LangChainTravelAgent: initialized successfully")
        print(f"✅ Tools available: {len(agent.agent_executor.tools) if agent.agent_executor else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {str(e)[:100]}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 LANGCHAIN INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {
        "Imports": test_imports(),
        "Environment": test_environment(),
        "LangChain LLM": test_langchain_llm(),
        "Structured Tools": test_structured_tools(),
        "Project Agents": test_agents(),
        "Main Orchestrator": test_main_orchestrator(),
    }
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nYou're ready to use the LangChain Travel Agent!")
        print("Run: python llm_orchestrator.py")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("="*70)
        print("\nPlease fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set GOOGLE_API_KEY in .env file")
        print("3. Check that all agent files are present")
        return 1


if __name__ == "__main__":
    sys.exit(main())