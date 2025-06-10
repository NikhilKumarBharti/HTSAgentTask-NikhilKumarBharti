from typing import Dict, Any, Optional
import re
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from rag_tool import RAGTool
from duty_calculator import DutyCalculator, ProductInfo
from config import Config

class HTSAgent:
    def __init__(self):
        self.config = Config()
        self.llm = self._initialize_llm()
        
        # Initialize tools
        self.rag_tool = RAGTool()
        self.duty_calculator = DutyCalculator()
        
        # Setup agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration"""
        model_config = self.config.get_model_config()
        
        if model_config["provider"] == "openai":
            if not model_config["api_key"]:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            
            return ChatOpenAI(
                model=model_config["model"],
                api_key=model_config["api_key"],
                temperature=0.1,
                max_tokens=1000
            )
        
        elif model_config["provider"] == "anthropic":
            if not model_config["api_key"]:
                raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.")
            
            return ChatAnthropic(
                model=model_config["model"],
                api_key=model_config["api_key"],
                temperature=0.1,
                max_tokens=1000
            )
        
        elif model_config["provider"] == "together":
            # Using Together AI via OpenAI-compatible API
            if not model_config["api_key"]:
                raise ValueError("Together API key not found. Please set TOGETHER_API_KEY environment variable.")
            
            return ChatOpenAI(
                base_url="https://api.together.xyz/v1",
                api_key=model_config["api_key"],
                model=model_config["model"],
                temperature=0.1,
                max_tokens=1000
            )
        
        else:  # Default to Ollama (local)
            return Ollama(
                model=model_config["model"],
                base_url=model_config["base_url"],
                temperature=0.1,
                num_predict=512,
            )
    
    def initialize(self, pdf_path: str = None):
        """Initialize the agent with data"""
        self.rag_tool.initialize(pdf_path)
    
    def _create_tools(self) -> list:
        """Create tools for the agent"""
        
        def rag_search(query: str) -> str:
            """Search HTS documentation for policy and agreement information"""
            try:
                result = self.rag_tool.ask_question(query)
                
                response = f"Answer: {result['answer']}\n"
                if result['sources']:
                    response += f"\nSources: {len(result['sources'])} documents found"
                
                return response
            except Exception as e:
                return f"Error searching documentation: {str(e)}"
        
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
        # Different prompts for different model types
        model_config = self.config.get_model_config()
        
        if model_config["provider"] in ["openai", "anthropic", "together"]:
            # More sophisticated prompt for advanced models
            prompt_template = PromptTemplate.from_template("""
You are TariffBot, an intelligent assistant for U.S. International Trade Commission data.
You help importers, analysts, and trade professionals with tariff rules, duty rates, and policy agreements.

Available tools:
{tools}

Tool names: {tool_names}

Guidelines:
1. Always provide clear, factual answers based on official HTS documentation
2. Use HTS_Documentation_Search for questions about trade policies, agreements, and general information
3. Use Duty_Calculator for calculating duties and landed costs
4. If unsure, explain what information you need to provide an accurate answer

Question: {input}

Think step by step:
Thought: I need to understand what the user is asking and determine if I need to use any tools.
Action: [tool name if needed]
Action Input: [input for the tool if using one]
Observation: [result from the tool]
Thought: Based on the information, I can now provide a complete answer.
Final Answer: [your comprehensive answer]

{agent_scratchpad}
            """)
        else:
            # Simpler prompt for local models
            prompt_template = PromptTemplate.from_template("""
You are TariffBot, an assistant for U.S. trade and tariff information.

Available tools:
{tools}

Tool names: {tool_names}

Answer the user's question. If you need to use a tool, follow this format:

Question: {input}
Thought: Let me think about what I need to do.
Action: [tool name]
Action Input: [input for the tool]
Observation: [result from the tool]
Final Answer: [your answer]

Question: {input}
{agent_scratchpad}
            """)
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt_template
        )
        
        # Adjust settings based on model type
        max_iterations = 15 if model_config["provider"] in ["openai", "anthropic", "together"] else 8
        max_time = 120 if model_config["provider"] in ["openai", "anthropic", "together"] else 60
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            max_execution_time=max_time,
            return_intermediate_steps=True,
            early_stopping_method="generate"
        )
    
    def process_query(self, query: str) -> str:
        """Process user query and return response"""
        try:
            # For simple questions about trade agreements, try direct processing first
            if any(keyword in query.lower() for keyword in 
                ['agreement', 'trade', 'policy', 'free trade', 'nafta', 'usmca', 'israel']):
                try:
                    result = self.rag_tool.ask_question(query)
                    if result['answer'] and len(result['answer']) > 50:  # Good answer found
                        return f"Based on HTS documentation:\n\n{result['answer']}"
                except Exception as e:
                    print(f"Direct RAG search failed: {e}")
                    pass  # Fall back to agent
            
            # Use the agent for complex queries
            response = self.agent.invoke({"input": query})
            return response.get("output", "I apologize, but I couldn't process your query properly. Please try rephrasing your question.")
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print(error_msg)
            
            # Fallback: try direct RAG search
            try:
                result = self.rag_tool.ask_question(query)
                return f"Here's what I found in the documentation:\n\n{result['answer']}"
            except:
                return "I'm having trouble processing your request. Please check that the system is properly initialized and try again."
    
    def quick_duty_calculation(self, hts_code: str, cost: float, 
                             freight: float, insurance: float, 
                             quantity: int, unit_weight: float) -> str:
        """Quick duty calculation without agent"""
        try:
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
        except Exception as e:
            return f"Error calculating duty: {str(e)}"

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