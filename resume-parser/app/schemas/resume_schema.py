"""Validated public resume response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CandidateInformation(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    email: str | None = None
    linkedin: str | None = None
    phoneNum: str | None = None
    languages: list[str] = Field(default_factory=list)
    frameworks_libraries: list[str] = Field(default_factory=list, alias="frameworks/libraries")
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)


class Project(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str
    summary: str
    problem: str | None = None
    solution: str | None = None
    technologies: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    role: str | None = None
    duration: str | None = None
    results: str | None = None


class Resume(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    email: str | None = None
    linkedin: str | None = None
    phoneNum: str | None = None
    languages: list[str] = Field(default_factory=list)
    frameworks_libraries: list[str] = Field(default_factory=list, alias="frameworks/libraries")
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: Resume


class SkillsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: CandidateInformation


class ProjectsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projects: list[Project] = Field(default_factory=list)


class ProjectsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: ProjectsData
