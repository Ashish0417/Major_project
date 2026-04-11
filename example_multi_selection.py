"""
Example: Using the new itinerary selection system
Shows how to generate 3 itineraries and let user select top 3
"""

from llm_orchestrator import TravelItineraryOrchestrator
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    """
    Example usage of the new multi-itinerary selection system
    """
    
    print("\n" + "="*80)
    print("🌍 TRAVEL ITINERARY GENERATOR - MULTI-OPTION SELECTION")
    print("="*80)
    
    # Initialize orchestrator
    orchestrator = TravelItineraryOrchestrator()
    
    if not orchestrator.llm:
        print("❌ Setup required: Check GOOGLE_API_KEY in .env")
        return
    
    # Example trip details
    trip_details = {
        'origin_city': 'Bangalore',
        'destination_city': 'Paris',
        'departure_date': '2026-04-15',
        'num_days': 7,
        'budget_inr': 200000,
        'interests': ['museums', 'food', 'architecture'],
        'dietary_restrictions': ['vegetarian'],
        'user_id': 'demo_user_123'  # Can store to database
    }
    
    print("\n📋 TRIP DETAILS:")
    print(f"  From: {trip_details['origin_city']}")
    print(f"  To: {trip_details['destination_city']}")
    print(f"  Duration: {trip_details['num_days']} days")
    print(f"  Budget: ₹{trip_details['budget_inr']:,}")
    print(f"  Interests: {', '.join(trip_details['interests'])}")
    
    print("\n🔄 Generating 3 itinerary strategies...")
    print("   This may take 2-5 minutes depending on data availability\n")
    
    # Generate itinerary (uses new selection system internally)
    result = orchestrator.generate_itinerary(trip_details)
    
    if result:
        print("\n" + "="*80)
        print("✅ ITINERARY SUCCESSFULLY GENERATED AND SAVED!")
        print("="*80)
        print(f"\nYour selected itinerary has been saved to the database.")
        print(f"Total Cost: ₹{result.get('total_cost', 0):,.2f}")
        print(f"Duration: {result.get('num_days')} days")
        print(f"\nYou can retrieve this itinerary from your account at any time.")
    else:
        print("\n" + "="*80)
        print("❌ ITINERARY GENERATION CANCELLED")
        print("="*80)


def interactive_demo():
    """
    Interactive demo - natural language queries
    """
    
    orchestrator = TravelItineraryOrchestrator()
    
    if not orchestrator.llm:
        print("❌ Setup required: Check GOOGLE_API_KEY in .env")
        return
    
    print("\n" + "="*80)
    print("🌍 INTERACTIVE TRAVEL PLANNER")
    print("="*80)
    print("\nDescribe your trip in natural language!")
    print("Examples:")
    print("  • 'Plan a 5-day trip from Mumbai to Singapore with ₹100000 budget'")
    print("  • 'I want to visit Tokyo for a week from Delhi'")
    print("  • 'Create a budget trip from Bangalore to Bali for 3 days'")
    print("\nType 'quit' to exit")
    
    while True:
        query = input("\n🎯 Your query: ").strip()
        
        if query.lower() == 'quit':
            print("\n👋 Thank you for using Travel Planner!")
            break
        
        if not query:
            continue
        
        # Use natural language query to generate itinerary
        response = orchestrator.ask(query, user_id='interactive_user')
        print(f"\n{response}")


if __name__ == "__main__":
    print("\n📍 TRAVEL ITINERARY MULTI-SELECTION DEMO")
    print("="*80)
    print("\nChoose mode:")
    print("1. Structured trip (define details explicitly)")
    print("2. Interactive (describe trip in natural language)")
    print("3. Demo with sample trip")
    
    choice = input("\nEnter Choice (1-3): ").strip()
    
    if choice == "1":
        # Structured mode - user enters details
        print("\n📝 ENTER YOUR TRIP DETAILS\n")
        
        origin = input("From (city): ").strip()
        destination = input("To (city): ").strip()
        departure = input("Departure date (YYYY-MM-DD): ").strip()
        num_days = int(input("Number of days: ").strip() or "7")
        budget = float(input("Budget (INR): ").strip() or "150000")
        interests_str = input("Interests (comma-separated, optional): ").strip()
        
        trip_details = {
            'origin_city': origin,
            'destination_city': destination,
            'departure_date': departure,
            'num_days': num_days,
            'budget_inr': budget,
            'interests': [i.strip() for i in interests_str.split(',')] if interests_str else [],
            'user_id': f"user_{hash(origin + destination) % 10000}"
        }
        
        orchestrator = TravelItineraryOrchestrator()
        orchestrator.generate_itinerary(trip_details)
        
    elif choice == "2":
        interactive_demo()
    elif choice == "3":
        main()
    else:
        print("Invalid choice")
