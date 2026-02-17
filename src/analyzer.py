import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

env_path = Path(__file__).parent / '.env'
load_dotenv()

class AnalyzeLogs:
    """
        Generate analysis of the conversation logs.
    """

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = base_dir
        
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'analysis'
        self.analysis_dir.mkdir(exist_ok = True)

        # ---------------- LLM ----------------
        self.model = 'gemini-2.5-flash-lite'
        self.llm = ChatGoogleGenerativeAI(
            model = self.model,
            temperature = 0.3,  # Low temperature typically tends to be more deterministic and focused.
            streaming = False,
            api_key = os.getenv('GOOGLE_API_KEY'),
        )
        # ---------------------------------------   

    def get_summary_prompt(self, log_content: str, scenario: str, run_number: int) -> str:
        return f"""You are an expert QA analyst reviewing a conversation log from from a stress-test call to an AI operator at Pivot Point Orthopedics clinic. 
        Your task is to generate a comprehensive, structured summary that identifies bugs, evaluates quality, and documents findings.

        **CONTEXT**
        - Scenario: {scenario}
        - Run Number: {run_number}
        - This was a stress-test call where a patient bot (Bipin) tested the AI operator for edge cases, bugs, and quality issues.

        **CONVERSATION LOG:**
        {log_content}

        **YOUR TASK:**
        Generate a detailed summary in the following structured format. Be thorough, objective, and specific. Cite exact quotes from the convresation when identifying issues.

        ## SUMMARY FORMAT:

        ### 1. CONVERSATION OVERVIEW
        - **Objective**: What was the patient trying to accomplish?
        - **Outcome**: Was the objective achieved? (Yes/No/Partially)

        ### 2. STRESS TEST TACTICS USED
        List all stress-test tactics that were attempted (e.g., rapid topic changes, contradictory information, boundary conditions, etc.)
        
        ### 3. BUGS IDENTIFIED
        For each bug found, provide:
        - **Bug Type**: (Hallucination / Memory Failure / Error Handling / Misunderstanding / Awkward Phrasing / Conversational Flow / Other)
        - **Description**: Clear description of the issue
        - **Evidence**: Exact quote(s) from the conversation showing the bug
        - **Severity**: (Critical / High / Medium / Low)
        - **Impact**: How this bug affects user experience or system reliability

        ### 4. OPERATOR PERFORMANCE EVALUATION

        #### 4.1 Strengths
        - What did the operator handle well?
        - Any positive behaviors or responses?

        #### 4.2 Weaknesses
        - Where did the operator struggle?
        - What patterns of failure emerged?

        ### 4.3 Hallucinations Detection
        - Did the operator make up information? (Yes/No)
        - If yes, list specific instances with quotes.
        - Did the operator correctly say "I don't know" when appropriate?

        #### 4.4 Memory & Context Retention
        - Did the operator remember information from earlier in the conversation?
        - Any contradictions or memory failures?
        - Did the operator lose track of conversation threads?

        #### 4.5 Error Handling
        - How did the operator handle invalid inputs (wrong dates, times, names)?
        - Did the operator provide helpful error messages?
        - Did the operator gracefully handle edge cases?

        #### 4.6 Conversational Flow
        - Was the conversation natural and coherent?
        - Did the operator handle interruptions well?
        - Any awkward phrasing or robotic responses?

        ### 5. EDGE CASE TESTING RESULTS
        For each edge case tested, document:
        - **Edge Case**: Description of what was tested
        - **Operator Response**: How the operator handled it
        - **Result**: (Passed / Failed / Partially Handled)
        - **Notes**: Additional observations

        ### 6. LANGUAGE & COMMUNICATION
        - Language used (English/Hindi/Other)
        - Any language barriers or communication issues?
        - Clarity of operator responses

        ### 7. KEY QUOTES
        Extract 3-5 most significant quotes that demonstrate:
        - Critical bugs
        - Operator strengths
        - Operator failures
        - Interesting edge case handling

        ### 8. RECOMMENDATIONS
        - **Immediate Fixes**: Critical bugs that need urgent attention
        - **Improvements**: Areas for enhancement
        - **Testing Gaps**: Edge cases that weren't adequately tested
        - **Follow-up Tests**: Additional scenarios to test based on findings

        ### 9. OVERALL ASSESSMENT
        - **Quality Score**: Rate operator performance 1-10 (10 = excellent)
        - **Reliability**: Can this operator be trusted in production? (Yes/No/With Conditions)
        - **Summary Statement**: One paragraph overall assessment

        **IMPORTANT GUIDELINES:**
        - Be objective and evidence-based - cite specific quotes
        - Distinguish between actual bugs and minor issues
        - Focus on actionable findings
        - If no bugs were found, explicitly state this
        - Be thorough but concise
        - Use clear, professional language
        - Highlight the most critical issues first

        Generate the summary now:"""

    def analyze_log(self, log_file: Path) -> str:
        """
            Analyze a single log file and generate a summary.
        """
        try:
            with open(log_file, 'r', encoding = 'utf-8') as f:
                log_content = f.read()

            filename = log_file.stem
            parts = filename.split('_')
            scenario = parts[0] if len(parts) > 0 else 'Unknown'
            run_number = parts[2] if len(parts) > 2 else 'Unknown'

            prompt = self.get_summary_prompt(log_content, scenario, run_number)

            # Get summary from LLM
            messages = [HumanMessage(content = prompt)]
            response = self.llm.invoke(messages)
            summary = response.content

            return summary

        except Exception as e:
            return f"Error analyzing log file {log_file}: {e}"

    
    def save_summary(self, log_file: Path, summary: str):
        try:
            summary_filename = log_file.stem + '_summary.md'
            summary_path = self.analysis_dir / summary_filename

            with open(summary_path, 'w', encoding = 'utf-8') as f:
                f.write(f"Source Log: {log_file.name}\n")
                f.write("=" * 80 + "\n\n")
                f.write(summary)

            print(f"Summary saved to: {summary_path}")
            return summary_path

        except Exception as e:
            print (f"Error saving summary: {e}")
            return None

    
    def analyze_all_logs(self):
        log_files = sorted(self.logs_dir.glob('*.txt'))

        if not log_files:
            print ("No log files found in the logs directory.")
            return

        print (f"Found {len(log_files)} log files to analyze.")
        print ("Starting analysis...")

        for log_file in log_files:
            print (f"Analyzing {log_file.name}...")
            summary = self.analyze_log(log_file)
            self.save_summary(log_file, summary)

        print(f"\nAnalysis complete! Summaries saved to: {self.analysis_dir}")


if __name__ == "__main__":
    analyzer = AnalyzeLogs()
    analyzer.analyze_all_logs()