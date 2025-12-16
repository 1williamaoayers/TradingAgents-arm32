
import json
import os

path = 'eval_results/02128.HK/TradingAgentsStrategy_logs/full_states_log.json'
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
        state = list(data.values())[0]
        print("Top Level Keys:", list(state.keys()))
        
        if 'investment_debate_state' in state:
            print("\nInvestment Debate Keys:", list(state['investment_debate_state'].keys()))
            
        if 'risk_debate_state' in state:
            print("\nRisk Debate Keys:", list(state['risk_debate_state'].keys()))
            
        for key in ['bull_researcher', 'bear_researcher', 'research_team_decision', 'risky_analyst', 'safe_analyst', 'neutral_analyst', 'risk_management_decision', 'investment_plan', 'trader_investment_decision']:
            val = state.get(key)
            print(f"Key '{key}' length: {len(str(val)) if val else 0}")
            if val:
                print(f"  Content preview: {str(val)[:50]}...")

else:
    print("File not found")
