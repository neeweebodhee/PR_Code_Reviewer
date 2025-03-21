import streamlit as st
import os
import zipfile
import re
from io import BytesIO
from git_hub_pr_utils import get_open_pr_numbers, get_pr_diff, extract_function_changes
from llm_analysis import analyze_with_llm

# Temp Directory
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

st.title("GitHub PR Function Change Tracker")
st.markdown("### Fetch and analyze function changes from open pull requests.")

# Store PR reports in session state
if "pr_reports" not in st.session_state:
    st.session_state.pr_reports = {}
if "llm_reports" not in st.session_state:
    st.session_state.llm_reports = {}

# Function to extract owner and repo name from URL
def extract_repo_details(repo_url):
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", repo_url)
    if match:
        return match.group(1), match.group(2)
    return None, None

# Input fields
repo_url = st.text_input("Enter GitHub Repository URL (Optional)", value="")
repo_owner, repo_name = "", ""

if repo_url:
    repo_owner, repo_name = extract_repo_details(repo_url)
    if repo_owner and repo_name:
        st.success(f"Extracted Repository: {repo_owner}/{repo_name}")
    else:
        st.error("Invalid GitHub URL format. Please enter a valid GitHub repository link.")

repo_owner = st.text_input("Enter Repository Owner", value=repo_owner)
repo_name = st.text_input("Enter Repository Name", value=repo_name)

if st.button("Fetch Open PRs"):
    if not repo_name:
        st.error("Please enter a repository name.")
    else:
        open_prs = get_open_pr_numbers(repo_owner, repo_name)
        
        if open_prs:
            st.success(f"Found {len(open_prs)} open PR(s).")
            for pr_number, title in open_prs:
                diff_text = get_pr_diff(repo_owner, repo_name, pr_number)
                if diff_text:
                    changes = extract_function_changes(diff_text)
                    report_text = f"Pull Request #{pr_number}: {title}\n" + "="*50 + "\n\n"
                    
                    if changes:
                        for item in changes:
                            report_text += f"File: {item['file']}\n" + "-"*len(item['file']) + "\n"
                            for change in item["changes"]:
                                sign = "+" if change["type"] == "added" else "-"
                                report_text += f"{sign} {change['line']}\n"
                            report_text += "\n"
                    else:
                        report_text += "No function changes detected.\n"
                    
                    st.session_state.pr_reports[pr_number] = report_text
        else:
            st.warning("No open pull requests found.")

for pr_number, report_text in st.session_state.pr_reports.items():
    with st.expander(f"PR #{pr_number}"):
        st.text_area(f"PR #{pr_number} Report", report_text, height=200)
        
        # LLM Analysis Button
        if st.button(f"Run LLM Analysis for PR #{pr_number}", key=f"llm_{pr_number}"):
            temp_diff_file = os.path.join(TEMP_DIR, f"pr_{pr_number}_diff.txt")
            with open(temp_diff_file, "w", encoding="utf-8") as f:
                f.write(report_text)
            
            llm_report_content = analyze_with_llm(temp_diff_file)
            st.session_state.llm_reports[pr_number] = llm_report_content
            
            # Save LLM Report as Markdown
            md_file_path = os.path.join(TEMP_DIR, f"PR_{pr_number}_Analysis.md")
            with open(md_file_path, "w", encoding="utf-8") as md_file:
                md_file.write(llm_report_content)
            st.session_state[f"md_file_{pr_number}"] = md_file_path
        
        # Display LLM Analysis if available
        if pr_number in st.session_state.llm_reports:
            st.text_area(f"LLM Analysis - PR #{pr_number}", st.session_state.llm_reports[pr_number], height=300)
            
            # Download LLM Analysis Markdown File
            md_file_path = st.session_state.get(f"md_file_{pr_number}", "")
            if md_file_path and os.path.exists(md_file_path):
                with open(md_file_path, "rb") as md_file:
                    st.download_button(
                        label="📥 Download Analysis as Markdown",
                        data=md_file,
                        file_name=f"PR_{pr_number}_Analysis.md",
                        mime="text/markdown"
                    )

# Download All PR Reports as ZIP
if st.session_state.pr_reports:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for pr_number, report_text in st.session_state.pr_reports.items():
            zipf.writestr(f"PR_{pr_number}_Report.txt", report_text)
    zip_buffer.seek(0)
    st.download_button(label="📥 Download All PR Reports as ZIP",
                       data=zip_buffer,
                       file_name="All_PR_Reports.zip",
                       mime="application/zip")
