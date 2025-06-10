# 🚢 HTS TariffBot - AI-Powered Multi-Tool Agent

An intelligent assistant for U.S. International Trade Commission (USITC) Harmonized Tariff Schedule (HTS) data, powered by open-source LLMs.

## 🌟 Features

### 🔹 RAG-Based Question Answering
- Query HTS General Notes documentation
- Answer trade policy and agreement questions
- Semantic search through official HTS documents

### 🔹 HTS Duty Calculator
- Calculate duties for any HTS code
- Support for multiple duty rate formats (%, ¢/kg, $/unit)
- Complete landed cost breakdown
- Batch processing capabilities

### 🔹 Multi-Tool Agent
- Intelligent query routing
- Conversational interface
- Memory of previous interactions
- User-friendly Streamlit interface

## 🏗️ Architecture

```
├── config.py              # Configuration settings
├── data_ingestion.py      # HTS data download and processing
├── rag_tool.py           # RAG question answering tool
├── duty_calculator.py    # HTS duty calculation tool
├── hts_agent.py          # Main agent orchestrator
├── app.py               # Streamlit user interface
├── setup.py             # Setup and installation script
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) for local LLM inference

### Installation

1. **Clone and setup:**
```bash
git clone <repository>
cd hts-tariffbot
python setup.py
```

2. **Install and start Ollama:**
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull llama2:7b
```

3. **Run the application:**
```bash
streamlit run app.py
```

## 📊 Usage Examples

### Ask Questions
```
"What is United States-Israel Free Trade?"
"How does the GSP (Generalized System of Preferences) work?"
"What are the special provisions for NAFTA countries?"
```

### Calculate Duties
```
HTS Code: 0101.21.00
Product Cost: $1,000
Freight: $100
Insurance: $50
Quantity: 10
Unit Weight: 100kg
```

### Batch Processing
Upload a CSV file with multiple products for automated duty calculations.

## 🛠️ Technical Details

### Core Components

#### 1. RAG Tool (`rag_tool.py`)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Store**: ChromaDB for document storage
- **LLM**: Ollama (Llama2/Mistral)
- **Framework**: LangChain ConversationalRetrievalChain

#### 2. Duty Calculator (`duty_calculator.py`)
- **Database**: SQLite for HTS tariff data
- **Parsing**: Regex-based duty rate parsing
- **Formats**: Percentage (%), Cents per kg (¢/kg), Dollars per unit ($/unit)
- **Enhancement**: Country code expansion, data cleaning

#### 3. HTS Agent (`hts_agent.py`)
- **Framework**: LangChain ReAct Agent
- **Tools**: RAG search, Duty calculation
- **Routing**: Intelligent query type detection
- **Memory**: Conversation buffer for context

### Data Processing

#### HTS Data Sources
- **General Notes**: PDF documentation from hts.usitc.gov
- **Tariff Data**: CSV files from HTS sections
- **Enhancement**: Country codes → full names, data standardization

#### Vector Database
- **Chunking**: Recursive character text splitter
- **Chunk Size**: 1000 characters with 200 overlap
- **Storage**: Persistent ChromaDB database

## 🎯 Agent Personality

**TariffBot** operates with the following principles:

1. **Accuracy**: Provides clear, compliant, and factual answers
2. **Precision**: Explains all applicable duties and cost components
3. **Transparency**: Defers when information is ambiguous or unsupported
4. **Compliance**: Never speculates or makes unsupported policy interpretations

## 📁 Data Structure

### Product Information
```python
@dataclass
class ProductInfo:
    hts_code: str
    cost: float
    freight: float
    insurance: float
    quantity: int
    unit_weight: float
    country_of_origin: str = "CN"
```

### Duty Calculation Result
```python
@dataclass
class DutyCalculation:
    hts_code: str
    product_description: str
    cif_value: float
    duty_rate: str
    duty_amount: float
    total_landed_cost: float
    duty_type: str
    breakdown: Dict[str, float]
```

## 🔧 Configuration

Edit `config.py` to customize:

- **LLM Model**: Change Ollama model (llama2:7b, mistral:7b, etc.)
- **Embedding Model**: Modify sentence transformer model
- **Chunk Settings**: Adjust text splitting parameters
- **Database Paths**: Modify storage locations

## 🚨 Limitations

- **Data Dependency**: Requires HTS data download and processing
- **Local LLM**: Performance depends on local compute resources
- **Policy Interpretation**: Does not provide legal advice or policy interpretations
- **Data Currency**: HTS data accuracy depends on source updates

## 🔮 Future Enhancements

- [ ] Support for all HTS sections (currently Section I)
- [ ] Export results to Excel/PDF
- [ ] Integration with additional trade databases
- [ ] Advanced duty calculation features (VAT, shipping fees)
- [ ] Multi-language support
- [ ] API endpoint development

## 📝 Sample Calculation

```
HTS Code: 0101.21.00
Product: Live horses - Pure-bred breeding animals

Cost Breakdown:
- Product Cost: $1,000.00
- Freight: $100.00
- Insurance: $50.00
- CIF Value: $1,150.00

Duty Calculation:
- Duty Rate: Free
- Duty Type: free
- Duty Amount: $0.00

Total Landed Cost: $1,150.00
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open-source and available under the MIT License.

## 🙏 Acknowledgments

- U.S. International Trade Commission for HTS data
- Ollama team for local LLM infrastructure
- LangChain community for agent frameworks
- Streamlit for the user interface framework

---

**Disclaimer**: This tool is for informational purposes only and does not constitute legal or professional trade advice. Always consult with qualified trade professionals for official import/export decisions.