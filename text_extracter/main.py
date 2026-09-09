"""
FlexConnect Candidate Profile Extractor — main entry point.

RULE-BASED VERSION — no LLM call anywhere in this pipeline.

Pipeline:
    GitHub username -----\
    Resume file (pdf/docx) --> rule_engine (Python logic) -> JSON
    Portfolio URL --------/

At least one source must be provided. LinkedIn is not supported yet
(login-walled + JS-rendered).

Run:
    python main.py --github abinasri --resume resume.pdf --portfolio https://example.com

Any combination of the three flags is allowed, as long as at least one is given.
"""

import argparse
import json
import sys

from profile_extractor.github_source import fetch_github_data, GitHubSourceError
from profile_extractor.resume_source import fetch_resume_text, ResumeSourceError
from profile_extractor.portfolio_source import fetch_portfolio_text, PortfolioSourceError
from profile_extractor.rule_engine import build_profile_rule_based
from profile_extractor.schema import ProfileResult


def build_profile(
    github: str = None,
    resume: str = None,
    portfolio: str = None,
) -> ProfileResult:
    """
    Run the full rule-based pipeline for whichever sources are provided
    and return a ProfileResult (never raises — errors are captured in
    the result).
    """
    if not any([github, resume, portfolio]):
        return ProfileResult(
            success=False,
            sources_used=[],
            error="No source provided — pass at least one of github/resume/portfolio.",
        )

    github_data = None
    resume_text = None
    portfolio_text = None
    sources_used = []
    source_errors = []

    if github:
        try:
            github_data = fetch_github_data(github)
            sources_used.append("github")
        except GitHubSourceError as e:
            source_errors.append(f"GitHub: {e}")

    if resume:
        try:
            resume_text = fetch_resume_text(resume)
            sources_used.append("resume")
        except ResumeSourceError as e:
            source_errors.append(f"Resume: {e}")

    if portfolio:
        try:
            portfolio_text = fetch_portfolio_text(portfolio)
            sources_used.append("portfolio")
        except PortfolioSourceError as e:
            source_errors.append(f"Portfolio: {e}")

    if not sources_used:
        return ProfileResult(
            success=False,
            sources_used=[],
            error="All sources failed: " + " | ".join(source_errors),
        )

    try:
        profile = build_profile_rule_based(
            github_data=github_data,
            github_input=github,
            resume_text=resume_text,
            portfolio_text=portfolio_text,
            portfolio_url=portfolio,
        )
    except Exception as e:
        # Rule-based building is pure Python — a failure here means a
        # genuine bug, not a bad external response, so surface it plainly.
        return ProfileResult(
            success=False, sources_used=sources_used, error=f"Profile building failed: {e}"
        )

    result = ProfileResult(success=True, sources_used=sources_used, profile=profile)

    if source_errors:
        result.error = "Partial success — some sources failed: " + " | ".join(source_errors)

    return result


def main():
    parser = argparse.ArgumentParser(description="FlexConnect candidate profile extractor (rule-based)")
    parser.add_argument("--github", help="GitHub username or profile URL")
    parser.add_argument("--resume", help="Path to a resume file (.pdf or .docx)")
    parser.add_argument("--portfolio", help="Portfolio website URL")
    args = parser.parse_args()

    if not any([args.github, args.resume, args.portfolio]):
        print("Provide at least one of: --github, --resume, --portfolio")
        sys.exit(1)

    result = build_profile(github=args.github, resume=args.resume, portfolio=args.portfolio)
    print(json.dumps(result.model_dump(), indent=2))

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
