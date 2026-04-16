"""
Itinerary Selector Module
Ranks multiple itineraries and provides CLI-based selection interface
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class ItinerarySummary:
    """Summary of an itinerary for comparison"""
    strategy_name: str
    total_cost: float
    num_days: int
    currency: str = "INR"
    score: float = 0.0
    combinations_evaluated: int = 0
    optimizer: str = "unknown"
    full_data: Dict[str, Any] = None
    
    def get_cost_per_day(self) -> float:
        """Calculate cost per day"""
        return self.total_cost / self.num_days if self.num_days > 0 else 0
    
    def get_budget_efficiency(self, budget: float) -> float:
        """Get efficiency score (lower is better - uses less budget)"""
        if budget <= 0:
            return float('inf')
        return self.total_cost / budget


class ItineraryRanker:
    """Ranks itineraries based on multiple criteria"""
    
    def __init__(self, budget: float):
        self.budget = budget
    
    def rank_itineraries(
        self, 
        flat_itineraries: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, ItinerarySummary]]:
        """
        Rank flat list of itineraries from all strategies.
        
        Args:
            flat_itineraries: List of (strategy_name, itinerary_data) tuples
                Example: [
                    ('One-by-One #1', {...}),
                    ('One-by-One #2', {...}),
                    ('Parallel #1', {...}),
                    ('Sequential #1', {...}),
                ]
        
        Returns:
            List of (strategy_name, summary) tuples sorted by score (best first)
        """
        summaries = []
        
        for strategy_name, itinerary in flat_itineraries:
            if itinerary is None or 'error' in itinerary:
                continue
            
            summary = self._create_summary(strategy_name, itinerary)
            if summary:
                summaries.append((strategy_name, summary))
        
        # Sort by score (lower cost per day, budget efficiency, etc.)
        summaries.sort(key=lambda x: self._compute_rank_score(x[1]))
        
        return summaries
    
    def _create_summary(self, strategy_name: str, itinerary: Dict[str, Any]) -> Optional[ItinerarySummary]:
        """Create a summary from itinerary data"""
        try:
            total_cost = itinerary.get('total_cost', 0)
            num_days = itinerary.get('num_days', 0)
            
            # Get optimizer metadata if available
            metadata = itinerary.get('optimizer_metadata', {})
            
            summary = ItinerarySummary(
                strategy_name=strategy_name,
                total_cost=total_cost,
                num_days=num_days,
                currency=itinerary.get('currency', 'INR'),
                score=metadata.get('score', 0),
                combinations_evaluated=metadata.get('combinations_evaluated', 0),
                optimizer=metadata.get('optimizer', 'unknown'),
                full_data=itinerary
            )
            return summary
        except Exception as e:
            print(f"Error creating summary for {strategy_name}: {e}")
            return None
    
    def _compute_rank_score(self, summary: ItinerarySummary) -> float:
        """
        Compute ranking score (lower is better).
        
        Factors:
        1. Budget efficiency (how close to budget without exceeding)
        2. Cost per day (value for money)
        3. Optimization score (if available)
        """
        # Primary factor: cost within budget is good, exceeding is bad
        efficiency = summary.get_budget_efficiency(self.budget)
        
        # If within budget, reward it more than exceeding budget
        if summary.total_cost <= self.budget:
            # Within budget: lower cost is better
            # Normalize to 0-1 range where 1.0 = at budget
            efficiency_score = summary.total_cost / self.budget  # 0.0 = free, 1.0 = at budget
            cost_per_day_score = summary.get_cost_per_day() / 10000  # Normalize
            
            # Final score for within-budget: emphasize staying within budget more
            score = efficiency_score * 0.6 + cost_per_day_score * 0.3 + (1 - summary.score) * 0.1 if summary.score else efficiency_score * 0.6 + cost_per_day_score * 0.4
        else:
            # Over budget: penalize heavily
            overage_penalty = (summary.total_cost - self.budget) / self.budget
            score = 1.0 + overage_penalty * 2  # At least 1.0 + overage penalty
        
        return score


class ItinerarySelector:
    """Provides CLI interface for selecting itinerary"""
    
    def __init__(self):
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'end': '\033[0m',
            'bold': '\033[1m',
        }
    
    def display_and_select(
        self, 
        ranked_itineraries: List[Tuple[str, ItinerarySummary]],
        budget: float,
        trip_details: Dict[str, Any],
        strategy_metrics: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Display all itineraries grouped by strategy, then top 3 ranked overall.
        Let user select one.
        
        Returns:
            (strategy_name, full_itinerary_data) or None if user cancels
        """
        if not ranked_itineraries:
            self._print_error("❌ No valid itineraries found")
            return None
        
        # ── Performance Summary Table ──────────────────────────────────────────
        if strategy_metrics:
            print("\n" + "="*100)
            print("📊 GENERATION PERFORMANCE SUMMARY (All 3 Methods)")
            print("="*100)
            print(f"{'Method':<25} | {'Time Taken':>12} | {'Memory Used':>13} | {'Total Cost (INR)':>18} | {'Valid':>7}")
            print("-" * 100)
            method_display = [
                ("One-by-One",  "One-by-One"),
                ("Parallel",    "Parallel"),
                ("Sequential",  "Sequential"),
            ]
            for key, label in method_display:
                m = strategy_metrics.get(key, {})
                time_s  = m.get("time_s",   0.0)
                mem_mb  = m.get("memory_mb", 0.0)
                cost    = m.get("cost",     float("inf"))
                valid   = m.get("valid",    False)
                status  = "✅ Yes" if valid else "❌ No"
                cost_str = f"₹{cost:,.0f}" if cost < float("inf") else "N/A"
                print(
                    f"{label:<25} | {time_s:>10.2f}s | {mem_mb:>+11.1f} MB | "
                    f"{cost_str:>18} | {status:>7}"
                )
            print("="*100 + "\n")

        # Group by strategy for display
        by_strategy = {}
        for idx, (strategy_name, summary) in enumerate(ranked_itineraries):
            base_strategy = strategy_name.split('#')[0].strip()  # Remove "#1", "#2", etc.
            if base_strategy not in by_strategy:
                by_strategy[base_strategy] = []
            by_strategy[base_strategy].append((strategy_name, summary))
        
        # Show all itineraries grouped by strategy
        print("\n" + "="*80)
        print("📊 ALL GENERATED ITINERARIES (Grouped by Strategy)")
        print("="*80)
        print(f"\n📍 Trip: {trip_details.get('origin_city')} → {trip_details.get('destination_city')}")
        print(f"📅 Duration: {trip_details.get('num_days')} days")
        print(f"💰 Budget: ₹{budget:,.0f}\n")
        
        for strategy, itineraries in by_strategy.items():
            print(f"\n🔹 {strategy.upper()}")
            print("-" * 80)
            for strat_name, summary in itineraries:
                cost_str = f"₹{summary.total_cost:,.0f}"
                cost_per_day = f"₹{summary.get_cost_per_day():,.0f}"
                
                # Status indicator
                if summary.total_cost <= budget:
                    status = "✅"
                elif summary.total_cost <= budget * 1.2:
                    status = "⚠️"
                else:
                    status = "❌"
                
                remaining = budget - summary.total_cost
                remaining_str = f"(Remaining: ₹{remaining:,.0f})" if remaining >= 0 else f"(Over: ₹{abs(remaining):,.0f})"
                
                print(f"  {strat_name:<25} | Cost: {cost_str:>12} | /Day: {cost_per_day:>10} | {status} {remaining_str}")
        
        # Show top 3 ranked — deduplicate first so we never show the same plan twice
        print("\n" + "="*80)
        print("🏆 TOP 3 BEST OPTIONS (Ranked Across All Strategies)")
        print("="*80 + "\n")

        def _plan_fingerprint(summary: ItinerarySummary) -> tuple:
            """Content-based fingerprint: (rounded_cost, frozenset_of_all_item_names)."""
            cost_key = round(summary.total_cost)
            all_names = []
            if summary.full_data:
                for day_items in summary.full_data.get('itinerary', {}).values():
                    for item in day_items:
                        name = getattr(item, 'name', None) or ''
                        if name:
                            all_names.append(name.strip().lower())
            return (cost_key, frozenset(all_names))

        seen_fps: set = set()
        unique_ranked: list = []
        for entry in ranked_itineraries:
            fp = _plan_fingerprint(entry[1])
            if fp not in seen_fps:
                seen_fps.add(fp)
                unique_ranked.append(entry)
            # silently skip duplicates — they were already shown grouped by strategy above

        top_3 = unique_ranked[:3]
        
        print(f"{'Rank':<6} | {'Strategy':<30} | {'Total Cost':<15} | {'Cost/Day':<12} | {'Status':<12}")
        print("-" * 90)
        
        for idx, (strategy_name, summary) in enumerate(top_3, 1):
            cost_str = f"₹{summary.total_cost:,.0f}"
            cost_per_day = f"₹{summary.get_cost_per_day():,.0f}"
            
            # Status indicator
            if summary.total_cost <= budget:
                status = "✅ Within"
                status_color = self.colors['green']
            elif summary.total_cost <= budget * 1.2:
                status = "⚠️ Slight Over"
                status_color = self.colors['yellow']
            else:
                status = "❌ Over"
                status_color = self.colors['red']
            
            print(
                f"{idx:<6} | {strategy_name:<30} | {cost_str:>13} | {cost_per_day:>10} | {status_color}{status:<12}{self.colors['end']}"
            )
        
        print("\n" + "="*80)
        print("📋 DETAILED BREAKDOWN OF TOP 3:\n")
        for idx, (strategy_name, summary) in enumerate(top_3, 1):
            print(f"\n{idx}️⃣  {strategy_name}")
            print("="*80)
            # Display full day-by-day itinerary for each top 3
            self._display_detailed_itinerary(summary, trip_details, idx)
        
        print("\n" + "="*80)
        # Get user selection
        return self._get_user_selection(top_3)
    
    
    def _display_detailed_itinerary(self, summary: ItinerarySummary, trip_details: Dict[str, Any], rank_num: int) -> None:
        """Display full day-by-day itinerary for a top 3 option"""
        itinerary = summary.full_data
        
        # Header info
        print(f"🌍 Destination: {trip_details.get('destination_city', 'N/A')}")
        print(f"📤 From: {trip_details.get('origin_city', 'N/A')}")
        print(f"💰 Total Cost: INR {itinerary.get('total_cost', 0):,.2f}")
        print(f"📅 Duration: {itinerary.get('num_days', 0)} days")
        
        # Optimization metadata
        if 'optimizer_metadata' in itinerary:
            meta = itinerary['optimizer_metadata']
            if meta.get('optimizer') == 'langgraph':
                print(f"\n🤖 LangGraph Optimization:")
                print(f"   Score: {meta.get('score', 0):.1f}/100")
                print(f"   Combinations evaluated: {meta.get('combinations_evaluated', 0)}")
        
        print("\n" + "━"*80)
        
        # Day-by-day breakdown
        itinerary_data = itinerary.get('itinerary', {})
        num_days = itinerary.get('num_days', 0)
        
        for day_num in range(num_days):
            items = itinerary_data.get(day_num, [])
            
            print(f"📅 DAY {day_num + 1}")
            print("━"*80)
            
            if not items:
                print("   🌴 Rest day / Free time")
                print()
                continue
            
            day_cost = 0
            
            for item in items:
                # Get item details
                name = getattr(item, 'name', None)
                if not name or name == 'Unknown':
                    item_type_check = (getattr(item, 'item_type', '')
                                    or getattr(item, 'category', '')).lower()
                    if 'flight' in item_type_check or 'transport' in item_type_check:
                        carrier = getattr(item, 'carrier', None)
                        if not carrier and hasattr(item, 'properties'):
                            carrier = item.properties.get('provider', '')
                        orig = getattr(item, 'origin', '')
                        dest = getattr(item, 'destination', '')
                        if not orig and hasattr(item, 'properties'):
                            orig = item.properties.get('origin', '')
                        if not dest and hasattr(item, 'properties'):
                            dest = item.properties.get('destination', '')
                        is_ret = getattr(item, 'is_return', False)
                        ret_label = ' (Return)' if is_ret else ''
                        name = (f"{carrier} {orig}→{dest}{ret_label}"
                                if carrier else f"Transport {orig}→{dest}{ret_label}")
                    else:
                        name = 'Unknown'
                
                item_type = getattr(item, 'item_type', None) or getattr(item, 'category', 'unknown')
                item_type = item_type.lower() if item_type else 'unknown'
                
                # Get icon (pass item so cuisine_type can disambiguate 'Hotel XYZ' restaurants)
                icon = self._get_item_icon(item_type, name, item=item)
                
                # Get time
                time_str = self._get_item_time(item)
                
                # Get duration
                duration_str = self._get_item_duration(item)
                
                # Get cost
                cost = self._get_item_cost(item)
                if cost:
                    day_cost += cost
                
                # Print main line
                print(f"{icon} {time_str} • {name}{duration_str}")
                
                # Print cost
                if cost > 0:
                    print(f"   💵 INR {cost:,.2f}")
                
                # Print rating
                if hasattr(item, 'rating') and item.rating and item.rating > 0:
                    stars = min(5, int(item.rating))
                    rating_str = '⭐' * stars
                    if item.rating % 1 > 0.4:
                        rating_str += '✨'
                    print(f"   {rating_str} {item.rating:.1f}/5")
                
                # Print transport details
                if item_type in ['flight', 'transport']:
                    carrier = getattr(item, 'carrier', None)
                    if not carrier and hasattr(item, 'properties') and isinstance(item.properties, dict):
                        carrier = item.properties.get('provider') or item.properties.get('carrier')
                    if carrier and carrier != 'Unknown':
                        origin = getattr(item, 'origin', '')
                        destination = getattr(item, 'destination', '')
                        if not origin and hasattr(item, 'properties'):
                            origin = item.properties.get('origin', '')
                        if not destination and hasattr(item, 'properties'):
                            destination = item.properties.get('destination', '')
                        route = f" {origin}→{destination}" if (origin and destination) else ""
                        
                        carrier_icon = self._get_item_icon(item_type, carrier)
                        
                        transport_type = ''
                        carrier_lower = carrier.lower()
                        if 'train' in carrier_lower or 'railway' in carrier_lower:
                            transport_type = ' (Train)'
                        elif 'bus' in carrier_lower or 'public' in carrier_lower:
                            transport_type = ' (Bus)'
                        elif 'taxi' in carrier_lower or 'cab' in carrier_lower or 'ola' in carrier_lower or 'uber' in carrier_lower:
                            transport_type = ' (Taxi)'
                        
                        print(f"   {carrier_icon} {carrier}{transport_type}{route}")
                    
                    if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
                        hrs = item.duration_minutes // 60
                        mins = item.duration_minutes % 60
                        print(f"   ⏱️ Duration: {hrs}h {mins}m")
                
                # Show cuisine for any item that has one (catches 'Hotel XYZ' restaurants
                # where item_type may have been set to 'accommodation' upstream)
                elif (
                    'restaurant' in item_type or 'dining' in item_type
                    or (hasattr(item, 'cuisine_type') and item.cuisine_type)
                    or (hasattr(item, 'properties') and isinstance(item.properties, dict)
                        and item.properties.get('cuisine'))
                ):
                    if hasattr(item, 'cuisine_type') and item.cuisine_type:
                        print(f"   🍜 {item.cuisine_type} cuisine")
                    elif hasattr(item, 'properties') and item.properties.get('cuisine'):
                        print(f"   🍜 {item.properties.get('cuisine')} cuisine")
            
            # Day total
            if day_cost > 0:
                print(f"\n   {'─'*76}")
                print(f"   💰 Day {day_num + 1} Total: INR {day_cost:,.2f}")
            
            print()
        
        print("="*80 + "\n")
    
    def _get_item_icon(self, item_type: str, name: str, item=None) -> str:
        """Get appropriate emoji icon for item type.
        
        IMPORTANT: item_type always wins over name-based heuristics.
        South Indian eateries are often named 'Hotel XYZ' but are restaurants.
        """
        item_type = item_type.lower()
        name_lower = name.lower()
        
        # --- 1. Transport / Flight (highest priority) ---
        if 'transport' in item_type or 'flight' in item_type or '→' in name_lower:
            if 'train' in name_lower or 'railway' in name_lower or 'rajdhani' in name_lower or 'express' in name_lower:
                return "🚆"
            elif 'bus' in name_lower or 'vrl' in name_lower or 'redbus' in name_lower or 'public transport' in name_lower:
                return "🚌"
            elif 'taxi' in name_lower or 'uber' in name_lower or 'ola' in name_lower or 'cab' in name_lower:
                return "🚕"
            elif 'car' in name_lower:
                return "🚗"
            else:
                return "✈️"
        
        # --- 2. Restaurant (check item_type BEFORE name for 'hotel') ---
        # This prevents South-Indian 'Hotel XYZ' restaurants from being
        # shown with a 🏨 icon just because 'hotel' appears in the name.
        if 'restaurant' in item_type or 'dining' in item_type:
            return "🍽️"
        
        # Also treat any item that carries a cuisine_type/cuisine as a restaurant
        if item is not None:
            has_cuisine = (
                (hasattr(item, 'cuisine_type') and item.cuisine_type)
                or (hasattr(item, 'properties') and isinstance(item.properties, dict)
                    and item.properties.get('cuisine'))
            )
            if has_cuisine:
                return "🍽️"
        
        # --- 3. Accommodation ---
        if 'accommodation' in item_type:
            return "🏨"
        
        # --- 4. Activity / Attraction ---
        if 'activity' in item_type or 'attraction' in item_type:
            return "🎭"
        
        # --- 5. Name-based fallback (only when item_type gives no signal) ---
        if 'restaurant' in name_lower or 'café' in name_lower or 'bistro' in name_lower or 'canteen' in name_lower or 'bhavan' in name_lower or 'darshini' in name_lower:
            return "🍽️"
        elif 'hotel' in name_lower or 'hôtel' in name_lower or 'inn' in name_lower or 'hostel' in name_lower or 'lodge' in name_lower:
            return "🏨"
        elif 'flight' in name_lower or 'air' in name_lower:
            return "✈️"
        elif 'train' in name_lower or 'railway' in name_lower or 'express' in name_lower:
            return "🚆"
        elif 'bus' in name_lower or 'public transport' in name_lower:
            return "🚌"
        elif 'taxi' in name_lower or 'cab' in name_lower:
            return "🚕"
        elif 'museum' in name_lower or 'palace' in name_lower or 'cathedral' in name_lower or 'tower' in name_lower or 'park' in name_lower or 'beach' in name_lower or 'garden' in name_lower:
            return "🎭"
        else:
            return "📍"
    
    def _get_item_time(self, item) -> str:
        """Extract proper time string from item"""
        # Check properties dict for scheduled_time (OptionCandidate)
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            st = item.properties.get('scheduled_time')
            if st:
                return f"[{st}]"
        
        # Check monkey-patched fallback
        if hasattr(item, '_scheduled_time') and item._scheduled_time:
            return f"[{item._scheduled_time}]"
        
        # Real departure_time on flight/transport
        if hasattr(item, 'departure_time') and item.departure_time:
            time_val = item.departure_time
            if isinstance(time_val, str):
                if 'T' in time_val:
                    time_part = time_val.split('T')[1][:5]
                    return f"[{time_part}]"
                return f"[{time_val}]"
        
        # Check properties for departure_time
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            tv = item.properties.get('departure_time')
            if tv and isinstance(tv, str) and 'T' in tv:
                return f"[{tv.split('T')[1][:5]}]"
        
        # Numeric start_time
        if hasattr(item, 'start_time') and item.start_time and item.start_time > 0:
            hours = int(item.start_time // 60)
            mins = int(item.start_time % 60)
            return f"[{hours:02d}:{mins:02d}]"
        
        # Plain string time_str
        if hasattr(item, 'time_str') and item.time_str:
            return f"[{item.time_str}]"
        
        return "[All day]"
    
    def _get_item_duration(self, item) -> str:
        """Extract duration string from item"""
        # Check properties dict
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            if 'duration_minutes' in item.properties:
                dur = item.properties['duration_minutes']
                if dur > 0:
                    hrs = dur // 60
                    mins = dur % 60
                    if hrs > 0:
                        return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
                    elif mins > 0:
                        return f" ({mins}m)"
        
        if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
            hrs = item.duration_minutes // 60
            mins = item.duration_minutes % 60
            if hrs > 0:
                return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
            elif mins > 0:
                return f" ({mins}m)"
        elif hasattr(item, 'duration') and item.duration > 0:
            hrs = item.duration // 60
            mins = item.duration % 60
            if hrs > 0:
                return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
            elif mins > 0:
                return f" ({mins}m)"
        elif hasattr(item, 'duration_hours') and item.duration_hours > 0:
            return f" ({item.duration_hours}h)"
        return ""
    
    def _get_item_cost(self, item) -> float:
        """Extract cost from item"""
        # Check properties dict
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            if 'cost' in item.properties and item.properties['cost'] > 0:
                return item.properties['cost']
        
        if hasattr(item, 'cost') and item.cost:
            return item.cost
        elif hasattr(item, 'price') and item.price:
            return item.price
        elif hasattr(item, 'price_per_night') and item.price_per_night:
            return item.price_per_night
        return 0
    
    def _get_user_selection(
        self, 
        itineraries: List[Tuple[str, ItinerarySummary]]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get user's itinerary selection"""
        while True:
            print("="*80)
            try:
                choice = input(
                    f"\n🎯 Select an itinerary (1-{len(itineraries)}) or 'c' to cancel:\n➤ "
                ).strip().lower()
                
                if choice == 'c':
                    print("\n👋 Selection cancelled")
                    return None
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(itineraries):
                    strategy_name, summary = itineraries[choice_idx]
                    print(f"\n✅ Selected: {strategy_name}")
                    return (strategy_name, summary.full_data)
                else:
                    self._print_error(f"Please enter a number between 1 and {len(itineraries)}")
            
            except ValueError:
                self._print_error("Invalid input. Please enter a number or 'c'")
    
    def display_selected(self, strategy_name: str, itinerary: Dict[str, Any]) -> None:
        """Display the selected itinerary in detail"""
        print("\n" + "="*80)
        print(f"✅ SELECTED ITINERARY: {strategy_name}")
        print("="*80)
        print(f"\n💵 Total Cost: ₹{itinerary.get('total_cost', 0):,.2f}")
        print(f"📅 Duration: {itinerary.get('num_days')} days")
        
        # Show day-by-day summary
        itinerary_data = itinerary.get('itinerary', {})
        num_days = itinerary.get('num_days', 0)
        
        print(f"\n📋 Day-by-Day Preview:")
        for day_num in range(num_days):
            items = itinerary_data.get(day_num, [])
            if items:
                item_names = [getattr(item, 'name', str(item)) for item in items]
                print(f"  Day {day_num + 1}: {', '.join(str(name)[:30] for name in item_names)}")
    
    def _print_error(self, text: str) -> None:
        """Print colored error message"""
        print(f"{self.colors['red']}❌ {text}{self.colors['end']}")
    
    def _print_success(self, text: str) -> None:
        """Print colored success message"""
        print(f"{self.colors['green']}✅ {text}{self.colors['end']}")


class SaveItineraryHandler:
    """Handles saving selected itinerary to database"""
    
    @staticmethod
    def prepare_for_storage(
        strategy_name: str,
        itinerary: Dict[str, Any],
        trip_details: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Prepare itinerary data for database storage"""
        
        # Extract daily schedules for storage
        daily_schedules = []
        itinerary_data = itinerary.get('itinerary', {})
        num_days = itinerary.get('num_days', 0)
        
        for day_num in range(num_days):
            items = itinerary_data.get(day_num, [])
            day_schedule = {
                'day': day_num + 1,
                'items': []
            }
            
            for item in items:
                item_info = {
                    'name': getattr(item, 'name', 'Unknown'),
                    'type': getattr(item, 'category', getattr(item, 'item_type', 'unknown')),
                    'cost': getattr(item, 'price', getattr(item, 'cost', 0)),
                    'time': SaveItineraryHandler._extract_time(item),
                    'description': getattr(item, 'description', '')
                }
                day_schedule['items'].append(item_info)
            
            daily_schedules.append(day_schedule)
        
        # Create storage record
        storage_data = {
            'user_id': user_id,
            'strategy_used': strategy_name,
            'origin': trip_details.get('origin_city', ''),
            'destination': trip_details.get('destination_city', ''),
            'departure_date': trip_details.get('departure_date', ''),
            'return_date': trip_details.get('return_date', ''),
            'num_days': num_days,
            'total_budget_inr': trip_details.get('budget_inr', 0),
            'total_cost_inr': itinerary.get('total_cost', 0),
            'currency': itinerary.get('currency', 'INR'),
            'optimization_score': itinerary.get('optimizer_metadata', {}).get('score', 0),
            'combinations_evaluated': itinerary.get('optimizer_metadata', {}).get('combinations_evaluated', 0),
            'optimizer': itinerary.get('optimizer_metadata', {}).get('optimizer', 'unknown'),
            'daily_schedules': daily_schedules,
            'interests': trip_details.get('interests', []),
            'dietary_restrictions': trip_details.get('dietary_restrictions', []),
            'trip_details': trip_details
        }
        
        return storage_data
    
    @staticmethod
    def _extract_time(item) -> str:
        """Extract time information from item"""
        # Check properties dict
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            scheduled_time = item.properties.get('scheduled_time', '')
            if scheduled_time:
                return str(scheduled_time)
        
        # Check departure_time
        if hasattr(item, 'departure_time') and item.departure_time:
            time_val = item.departure_time
            if isinstance(time_val, str) and 'T' in time_val:
                return time_val.split('T')[1][:5]
            return str(time_val)
        
        # Check start_time
        if hasattr(item, 'start_time') and item.start_time > 0:
            hours = int(item.start_time // 60)
            mins = int(item.start_time % 60)
            return f"{hours:02d}:{mins:02d}"
        
        return "All day"
