#!/usr/bin/env python3
"""
Quick test to verify solution deduplication logic
"""

def test_deduplication():
    """Test the signature-based deduplication logic"""
    
    # Simulate the unique_solutions dictionary behavior
    unique_solutions = {}
    
    def _get_solution_signature(sol):
        """Create a unique signature for a solution to detect duplicates"""
        if not sol or "error" in sol:
            return None
        # Use cost + score as approximate signature
        cost = round(sol.get('total_cost', 0), 2)
        score = round(sol.get('optimizer_metadata', {}).get('score', 0), 1)
        return (cost, score)
    
    # Simulate collecting solutions from multiple rounds
    test_solutions = [
        {
            'total_cost': 16942.50,
            'optimizer_metadata': {'score': 63.5},
            'name': 'Solution 1 - Best'
        },
        {
            'total_cost': 16942.50,
            'optimizer_metadata': {'score': 63.5},
            'name': 'Solution 1 - Duplicate (should be skipped)'
        },
        {
            'total_cost': 17200.00,
            'optimizer_metadata': {'score': 62.8},
            'name': 'Solution 2 - Alternative'
        },
        {
            'total_cost': 17850.75,
            'optimizer_metadata': {'score': 61.2},
            'name': 'Solution 3 - Another alternative'
        },
        {
            'total_cost': 17200.00,
            'optimizer_metadata': {'score': 62.8},
            'name': 'Solution 2 - Duplicate (should be skipped)'
        },
    ]
    
    # Process solutions
    for sol in test_solutions:
        sig = _get_solution_signature(sol)
        if sig:
            if sig not in unique_solutions:
                unique_solutions[sig] = sol
                print(f"✨ Added: {sol['name']} (Cost: ₹{sol['total_cost']:.0f}, Score: {sol['optimizer_metadata']['score']:.1f})")
            else:
                print(f"⚠️  Skipped duplicate: {sol['name']} (same signature: {sig})")
    
    # Sort by score (descending)
    def _get_opt_score(itinerary):
        metadata = itinerary.get('optimizer_metadata', {})
        return metadata.get('score', 0)
    
    unique_list = list(unique_solutions.values())
    unique_list.sort(key=_get_opt_score, reverse=True)
    
    print("\n" + "="*80)
    print(f"📊 Found {len(unique_list)} UNIQUE solutions (out of {len(test_solutions)} total):")
    print("="*80)
    
    for idx, sol in enumerate(unique_list[:3], 1):
        score = _get_opt_score(sol)
        cost = sol.get('total_cost', 0)
        print(f"{idx}. Score: {score:.1f}/100 | Cost: ₹{cost:,.0f} | {sol['name']}")
    
    # Verify we have 3 unique solutions
    assert len(unique_list) == 3, f"Expected 3 unique solutions, got {len(unique_list)}"
    
    # Verify they're sorted by score (highest first)
    assert _get_opt_score(unique_list[0]) >= _get_opt_score(unique_list[1]), \
        "Solutions not sorted correctly"
    assert _get_opt_score(unique_list[1]) >= _get_opt_score(unique_list[2]), \
        "Solutions not sorted correctly"
    
    print("\n✅ All tests passed! Deduplication working correctly.")
    return unique_list

if __name__ == "__main__":
    results = test_deduplication()
