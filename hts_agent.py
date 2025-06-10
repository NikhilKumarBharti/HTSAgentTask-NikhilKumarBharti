from typing import Dict, Any, Optional
import re
from langchain_community.llms import Ollama
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from rag_tool import RAGTool
from duty_calculator import DutyCalculator, ProductInfo
from config import Config

class HTSAgent:
    def __init__(self):
        self.config = Config()
        self.llm = Ollama(
            model=self.config.LLM_MODEL,
            base_url=self.config.OLLAMA_BASE_URL
        )
        
        # Initialize tools
        self.rag_tool = RAGTool()
        self.duty_calculator = DutyCalculator()
        
        # Setup agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def initialize(self, pdf_path: str = None):
        """Initialize the agent with data"""
        self.rag_tool.initialize(pdf_path)
    
    def _create_tools(self) -> list:
        """Create tools for the agent"""
        
        def rag_search(query: str) -> str:
            """Search HTS documentation for policy and agreement information"""
            result = self.rag_tool.ask_question(query)
            
            response = f"Answer: {result['answer']}\n"
            if result['sources']:
                response += f"\nSources: {len(result['sources'])} documents found"
            
            return response
        
        def calculate_duty(input_str: str) -> str:
            """Calculate duty for HTS code and product information.
            Input format: 'hts_code,cost,freight,insurance,quantity,unit_weight'
            Example: '0101.21.00,1000,100,50,10,100'
            """
            try:
                parts = input_str.split(',')
                if len(parts) < 6:
                    return "Error: Please provide input in format 'hts_code,cost,freight,insurance,quantity,unit_weight'"
                
                product_info = ProductInfo(
                    hts_code=parts[0].strip(),
                    cost=float(parts[1]),
                    freight=float(parts[2]),
                    insurance=float(parts[3]),
                    quantity=int(parts[4]),
                    unit_weight=float(parts[5])
                )
                
                calculation = self.duty_calculator.calculate_duty(product_info)
                return self.duty_calculator.format_calculation_result(calculation)
                
            except Exception as e:
                return f"Error calculating duty: {str(e)}"
        
        return [
            Tool(
                name="HTS_Documentation_Search",
                func=rag_search,
                description="Search HTS documentation for trade policies, agreements, and general information. Use this for questions about trade rules, country agreements, or policy explanations."
            ),
            Tool(
                name="Duty_Calculator",
                func=calculate_duty,
                description="Calculate duties and landed costs for HTS codes. Input format: 'hts_code,cost,freight,insurance,quantity,unit_weight'. Use this for duty calculations and cost analysis."
            )
        ]
    
    def _create_agent(self):
        """Create the main agent"""
        prompt_template = PromptTemplate.from_template("""
You are TariffBot — an intelligent assistant trained on U.S. International Trade Commission data. 
You exist to help importers, analysts, and trade professionals quickly understand tariff rules, duty rates, and policy agreements.

Guidelines:
1. Always provide clear, compliant, and factual answers grounded in official HTS documentation
2. When given an HTS code and product information, explain all applicable duties and cost components
3. If a query is ambiguous or unsupported, politely defer or recommend reviewing the relevant HTS section manually
4. Do not speculate or make policy interpretations — clarify with precision and data

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
        """)
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt_template
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def _detect_query_type(self, query: str) -> str:
        """Detect if query is about duty calculation or general information"""
        # Check for HTS code pattern
        hts_pattern = r'\b\d{4}\.\d{2}\.\d{2}\b'
        has_hts_code = bool(re.search(hts_pattern, query))
        
        # Check for calculation keywords
        calc_keywords = ['calculate', 'duty', 'cost', 'freight', 'insurance', 'landed cost']
        has_calc_keywords = any(keyword in query.lower() for keyword in calc_keywords)
        
        if has_hts_code and has_calc_keywords:
            return "calculation"
        elif has_hts_code:
            return "hts_lookup"
        else:
            return "general"
    
    def process_query(self, query: str) -> str:
        """Process user query and return response"""
        try:
            # Use the agent to process the query
            response = self.agent.invoke({"input": query})
            return response["output"]
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def quick_duty_calculation(self, hts_code: str, cost: float, 
                             freight: float, insurance: float, 
                             quantity: int, unit_weight: float) -> str:
        """Quick duty calculation without agent"""
        product_info = ProductInfo(
            hts_code=hts_code,
            cost=cost,
            freight=freight,
            insurance=insurance,
            quantity=quantity,
            unit_weight=unit_weight
        )
        
        calculation = self.duty_calculator.calculate_duty(product_info)
        return self.duty_calculator.format_calculation_result(calculation)

if __name__ == "__main__":
    # Test the agent
    agent = HTSAgent()
    agent.initialize("data/general_notes.pdf")
    
    # Test queries
    test_queries = [
        "What is United States-Israel Free Trade?",
        "Calculate duty for HTS code 0101.21.00 with cost $1000, freight $100, insurance $50, quantity 10, weight 100kg"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = agent.process_query(query)
        print(f"Response: {response}")
        print("-" * 50)