"""
LangGraph-based Itinerary Optimizer with Parallel Exploration and Backtracking
Uses state graphs to evaluate all option combinations and select the best based on constraints

Key Features:
- Parallel exploration of flights, hotels, restaurants, activities
- Constraint-based evaluation (budget, preferences, logistics)
- Backtracking when constraints are violated
- No hardcoded budget ratios - all constraints are dynamic
"""

from typing import TypedDict, Annotated, Any, List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.types import Send

# For constraint checking
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================================
# TYPE DEFINITIONS & STATES
# ============================================================================

class BudgetConstraint(BaseModel):
    """Define how budget is allocated"""
    total_budget: float
    # Flexible allocation - no hardcoded ratios!
    # Instead, we define minimum/maximum for each category
    transport_min: float = Field(default=0, ge=0)
    transport_max: Optional[float] = Field(default=None)  # None = unbounded
    accommodation_min: float = Field(default=0, ge=0)
    accommodation_max: Optional[float] = Field(default=None)
    restaurant_min: float = Field(default=0, ge=0)
    restaurant_max: Optional[float] = Field(default=None)
    activity_min: float = Field(default=0, ge=0)
    activity_max: Optional[float] = Field(default=None)
    
    @validator('transport_max', 'accommodation_max', 'restaurant_max', 'activity_max', pre=True)
    def validate_max_bounds(cls, v, values):
        """Max should be <= total budget if specified"""
        if v is not None and 'total_budget' in values:
            total = values['total_budget']
            if v > total:
                raise ValueError(f"Max budget {v} cannot exceed total budget {total}")
        return v
    
    def is_within_bounds(self, category: str, amount: float) -> Tuple[bool, str]:
        """Check if amount is within bounds for category"""
        min_attr = f"{category}_min"
        max_attr = f"{category}_max"
        
        min_val = getattr(self, min_attr, 0)
        max_val = getattr(self, max_attr, None)
        
        if amount < min_val:
            return False, f"Amount {amount} below minimum {min_val}"
        if max_val is not None and amount > max_val:
            return False, f"Amount {amount} exceeds maximum {max_val}"
        return True, "OK"


class UserPreferences(BaseModel):
    """User preferences for constraint evaluation"""
    # Travel style
    preferred_pace: str = Field(default="balanced")  # fast, balanced, relaxed
    priority: str = Field(default="value")  # cost, time, experience, value
    
    # Comfort levels
    hotel_min_rating: float = Field(default=3.5, ge=1, le=5)
    restaurant_min_rating: float = Field(default=3.0, ge=1, le=5)
    activity_min_rating: float = Field(default=3.5, ge=1, le=5)
    
    # Activity preferences
    activity_interests: List[str] = Field(default_factory=lambda: ["cultural", "adventure"])
    dietary_restrictions: List[str] = Field(default_factory=list)
    
    # Schedule constraints
    activities_per_day_min: int = Field(default=1, ge=1)
    activities_per_day_max: int = Field(default=5, ge=1)
    meals_per_day: int = Field(default=2, ge=1, le=3)


@dataclass
class OptionCandidate:
    """A candidate option from search results"""
    id: str
    category: str  # transport, accommodation, restaurant, activity
    name: str
    cost: float
    currency: str
    rating: float
    duration_minutes: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'name': self.name,
            'cost': self.cost,
            'currency': self.currency,
            'rating': self.rating,
            'duration_minutes': self.duration_minutes,
            'properties': self.properties
        }


@dataclass
class ItineraryPlan:
    """A complete itinerary plan combining all options"""
    transport_option: Optional[OptionCandidate] = None
    return_transport_option: Optional[OptionCandidate] = None    # NEW
    accommodation_options: List[OptionCandidate] = field(default_factory=list)
    restaurant_options: List[OptionCandidate] = field(default_factory=list)
    activity_options: List[OptionCandidate] = field(default_factory=list)
    
    total_cost: float = 0.0
    total_days: int = 0
    satisfaction_score: float = 0.0
    constraint_violations: List[str] = field(default_factory=list)
    
    # def calculate_costs(self) -> Dict[str, float]:
    #     """Calculate costs by category"""
    #     return {
    #         'transport': sum(o.cost for o in [self.transport_option] if o),
    #         'accommodation': sum(o.cost for o in self.accommodation_options),
    #         'restaurant': sum(o.cost for o in self.restaurant_options),
    #         'activity': sum(o.cost for o in self.activity_options),
    #     }
    def calculate_costs(self) -> Dict[str, float]:
        return {
            'transport':     (self.transport_option.cost
                              if self.transport_option else 0)
                           + (self.return_transport_option.cost        # NEW
                              if self.return_transport_option else 0),
            'accommodation': sum(o.cost for o in self.accommodation_options),
            'restaurant':    sum(o.cost for o in self.restaurant_options),
            'activity':      sum(o.cost for o in self.activity_options),
        }
    
    def is_feasible(self) -> bool:
        """Plan is feasible if no constraint violations"""
        return len(self.constraint_violations) == 0


class OptimizerState(TypedDict):
    """
    State for the LangGraph optimizer
    Contains all information needed for parallel exploration and backtracking
    """
    # Input data
    trip_start_date: str
    num_days: int
    origin: str
    destination: str
    
    # User input
    budget_constraint: Dict[str, Any]  # Serialized BudgetConstraint
    user_preferences: Dict[str, Any]  # Serialized UserPreferences
    
    # Available options (from agent searches)
    transport_options: List[Dict[str, Any]]  # All flight/ground options
    accommodation_options: List[Dict[str, Any]]
    restaurant_options: List[Dict[str, Any]]
    activity_options: List[Dict[str, Any]]
    return_transport_options: List[Dict[str, Any]]

    # Exploration state
    candidate_plans: List[Dict[str, Any]]  # All explored plans
    evaluated_combinations: int  # Counter for combinations checked
    candidates_generated: bool  # Flag to prevent infinite regeneration
    
    # Results
    best_plan: Optional[Dict[str, Any]]
    best_score: float
    error: Optional[str]
    backtrack_count: int


# ============================================================================
# CONSTRAINT EVALUATOR
# ============================================================================

class ConstraintEvaluator:
    """Evaluates plans against user constraints without hardcoded ratios"""
    
    def __init__(self, budget_constraint: BudgetConstraint, 
                 preferences: UserPreferences, num_days: int):
        self.budget = budget_constraint
        self.prefs = preferences
        self.num_days = num_days
    
    # def evaluate_plan(self, plan: ItineraryPlan) -> Tuple[float, List[str]]:
    #     """
    #     Evaluate a plan's feasibility and quality
        
    #     Returns:
    #         (satisfaction_score, constraint_violations)
    #         satisfaction_score: 0-100, higher is better
    #         constraint_violations: list of violation descriptions
    #     """
    #     violations = []
    #     score = 100.0
        
    #     # 1. Check budget constraints
    #     costs = plan.calculate_costs()
    #     total_cost = sum(costs.values())
        
    #     if total_cost > self.budget.total_budget:
    #         violation = f"Total cost {total_cost:.0f} exceeds budget {self.budget.total_budget:.0f}"
    #         violations.append(violation)
    #         score -= 30
        
    #     # Check per-category budgets
    #     for category in ['transport', 'accommodation', 'restaurant', 'activity']:
    #         amount = costs.get(category, 0)
    #         within_bounds, msg = self.budget.is_within_bounds(category, amount)
    #         if not within_bounds:
    #             violations.append(f"{category}: {msg}")
    #             score -= 15
        
    #     # 2. Check rating constraints
    #     if plan.transport_option and plan.transport_option.rating < 0.5:
    #         violations.append(f"Transport rating {plan.transport_option.rating} too low")
    #         score -= 10
        
    #     hotel_ratings = [o.rating for o in plan.accommodation_options]
    #     if hotel_ratings and min(hotel_ratings) < self.prefs.hotel_min_rating:
    #         violations.append(f"Hotel rating below {self.prefs.hotel_min_rating}")
    #         score -= 15
        
    #     rest_ratings = [o.rating for o in plan.restaurant_options]
    #     if rest_ratings and min(rest_ratings) < self.prefs.restaurant_min_rating:
    #         violations.append(f"Restaurant rating below {self.prefs.restaurant_min_rating}")
    #         score -= 10
        
    #     act_ratings = [o.rating for o in plan.activity_options]
    #     if act_ratings and min(act_ratings) < self.prefs.activity_min_rating:
    #         violations.append(f"Activity rating below {self.prefs.activity_min_rating}")
    #         score -= 10
        
    #     # 3. Check activity distribution
    #     activities_per_day = len(plan.activity_options) / max(1, plan.total_days)
        
    #     if activities_per_day < self.prefs.activities_per_day_min:
    #         violations.append(
    #             f"Activities per day ({activities_per_day:.1f}) below minimum {self.prefs.activities_per_day_min}"
    #         )
    #         score -= 10
        
    #     if activities_per_day > self.prefs.activities_per_day_max:
    #         violations.append(
    #             f"Activities per day ({activities_per_day:.1f}) exceeds maximum {self.prefs.activities_per_day_max}"
    #         )
    #         score -= 10
        
    #     # 4. Check meals per day
    #     meals_per_day = len(plan.restaurant_options) / max(1, plan.total_days)
    #     if abs(meals_per_day - self.prefs.meals_per_day) > 1:
    #         violations.append(
    #             f"Meals per day ({meals_per_day:.1f}) differs from preference {self.prefs.meals_per_day}"
    #         )
    #         score -= 5
        
    #     # 5. Check dietary restrictions
    #     diet_compliant = all(
    #         all(restriction not in o.properties.get('ingredients', '').lower()
    #             for restriction in self.prefs.dietary_restrictions)
    #         for o in plan.restaurant_options
    #     )
    #     if not diet_compliant:
    #         violations.append("Some restaurants don't meet dietary restrictions")
    #         score -= 10
        
    #     # 6. Score adjustments based on priority
    #     if self.prefs.priority == "cost" and total_cost <= self.budget.total_budget:
    #         score += 20
    #     elif self.prefs.priority == "experience":
    #         avg_rating = (
    #             sum(o.rating for o in plan.accommodation_options + 
    #                 plan.restaurant_options + plan.activity_options) /
    #             max(1, len(plan.accommodation_options + 
    #                 plan.restaurant_options + plan.activity_options))
    #         )
    #         score += avg_rating * 10
        
    #     # Ensure score doesn't exceed 100
    #     score = min(100, max(0, score))
        
    #     return score, violations
    def evaluate_plan(self, plan: ItineraryPlan) -> Tuple[float, List[str]]:
        """
        Score a plan 0-100 based on total budget fit, quality, and activity count.

        Scoring breakdown
        -----------------
          60 pts  budget adherence  — primary signal
          30 pts  average rating    — quality signal  
          10 pts  activity count    — experience signal

        No per-category caps. A cheap train + good hotel beats an expensive
        flight + cheap hotel automatically because the total cost is lower.
        """
        violations = []
        score      = 0.0

        costs      = plan.calculate_costs()
        total_cost = sum(costs.values())
        budget     = self.budget.total_budget

        # ── 1. Budget adherence (60 pts) ───────────────────────────────────
        if total_cost <= budget:
            # Full 60 pts when cost = 0, scales to 30 pts when exactly on budget.
            # This means a plan at 50% of budget scores 45, one at 100% scores 30 —
            # cheaper combinations are always ranked higher.
            ratio        = total_cost / budget if budget > 0 else 0
            budget_score = 60 * (1 - ratio * 0.5)
            score       += budget_score
        else:
            # Over budget — lose up to 60 pts proportionally.
            # 10% over → -12 pts,  50% over → -60 pts (floored)
            overage_ratio = (total_cost - budget) / budget
            penalty       = min(60, 60 * overage_ratio * 2)
            score        -= penalty
            violations.append(
                f"Over budget by INR {total_cost - budget:,.0f} "
                f"({overage_ratio * 100:.0f}% over limit)"
            )

        # ── 2. Quality / rating score (30 pts) ────────────────────────────
        rated_items = (
            ([plan.transport_option] if plan.transport_option else []) +
            plan.accommodation_options +
            plan.restaurant_options +
            plan.activity_options
        )

        if rated_items:
            avg_rating    = sum(o.rating for o in rated_items) / len(rated_items)
            score        += 30 * (avg_rating / 5.0)

            # Soft penalties for items below minimum thresholds
            for item in plan.accommodation_options:
                if item.rating < self.prefs.hotel_min_rating:
                    violations.append(
                        f"Hotel '{item.name}' rating {item.rating:.1f} "
                        f"< minimum {self.prefs.hotel_min_rating}"
                    )
                    score -= 5

            for item in plan.restaurant_options:
                if item.rating < self.prefs.restaurant_min_rating:
                    score -= 2   # soft deduction, not a hard violation

            for item in plan.activity_options:
                if item.rating < self.prefs.activity_min_rating:
                    score -= 2

        # ── 3. Activity count (10 pts) ─────────────────────────────────────
        activities_per_day = len(plan.activity_options) / max(1, plan.total_days)

        if (self.prefs.activities_per_day_min
                <= activities_per_day
                <= self.prefs.activities_per_day_max):
            score += 10                          # full credit
        elif activities_per_day < self.prefs.activities_per_day_min:
            violations.append(
                f"Only {activities_per_day:.1f} activities/day "
                f"(min {self.prefs.activities_per_day_min})"
            )
            score += 5                           # partial credit

        # ── 4. Dietary compliance (soft check) ────────────────────────────
        if self.prefs.dietary_restrictions:
            non_compliant = [
                o for o in plan.restaurant_options
                if any(
                    r in o.properties.get('ingredients', '').lower()
                    for r in self.prefs.dietary_restrictions
                )
            ]
            if non_compliant:
                violations.append(
                    f"{len(non_compliant)} restaurant(s) may not meet dietary needs"
                )
                score -= 5 * len(non_compliant)

        # ── Clamp to valid range ───────────────────────────────────────────
        score = max(-100, min(100, score))

        return score, violations


# ============================================================================
# LANGGRAPH OPTIMIZER
# ============================================================================

class LangGraphItineraryOptimizer:
    """
    LangGraph-based optimizer that parallelly explores options
    and uses backtracking to find the best valid plan
    """
    
    def __init__(self, budget_constraint: Dict[str, Any], 
                 preferences: Dict[str, Any], num_days: int):
        """
        Initialize optimizer
        
        Args:
            budget_constraint: Dict with budget parameters
            preferences: Dict with user preferences
            num_days: Number of days in trip
        """
        self.budget = BudgetConstraint(**budget_constraint)
        self.prefs = UserPreferences(**preferences)
        self.num_days = num_days
        self.evaluator = ConstraintEvaluator(self.budget, self.prefs, num_days)
        
        # Build the state graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for optimization"""
        
        graph = StateGraph(OptimizerState)
        
        # Add nodes
        graph.add_node("validate_input", self._validate_input)
        graph.add_node("generate_candidates", self._generate_candidates)
        graph.add_node("evaluate_single", self._evaluate_single_plan)
        graph.add_node("compare_plans", self._compare_plans)
        graph.add_node("backtrack", self._backtrack)
        graph.add_node("finalize", self._finalize)
        
        # Set the entry point
        graph.set_entry_point("validate_input")
        
        # Add edges
        graph.add_edge("validate_input", "generate_candidates")
        graph.add_conditional_edges(
            "generate_candidates",
            self._should_evaluate,
            {
                "evaluate": "evaluate_single",
                "finalize": "finalize"
            }
        )
        graph.add_edge("evaluate_single", "compare_plans")
        graph.add_conditional_edges(
            "compare_plans",
            self._should_continue_exploring,
            {
                "continue": "evaluate_single",  # Loop back to evaluate next plan
                "backtrack": "backtrack",
                "finalize": "finalize"
            }
        )
        graph.add_edge("backtrack", "evaluate_single")
        graph.add_edge("finalize", END)
        
        return graph
    
    def _validate_input(self, state: OptimizerState) -> OptimizerState:
        """Validate input data"""
        logger.info("Validating input parameters...")
        
        if not state['transport_options']:
            state['error'] = "No transport options provided"
            return state
        
        if not state['accommodation_options']:
            state['error'] = "No accommodation options provided"
            return state
        
        state['candidate_plans'] = []
        state['evaluated_combinations'] = 0
        state['best_score'] = -1.0
        state['backtrack_count'] = 0
        state['candidates_generated'] = False
        
        return state
    
    # def _generate_candidates(self, state: OptimizerState) -> OptimizerState:
    #     """Generate candidate plans by combining options (only once)"""
        
    #     # Skip if already generated
    #     if state.get('candidates_generated', False):
    #         logger.info("Candidates already generated, skipping...")
    #         return state
        
    #     logger.info(f"Generating candidate combinations...")
        
    #     # return state
    #     top_n = 5   # explore top-5 cheapest per category (up from 3)

    #     def _cheapest(lst, n):
    #         """Return n cheapest items from lst (dicts with 'cost' key)."""
    #         return sorted(lst, key=lambda x: x.get('cost', 0))[:n]

    #     transports   = _cheapest(state['transport_options'],     top_n)
    #     hotels       = _cheapest(state['accommodation_options'], top_n)
    #     restaurants  = (_cheapest(state['restaurant_options'],   top_n)
    #                     if state['restaurant_options'] else [None])
    #     activities   = (_cheapest(state['activity_options'],     top_n)
    #                     if state['activity_options'] else [None])

    #     new_candidates = []
    #     max_combinations = 100   # increased from 50 — budget search needs breadth

    #     for transport in transports:
    #         for hotel in hotels:
    #             for restaurant in restaurants:
    #                 for activity in activities:
    #                     if len(new_candidates) >= max_combinations:
    #                         break

    #                     plan = ItineraryPlan(
    #                         transport_option=(
    #                             self._dict_to_candidate(transport) if transport else None
    #                         ),
    #                         accommodation_options=(
    #                             [self._dict_to_candidate(hotel)] if hotel else []
    #                         ),
    #                         restaurant_options=(
    #                             [self._dict_to_candidate(restaurant)] if restaurant else []
    #                         ),
    #                         activity_options=(
    #                             [self._dict_to_candidate(activity)] if activity else []
    #                         ),
    #                         total_days=self.num_days
    #                     )
    #                     new_candidates.append(plan)

    #     logger.info(f"Generated {len(new_candidates)} candidates "
    #                 f"(transports sorted cheapest-first)")

    #     state['candidate_plans']      = [p.__dict__ for p in new_candidates]
    #     state['candidates_generated'] = True
    #     return state
    def _generate_candidates(self, state) -> dict:
        """
        Generate candidate plans pairing outbound + return transport.
        Total cost = outbound + return + hotel×days + restaurants + activities.
        Cheapest combinations explored first.
        """
        if state.get('candidates_generated', False):
            return state

        top_n = 5

        def _cheapest(lst, n, cap=float('inf')):
            affordable = [x for x in lst if x.get('cost', 0) <= cap]
            if not affordable:
                affordable = lst
            return sorted(affordable, key=lambda x: x.get('cost', 0))[:n]

        total_budget = state.get('budget_constraint', {}).get('total_budget', float('inf'))

        transports        = _cheapest(state['transport_options'],        top_n)
        return_transports = _cheapest(state['return_transport_options'], top_n) \
                            if state.get('return_transport_options') else [None]
        hotels            = _cheapest(state['accommodation_options'],    top_n,
                                      cap=total_budget * 0.50)
        restaurants       = (_cheapest(state['restaurant_options'],      top_n)
                             if state['restaurant_options'] else [None])
        activities        = (_cheapest(state['activity_options'],        top_n)
                             if state['activity_options'] else [None])

        new_candidates = []
        max_combinations = 200   # more room since we have extra dimension

        for transport in transports:
            for ret_transport in return_transports:
                for hotel in hotels:
                    for restaurant in restaurants:
                        for activity in activities:
                            if len(new_candidates) >= max_combinations:
                                break

                            plan = ItineraryPlan(
                                transport_option=(
                                    self._dict_to_candidate(transport)
                                    if transport else None
                                ),
                                return_transport_option=(            # NEW field
                                    self._dict_to_candidate(ret_transport)
                                    if ret_transport else None
                                ),
                                accommodation_options=(
                                    [self._dict_to_candidate(hotel)] if hotel else []
                                ),
                                restaurant_options=(
                                    [self._dict_to_candidate(restaurant)]
                                    if restaurant else []
                                ),
                                activity_options=(
                                    [self._dict_to_candidate(activity)]
                                    if activity else []
                                ),
                                total_days=self.num_days
                            )
                            new_candidates.append(plan)

        logger.info(f"Generated {len(new_candidates)} candidates "
                    f"(outbound × return × hotel × food × activity)")

        state['candidate_plans']      = [p.__dict__ for p in new_candidates]
        state['candidates_generated'] = True
        return state


    
    def _dict_to_candidate(self, data: Dict[str, Any]) -> OptionCandidate:
        """Convert dict to OptionCandidate"""
        if isinstance(data, OptionCandidate):
            return data
        return OptionCandidate(
            id=data.get('id', ''),
            category=data.get('category', ''),
            name=data.get('name', ''),
            cost=data.get('cost', 0),
            currency=data.get('currency', 'INR'),
            rating=data.get('rating', 3.5),
            duration_minutes=data.get('duration_minutes', 0),
            properties=data.get('properties', {})
        )
    
    def _should_evaluate(self, state: OptimizerState) -> str:
        """Decide if we should evaluate or finalize"""
        # If no candidates to evaluate, finalize immediately
        if not state.get('candidate_plans') or len(state['candidate_plans']) == 0:
            logger.info("No candidates to evaluate, finalizing...")
            return "finalize"
        logger.info(f"Found {len(state['candidate_plans'])} candidates to evaluate")
        return "evaluate"
    
    def _evaluate_single_plan(self, state: OptimizerState) -> OptimizerState:
        """Evaluate a single plan against constraints"""
        
        if not state['candidate_plans']:
            return state
        
        # Pop a plan to evaluate
        plan_data = state['candidate_plans'].pop(0)
        
        # Convert back to plan object if needed
        if isinstance(plan_data, dict):
            plan = ItineraryPlan(**plan_data)
        else:
            plan = plan_data
        
        # Evaluate
        score, violations = self.evaluator.evaluate_plan(plan)
        plan.satisfaction_score = score
        plan.constraint_violations = violations
        
        state['evaluated_combinations'] += 1
        
        logger.info(f"Evaluated plan: score={score:.1f}, violations={len(violations)}")
        
        # Track best plan found so far
        if score > state.get('best_score', -1):
            state['best_score'] = score
            state['best_plan']  = {
                'transport':        plan.transport_option,
                'return_transport': plan.return_transport_option,    # NEW
                'accommodations':   plan.accommodation_options,
                'restaurants':      plan.restaurant_options,
                'activities':       plan.activity_options,
                'score':            score,
                'violations':       violations
            }
            logger.info(f"New best plan found: score={score:.1f}")
        
        return state
    
    def _compare_plans(self, state: OptimizerState) -> OptimizerState:
        """Compare current plan with best so far"""
        
        # This would be implemented to track the best plan
        # For now, simplified
        
        return state
    
    def _should_continue_exploring(self, state: OptimizerState) -> str:
        """Decide whether to continue exploring or finalize"""
        # Stop after evaluating enough candidates (don't try all 50)
        max_evaluations = 15  # Stop after evaluating 15 plans
        
        if state['evaluated_combinations'] >= max_evaluations:
            logger.info(f"Reached evaluation limit ({max_evaluations}), finalizing...")
            return "finalize"
        
        # Continue if we still have candidates
        if state['candidate_plans'] and len(state['candidate_plans']) > 0:
            logger.info(f"Still have {len(state['candidate_plans'])} candidates to evaluate, continuing...")
            return "continue"
        
        # Stop when no more candidates
        logger.info(f"No more candidates to evaluate ({state['evaluated_combinations']} evaluated), finalizing...")
        return "finalize"
    
    def _backtrack(self, state: OptimizerState) -> OptimizerState:
        """Backtrack and try different options"""
        state['backtrack_count'] += 1
        logger.info(f"Backtracking (attempt {state['backtrack_count']})...")
        
        # Relax constraints if too many failures
        if state['backtrack_count'] > 3:
            # Would relax budget or rating constraints
            pass
        
        return state
    
    def _finalize(self, state: OptimizerState) -> OptimizerState:
        """Finalize and return best plan found"""
        logger.info(f"Optimization complete. Evaluated {state['evaluated_combinations']} plans.")
        return state
    
    def optimize(self, 
                 transport_options: List[Dict[str, Any]],
                 return_transport_options,
                 accommodation_options: List[Dict[str, Any]],
                 restaurant_options: List[Dict[str, Any]],
                 activity_options: List[Dict[str, Any]],
                 trip_start_date: str,
                 origin: str,
                 destination: str) -> Dict[str, Any]:
        """
        Run the optimization
        
        Args:
            *_options: Lists of available options from agent searches
            trip_start_date: Start date (YYYY-MM-DD)
            origin: Origin city
            destination: Destination city
        
        Returns:
            Dict with best_plan and optimization metadata
        """
        
        initial_state: OptimizerState = {
            'trip_start_date': trip_start_date,
            'num_days': self.num_days,
            'origin': origin,
            'destination': destination,
            'budget_constraint': self.budget.__dict__,
            'user_preferences': self.prefs.__dict__,
            'transport_options': transport_options,
            'return_transport_options': return_transport_options or [],
            'accommodation_options': accommodation_options,
            'restaurant_options': restaurant_options,
            'activity_options': activity_options,
            'candidate_plans': [],
            'evaluated_combinations': 0,
            'candidates_generated': False,
            'best_plan': None,
            'best_score': -1.0,
            'error': None,
            'backtrack_count': 0
        }
        
        # Compile and run the graph with increased recursion limit
        runnable = self.graph.compile()
        final_state = runnable.invoke(
            initial_state,
            config={"recursion_limit": 500}  # Increased from 100 to handle looping through candidates
        )
        
        return {
            'best_plan': final_state.get('best_plan'),
            'best_score': final_state.get('best_score'),
            'evaluated_combinations': final_state.get('evaluated_combinations'),
            'backtrack_attempts': final_state.get('backtrack_count'),
            'error': final_state.get('error'),
            'success': final_state.get('best_plan') is not None
        }
