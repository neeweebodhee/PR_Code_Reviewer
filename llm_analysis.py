import os
import time
from langchain_ollama import OllamaLLM  # Updated import
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate

# Initialize Ollama with local server
llm = OllamaLLM(base_url="http://172.20.10.64:11435", model="qwen:1.8b")  # Using Qwen 1.8B model

# Define temp directory for storing files
TEMP_DIR = "temp"

# Ensure temp folder exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def get_unique_filename(base_name, extension):
    """Generates a unique filename inside the temp directory."""
    timestamp = int(time.time())  # Unique identifier
    return os.path.join(TEMP_DIR, f"{base_name}_{timestamp}{extension}")

def analyze_with_llm(diff_file):
    """Uses Ollama to analyze code differences and provide structured review insights."""
    if not os.path.exists(diff_file):
        return "⚠️ Diff report file not found!"

    with open(diff_file, "r", encoding="utf-8") as f:
        diff_content = f.read()

    # Define prompt template for structured code analysis
    prompt_template = PromptTemplate(
        input_variables=["diff"],
        template="""
    Analyze the following Git diff and provide a structured review for all separately. If multiple files are present, analyze them **individually headings** and provide a **final summary**.

    ### **Code Changes:**
    {diff}

    ### **Review Process:**
    - Identify and extract each file section.
    - Analyze **each file separately**, listing the issues, risks, and concerns.
    - After reviewing all files, provide a **consolidated summary**.

    ### **Review Criteria Per File:**
    #### **1. Functionality Analysis**
    - Identify logical inconsistencies or broken flows.
    - Verify if the changes align with expected behavior and do not introduce regressions.

    #### **2. Code Quality & Optimization**
    - Assess maintainability, readability, and adherence to best practices.
    - Evaluate efficiency, redundancy, and unnecessary complexity.

    #### **3. Security Assessment (NIST Levels 1 & 2)**
    - **Level 1 (Basic Security Checks):** Detect common vulnerabilities (e.g., injection risks, hardcoded credentials, improper input validation).
    - **Level 2 (Advanced Security Compliance - NIST):** Analyze authentication mechanisms, encryption, and privilege escalation risks.

    #### **4. Null Handling & Future Risk Assessment**
    - Identify unhandled edge cases and potential null reference errors.
    - Ensure defensive coding techniques prevent crashes.

    ### **Instructions**
    - **DO NOT** suggest alternative code or modifications.
    - **STRICTLY** review and analyze each file individually.
    - After analyzing all files, provide a final summary.

    ### **Overall Summary**
    - **Most Critical Issues:** [List top concerns across all files]
    - **Final Recommendation:** (Safe, Needs Review, High Risk)
    """
    )

    # Use the new RunnableSequence API
    chain = RunnableSequence(prompt_template | llm)
    response = chain.invoke({"diff": diff_content})  # Get LLM output text

    return response  # Return the generated text instead of saving to file

