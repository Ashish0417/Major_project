import sys

path = r'c:\Users\tanvi\Personal\TravelPlanner\Major_project\llm_orchestrator.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'def _convert_langgraph_result(self, lg_result: dict, flights, accommodations,' in line:
        start_idx = i
    if 'def _assign_item_times' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    body = lines[start_idx:end_idx]
    
    new_lines = []
    new_lines.append('    def _convert_langgraph_result(self, lg_result: dict, flights, accommodations,\n')
    new_lines.append('                              restaurants, activities, num_days) -> dict:\n')
    new_lines.append('        top_plans = lg_result.get("top_plans", [])\n')
    new_lines.append('        if not top_plans and lg_result.get("best_plan"):\n')
    new_lines.append('            top_plans = [lg_result.get("best_plan")]\n')
    new_lines.append('        \n')
    new_lines.append('        all_converted = []\n')
    new_lines.append('        import copy\n')
    new_lines.append('        for p in top_plans:\n')
    new_lines.append('            score = p.get("score", lg_result.get("best_score", 0))\n')
    new_lines.append('            converted = self._convert_langgraph_single_plan(p, score, lg_result.get("evaluated_combinations", 0), lg_result.get("backtrack_attempts", 0), flights, accommodations, restaurants, activities, num_days)\n')
    new_lines.append('            all_converted.append(converted)\n')
    new_lines.append('            \n')
    new_lines.append('        if not all_converted:\n')
    new_lines.append('            return {}\n')
    new_lines.append('            \n')
    new_lines.append('        main_result = all_converted[0]\n')
    new_lines.append('        main_result["all_top_itineraries"] = all_converted\n')
    new_lines.append('        return main_result\n')
    new_lines.append('\n')
    new_lines.append('    def _convert_langgraph_single_plan(self, best_plan: dict, score: float, eval_comb: int, backtrack: int, flights, accommodations, restaurants, activities, num_days) -> dict:\n')
    
    for line in body[2:]:
        if "best_plan = lg_result.get('best_plan', {})" in line:
            new_lines.append(line.replace("best_plan = lg_result.get('best_plan', {})", "# best_plan passed as arg"))
            continue
        if "lg_result.get('best_score', 0)" in line:
            line = line.replace("lg_result.get('best_score', 0)", "score")
        if "lg_result.get('evaluated_combinations', 0)" in line:
            line = line.replace("lg_result.get('evaluated_combinations', 0)", "eval_comb")
        if "lg_result.get('backtrack_attempts', 0)" in line:
            line = line.replace("lg_result.get('backtrack_attempts', 0)", "backtrack")
            
        new_lines.append(line)
        
    lines = lines[:start_idx] + new_lines + lines[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS")
else:
    print("FAILED", start_idx, end_idx)
