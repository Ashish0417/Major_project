"""
Interactive User Profile Builder
Collects travel preferences through conversational questions
"""

from typing import Optional, List
from datetime import datetime, timedelta
from user_profile import UserProfile, TravelPreferences, TripDates, ContactInfo
import re


class InteractiveProfileBuilder:
    """Interactive builder for user travel profiles"""

    def __init__(self):
        self.profile = UserProfile()
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'end': '\033[0m',
            'bold': '\033[1m',
        }

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{self.colors['bold']}{self.colors['header']}{text}{self.colors['end']}")
        print("=" * 70)

    def print_info(self, text: str):
        """Print info message"""
        print(f"{self.colors['blue']}ℹ️  {text}{self.colors['end']}")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{self.colors['green']}✅ {text}{self.colors['end']}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{self.colors['yellow']}⚠️  {text}{self.colors['end']}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{self.colors['red']}❌ {text}{self.colors['end']}")

    def ask_question(self, question: str, default: Optional[str] = None,
                    required: bool = True) -> str:
        """Ask a question and get user input"""
        while True:
            if default:
                prompt = f"\n{question}\n{self.colors['yellow']}[Default: {default}]{self.colors['end']}\n➤ "
            else:
                prompt = f"\n{question}\n➤ "

            answer = input(prompt).strip()

            if not answer and default:
                return default

            if not answer and required:
                self.print_error("This field is required. Please provide an answer.")
                continue

            if not answer and not required:
                return ""

            return answer

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question"""
        default_text = "Y/n" if default else "y/N"
        while True:
            answer = input(f"\n{question} [{default_text}]\n➤ ").strip().lower()

            if not answer:
                return default

            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                self.print_error("Please answer 'y' or 'n'")

    def ask_number(self, question: str, min_val: float = 0,
                  max_val: Optional[float] = None, default: Optional[float] = None) -> float:
        """Ask for a numeric input"""
        while True:
            default_str = str(default) if default else None
            answer = self.ask_question(question, default=default_str, required=default is None)

            try:
                value = float(answer)

                if value < min_val:
                    self.print_error(f"Value must be at least {min_val}")
                    continue

                if max_val and value > max_val:
                    self.print_error(f"Value must be at most {max_val}")
                    continue

                return value

            except ValueError:
                self.print_error("Please enter a valid number")

    def ask_date(self, question: str, min_date: Optional[datetime] = None) -> str:
        """Ask for a date in YYYY-MM-DD format"""
        while True:
            self.print_info("Format: YYYY-MM-DD (e.g., 2026-03-20)")
            answer = self.ask_question(question)

            try:
                date_obj = datetime.strptime(answer, '%Y-%m-%d')

                if min_date and date_obj < min_date:
                    self.print_error(f"Date must be on or after {min_date.strftime('%Y-%m-%d')}")
                    continue

                return answer

            except ValueError:
                self.print_error("Invalid date format. Please use YYYY-MM-DD")

    def ask_choice(self, question: str, choices: List[str],
                  allow_multiple: bool = False) -> List[str]:
        """Ask user to choose from options"""
        self.print_info("Available options:")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")

        if allow_multiple:
            self.print_info("Enter numbers separated by commas (e.g., 1,3,4)")
        else:
            self.print_info("Enter the number of your choice")

        while True:
            answer = input("➤ ").strip()

            try:
                if allow_multiple:
                    indices = [int(x.strip()) - 1 for x in answer.split(',')]
                else:
                    indices = [int(answer) - 1]

                # Validate indices
                if any(i < 0 or i >= len(choices) for i in indices):
                    self.print_error(f"Please enter numbers between 1 and {len(choices)}")
                    continue

                return [choices[i] for i in indices]

            except ValueError:
                self.print_error("Please enter valid number(s)")

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_phone(self, phone: str) -> bool:
        """Validate phone format"""
        # Accept formats like +91-1234567890 or +1-234-567-8900
        pattern = r'^\+\d{1,3}-[\d-]+$'
        return re.match(pattern, phone) is not None

    def build_profile(self) -> UserProfile:
        """Main function to build user profile interactively"""

        self.print_header("🌍 AI TRAVEL ITINERARY GENERATOR")
        print("\nWelcome! Let's plan your perfect trip together.")
        print("I'll ask you a few questions to understand your preferences.")

        # === BASIC INFORMATION ===
        self.print_header("📋 Step 1: Basic Information")

        # Name
        name = self.ask_question("What's your name?")
        self.profile.name = name
        self.print_success(f"Nice to meet you, {name}!")

        # Contact (optional but recommended)
        if self.ask_yes_no("Would you like to provide contact information? (optional)", default=False):
            while True:
                email = self.ask_question("Email address:", required=False)
                if not email or self.validate_email(email):
                    break
                self.print_error("Invalid email format")

            while True:
                self.print_info("Format: +country-number (e.g., +91-9876543210)")
                phone = self.ask_question("Phone number:", required=False)
                if not phone or self.validate_phone(phone):
                    break
                self.print_error("Invalid phone format")

            if email or phone:
                self.profile.contact = ContactInfo(
                    email=email or "not_provided@example.com",
                    phone=phone or "+00-0000000000"
                )

        # === DESTINATION ===
        self.print_header("📍 Step 2: Destination")

        destination = self.ask_question("Where would you like to go?",
                                       default="Tokyo, Japan")
        self.profile.destinations = [destination]
        self.print_success(f"Great choice! {destination} it is!")

        # === DATES ===
        self.print_header("📅 Step 3: Travel Dates")

        today = datetime.now()
        min_start = today + timedelta(days=1)

        start_date = self.ask_date("When do you want to start your trip?", min_date=min_start)
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')

        min_end = start_dt + timedelta(days=1)
        end_date = self.ask_date("When do you want to end your trip?", min_date=min_end)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        trip_days = (end_dt - start_dt).days + 1
        self.profile.dates = TripDates(start=start_date, end=end_date)
        self.print_success(f"Your trip will be {trip_days} days long!")

        # === BUDGET ===
        self.print_header("💰 Step 4: Budget")

        # Currency selection
        currencies = ["INR", "USD", "EUR", "GBP", "JPY"]
        self.print_info("What currency would you like to use?")
        currency_choice = self.ask_choice("Select currency:", currencies)[0]
        self.profile.default_currency = currency_choice

        # Total budget
        total_budget = self.ask_number(
            f"What's your total budget for the trip? (in {currency_choice})",
            min_val=1000
        )

        per_day_budget = total_budget / trip_days
        self.print_info(f"That's approximately {per_day_budget:,.2f} {currency_choice} per day")

        if self.ask_yes_no("Is this daily budget acceptable?", default=True):
            budget_per_day = per_day_budget
        else:
            budget_per_day = self.ask_number(
                f"What's your preferred daily budget? (in {currency_choice})",
                min_val=100,
                max_val=total_budget
            )
            total_budget = budget_per_day * trip_days
            self.print_info(f"Adjusted total budget: {total_budget:,.2f} {currency_choice}")

        # === COMFORT LEVEL ===
        self.print_header("🛏️ Step 5: Comfort Level")

        comfort_levels = ["economy", "premium", "luxury"]
        self.print_info("Economy: Budget-friendly options")
        self.print_info("Premium: Comfortable mid-range options")
        self.print_info("Luxury: High-end premium options")

        comfort_level = self.ask_choice("What's your preferred comfort level?",
                                       comfort_levels)[0]
        self.print_success(f"Got it! Looking for {comfort_level} options.")

        # === PREFERENCES ===
        self.print_header("🎯 Step 6: Travel Preferences")

        # Transport
        transport_options = ["flight", "train", "bus", "car rental"]
        transport_pref = self.ask_choice("Preferred modes of transport?",
                                        transport_options, allow_multiple=True)

        # Accommodation
        accommodation_options = ["hotel", "apartment", "hostel", "guesthouse"]
        accommodation_pref = self.ask_choice("Preferred accommodation types?",
                                            accommodation_options, allow_multiple=True)

        # === DIETARY RESTRICTIONS ===
        self.print_header("🍽️ Step 7: Dietary Preferences")

        if self.ask_yes_no("Do you have any dietary restrictions?", default=False):
            dietary_options = ["vegetarian", "vegan", "gluten-free", "halal", "kosher", "none"]
            dietary_restrictions = self.ask_choice("Select your dietary restrictions:",
                                                  dietary_options, allow_multiple=True)
            if "none" in dietary_restrictions:
                dietary_restrictions = []
        else:
            dietary_restrictions = []

        # === INTERESTS ===
        self.print_header("🎨 Step 8: Activity Interests")

        interest_options = [
            "museums", "art", "history", "culture", "culinary", "food",
            "hiking", "outdoor", "adventure", "shopping", "nightlife",
            "beaches", "nature", "photography", "architecture"
        ]

        self.print_info("What are you interested in? (Choose at least 2)")
        activity_interests = self.ask_choice("Select your interests:",
                                            interest_options, allow_multiple=True)

        if len(activity_interests) < 2:
            self.print_warning("We recommend selecting at least 2 interests for better recommendations")
            if self.ask_yes_no("Would you like to add more interests?"):
                more_interests = self.ask_choice("Select additional interests:",
                                                interest_options, allow_multiple=True)
                activity_interests.extend(more_interests)
                activity_interests = list(set(activity_interests))  # Remove duplicates

        # === THINGS TO AVOID ===
        self.print_header("🚫 Step 9: Things to Avoid")

        if self.ask_yes_no("Are there things you'd like to avoid?", default=False):
            avoid_options = [
                "red-eye flights", "early morning activities", "late-night travel",
                "long walks", "crowded places", "heights", "water activities"
            ]
            avoid = self.ask_choice("Select things to avoid:", avoid_options,
                                   allow_multiple=True)
        else:
            avoid = []

        # === ACTIVITY LIMITS ===
        self.print_header("⏱️ Step 10: Activity Preferences")

        max_activities = self.ask_number(
            "Maximum activities per day?",
            min_val=1,
            max_val=8,
            default=4
        )

        max_travel = self.ask_number(
            "Maximum daily travel time (in minutes)?",
            min_val=30,
            max_val=300,
            default=90
        )

        # === BUILD PREFERENCES ===
        self.profile.travel_preferences = TravelPreferences(
            budget_total=total_budget,
            budget_per_day=budget_per_day,
            comfort_level=comfort_level,
            transport_pref=transport_pref,
            accommodation_pref=accommodation_pref,
            dietary_restrictions=dietary_restrictions,
            activity_interests=activity_interests,
            avoid=avoid,
            max_daily_travel_minutes=int(max_travel),
            max_activities_per_day=int(max_activities)
        )

        # === DATA CONSENT ===
        self.print_header("🔒 Step 11: Data Storage")

        store_history = self.ask_yes_no(
            "May we save your trip for future recommendations?",
            default=True
        )
        share_anonymized = self.ask_yes_no(
            "May we use anonymized data to improve recommendations?",
            default=False
        )

        self.profile.consent = {
            "store_history": store_history,
            "share_anonymized": share_anonymized
        }

        # === SUMMARY ===
        self.print_header("📊 Profile Summary")
        self.display_summary()

        if self.ask_yes_no("\nIs this information correct?", default=True):
            self.print_success("Great! Your profile is complete!")
            return self.profile
        else:
            if self.ask_yes_no("Would you like to start over?"):
                return self.build_profile()
            else:
                self.print_info("You can edit specific fields or continue with current profile")
                return self.profile

    def display_summary(self):
        """Display profile summary"""
        p = self.profile
        prefs = p.travel_preferences

        print(f"\n{self.colors['bold']}👤 Name:{self.colors['end']} {p.name}")
        print(f"{self.colors['bold']}📍 Destination:{self.colors['end']} {p.destinations[0]}")
        print(f"{self.colors['bold']}📅 Dates:{self.colors['end']} {p.dates.start} to {p.dates.end}")
        print(f"{self.colors['bold']}💰 Budget:{self.colors['end']} {prefs.budget_total:,.2f} {p.default_currency} ({prefs.budget_per_day:,.2f}/day)")
        print(f"{self.colors['bold']}🛏️ Comfort:{self.colors['end']} {prefs.comfort_level}")
        print(f"{self.colors['bold']}🚗 Transport:{self.colors['end']} {', '.join(prefs.transport_pref)}")
        print(f"{self.colors['bold']}🏨 Accommodation:{self.colors['end']} {', '.join(prefs.accommodation_pref)}")

        if prefs.dietary_restrictions:
            print(f"{self.colors['bold']}🍽️ Dietary:{self.colors['end']} {', '.join(prefs.dietary_restrictions)}")

        print(f"{self.colors['bold']}🎨 Interests:{self.colors['end']} {', '.join(prefs.activity_interests)}")

        if prefs.avoid:
            print(f"{self.colors['bold']}🚫 Avoid:{self.colors['end']} {', '.join(prefs.avoid)}")

        print(f"{self.colors['bold']}⏱️ Max activities/day:{self.colors['end']} {prefs.max_activities_per_day}")
        print(f"{self.colors['bold']}🚗 Max daily travel:{self.colors['end']} {prefs.max_daily_travel_minutes} minutes")

    def save_profile(self, filename: str = "my_travel_profile.json"):
        """Save profile to JSON file"""
        try:
            self.profile.to_json(filepath=filename)
            self.print_success(f"Profile saved to {filename}")
            return True
        except Exception as e:
            self.print_error(f"Error saving profile: {e}")
            return False


def main():
    """Main function for testing"""
    builder = InteractiveProfileBuilder()
    profile = builder.build_profile()

    # Ask if user wants to save
    print("\n" + "="*70)
    if builder.ask_yes_no("Would you like to save this profile?", default=True):
        filename = builder.ask_question(
            "Enter filename:",
            default="my_travel_profile.json",
            required=False
        )
        builder.save_profile(filename or "my_travel_profile.json")

    return profile


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌍 INTERACTIVE PROFILE BUILDER - STANDALONE MODE")
    print("="*70)
    print("\nThis module creates travel profiles interactively.")
    print("Import this in main.py to use with the travel generator.\n")
    
    profile = main()
    print("\n✅ Profile creation complete!")
    print("\nTo use this profile with the travel generator:")
    print("  python main.py")
